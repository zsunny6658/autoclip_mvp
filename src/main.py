"""
主程序 - 自动切片工具完整处理流水线
"""
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional
import codecs
import sys
from datetime import datetime

from .utils.project_manager import project_manager
from .pipeline.step1_outline import run_step1_outline
from .pipeline.step2_timeline import run_step2_timeline
from .pipeline.step3_scoring import run_step3_scoring
from .pipeline.step4_title import run_step4_title
from .pipeline.step5_clustering import run_step5_clustering
from .pipeline.step6_video import run_step6_video

# 配置日志
try:
    # This setup is more robust for terminals that don't support UTF-8
    # It attempts to wrap stdout in a UTF-8 writer with a fallback.
    utf8_writer = codecs.getwriter('utf-8')
    # Use 'replace' error handler to avoid crashes on un-encodable characters
    utf8_stdout = utf8_writer(sys.stdout.buffer, 'replace')
    stream_handler = logging.StreamHandler(utf8_stdout)
except (AttributeError, TypeError):
    # Fallback for environments where sys.stdout.buffer is not available
    stream_handler = logging.StreamHandler(sys.stdout)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_clips.log', encoding='utf-8'),
        stream_handler
    ]
)

logger = logging.getLogger(__name__)

class AutoClipsProcessor:
    """自动切片处理器"""
    
    def __init__(self, project_id: str):
        """
        初始化处理器
        
        Args:
            project_id: 项目ID
        """
        self.project_id = project_id
        self.results = {}
        
        # 验证项目存在
        if not project_manager.validate_project_exists(project_id):
            raise ValueError(f"项目不存在: {project_id}")
        
        # 获取项目路径
        self.paths = project_manager.get_project_paths(project_id)
        
        # 确保项目目录存在
        project_manager.config.ensure_project_directories(project_id)
        
        logger.info(f"初始化处理器，项目ID: {project_id}")
    
    def run_full_pipeline(self, progress_callback=None) -> Dict[str, Any]:
        """
        运行完整的处理流水线
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            处理结果汇总
        """
        logger.info(f"🚀 开始项目 {self.project_id} 的自动切片处理流水线")
        
        try:
            # 验证输入文件
            validation = project_manager.validate_input_files(self.project_id)
            if not validation["can_process"]:
                raise ValueError("缺少必要的输入文件（视频文件和字幕文件）")
            
            # 获取输入文件路径
            input_files = project_manager.get_input_files(self.project_id)
            input_video = input_files["video_file"]
            input_srt = input_files["srt_file"]
            
            if not input_video or not input_srt:
                raise ValueError("视频文件或字幕文件不存在")
            
            # Step 1: 大纲提取
            logger.info("📖 Step 1: 提取视频大纲")
            if progress_callback:
                progress_callback(1, 6, "提取视频大纲", 0)
            
            outlines = run_step1_outline(
                input_srt, 
                self.paths["metadata_dir"]
            )
            self.results['step1_outlines'] = outlines
            
            # 保存步骤结果
            project_manager.save_processing_result(self.project_id, 1, {"outlines": outlines})
            
            logger.info(f"✅ Step 1 完成，提取到 {len(outlines)} 个话题")
            if progress_callback:
                progress_callback(1, 6, "大纲提取完成", 16.7)
            
            # Step 2: 时间点提取
            logger.info("⏰ Step 2: 提取时间区间")
            if progress_callback:
                progress_callback(2, 6, "提取时间区间", 16.7)
            
            timeline_data = run_step2_timeline(
                self.paths["metadata_dir"] / "step1_outline.json",
                self.paths["metadata_dir"]
            )
            self.results['step2_timeline'] = timeline_data
            
            # 保存步骤结果
            project_manager.save_processing_result(self.project_id, 2, {"timeline": timeline_data})
            
            logger.info(f"✅ Step 2 完成，定位到 {len(timeline_data)} 个时间区间")
            if progress_callback:
                progress_callback(2, 6, "时间定位完成", 33.3)
            
            # Step 3: 内容评分
            logger.info("🔥 Step 3: 内容评分与筛选")
            if progress_callback:
                progress_callback(3, 6, "内容评分与筛选", 33.3)
            
            high_score_clips = run_step3_scoring(
                self.paths["metadata_dir"] / "step2_timeline.json",
                self.paths["metadata_dir"]
            )
            self.results['step3_scoring'] = high_score_clips
            
            # 保存步骤结果
            project_manager.save_processing_result(self.project_id, 3, {"high_score_clips": high_score_clips})
            
            logger.info(f"✅ Step 3 完成，筛选出 {len(high_score_clips)} 个高分片段")
            if progress_callback:
                progress_callback(3, 6, "内容评分完成", 50.0)
            
            # Step 4: 标题生成
            logger.info("📝 Step 4: 生成爆点标题")
            if progress_callback:
                progress_callback(4, 6, "生成爆点标题", 50.0)
            
            clips_with_titles = run_step4_title(
                self.paths["metadata_dir"] / "step3_high_score_clips.json",
                output_path=None,
                metadata_dir=str(self.paths["metadata_dir"])
            )
            self.results['step4_titles'] = clips_with_titles
            
            # 保存步骤结果
            project_manager.save_processing_result(self.project_id, 4, {"clips_with_titles": clips_with_titles})
            
            logger.info(f"✅ Step 4 完成，为 {len(clips_with_titles)} 个片段生成标题")
            if progress_callback:
                progress_callback(4, 6, "标题生成完成", 66.7)
            
            # Step 5: 主题聚类
            logger.info("📦 Step 5: 主题聚类成合集")
            if progress_callback:
                progress_callback(5, 6, "主题聚类成合集", 66.7)
            
            collections_data = run_step5_clustering(
                self.paths["metadata_dir"] / "step4_titles.json",
                output_path=None,
                metadata_dir=str(self.paths["metadata_dir"])
            )
            self.results['step5_collections'] = collections_data
            
            # 保存步骤结果
            project_manager.save_processing_result(self.project_id, 5, {"collections": collections_data})
            
            logger.info(f"✅ Step 5 完成，生成 {len(collections_data)} 个合集")
            if progress_callback:
                progress_callback(5, 6, "主题聚类完成", 83.3)
            
            # Step 6: 视频切割
            logger.info("✂️ Step 6: 生成切片与合集视频")
            if progress_callback:
                progress_callback(6, 6, "生成切片与合集视频", 83.3)
            
            video_result = run_step6_video(
                self.paths["metadata_dir"] / "step4_titles.json",
                self.paths["metadata_dir"] / "step5_collections.json",
                input_video,
                output_dir=self.paths["output_dir"],
                clips_dir=str(self.paths["clips_dir"]),
                collections_dir=str(self.paths["collections_dir"]),
                metadata_dir=str(self.paths["metadata_dir"])
            )
            self.results['step6_video'] = video_result
            
            # 保存步骤结果
            project_manager.save_processing_result(self.project_id, 6, video_result)
            
            logger.info(f"✅ Step 6 完成，生成 {video_result['clips_generated']} 个切片，{video_result['collections_generated']} 个合集")
            if progress_callback:
                progress_callback(6, 6, "视频生成完成", 100.0)
            
            # 保存完整结果
            self._save_final_results()
            
            # 更新项目状态为完成
            project_manager.update_project_metadata(self.project_id, {
                "status": "completed",
                "current_step": 6,
                "completed_at": datetime.now().isoformat()
            })
            
            logger.info(f"🎉 项目 {self.project_id} 的自动切片处理流水线完成！")
            return {'success': True, 'results': self.results}
            
        except Exception as e:
            logger.error(f"❌ 项目 {self.project_id} 处理流水线失败: {str(e)}")
            
            # 更新项目状态为错误
            project_manager.update_project_metadata(self.project_id, {
                "status": "error",
                "error_message": str(e),
                "error_at": datetime.now().isoformat()
            })
            
            return {'success': False, 'error': str(e)}
    
    def run_single_step(self, step: int, **kwargs) -> Any:
        """
        运行单个步骤
        
        Args:
            step: 步骤编号 (1-6)
            **kwargs: 步骤特定参数
            
        Returns:
            步骤结果
        """
        logger.info(f"🔄 运行项目 {self.project_id} 的 Step {step}")
        
        try:
            # 获取输入文件路径
            input_files = project_manager.get_input_files(self.project_id)
            input_video = input_files["video_file"]
            input_srt = input_files["srt_file"]
            
            if step == 1:
                if not input_srt:
                    raise ValueError("字幕文件不存在，无法进行大纲提取")
                result = run_step1_outline(input_srt, self.paths["metadata_dir"])
            elif step == 2:
                result = run_step2_timeline(
                    self.paths["metadata_dir"] / "step1_outline.json",
                    self.paths["metadata_dir"]
                )
            elif step == 3:
                result = run_step3_scoring(
                    self.paths["metadata_dir"] / "step2_timeline.json",
                    self.paths["metadata_dir"]
                )
            elif step == 4:
                result = run_step4_title(
                    self.paths["metadata_dir"] / "step3_high_score_clips.json",
                    output_path=None,
                    metadata_dir=str(self.paths["metadata_dir"])
                )
            elif step == 5:
                result = run_step5_clustering(
                    self.paths["metadata_dir"] / "step4_titles.json",
                    output_path=None,
                    metadata_dir=str(self.paths["metadata_dir"])
                )
            elif step == 6:
                if not input_video:
                    raise ValueError("视频文件不存在，无法进行视频切割")
                
                result = run_step6_video(
                    self.paths["metadata_dir"] / "step4_titles.json",
                    self.paths["metadata_dir"] / "step5_collections.json",
                    input_video,
                    output_dir=self.paths["output_dir"],
                    clips_dir=str(self.paths["clips_dir"]),
                    collections_dir=str(self.paths["collections_dir"]),
                    metadata_dir=str(self.paths["metadata_dir"])
                )
            else:
                raise ValueError(f"无效的步骤编号: {step}")
            
            # 保存步骤结果 - 确保结果是字典类型
            if isinstance(result, dict):
                step_result = result
            else:
                step_result = {"result": result}
            
            project_manager.save_processing_result(self.project_id, step, step_result)
            
            logger.info(f"✅ Step {step} 完成")
            return result
            
        except Exception as e:
            logger.error(f"❌ Step {step} 失败: {str(e)}")
            raise
    
    def _save_final_results(self):
        """保存最终处理结果"""
        try:
            final_results_file = self.paths["metadata_dir"] / "final_results.json"
            with open(final_results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"最终结果已保存到: {final_results_file}")
        except Exception as e:
            logger.error(f"保存最终结果失败: {e}")
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        获取处理状态
        
        Returns:
            处理状态信息
        """
        return project_manager.get_project_summary(self.project_id)
    
    def check_step_completion(self, step_number: int) -> bool:
        """
        检查步骤是否完成
        
        Args:
            step_number: 步骤编号
            
        Returns:
            是否完成
        """
        step_result = project_manager.get_processing_result(self.project_id, step_number)
        return step_result is not None
    
    def get_completed_steps(self) -> list:
        """
        获取已完成的步骤列表
        
        Returns:
            已完成的步骤编号列表
        """
        completed_steps = []
        for step in range(1, 7):
            if self.check_step_completion(step):
                completed_steps.append(step)
        return completed_steps
    
    def run_from_step(self, start_step: int, progress_callback=None) -> Dict[str, Any]:
        """
        从指定步骤开始运行处理流水线
        
        Args:
            start_step: 开始步骤编号 (1-6)
            progress_callback: 进度回调函数
            
        Returns:
            处理结果汇总
        """
        logger.info(f"🔄 从步骤 {start_step} 开始重新处理项目 {self.project_id}")
        
        try:
            # 验证输入文件
            validation = project_manager.validate_input_files(self.project_id)
            if not validation["can_process"]:
                raise ValueError("缺少必要的输入文件（视频文件和字幕文件）")
            
            # 获取输入文件路径
            input_files = project_manager.get_input_files(self.project_id)
            input_video = input_files["video_file"]
            input_srt = input_files["srt_file"]
            
            if not input_video or not input_srt:
                raise ValueError("视频文件或字幕文件不存在")
            
            # 从指定步骤开始执行
            for step in range(start_step, 7):
                step_progress = ((step - 1) / 6) * 100
                
                if step == 1:
                    logger.info("📖 Step 1: 提取视频大纲")
                    if progress_callback:
                        progress_callback(1, 6, "提取视频大纲", step_progress)
                    
                    outlines = run_step1_outline(input_srt, self.paths["metadata_dir"])
                    self.results['step1_outlines'] = outlines
                    project_manager.save_processing_result(self.project_id, 1, {"outlines": outlines})
                    
                    logger.info(f"✅ Step 1 完成，提取到 {len(outlines)} 个话题")
                    if progress_callback:
                        progress_callback(1, 6, "大纲提取完成", 16.7)
                
                elif step == 2:
                    logger.info("⏰ Step 2: 提取时间区间")
                    if progress_callback:
                        progress_callback(2, 6, "提取时间区间", step_progress)
                    
                    timeline_data = run_step2_timeline(
                        self.paths["metadata_dir"] / "step1_outline.json",
                        self.paths["metadata_dir"]
                    )
                    self.results['step2_timeline'] = timeline_data
                    project_manager.save_processing_result(self.project_id, 2, {"timeline": timeline_data})
                    
                    logger.info(f"✅ Step 2 完成，定位到 {len(timeline_data)} 个时间区间")
                    if progress_callback:
                        progress_callback(2, 6, "时间定位完成", 33.3)
                
                elif step == 3:
                    logger.info("🔥 Step 3: 内容评分与筛选")
                    if progress_callback:
                        progress_callback(3, 6, "内容评分与筛选", step_progress)
                    
                    high_score_clips = run_step3_scoring(
                        self.paths["metadata_dir"] / "step2_timeline.json",
                        self.paths["metadata_dir"]
                    )
                    self.results['step3_scoring'] = high_score_clips
                    project_manager.save_processing_result(self.project_id, 3, {"high_score_clips": high_score_clips})
                    
                    logger.info(f"✅ Step 3 完成，筛选出 {len(high_score_clips)} 个高分片段")
                    if progress_callback:
                        progress_callback(3, 6, "内容评分完成", 50.0)
                
                elif step == 4:
                    logger.info("📝 Step 4: 生成爆点标题")
                    if progress_callback:
                        progress_callback(4, 6, "生成爆点标题", step_progress)
                    
                    clips_with_titles = run_step4_title(
                        self.paths["metadata_dir"] / "step3_high_score_clips.json",
                        output_path=None,
                        metadata_dir=str(self.paths["metadata_dir"])
                    )
                    self.results['step4_titles'] = clips_with_titles
                    project_manager.save_processing_result(self.project_id, 4, {"clips_with_titles": clips_with_titles})
                    
                    logger.info(f"✅ Step 4 完成，为 {len(clips_with_titles)} 个片段生成标题")
                    if progress_callback:
                        progress_callback(4, 6, "标题生成完成", 66.7)
                
                elif step == 5:
                    logger.info("📦 Step 5: 主题聚类成合集")
                    if progress_callback:
                        progress_callback(5, 6, "主题聚类成合集", step_progress)
                    
                    collections_data = run_step5_clustering(
                        self.paths["metadata_dir"] / "step4_titles.json",
                        output_path=None,
                        metadata_dir=str(self.paths["metadata_dir"])
                    )
                    self.results['step5_collections'] = collections_data
                    project_manager.save_processing_result(self.project_id, 5, {"collections": collections_data})
                    
                    logger.info(f"✅ Step 5 完成，生成 {len(collections_data)} 个合集")
                    if progress_callback:
                        progress_callback(5, 6, "主题聚类完成", 83.3)
                
                elif step == 6:
                    logger.info("✂️ Step 6: 生成切片与合集视频")
                    if progress_callback:
                        progress_callback(6, 6, "生成切片与合集视频", step_progress)
                    
                    video_result = run_step6_video(
                        self.paths["metadata_dir"] / "step4_titles.json",
                        self.paths["metadata_dir"] / "step5_collections.json",
                        input_video,
                        output_dir=self.paths["output_dir"],
                        clips_dir=str(self.paths["clips_dir"]),
                        collections_dir=str(self.paths["collections_dir"]),
                        metadata_dir=str(self.paths["metadata_dir"])
                    )
                    self.results['step6_video'] = video_result
                    project_manager.save_processing_result(self.project_id, 6, video_result)
                    
                    logger.info(f"✅ Step 6 完成，生成 {video_result['clips_generated']} 个切片，{video_result['collections_generated']} 个合集")
                    if progress_callback:
                        progress_callback(6, 6, "视频生成完成", 100.0)
            
            # 保存完整结果
            self._save_final_results()
            
            # 更新项目状态为完成
            project_manager.update_project_metadata(self.project_id, {
                "status": "completed",
                "current_step": 6,
                "completed_at": datetime.now().isoformat()
            })
            
            logger.info(f"🎉 项目 {self.project_id} 从步骤 {start_step} 开始的处理流水线完成！")
            return {'success': True, 'results': self.results}
            
        except Exception as e:
            logger.error(f"❌ 项目 {self.project_id} 从步骤 {start_step} 开始的处理流水线失败: {str(e)}")
            
            # 更新项目状态为错误
            project_manager.update_project_metadata(self.project_id, {
                "status": "error",
                "error_message": str(e),
                "error_at": datetime.now().isoformat()
            })
            
            return {'success': False, 'error': str(e)}

def create_and_process_project(
    video_file: Path, 
    srt_file: Path, 
    project_name: Optional[str] = None,
    progress_callback=None
) -> Dict[str, Any]:
    """
    创建项目并运行完整处理流水线
    
    Args:
        video_file: 视频文件路径
        srt_file: 字幕文件路径
        project_name: 项目名称
        progress_callback: 进度回调函数
        
    Returns:
        处理结果
    """
    try:
        # 创建新项目
        project_id = project_manager.create_project(project_name)
        
        # 保存输入文件
        project_manager.save_input_file(project_id, video_file, "video")
        project_manager.save_input_file(project_id, srt_file, "srt")
        
        # 创建处理器并运行流水线
        processor = AutoClipsProcessor(project_id)
        result = processor.run_full_pipeline(progress_callback)
        
        # 添加项目ID到结果中
        result['project_id'] = project_id
        
        return result
        
    except Exception as e:
        logger.error(f"创建和处理项目失败: {e}")
        return {'success': False, 'error': str(e)}

def process_existing_project(
    project_id: str,
    progress_callback=None
) -> Dict[str, Any]:
    """
    处理现有项目
    
    Args:
        project_id: 项目ID
        progress_callback: 进度回调函数
        
    Returns:
        处理结果
    """
    try:
        processor = AutoClipsProcessor(project_id)
        result = processor.run_full_pipeline(progress_callback)
        result['project_id'] = project_id
        return result
        
    except Exception as e:
        logger.error(f"处理项目 {project_id} 失败: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """主函数 - 用于命令行运行"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自动切片工具')
    parser.add_argument('--video', type=Path, required=True, help='视频文件路径')
    parser.add_argument('--srt', type=Path, required=True, help='字幕文件路径')
    parser.add_argument('--project-name', type=str, help='项目名称')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not args.video.exists():
        print(f"❌ 视频文件不存在: {args.video}")
        return
    
    if not args.srt.exists():
        print(f"❌ 字幕文件不存在: {args.srt}")
        return
    
    # 运行处理
    result = create_and_process_project(args.video, args.srt, args.project_name)
    
    if result['success']:
        print(f"✅ 处理完成！项目ID: {result['project_id']}")
    else:
        print(f"❌ 处理失败: {result['error']}")

if __name__ == "__main__":
    main()