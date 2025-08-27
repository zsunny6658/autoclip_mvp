"""
Step 3: 内容评分 - 对每个话题片段进行多维度评分
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from collections import defaultdict

from ..utils.llm_factory import LLMFactory
from ..utils.text_processor import TextProcessor
from ..config import PROMPT_FILES, METADATA_DIR, MIN_SCORE_THRESHOLD

logger = logging.getLogger(__name__)

class ClipScorer:
    """内容评分器"""
    
    def __init__(self, prompt_files: Dict = None):
        self.llm_client = LLMFactory.get_default_client()
        self.text_processor = TextProcessor()
        
        # 加载提示词
        prompt_files_to_use = prompt_files if prompt_files is not None else PROMPT_FILES
        with open(prompt_files_to_use['recommendation'], 'r', encoding='utf-8') as f:
            self.recommendation_prompt = f.read()
    
    def score_clips(self, timeline_data: List[Dict]) -> List[Dict]:
        """
        为切片评分 (新版：按块批量处理，并使用LLM进行综合评估)
        """
        if not timeline_data:
            logger.warning("时间线数据为空，无法评分")
            return []
            
        logger.info(f"开始为 {len(timeline_data)} 个切片进行批量评分...")
        
        # 1. 按 chunk_index 对所有 timeline 数据进行分组
        timeline_by_chunk = defaultdict(list)
        for item in timeline_data:
            chunk_index = item.get('chunk_index')
            if chunk_index is not None:
                timeline_by_chunk[chunk_index].append(item)
            else:
                logger.warning(f"  > 话题 '{item.get('outline', '未知')}' 缺少 chunk_index，将被跳过。")
        
        all_scored_clips = []
        # 2. 遍历每个块，批量处理其中的所有话题
        for chunk_index, chunk_items in timeline_by_chunk.items():
            logger.info(f"处理块 {chunk_index}，其中包含 {len(chunk_items)} 个话题...")
            try:
                # 3. 使用LLM进行批量评估
                scored_chunk_items = self._get_llm_evaluation(chunk_items)
                
                if scored_chunk_items:
                    all_scored_clips.extend(scored_chunk_items)
                else:
                    logger.warning(f"块 {chunk_index} 的LLM评估返回为空，跳过。")

            except Exception as e:
                logger.error(f"  > 处理块 {chunk_index} 进行评分时出错: {str(e)}")
                continue

        # 4. 按最终得分对所有结果进行排序
        if all_scored_clips:
            all_scored_clips.sort(key=lambda x: x.get('final_score', 0), reverse=True)
            # 保持Step 2分配的固定ID，不再重新分配
            logger.info("按评分排序完成，保持原有固定ID不变")
            
            # 最终按ID排序，确保时间顺序的一致性
            all_scored_clips.sort(key=lambda x: int(x.get('id', 0)))
            logger.info("按ID排序完成，保持时间顺序")
                
        logger.info("所有切片评分完成")
        return all_scored_clips
    
    def _get_llm_evaluation(self, clips: List[Dict]) -> List[Dict]:
        """
        使用LLM进行批量评估，为每个clip添加 final_score 和 recommend_reason
        """
        try:
            # 输入给LLM的数据不需要包含所有字段，只给必要的
            input_for_llm = [
                {
                    "outline": clip.get('outline'), 
                    "content": clip.get('content'),
                    "start_time": clip.get('start_time'),
                    "end_time": clip.get('end_time'),
                } for clip in clips
            ]
            
            response = self.llm_client.call_with_retry(self.recommendation_prompt, input_for_llm)
            
            logger.info(f"✅ [评分响应成功] 获得LLM响应，长度: {len(response) if response else 0} 字符")
            logger.debug(f"📄 [评分响应内容]: {response[:300] if response else 'N/A'}...")
            
            logger.info(f"🔍 [开始解析] 解析LLM评分响应...")
            parsed_list = self.llm_client.parse_json_response(response)
            
            if not isinstance(parsed_list, list) or len(parsed_list) != len(clips):
                logger.error(f"❌ [评分结果错误] LLM返回的评分结果数量与输入不匹配。输入: {len(clips)}, 输出: {len(parsed_list) if isinstance(parsed_list, list) else '非列表'}")
                logger.debug(f"📄 [评分解析结果类型]: {type(parsed_list)}")
                if isinstance(parsed_list, list):
                    logger.debug(f"📄 [评分结果前3个]: {parsed_list[:3]}")
                return []
                
            # 将评分结果合并回原始的clips数据
            for original_clip, llm_result in zip(clips, parsed_list):
                score = llm_result.get('final_score')
                reason = llm_result.get('recommend_reason')
                
                if score is None or reason is None:
                    logger.warning(f"LLM返回的某个结果缺少score或reason: {llm_result}")
                    original_clip['final_score'] = 0.0
                    original_clip['recommend_reason'] = "评估失败"
                else:
                    original_clip['final_score'] = round(float(score), 2)
                    original_clip['recommend_reason'] = reason
                    logger.info(f"  > 评分成功: {original_clip.get('outline', '')[:20]}... [分数: {score}]")

            return clips

        except Exception as e:
            logger.error(f"LLM批量评估失败: {e}")
            # 如果批量失败，为所有clips标记为失败
            for clip in clips:
                clip['final_score'] = 0.0
                clip['recommend_reason'] = "批量评估失败"
            return clips

    def save_scores(self, scored_clips: List[Dict], output_path: Path):
        """保存评分结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(scored_clips, f, ensure_ascii=False, indent=2)
        logger.info(f"评分结果已保存到: {output_path}")

def run_step3_scoring(timeline_path: Path, metadata_dir: Path = None, output_path: Optional[Path] = None, prompt_files: Dict = None) -> List[Dict]:
    """
    运行Step 3: 内容评分与筛选
    
    Args:
        timeline_path: 时间线文件路径
        output_path: 输出文件路径
        prompt_files: 自定义提示词文件
        
    Returns:
        高分切片列表
    """
    # 加载时间线数据
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline_data = json.load(f)
    
    # 创建评分器
    scorer = ClipScorer(prompt_files)
    
    # 评分
    scored_clips = scorer.score_clips(timeline_data)
    
    # 筛选高分切片
    high_score_clips = [clip for clip in scored_clips if clip['final_score'] >= MIN_SCORE_THRESHOLD]
    
    # 保存结果
    if metadata_dir is None:
        metadata_dir = METADATA_DIR
    
    # 保存所有评分后的片段（用于调试和分析）
    all_scored_path = metadata_dir / "step3_all_scored.json"
    scorer.save_scores(scored_clips, all_scored_path)
    
    # 保存筛选后的高分片段（用于后续步骤）
    if output_path is None:
        output_path = metadata_dir / "step3_high_score_clips.json"
        
    scorer.save_scores(high_score_clips, output_path)
    
    return high_score_clips