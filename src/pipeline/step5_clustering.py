"""
Step 5: 主题聚类 - 将相关片段聚合为合集
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

from ..utils.llm_factory import LLMFactory
from ..config import PROMPT_FILES, METADATA_DIR, MAX_CLIPS_PER_COLLECTION

logger = logging.getLogger(__name__)

class ClusteringEngine:
    """主题聚类引擎"""
    
    def __init__(self, metadata_dir: Optional[Path] = None, prompt_files: Dict = None):
        self.llm_client = LLMFactory.get_default_client()
        
        # 加载提示词
        prompt_files_to_use = prompt_files if prompt_files is not None else PROMPT_FILES
        with open(prompt_files_to_use['clustering'], 'r', encoding='utf-8') as f:
            self.clustering_prompt = f.read()
        
        # 使用传入的metadata_dir或默认值
        if metadata_dir is None:
            metadata_dir = METADATA_DIR
        self.metadata_dir = metadata_dir
    
    def cluster_clips(self, clips_with_titles: List[Dict]) -> List[Dict]:
        """
        对片段进行主题聚类
        
        Args:
            clips_with_titles: 带标题的片段列表
            
        Returns:
            合集数据列表
        """
        logger.info("开始进行主题聚类...")
        
        # 准备聚类数据
        clips_for_clustering = []
        for clip in clips_with_titles:
            clips_for_clustering.append({
                'id': clip['id'],
                'title': clip.get('generated_title', clip['outline']),
                'summary': clip.get('recommend_reason', ''),
                'score': clip.get('final_score', 0)
            })
        
        logger.info(f"📊 [聚类数据准备] 准备聚类数据，共{len(clips_for_clustering)}个片段")
        logger.debug(f"📄 [片段数据详情] 片段列表: {json.dumps(clips_for_clustering, ensure_ascii=False, indent=2)[:1000]}...")
        
        # 首先进行基于关键词的预聚类
        pre_clusters = self._pre_cluster_by_keywords(clips_for_clustering)
        
        # 构建完整的提示词
        full_prompt = self.clustering_prompt + "\n\n以下是视频切片列表：\n"
        for i, clip in enumerate(clips_for_clustering, 1):
            full_prompt += f"{i}. 标题：{clip['title']}\n   摘要：{clip['summary']}\n   评分：{clip['score']:.2f}\n\n"
        
        # 添加预聚类结果作为参考
        if pre_clusters:
            full_prompt += "\n\n基于关键词的预聚类结果（仅供参考）：\n"
            for theme, clip_ids in pre_clusters.items():
                full_prompt += f"{theme}: {', '.join(clip_ids)}\n"
    
        try:
            # 调用大模型进行聚类
            logger.info(f"🚀 [聚类开始] 调用LLM进行主题聚类，待处理片段数: {len(clips_for_clustering)}")
            logger.info(f"📄 [提示词长度]: {len(full_prompt)} 字符")
            logger.debug(f"📄 [提示词预览]: {full_prompt[:500]}...")
            
            response = self.llm_client.call_with_retry(full_prompt)
            
            logger.info(f"✅ [聚类响应成功] 获得LLM响应，长度: {len(response) if response else 0} 字符")
            # 记录完整的LLM响应用于调试
            if response:
                logger.debug(f"📄 [聚类完整响应]: {response}")
            else:
                logger.warning("⚠️ [聚类响应为空] LLM返回空响应")
                return self._create_default_collections(clips_with_titles)
            
            # 解析JSON响应
            logger.info(f"🔍 [开始解析] 解析LLM聚类响应...")
            collections_data = self.llm_client.parse_json_response(response)
            
            # 记录解析后的数据
            logger.info(f"✅ [解析完成] 解析后的合集数据数量: {len(collections_data) if isinstance(collections_data, list) else 'N/A'}")
            if collections_data is not None:
                if isinstance(collections_data, list):
                    logger.debug(f"📄 [解析后数据预览]: {json.dumps(collections_data[:3] if len(collections_data) > 3 else collections_data, ensure_ascii=False, indent=2)}")
                else:
                    logger.warning(f"⚠️ [解析数据类型异常] 解析结果不是列表类型: {type(collections_data)}")
                    logger.debug(f"📄 [解析结果内容]: {str(collections_data)[:500]}")
            else:
                logger.warning("⚠️ [解析结果为空] 解析后的collections_data为None")
                # 尝试直接解析response
                try:
                    direct_parse = json.loads(response)
                    logger.info(f"🔄 [直接解析成功] 直接解析response得到的数据类型: {type(direct_parse)}")
                    logger.debug(f"📄 [直接解析数据]: {json.dumps(direct_parse, ensure_ascii=False, indent=2)[:500]}")
                    collections_data = direct_parse
                except json.JSONDecodeError as je:
                    logger.error(f"❌ [直接解析失败] 无法直接解析response为JSON: {str(je)}")
                    logger.debug(f"📄 [原始响应内容]: {response}")
            
            # 验证和清理合集数据
            validated_collections = self._validate_collections(collections_data, clips_with_titles)
            
            # 如果LLM聚类结果不理想，使用预聚类结果
            if len(validated_collections) < 3:
                logger.warning("LLM聚类结果不理想，使用预聚类结果")
                validated_collections = self._create_collections_from_pre_clusters(pre_clusters, clips_with_titles)
            
            logger.info(f"主题聚类完成，共{len(validated_collections)}个合集")
            return validated_collections
            
        except Exception as e:
            logger.error(f"主题聚类失败: {str(e)}")
            logger.exception(e)
            # 使用预聚类结果作为备选
            if pre_clusters:
                logger.info("使用预聚类结果作为备选方案")
                return self._create_collections_from_pre_clusters(pre_clusters, clips_with_titles)
            # 返回默认聚类结果
            return self._create_default_collections(clips_with_titles)
    
    def _pre_cluster_by_keywords(self, clips: List[Dict]) -> Dict[str, List[str]]:
        """
        基于关键词进行预聚类
        
        Args:
            clips: 片段列表
            
        Returns:
            预聚类结果
        """
        # 定义主题关键词
        theme_keywords = {
            '投资理财': ['投资', '理财', '股票', '基金', '炒股', '赚钱', '收益', '涨跌', '解套', '散户', 'A股', '北交所', '中免', '种业'],
            '职场成长': ['职场', '工作', '技能', '学习', '日语', '董秘', '逆袭', '教育', '大学生', '财商'],
            '社会观察': ['社会', '现象', '网络', '乱象', '垃圾', '分类', '平台', '机制', '主播', '行业'],
            '文化差异': ['文化', '差异', '欧美', '日本', '韩国', '饮食', '语言', '狐臭', '蒸锅', '邮轮'],
            '直播互动': ['直播', '互动', '弹幕', '粉丝', '舰长', '打赏', '连麦', 'PK', '抽奖'],
            '情感关系': ['恋爱', '情感', '社交', '搭讪', '关系', '心理', '心动', '冷淡'],
            '健康生活': ['健康', '运动', '跑步', '饮食', '牛奶', '生活方式', '锻炼'],
            '创作平台': ['创作', '平台', 'B站', '小红书', '摄影', '内容', '运营', '自媒体']
        }
        
        pre_clusters = {theme: [] for theme in theme_keywords.keys()}
        
        for clip in clips:
            # 合并标题和摘要进行关键词匹配
            text = f"{clip['title']} {clip['summary']}".lower()
            
            # 计算每个主题的匹配分数
            theme_scores = {}
            for theme, keywords in theme_keywords.items():
                score = sum(1 for keyword in keywords if keyword in text)
                if score > 0:
                    theme_scores[theme] = score
            
            # 选择匹配分数最高的主题
            if theme_scores:
                best_theme = max(theme_scores.keys(), key=lambda k: theme_scores[k])
                pre_clusters[best_theme].append(clip['id'])
        
        # 过滤掉空的主题
        return {theme: clip_ids for theme, clip_ids in pre_clusters.items() if len(clip_ids) >= 2}
    
    def _create_collections_from_pre_clusters(self, pre_clusters: Dict[str, List[str]], clips_with_titles: List[Dict]) -> List[Dict]:
        """
        从预聚类结果创建合集
        
        Args:
            pre_clusters: 预聚类结果
            clips_with_titles: 片段数据
            
        Returns:
            合集数据列表
        """
        collections = []
        collection_id = 1
        
        # 主题标题映射
        theme_titles = {
            '投资理财': '投资理财启示',
            '职场成长': '职场成长记', 
            '社会观察': '社会观察笔记',
            '文化差异': '文化差异趣谈',
            '直播互动': '直播互动现场',
            '情感关系': '情感与关系',
            '健康生活': '健康生活方式',
            '创作平台': '创作与平台生态'
        }
        
        # 主题简介映射
        theme_summaries = {
            '投资理财': '通过生活化案例分享投资理念，兼具实用与共鸣。',
            '职场成长': '探讨职业发展、技能提升与职场心态变化。',
            '社会观察': '理性点评社会现象与网络乱象，观点鲜明。',
            '文化差异': '从饮食到语言，展现跨文化交流的趣味视角。',
            '直播互动': '还原真实直播间互动场景，展现主播临场反应。',
            '情感关系': '解析恋爱心理、社交困惑与情感共鸣话题。',
            '健康生活': '分享运动、饮食、心理调适等健康管理经验。',
            '创作平台': '剖析内容创作困境与平台机制，适合创作者参考。'
        }
        
        for theme, clip_ids in pre_clusters.items():
            # 限制每个合集的片段数量
            if len(clip_ids) > MAX_CLIPS_PER_COLLECTION:
                clip_ids = clip_ids[:MAX_CLIPS_PER_COLLECTION]
            
            collections.append({
                'id': str(collection_id),
                'collection_title': theme_titles.get(theme, theme),
                'collection_summary': theme_summaries.get(theme, f'{theme}相关精彩片段合集'),
                'clip_ids': clip_ids
            })
            collection_id += 1
        
        return collections
    
    def _validate_collections(self, collections_data: List[Dict], clips_with_titles: List[Dict]) -> List[Dict]:
        """
        验证和清理合集数据
        
        Args:
            collections_data: 原始合集数据
            clips_with_titles: 片段数据
            
        Returns:
            验证后的合集数据
        """
        logger.info(f"🔍 [开始验证] 验证合集数据，原始合集数量: {len(collections_data) if collections_data else 0}")
        
        # 记录所有实际可用的片段标题供调试
        all_actual_titles = []
        for clip in clips_with_titles:
            generated_title = clip.get('generated_title', clip['outline'])
            outline = clip['outline']
            all_actual_titles.append({
                'generated_title': generated_title,
                'outline': outline,
                'id': clip['id']
            })
        
        logger.debug(f"📚 [实际片段标题] 所有可用片段标题: {json.dumps(all_actual_titles, ensure_ascii=False, indent=2)}")
        
        # 检查collections_data是否为None或不是列表
        if collections_data is None:
            logger.warning("⚠️ [验证数据为空] collections_data为None")
            return []
        
        if not isinstance(collections_data, list):
            logger.warning(f"⚠️ [验证数据类型错误] collections_data不是列表类型，实际类型: {type(collections_data)}")
            logger.debug(f"📄 [验证数据内容]: {str(collections_data)[:1000]}")
            return []
        
        logger.debug(f"📄 [原始合集数据]: {json.dumps(collections_data, ensure_ascii=False, indent=2)[:1000]}...")
        
        validated_collections = []
        
        for i, collection in enumerate(collections_data):
            try:
                logger.info(f"🔍 [验证合集 {i}] 开始验证第 {i} 个合集")
                logger.debug(f"📄 [合集 {i} 原始数据]: {json.dumps(collection, ensure_ascii=False, indent=2) if isinstance(collection, dict) else str(collection)}")
                
                # 检查collection是否为字典类型
                if not isinstance(collection, dict):
                    logger.warning(f"⚠️ [合集 {i} 类型错误] 合集数据不是字典类型，实际类型: {type(collection)}")
                    continue
                
                # 验证必需字段
                required_fields = ['collection_title', 'collection_summary', 'clips']
                missing_fields = [key for key in required_fields if key not in collection]
                
                if missing_fields:
                    logger.warning(f"⚠️ [合集 {i} 缺少字段] 缺少必需字段: {missing_fields}")
                    logger.debug(f"📄 [合集 {i} 实际字段]: {list(collection.keys())}")
                    logger.debug(f"📄 [合集 {i} 完整数据]: {json.dumps(collection, ensure_ascii=False, indent=2)}")
                    continue
                
                logger.info(f"✅ [合集 {i} 字段验证通过] 包含所有必需字段")
                
                # 验证片段列表
                clip_titles = collection['clips']
                logger.info(f"🔍 [合集 {i} 片段验证] 片段标题数量: {len(clip_titles) if isinstance(clip_titles, list) else 'N/A'}")
                logger.debug(f"📄 [合集 {i} 片段标题]: {clip_titles}")
                
                # 检查clips是否为列表类型
                if not isinstance(clip_titles, list):
                    logger.warning(f"⚠️ [合集 {i} 片段类型错误] clips字段不是列表类型，实际类型: {type(clip_titles)}")
                    logger.debug(f"📄 [合集 {i} clips字段内容]: {str(clip_titles)}")
                    continue
                
                valid_clip_ids = []
                
                for j, clip_title in enumerate(clip_titles):
                    logger.debug(f"🔍 [合集 {i} 片段 {j}] 查找片段标题: '{clip_title}'")
                    # 根据标题找到对应的片段ID
                    found_clip = None
                    
                    # 清理LLM返回的标题（去除多余空格和特殊字符）
                    cleaned_clip_title = clip_title.strip()
                    # 去除可能的引号
                    if cleaned_clip_title.startswith('"') and cleaned_clip_title.endswith('"'):
                        cleaned_clip_title = cleaned_clip_title[1:-1]
                    if cleaned_clip_title.startswith("'") and cleaned_clip_title.endswith("'"):
                        cleaned_clip_title = cleaned_clip_title[1:-1]
                    
                    # 处理可能的Unicode字符问题
                    import unicodedata
                    cleaned_clip_title = unicodedata.normalize('NFKC', cleaned_clip_title)
                    
                    logger.debug(f"   清理后标题: '{cleaned_clip_title}'")
                    logger.debug(f"   原始标题ASCII码: {[ord(c) for c in clip_title]}")
                    logger.debug(f"   清理后标题ASCII码: {[ord(c) for c in cleaned_clip_title]}")
                    
                    # 记录所有实际片段标题的详细信息
                    logger.debug(f"   实际片段标题列表:")
                    for k, clip in enumerate(clips_with_titles):
                        generated_title = clip.get('generated_title', clip['outline'])
                        outline = clip['outline']
                        # 清理实际的标题
                        cleaned_generated_title = generated_title.strip()
                        cleaned_outline = outline.strip()
                        
                        # 处理Unicode字符
                        cleaned_generated_title = unicodedata.normalize('NFKC', cleaned_generated_title)
                        cleaned_outline = unicodedata.normalize('NFKC', cleaned_outline)
                        
                        logger.debug(f"     片段{k} - Generated: '{generated_title}' (清理后: '{cleaned_generated_title}')")
                        logger.debug(f"     片段{k} - Outline: '{outline}' (清理后: '{cleaned_outline}')")
                        logger.debug(f"     片段{k} - Generated ASCII: {[ord(c) for c in generated_title]}")
                        logger.debug(f"     片段{k} - Outline ASCII: {[ord(c) for c in outline]}")
                    
                    # 尝试多种匹配策略
                    for clip in clips_with_titles:
                        generated_title = clip.get('generated_title', clip['outline'])
                        outline = clip['outline']
                        
                        # 清理实际的标题
                        cleaned_generated_title = generated_title.strip()
                        cleaned_outline = outline.strip()
                        
                        # 处理Unicode字符
                        cleaned_generated_title = unicodedata.normalize('NFKC', cleaned_generated_title)
                        cleaned_outline = unicodedata.normalize('NFKC', cleaned_outline)
                        
                        logger.debug(f"   比较: '{cleaned_clip_title}' vs '{cleaned_generated_title}' | '{cleaned_outline}'")
                        
                        # 策略1: 精确匹配（忽略首尾空格）
                        if (cleaned_clip_title.strip() == cleaned_generated_title.strip() or 
                            cleaned_clip_title.strip() == cleaned_outline.strip()):
                            found_clip = clip
                            logger.info(f"✅ [合集 {i} 片段 {j} 精确匹配成功] 使用精确匹配找到片段")
                            break
                        
                        # 策略2: 去除标点符号后匹配
                        import re
                        def remove_punctuation(text):
                            # 移除常见的中文和英文标点符号
                            punctuation_pattern = r"""[，。！？；：""''（）【】《》、\s\.\,\!\?\;\:\"\''\(\)\[\]\<\>]*"""
                            return re.sub(punctuation_pattern, '', text).strip()
                        
                        no_punct_clip_title = remove_punctuation(cleaned_clip_title)
                        no_punct_generated_title = remove_punctuation(cleaned_generated_title)
                        no_punct_outline = remove_punctuation(cleaned_outline)
                        
                        logger.debug(f"   去标点比较: '{no_punct_clip_title}' vs '{no_punct_generated_title}' | '{no_punct_outline}'")
                        
                        if (no_punct_clip_title == no_punct_generated_title or 
                            no_punct_clip_title == no_punct_outline):
                            found_clip = clip
                            logger.info(f"✅ [合集 {i} 片段 {j} 去标点匹配成功] 使用去标点匹配找到片段")
                            break
                        
                        # 策略3: 包含匹配（LLM标题包含在实际标题中，或实际标题包含在LLM标题中）
                        if (no_punct_clip_title in no_punct_generated_title or 
                            no_punct_generated_title in no_punct_clip_title or
                            no_punct_clip_title in no_punct_outline or 
                            no_punct_outline in no_punct_clip_title):
                            found_clip = clip
                            logger.info(f"✅ [合集 {i} 片段 {j} 包含匹配成功] 使用包含匹配找到片段")
                            logger.debug(f"     包含关系: '{no_punct_clip_title}' in '{no_punct_generated_title}' or '{no_punct_generated_title}' in '{no_punct_clip_title}' or '{no_punct_clip_title}' in '{no_punct_outline}' or '{no_punct_outline}' in '{no_punct_clip_title}'")
                            break
                        
                        # 策略4: 模糊匹配（忽略标点和空格）
                        def normalize_text(text):
                            # 移除标点符号和多余空格，转换为小写
                            return re.sub(r'[^\w\s]', '', text).strip().lower()
                        
                        normalized_clip_title = normalize_text(cleaned_clip_title)
                        normalized_generated_title = normalize_text(cleaned_generated_title)
                        normalized_outline = normalize_text(cleaned_outline)
                        
                        logger.debug(f"   模糊比较: '{normalized_clip_title}' vs '{normalized_generated_title}' | '{normalized_outline}'")
                        
                        if (normalized_clip_title == normalized_generated_title or 
                            normalized_clip_title == normalized_outline):
                            found_clip = clip
                            logger.info(f"✅ [合集 {i} 片段 {j} 模糊匹配成功] 使用模糊匹配找到片段")
                            break
                    
                    if found_clip:
                        valid_clip_ids.append(found_clip['id'])
                        logger.debug(f"✅ [合集 {i} 片段 {j} 匹配成功] 找到匹配片段 ID: {found_clip['id']}")
                        logger.debug(f"   匹配详情 - LLM标题: '{clip_title}', 实际标题: '{found_clip.get('generated_title', found_clip['outline'])}'")
                    else:
                        logger.warning(f"⚠️ [合集 {i} 片段 {j} 匹配失败] 未找到匹配的片段: '{clip_title}'")
                        # 记录所有实际标题供调试
                        all_titles = [clip.get('generated_title', clip['outline']) for clip in clips_with_titles]
                        logger.debug(f"   可用标题列表: {all_titles}")
                        # 也记录清理后的标题
                        cleaned_titles = [title.strip() for title in all_titles]
                        logger.debug(f"   清理后标题列表: {cleaned_titles}")
                
                if len(valid_clip_ids) < 2:
                    logger.warning(f"⚠️ [合集 {i} 片段不足] 有效片段少于2个 ({len(valid_clip_ids)}个)，跳过")
                    continue
                
                # 限制每个合集的片段数量
                if len(valid_clip_ids) > MAX_CLIPS_PER_COLLECTION:
                    logger.info(f"✂️ [合集 {i} 片段超限] 片段数量 {len(valid_clip_ids)} 超过限制 {MAX_CLIPS_PER_COLLECTION}，截取前{MAX_CLIPS_PER_COLLECTION}个")
                    valid_clip_ids = valid_clip_ids[:MAX_CLIPS_PER_COLLECTION]
                
                validated_collection = {
                    'id': str(i + 1),
                    'collection_title': collection['collection_title'],
                    'collection_summary': collection['collection_summary'],
                    'clip_ids': valid_clip_ids
                }
                
                logger.info(f"✅ [合集 {i} 验证通过] 标题: '{validated_collection['collection_title']}', 片段数: {len(valid_clip_ids)}")
                validated_collections.append(validated_collection)
                
            except Exception as e:
                logger.error(f"❌ [验证合集 {i} 失败] 错误: {str(e)}")
                logger.exception(e)
                continue
        
        logger.info(f"✅ [验证完成] 最终有效合集数量: {len(validated_collections)}")
        return validated_collections
    
    def _create_default_collections(self, clips_with_titles: List[Dict]) -> List[Dict]:
        """
        创建默认合集（当聚类失败时）
        
        Args:
            clips_with_titles: 片段数据
            
        Returns:
            默认合集数据
        """
        logger.info("创建默认合集...")
        
        # 按评分分组
        high_score = []
        medium_score = []
        
        for clip in clips_with_titles:
            score = clip.get('final_score', 0)
            if score >= 0.8:
                high_score.append(clip)
            elif score >= 0.6:
                medium_score.append(clip)
        
        collections = []
        
        # 创建高分合集
        if len(high_score) >= 2:
            collections.append({
                'id': '1',
                'collection_title': '精选高分片段',
                'collection_summary': '评分最高的精彩片段合集',
                'clip_ids': [clip['id'] for clip in high_score[:MAX_CLIPS_PER_COLLECTION]]
            })
        
        # 创建中等分合集
        if len(medium_score) >= 2:
            collections.append({
                'id': '2',
                'collection_title': '优质内容推荐',
                'collection_summary': '精选优质内容片段',
                'clip_ids': [clip['id'] for clip in medium_score[:MAX_CLIPS_PER_COLLECTION]]
            })
        
        return collections
    
    def save_collections(self, collections_data: List[Dict], output_path: Optional[Path] = None) -> Path:
        """
        保存合集数据
        
        Args:
            collections_data: 合集数据
            output_path: 输出路径
            
        Returns:
            保存的文件路径
        """
        if output_path is None:
            output_path = self.metadata_dir / "collections.json"
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存数据
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(collections_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"合集数据已保存到: {output_path}")
        return output_path
    
    def load_collections(self, input_path: Path) -> List[Dict]:
        """
        从文件加载合集数据
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            合集数据
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)

def run_step5_clustering(clips_with_titles_path: Path, output_path: Optional[Path] = None, metadata_dir: Optional[str] = None, prompt_files: Dict = None) -> List[Dict]:
    """
    运行Step 5: 主题聚类
    
    Args:
        clips_with_titles_path: 带标题的片段文件路径
        output_path: 输出文件路径
        prompt_files: 自定义提示词文件
        
    Returns:
        合集数据
    """
    # 加载数据
    with open(clips_with_titles_path, 'r', encoding='utf-8') as f:
        clips_with_titles = json.load(f)
    
    # 创建聚类器
    if metadata_dir is None:
        metadata_dir = METADATA_DIR
    clusterer = ClusteringEngine(metadata_dir=Path(metadata_dir), prompt_files=prompt_files)
    
    # 进行聚类
    collections_data = clusterer.cluster_clips(clips_with_titles)
    
    # 保存结果
    if output_path is None:
        if metadata_dir is None:
            metadata_dir = METADATA_DIR
        output_path = Path(metadata_dir) / "step5_collections.json"
    
    clusterer.save_collections(collections_data, output_path)
    
    return collections_data
