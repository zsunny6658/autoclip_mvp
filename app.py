"""
Streamlit Web界面 - 自动切片工具演示
"""
import streamlit as st
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# 设置页面配置
st.set_page_config(
    page_title="🎬 自动切片工具",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 导入项目模块
sys.path.append(str(Path(__file__).parent))

from src.main import create_and_process_project, process_existing_project, AutoClipsProcessor
from src.utils.project_manager import project_manager
from src.config import config_manager

def main():
    """主界面"""
    st.title("🎬 自动切片工具")
    st.markdown("一个端到端视频切片推荐系统，通过多轮大模型推理实现智能视频内容分析与切片生成")
    
    # 初始化session_state
    if 'api_key_configured' not in st.session_state:
        st.session_state['api_key_configured'] = False
    if 'current_project_id' not in st.session_state:
        st.session_state['current_project_id'] = None
        
    # 侧边栏
    with st.sidebar:
        st.header("🔧 控制面板")
        
        # API密钥输入
        api_key = st.text_input(
            "🔑 请输入通义千问API Key", 
            type="password", 
            help="获取地址: https://dashscope.console.aliyun.com/apiKey"
        )
        
        if api_key:
            config_manager.update_api_key(api_key)
            st.session_state['api_key_configured'] = True
            st.success("✅ API密钥已配置")
        else:
            st.session_state['api_key_configured'] = False
            st.warning("❌ 请先输入API密钥")

        # 项目选择
        st.subheader("📁 项目管理")
        
        # 获取所有项目
        projects = project_manager.list_projects()
        
        if projects:
            project_options = {f"{p['project_name']} ({p['project_id'][:8]})": p['project_id'] 
                             for p in projects}
            selected_project = st.selectbox(
                "选择项目",
                options=list(project_options.keys()),
                index=0 if not st.session_state.get('current_project_id') else None
            )
            
            if selected_project:
                st.session_state['current_project_id'] = project_options[selected_project]
        else:
            st.info("📝 暂无项目，请创建新项目")
        
        # 创建新项目
        if st.button("➕ 创建新项目", type="primary"):
            st.session_state['show_create_project'] = True
        
        # 处理选项
        st.subheader("⚙️ 处理选项")
        process_mode = st.selectbox(
            "选择处理模式",
            ["完整流水线", "单步处理", "查看状态"]
        )
        
        step_number = 1
        if process_mode == "单步处理":
            step_number = st.selectbox(
                "选择步骤",
                [1, 2, 3, 4, 5, 6],
                format_func=lambda x: f"Step {x}: {get_step_name(x)}"
            )
        
        # 开始处理按钮
        if st.button("🚀 开始处理", type="primary", 
                    disabled=not st.session_state.get('api_key_configured', False)):
            if not st.session_state.get('current_project_id'):
                st.error("❌ 请先选择或创建项目")
            else:
                if process_mode == "完整流水线":
                    run_full_pipeline()
                elif process_mode == "单步处理":
                    run_single_step(step_number)
                else:
                    show_status()

    # 主界面
    if st.session_state.get('show_create_project', False):
        show_create_project()
    elif process_mode == "查看状态":
        show_status()
    else:
        show_main_interface()

def show_create_project():
    """显示创建项目界面"""
    st.header("➕ 创建新项目")
    
    with st.form("create_project_form"):
        project_name = st.text_input("项目名称", placeholder="输入项目名称（可选）")
        
        uploaded_video = st.file_uploader(
            "上传视频文件", 
            type=['mp4', 'avi', 'mov', 'mkv'],
            help="支持MP4、AVI、MOV、MKV格式"
        )
        
        uploaded_srt = st.file_uploader(
            "上传字幕文件", 
            type=['srt'],
            help="支持SRT格式字幕文件"
        )
        
        submitted = st.form_submit_button("创建项目", type="primary")
        
        if submitted:
            if not uploaded_video or not uploaded_srt:
                st.error("❌ 请上传视频文件和字幕文件")
                return
            
            if not st.session_state.get('api_key_configured', False):
                st.error("❌ 请先配置API密钥")
                return
            
            # 保存上传的文件
            with st.spinner("正在创建项目..."):
                try:
                    # 创建临时文件
                    temp_dir = Path("temp")
                    temp_dir.mkdir(exist_ok=True)
                    
                    video_path = temp_dir / uploaded_video.name
                    srt_path = temp_dir / uploaded_srt.name
                    
                    with open(video_path, "wb") as f:
                        f.write(uploaded_video.getbuffer())
                    
                    with open(srt_path, "wb") as f:
                        f.write(uploaded_srt.getbuffer())
                    
                    # 创建项目并处理
                    result = create_and_process_project(
                        video_path, 
                        srt_path, 
                        project_name or None
                    )
                    
                    if result['success']:
                        st.session_state['current_project_id'] = result['project_id']
                        st.session_state['show_create_project'] = False
                        st.success(f"✅ 项目创建成功！项目ID: {result['project_id']}")
                        st.rerun()
                    else:
                        st.error(f"❌ 项目创建失败: {result['error']}")
                        
                except Exception as e:
                    st.error(f"❌ 创建项目失败: {str(e)}")
    
    if st.button("返回"):
        st.session_state['show_create_project'] = False
        st.rerun()

def get_step_name(step: int) -> str:
    """获取步骤名称"""
    step_names = {
        1: "大纲提取",
        2: "时间定位", 
        3: "内容评分",
        4: "标题生成",
        5: "主题聚类",
        6: "视频切割"
    }
    return step_names.get(step, "未知步骤")

def run_full_pipeline():
    """运行完整流水线"""
    project_id = st.session_state.get('current_project_id')
    if not project_id:
        st.error("❌ 请先选择项目")
        return
    
    st.header("🚀 完整处理流水线")
    
    with st.spinner("正在运行完整处理流水线..."):
        try:
            result = process_existing_project(project_id)
            
            if result['success']:
                st.success("✅ 处理完成！")
                display_results(result)
            else:
                st.error(f"❌ 处理失败: {result['error']}")
                
        except Exception as e:
            st.error(f"❌ 处理失败: {str(e)}")

def run_single_step(step: int):
    """运行单个步骤"""
    project_id = st.session_state.get('current_project_id')
    if not project_id:
        st.error("❌ 请先选择项目")
        return
    
    st.header(f"🔄 Step {step}: {get_step_name(step)}")
    
    with st.spinner(f"正在运行 Step {step}..."):
        try:
            processor = AutoClipsProcessor(project_id)
            result = processor.run_single_step(step)
            st.success(f"✅ Step {step} 完成！")
            display_step_result(step, result)

        except Exception as e:
            st.error(f"❌ Step {step} 失败: {str(e)}")

def show_status():
    """显示处理状态"""
    project_id = st.session_state.get('current_project_id')
    if not project_id:
        st.error("❌ 请先选择项目")
        return
    
    st.header("📊 处理状态")
    
    try:
        summary = project_manager.get_project_summary(project_id)
        project_info = summary['project_info']
        file_validation = summary['file_validation']
        processing_progress = summary['processing_progress']
        
        # 项目信息
        st.subheader("📋 项目信息")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("项目名称", project_info['project_name'])
        with col2:
            st.metric("创建时间", project_info['created_at'][:10])
        with col3:
            status_color = {
                'created': 'blue',
                'processing': 'orange', 
                'completed': 'green',
                'error': 'red'
            }.get(project_info['status'], 'gray')
            st.metric("状态", project_info['status'], delta=None)
        
        # 文件验证
        st.subheader("📁 输入文件")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if file_validation['has_video']:
                st.success("✅ 视频文件")
            else:
                st.error("❌ 视频文件")
        
        with col2:
            if file_validation['has_srt']:
                st.success("✅ SRT文件")
            else:
                st.error("❌ SRT文件")
        
        with col3:
            if file_validation['has_txt']:
                st.success("✅ 文本文件")
            else:
                st.info("ℹ️ 文本文件（可选）")
        
        # 处理进度
        st.subheader("📈 处理进度")
        progress = processing_progress['progress_percentage']
        st.progress(progress / 100)
        st.metric(
            "完成进度", 
            f"{processing_progress['current_step']}/{processing_progress['total_steps']}",
            f"{progress:.1f}%"
        )
        
        # 输出统计
        st.subheader("📊 输出统计")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("切片数量", summary['clips_count'])
        with col2:
            st.metric("合集数量", summary['collections_count'])
        
        # 步骤完成状态
        st.subheader("📋 步骤状态")
        processor = AutoClipsProcessor(project_id)
        completed_steps = processor.get_completed_steps()
        
        cols = st.columns(3)
        for i in range(1, 7):
            with cols[(i-1) % 3]:
                if i in completed_steps:
                    st.success(f"✅ Step {i}: {get_step_name(i)}")
                else:
                    st.info(f"⏳ Step {i}: {get_step_name(i)}")
        
        # 错误信息
        if project_info.get('error_message'):
            st.error(f"❌ 错误信息: {project_info['error_message']}")
            
    except Exception as e:
        st.error(f"❌ 获取状态失败: {str(e)}")

def show_main_interface():
    """显示主界面"""
    project_id = st.session_state.get('current_project_id')
    if not project_id:
        st.info("📝 请先创建或选择项目")
        return
    
    st.header("📋 处理概览")
    
    try:
        summary = project_manager.get_project_summary(project_id)
        project_info = summary['project_info']
        
        # 显示项目基本信息
        st.subheader(f"📁 项目: {project_info['project_name']}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("切片数量", summary['clips_count'])
        with col2:
            st.metric("合集数量", summary['collections_count'])
        with col3:
            st.metric("处理状态", project_info['status'])
        
        # 显示切片列表
        if summary['clips_count'] > 0:
            st.subheader("🎬 生成的切片")
            clips = project_manager.get_clips(project_id)
            
            for i, clip in enumerate(clips[:5]):  # 只显示前5个
                with st.expander(f"切片 {i+1}: {clip.get('title', '无标题')}"):
                    st.write(f"**时间区间:** {clip.get('start_time', 'N/A')} - {clip.get('end_time', 'N/A')}")
                    st.write(f"**评分:** {clip.get('score', 'N/A')}")
                    st.write(f"**推荐理由:** {clip.get('recommendation', 'N/A')}")
        
        # 显示合集列表
        if summary['collections_count'] > 0:
            st.subheader("📦 生成的合集")
            collections = project_manager.get_collections(project_id)
            
            for i, collection in enumerate(collections):
                with st.expander(f"合集 {i+1}: {collection.get('theme', '无主题')}"):
                    st.write(f"**主题:** {collection.get('theme', 'N/A')}")
                    st.write(f"**包含切片:** {len(collection.get('clips', []))} 个")
                    st.write(f"**描述:** {collection.get('description', 'N/A')}")
                    
    except Exception as e:
        st.error(f"❌ 获取项目信息失败: {str(e)}")

def display_results(results: Dict[str, Any]):
    """显示处理结果"""
    st.subheader("📊 处理结果")
    
    if 'results' in results:
        result_data = results['results']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("提取话题数", len(result_data.get('step1_outlines', [])))
        with col2:
            st.metric("时间区间数", len(result_data.get('step2_timeline', [])))
        with col3:
            st.metric("高分片段数", len(result_data.get('step3_scoring', [])))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("生成标题数", len(result_data.get('step4_titles', [])))
        with col2:
            st.metric("合集数量", len(result_data.get('step5_collections', [])))
        with col3:
            video_result = result_data.get('step6_video', {})
            st.metric("生成切片", video_result.get('clips_generated', 0))

def display_step_result(step: int, result: Any):
    """显示步骤结果"""
    st.subheader(f"📋 Step {step} 结果")
    
    if isinstance(result, dict):
        st.json(result)
    else:
        st.write(result)

if __name__ == "__main__":
    main() 