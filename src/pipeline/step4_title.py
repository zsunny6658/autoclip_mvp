"""
Step 4: 标题生成 - 为高分片段生成爆点标题
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict

from ..utils.llm_factory import LLMFactory
from ..utils.text_processor import TextProcessor
from ..config import PROMPT_FILES, METADATA_DIR

logger = logging.getLogger(__name__)

class TitleGenerator:
    """标题生成器"""
    
    def __init__(self, metadata_dir: Optional[Path] = None, prompt_files: Dict = None):
        self.llm_client = LLMFactory.get_default_client()
        self.text_processor = TextProcessor()
        
        # 加载提示词
        prompt_files_to_use = prompt_files if prompt_files is not None else PROMPT_FILES
        with open(prompt_files_to_use['title'], 'r', encoding='utf-8') as f:
            self.title_prompt = f.read()
        
        # 使用传入的metadata_dir或默认值
        if metadata_dir is None:
            metadata_dir = METADATA_DIR
        self.metadata_dir = metadata_dir
        self.llm_raw_output_dir = self.metadata_dir / "step4_llm_raw_output"
    
    def generate_titles(self, high_score_clips: List[Dict]) -> List[Dict]:
        """
        为高分切片生成标题 (新版：按块批量处理，并增加缓存)
        """
        if not high_score_clips:
            return []
            
        logger.info(f"开始为 {len(high_score_clips)} 个高分片段进行批量标题生成...")
        
        self.llm_raw_output_dir.mkdir(parents=True, exist_ok=True)
        
        clips_by_chunk = defaultdict(list)
        for clip in high_score_clips:
            clips_by_chunk[clip.get('chunk_index', 0)].append(clip)
            
        all_clips_with_titles = []
        for chunk_index, chunk_clips in clips_by_chunk.items():
            logger.info(f"处理块 {chunk_index}，其中包含 {len(chunk_clips)} 个片段...")
            
            try:
                logger.info(f"  > 🚀 [块 {chunk_index} 标题生成] 开始调用LLM生成标题...")
                
                # 构建输入数据
                input_for_llm = [
                    {
                        "id": clip.get('id'),
                        "title": clip.get('outline'),  # 使用outline字段作为title
                        "content": clip.get('content'),
                        "recommend_reason": clip.get('recommend_reason')
                    } for clip in chunk_clips
                ]
                
                logger.info(f"  > 📊 [输入统计] 块 {chunk_index} 包含 {len(chunk_clips)} 个片段")
                logger.debug(f"  > 📄 [输入详情] 前3个片段: {input_for_llm[:3]}")
                
                raw_response = self.llm_client.call_with_retry(self.title_prompt, input_for_llm)
                
                if raw_response:
                    logger.info(f"  > ✅ [块 {chunk_index} 响应成功] 获得LLM响应，长度: {len(raw_response)} 字符")
                    # 保存LLM原始响应用于调试（但不用作缓存）
                    llm_cache_path = self.llm_raw_output_dir / f"chunk_{chunk_index}.txt"
                    with open(llm_cache_path, 'w', encoding='utf-8') as f:
                        f.write(raw_response)
                    logger.info(f"  > 💾 [LLM原始响应已保存到] {llm_cache_path}")
                    
                    logger.info(f"  > 🔍 [开始解析] 解析标题生成响应...")
                    titles_map = self.llm_client.parse_json_response(raw_response)
                else:
                    logger.warning(f"  > ⚠️ [块 {chunk_index} 空响应] LLM响应为空")
                    titles_map = {}
                
                if not isinstance(titles_map, dict):
                    logger.warning(f"  > LLM返回的标题不是一个字典: {titles_map}，跳过该块。")
                    # 即使失败，也把原始片段加回去，避免数据丢失
                    all_clips_with_titles.extend(chunk_clips)
                    continue

                for clip in chunk_clips:
                    clip_id = clip.get('id')
                    generated_title = titles_map.get(clip_id)
                    if generated_title and isinstance(generated_title, str):
                        clip['generated_title'] = generated_title
                        logger.info(f"  > 为片段 {clip_id} ('{clip.get('outline', '')[:20]}...') 生成标题: {generated_title}")
                    else:
                        clip['generated_title'] = clip.get('outline', f"片段_{clip_id}")  # 使用outline作为fallback
                        logger.warning(f"  > 未能为片段 {clip_id} 找到或解析标题，使用原始outline")
                
                all_clips_with_titles.extend(chunk_clips)

            except Exception as e:
                logger.error(f"  > 为块 {chunk_index} 生成标题时出错: {e}")
                # 即使出错，也添加原始数据以防丢失
                all_clips_with_titles.extend(chunk_clips)
                continue
                
        logger.info("所有高分片段标题生成完成")
        return all_clips_with_titles
        
    def save_clips_with_titles(self, clips_with_titles: List[Dict], output_path: Path):
        """保存带标题的片段数据"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clips_with_titles, f, ensure_ascii=False, indent=2)
        logger.info(f"带标题的片段数据已保存到: {output_path}")

def run_step4_title(high_score_clips_path: Path, output_path: Optional[Path] = None, metadata_dir: Optional[str] = None, prompt_files: Dict = None) -> List[Dict]:
    """
    运行Step 4: 标题生成
    
    Args:
        high_score_clips_path: 高分切片文件路径
        output_path: 输出文件路径，默认为step4_titles.json
        metadata_dir: 元数据目录路径
        prompt_files: 自定义提示词文件
        
    Returns:
        带标题的切片列表
        
    Note:
        此步骤只保存step4_titles.json文件，包含带标题的片段数据。
        clips_metadata.json文件将在step6中统一保存，避免重复保存。
    """
    # 加载高分片段
    with open(high_score_clips_path, 'r', encoding='utf-8') as f:
        high_score_clips = json.load(f)
        
    # 创建标题生成器
    if metadata_dir is None:
        metadata_dir = METADATA_DIR
    title_generator = TitleGenerator(metadata_dir=Path(metadata_dir), prompt_files=prompt_files)
    
    # 生成标题
    clips_with_titles = title_generator.generate_titles(high_score_clips)
    
    # 确定输出路径
    if metadata_dir is None:
        metadata_dir = METADATA_DIR
    
    if output_path is None:
        output_path = Path(metadata_dir) / "step4_titles.json"
        
    # 保存带标题的片段数据到step4_titles.json
    title_generator.save_clips_with_titles(clips_with_titles, output_path)
    
    # 重要说明：clips_metadata.json将在step6中保存，这里不重复保存
    # 这样可以避免数据重复和保存逻辑混乱
    
    return clips_with_titles