"""
Step 2: 时间点提取 - 基于大纲和SRT定位话题时间区间
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

class TimelineExtractor:
    """从大纲和SRT字幕中提取精确时间线"""
    
    def __init__(self, metadata_dir: Path = None, prompt_files: Dict = None):
        self.llm_client = LLMFactory.get_default_client()
        self.text_processor = TextProcessor()
        
        # 使用传入的metadata_dir或默认值
        if metadata_dir is None:
            metadata_dir = METADATA_DIR
        self.metadata_dir = metadata_dir
        
        # 加载提示词
        prompt_files_to_use = prompt_files if prompt_files is not None else PROMPT_FILES
        with open(prompt_files_to_use['timeline'], 'r', encoding='utf-8') as f:
            self.timeline_prompt = f.read()
            
        # SRT块的目录
        self.srt_chunks_dir = self.metadata_dir / "step1_srt_chunks"
        self.timeline_chunks_dir = self.metadata_dir / "step2_timeline_chunks"
        self.llm_raw_output_dir = self.metadata_dir / "step2_llm_raw_output"

    def extract_timeline(self, outlines: List[Dict]) -> List[Dict]:
        """
        提取话题时间区间。
        新版特性：
        - 基于预先分块的SRT
        - 按块批量处理
        - 缓存原始LLM响应，避免重复调用
        - 保存每个块的处理结果作为中间文件，增强健壮性
        """
        logger.info("开始提取话题时间区间...")
        
        if not outlines:
            logger.warning("大纲数据为空，无法提取时间线。")
            return []

        if not self.srt_chunks_dir.exists():
            logger.error(f"SRT块目录不存在: {self.srt_chunks_dir}。请先运行Step 1。")
            return []

        # 1. 创建本步骤需要的目录
        self.timeline_chunks_dir.mkdir(parents=True, exist_ok=True)
        self.llm_raw_output_dir.mkdir(parents=True, exist_ok=True)

        # 2. 按 chunk_index 对所有大纲进行分组
        outlines_by_chunk = defaultdict(list)
        for outline in outlines:
            chunk_index = outline.get('chunk_index')
            if chunk_index is not None:
                outlines_by_chunk[chunk_index].append(outline)
            else:
                logger.warning(f"  > 话题 '{outline.get('title', '未知')}' 缺少 chunk_index，将被跳过。")

        all_timeline_data = []
        # 3. 遍历每个块，批量处理，并将结果存为独立的JSON文件
        for chunk_index, chunk_outlines in outlines_by_chunk.items():
            logger.info(f"处理块 {chunk_index}，其中包含 {len(chunk_outlines)} 个话题...")
            
            # 每次都重新处理，不使用缓存
            chunk_output_path = self.timeline_chunks_dir / f"chunk_{chunk_index}.json"

            try:
                # 首先加载对应的SRT块文件，无论是否使用缓存都需要这些信息
                srt_chunk_path = self.srt_chunks_dir / f"chunk_{chunk_index}.json"
                if not srt_chunk_path.exists():
                    logger.warning(f"  > 找不到对应的SRT块文件: {srt_chunk_path}，跳过整个块。")
                    continue
                
                with open(srt_chunk_path, 'r', encoding='utf-8') as f:
                    srt_chunk_data = json.load(f)

                if not srt_chunk_data:
                    logger.warning(f"  > SRT块文件为空: {srt_chunk_path}，跳过整个块。")
                    continue

                # 获取时间范围信息
                chunk_start_time = srt_chunk_data[0]['start_time']
                chunk_end_time = srt_chunk_data[-1]['end_time']

                raw_response = ""
                llm_cache_path = self.llm_raw_output_dir / f"chunk_{chunk_index}.txt"

                if llm_cache_path.exists():
                    logger.info(f"  > 找到块 {chunk_index} 的LLM原始响应缓存，直接读取。")
                    with open(llm_cache_path, 'r', encoding='utf-8') as f:
                        raw_response = f.read()
                else:
                    logger.info(f"  > 未找到LLM缓存，开始调用API...")
                    
                    # 构建用于LLM的SRT文本
                    srt_text_for_prompt = ""
                    for sub in srt_chunk_data:
                        srt_text_for_prompt += f"{sub['index']}\\n{sub['start_time']} --> {sub['end_time']}\\n{sub['text']}\\n\\n"
                    
                    # 为LLM准备一个"干净"的输入，只包含它需要的信息
                    llm_input_outlines = [
                        {"title": o.get("title"), "subtopics": o.get("subtopics")}
                        for o in chunk_outlines
                    ]

                    input_data = {
                        "outline": llm_input_outlines,  # 使用干净的数据
                        "srt_text": srt_text_for_prompt
                    }
                    
                    # 调用LLM获取原始响应，带重试机制
                    parsed_items = None
                    max_parse_retries = 2
                    
                    for retry_count in range(max_parse_retries + 1):
                        try:
                            logger.info(f"  > 🚀 [块 {chunk_index} 第{retry_count + 1}次尝试] 调用LLM提取时间轴...")
                            logger.info(f"  > 📊 [输入统计] 大纲数量: {len(llm_input_outlines)}, SRT条目: {len(srt_chunk_data)}")
                            logger.debug(f"  > 📄 [输入详情] SRT文本前300字符: {srt_text_for_prompt[:300]}...")
                            
                            raw_response = self.llm_client.call_with_retry(self.timeline_prompt, input_data)
                            
                            if not raw_response:
                                logger.warning(f"  > ⚠️ [块 {chunk_index} 空响应] LLM响应为空，跳过")
                                break
                            
                            logger.info(f"  > ✅ [块 {chunk_index} 响应成功] 获得LLM响应，长度: {len(raw_response)} 字符")
                            
                            # 保存原始响应到缓存
                            cache_file = self.llm_raw_output_dir / f"chunk_{chunk_index}_attempt_{retry_count}.txt"
                            with open(cache_file, 'w', encoding='utf-8') as f:
                                f.write(raw_response)
                            logger.info(f"  > 💾 [缓存保存] 原始响应已保存到: {cache_file.name}")
                            
                            # 解析LLM的原始响应
                            parsed_items = self._parse_and_validate_response(
                                raw_response, 
                                chunk_start_time, 
                                chunk_end_time,
                                chunk_index
                            )
                            
                            if parsed_items:
                                # 保存解析后的结果
                                with open(chunk_output_path, 'w', encoding='utf-8') as f:
                                    json.dump(parsed_items, f, ensure_ascii=False, indent=2)
                                
                                logger.info(f"  > 块 {chunk_index} 成功解析 {len(parsed_items)} 个时间段")
                                break  # 成功解析，跳出重试循环
                            else:
                                if retry_count < max_parse_retries:
                                    logger.warning(f"  > 块 {chunk_index} 解析失败，尝试重试 ({retry_count + 1}/{max_parse_retries + 1})")
                                    # 在重试时强化提示词，强调JSON格式
                                    input_data['additional_instruction'] = "\n\n【重要】输出要求：\n1. 必须以[开始，以]结束\n2. 使用英文双引号，不要使用中文引号\n3. 字符串中的引号必须转义为\\\"\n4. 不要添加任何解释文字或代码块标记\n5. 确保JSON格式完全正确"
                                else:
                                    logger.error(f"  > 块 {chunk_index} 经过 {max_parse_retries + 1} 次尝试仍然解析失败")
                                    # 保存最后一次的原始响应以便调试
                                    self._save_debug_response(raw_response, chunk_index, "final_parse_failure")
                                    
                        except Exception as parse_error:
                            logger.error(f"  > 块 {chunk_index} 第 {retry_count + 1} 次尝试解析过程中发生异常: {parse_error}")
                            if retry_count == max_parse_retries:
                                # 保存原始响应以便调试
                                self._save_debug_response(raw_response if 'raw_response' in locals() else "No response", chunk_index, "parse_exception")
                            continue
                    
                    if not parsed_items:
                         logger.warning(f"  > 块 {chunk_index} 最终解析失败，跳过")
                         continue

            except Exception as e:
                logger.error(f"  > 处理块 {chunk_index} 时出错: {str(e)}")
                continue
        
        # 4. 从所有中间文件中拼接最终结果
        logger.info("所有块处理完毕，开始从中间文件拼接最终结果...")
        all_timeline_data = []
        chunk_files = sorted(self.timeline_chunks_dir.glob("*.json"))
        for chunk_file in chunk_files:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                chunk_data = json.load(f)
                all_timeline_data.extend(chunk_data)

        logger.info(f"成功从 {len(chunk_files)} 个块文件中加载了 {len(all_timeline_data)} 个话题。")
        
        # 最终排序：在返回所有结果前，按开始时间进行全局排序
        if all_timeline_data:
            logger.info("按开始时间对所有话题进行最终排序...")
            try:
                # 使用 text_processor 将时间字符串转换为秒数以便正确排序
                all_timeline_data.sort(key=lambda x: self.text_processor.time_to_seconds(x['start_time']))
                logger.info("排序完成。")
                
                # 为所有片段按时间顺序分配固定的ID
                logger.info("为所有片段按时间顺序分配固定ID...")
                for i, timeline_item in enumerate(all_timeline_data):
                    timeline_item['id'] = str(i + 1)
                logger.info(f"已为 {len(all_timeline_data)} 个片段分配了固定ID（1-{len(all_timeline_data)}）")
                
            except Exception as e:
                logger.error(f"对最终结果排序时出错: {e}。返回未排序的结果。")

        return all_timeline_data
        
    def _parse_and_validate_response(self, response: str, chunk_start: str, chunk_end: str, chunk_index: int) -> List[Dict]:
        """增强的解析LLM的批量响应、验证并调整时间"""
        validated_items = []
        
        # 保存原始响应用于调试
        self._save_debug_response(response, chunk_index, "original_response")
        
        try:
            # 尝试解析JSON
            parsed_response = self.llm_client.parse_json_response(response)
            
            # 验证JSON结构
            if not self.llm_client._validate_json_structure(parsed_response):
                logger.error(f"  > 块 {chunk_index} JSON结构验证失败")
                self._save_debug_response(str(parsed_response), chunk_index, "invalid_structure")
                return []
            
            if not isinstance(parsed_response, list):
                logger.warning(f"  > 块 {chunk_index} LLM返回的不是一个列表")
                self._save_debug_response(f"类型: {type(parsed_response)}, 内容: {parsed_response}", chunk_index, "not_list")
                return []
            
            for timeline_item in parsed_response:
                if 'outline' not in timeline_item or 'start_time' not in timeline_item or 'end_time' not in timeline_item:
                    logger.warning(f"  > 从LLM返回的某个JSON对象格式不正确: {timeline_item}")
                    continue
                
                # 将 chunk_index 添加回对象中，以便后续步骤使用
                timeline_item['chunk_index'] = chunk_index
                
                # 验证和调整时间范围
                try:
                    # 验证时间格式
                    if not self._validate_time_format(timeline_item['start_time']):
                        logger.warning(f"  > 话题 '{timeline_item['outline']}' 开始时间格式不正确: {timeline_item['start_time']}")
                        continue
                    
                    if not self._validate_time_format(timeline_item['end_time']):
                        logger.warning(f"  > 话题 '{timeline_item['outline']}' 结束时间格式不正确: {timeline_item['end_time']}")
                        continue
                    
                    start_time = self._convert_time_format(timeline_item['start_time'])
                    end_time = self._convert_time_format(timeline_item['end_time'])
                    
                    start_sec = self.text_processor.time_to_seconds(start_time)
                    end_sec = self.text_processor.time_to_seconds(end_time)
                    chunk_start_sec = self.text_processor.time_to_seconds(chunk_start)
                    chunk_end_sec = self.text_processor.time_to_seconds(chunk_end)
                    
                    if start_sec < chunk_start_sec:
                        logger.warning(f"  > 调整话题 '{timeline_item['outline']}' 的开始时间从 {start_time} 到 {chunk_start}")
                        timeline_item['start_time'] = chunk_start
                    
                    if end_sec > chunk_end_sec:
                        logger.warning(f"  > 调整话题 '{timeline_item['outline']}' 的结束时间从 {end_time} 到 {chunk_end}")
                        timeline_item['end_time'] = chunk_end
                    
                    logger.info(f"  > 定位成功: {timeline_item['outline']} ({timeline_item['start_time']} -> {timeline_item['end_time']})")
                    validated_items.append(timeline_item)
                except Exception as e:
                    logger.error(f"  > 验证单个时间戳时出错: {e} - 项目: {timeline_item}")
                    continue
            
            return validated_items

        except Exception as e:
            logger.error(f"  > 块 {chunk_index} 解析LLM响应时出错: {e}")
            # 保存详细的错误信息
            error_info = {
                "error": str(e),
                "error_type": type(e).__name__,
                "response_length": len(response),
                "response_preview": response[:200],
                "chunk_index": chunk_index,
                "chunk_start": chunk_start,
                "chunk_end": chunk_end
            }
            import json
            self._save_debug_response(json.dumps(error_info, indent=2, ensure_ascii=False), chunk_index, "parse_error")
            return []

    def _validate_time_format(self, time_str: str) -> bool:
        """
        验证时间格式是否正确 (HH:MM:SS,mmm)
        """
        import re
        pattern = r'^\d{2}:\d{2}:\d{2},\d{3}$'
        return bool(re.match(pattern, time_str))
    
    def _convert_time_format(self, time_str: str) -> str:
        """
        转换时间格式：SRT格式 -> FFmpeg格式
        """
        if not time_str or time_str == "end":
            return time_str
        return time_str.replace(',', '.')

    def _save_debug_response(self, response: str, chunk_index: int, error_type: str) -> None:
        """保存调试响应到文件"""
        try:
            debug_dir = self.metadata_dir / "debug_responses"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"chunk_{chunk_index}_{error_type}.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response)
            logger.info(f"调试响应已保存到: {debug_file}")
        except Exception as e:
            logger.error(f"保存调试响应失败: {e}")

    def save_timeline(self, timeline_data: List[Dict], output_path: Optional[Path] = None) -> Path:
        """
        保存时间区间数据
        """
        if output_path is None:
            output_path = METADATA_DIR / "step2_timeline.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(timeline_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"时间数据已保存到: {output_path}")
        return output_path

    def load_timeline(self, input_path: Path) -> List[Dict]:
        """
        从文件加载时间数据
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            return json.load(f)

def run_step2_timeline(outline_path: Path, metadata_dir: Path = None, output_path: Optional[Path] = None, prompt_files: Dict = None) -> List[Dict]:
    """
    运行Step 2: 时间点提取
    """
    if metadata_dir is None:
        metadata_dir = METADATA_DIR
        
    extractor = TimelineExtractor(metadata_dir, prompt_files)
    
    # 加载大纲
    with open(outline_path, 'r', encoding='utf-8') as f:
        outlines = json.load(f)
        
    timeline_data = extractor.extract_timeline(outlines)
    
    # 保存结果
    if output_path is None:
        output_path = metadata_dir / "step2_timeline.json"
        
    extractor.save_timeline(timeline_data, output_path)
    
    return timeline_data