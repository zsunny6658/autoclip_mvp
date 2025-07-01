#!/usr/bin/env python3
"""
FastAPI后端服务器 - 自动切片工具API服务
提供RESTful API接口，支持前端React应用的所有功能需求
"""

import os
import json
import uuid
import shutil
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# 导入项目模块
import sys
sys.path.append(str(Path(__file__).parent))

from src.main import AutoClipsProcessor
from src.config import OUTPUT_DIR, CLIPS_DIR, COLLECTIONS_DIR, METADATA_DIR, DASHSCOPE_API_KEY, VideoCategory, VIDEO_CATEGORIES_CONFIG
from src.upload.upload_manager import UploadManager, Platform, UploadStatus

# 配置日志
logger = logging.getLogger(__name__)

# 数据模型
class ProjectStatus(BaseModel):
    status: str  # 'uploading', 'processing', 'completed', 'error'
    current_step: Optional[int] = None
    total_steps: Optional[int] = 6
    step_name: Optional[str] = None
    progress: Optional[float] = 0.0
    error_message: Optional[str] = None

class Clip(BaseModel):
    id: str
    title: Optional[str] = None
    start_time: str
    end_time: str
    final_score: float
    recommend_reason: str
    generated_title: Optional[str] = None
    outline: str
    content: List[str]
    chunk_index: Optional[int] = None

class Collection(BaseModel):
    id: str
    collection_title: str
    collection_summary: str
    clip_ids: List[str]
    collection_type: str = "ai_recommended"  # "ai_recommended" or "manual"
    created_at: Optional[str] = None

class Project(BaseModel):
    id: str
    name: str
    video_path: str
    status: str
    created_at: str
    updated_at: str
    video_category: str = "default"  # 新增视频分类字段
    clips: List[Clip] = []
    collections: List[Collection] = []
    current_step: Optional[int] = None
    total_steps: Optional[int] = 6
    error_message: Optional[str] = None

class ClipUpdate(BaseModel):
    title: Optional[str] = None
    recommend_reason: Optional[str] = None
    generated_title: Optional[str] = None

class CollectionUpdate(BaseModel):
    collection_title: Optional[str] = None
    collection_summary: Optional[str] = None
    clip_ids: Optional[List[str]] = None

class ApiSettings(BaseModel):
    dashscope_api_key: str
    model_name: str = "qwen-plus"
    chunk_size: int = 5000
    min_score_threshold: float = 0.7
    max_clips_per_collection: int = 5

class UploadRequest(BaseModel):
    platform: str  # "bilibili"
    video_path: str
    title: str
    desc: str = ""
    tags: List[str] = []
    cover_path: Optional[str] = None
    tid: Optional[int] = 21  # B站分区ID

class BilibiliCredential(BaseModel):
    sessdata: str
    bili_jct: str
    buvid3: str = ""

class UploadTaskResponse(BaseModel):
    task_id: str
    platform: str
    status: str
    progress: float
    title: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 全局状态管理
class ProjectManager:
    def __init__(self):
        self.projects: Dict[str, Project] = {}
        self.processing_status: Dict[str, ProjectStatus] = {}
        self.data_dir = Path("./data")
        self.data_dir.mkdir(exist_ok=True)
        self.processing_lock = asyncio.Lock()  # 防止并发处理
        self.max_concurrent_processing = 1  # 最大并发处理数
        self.current_processing_count = 0
        self.upload_manager = UploadManager()  # 上传管理器
        self.load_projects()
    
    def load_projects(self):
        """从磁盘加载项目数据"""
        projects_file = self.data_dir / "projects.json"
        if projects_file.exists():
            try:
                with open(projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 限制一次加载的项目数量，避免内存占用过大
                    if len(data) > 100:
                        logger.warning(f"项目数量过多({len(data)})，只加载最近的100个项目")
                        # 按更新时间排序，取最新的100个
                        data = sorted(data, key=lambda x: x.get('updated_at', ''), reverse=True)[:100]
                    
                    for project_data in data:
                        try:
                            project = Project(**project_data)
                            self.projects[project.id] = project
                        except Exception as e:
                            logger.error(f"加载项目 {project_data.get('id', 'unknown')} 失败: {e}")
                            continue
                            
                logger.info(f"成功加载 {len(self.projects)} 个项目")
            except Exception as e:
                logger.error(f"加载项目数据失败: {e}")
    
    def save_projects(self):
        """保存项目数据到磁盘"""
        projects_file = self.data_dir / "projects.json"
        try:
            with open(projects_file, 'w', encoding='utf-8') as f:
                projects_data = [project.dict() for project in self.projects.values()]
                json.dump(projects_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存项目数据失败: {e}")
    
    def create_project(self, name: str, video_path: str, project_id: str = None, video_category: str = "default") -> Project:
        """创建新项目"""
        if project_id is None:
            project_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        project = Project(
            id=project_id,
            name=name,
            video_path=video_path,
            status="uploading",
            created_at=now,
            updated_at=now,
            video_category=video_category
        )
        
        self.projects[project_id] = project
        self.save_projects()
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # 动态加载最新的clips和collections数据
        try:
            project_dir = Path("./uploads") / project_id
            metadata_dir = project_dir / "output" / "metadata"
            
            # 加载clips数据
            clips_file = metadata_dir / "clips_metadata.json"
            if clips_file.exists():
                with open(clips_file, 'r', encoding='utf-8') as f:
                    clips_data = json.load(f)
                    project.clips = [Clip(**clip) for clip in clips_data]
            
            # 加载collections数据
            collections_file = metadata_dir / "collections_metadata.json"
            if collections_file.exists():
                with open(collections_file, 'r', encoding='utf-8') as f:
                    collections_data = json.load(f)
                    project.collections = [Collection(**collection) for collection in collections_data]
        except Exception as e:
            logger.error(f"加载项目 {project_id} 的最新数据失败: {e}")
        
        return project
    
    def update_project(self, project_id: str, **updates) -> Optional[Project]:
        """更新项目"""
        if project_id not in self.projects:
            return None
        
        project = self.projects[project_id]
        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        project.updated_at = datetime.now().isoformat()
        self.save_projects()
        return project
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        if project_id not in self.projects:
            return False
        
        project = self.projects[project_id]
        
        # 删除项目文件夹（uploads目录下的项目文件夹）
        try:
            uploads_dir = Path("./uploads")
            project_dir = uploads_dir / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir)
                logger.info(f"已删除项目目录: {project_dir}")
            else:
                logger.warning(f"项目目录不存在: {project_dir}")
        except Exception as e:
            logger.error(f"删除项目文件失败: {e}")
        
        # 删除项目记录
        del self.projects[project_id]
        if project_id in self.processing_status:
            del self.processing_status[project_id]
        
        self.save_projects()
        logger.info(f"项目已删除: {project_id}")
        return True

# 初始化项目管理器
project_manager = ProjectManager()

# 处理状态存储
processing_status = {}

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    print("🚀 FastAPI服务器启动")
    yield
    # 关闭时
    print("🛑 FastAPI服务器关闭")

# 创建FastAPI应用
app = FastAPI(
    title="自动切片工具 API",
    description="视频自动切片和智能推荐系统的后端API服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="output"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# API路由

@app.get("/")
async def root():
    """根路径"""
    return {"message": "自动切片工具 API 服务", "version": "1.0.0"}

@app.get("/api/video-categories")
async def get_video_categories():
    """获取视频分类配置"""
    categories = []
    for key, config in VIDEO_CATEGORIES_CONFIG.items():
        categories.append({
            "value": key,
            "name": config["name"],
            "description": config["description"],
            "icon": config["icon"],
            "color": config["color"]
        })
    
    return {
        "categories": categories,
        "default_category": VideoCategory.DEFAULT
    }

@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    """获取所有项目"""
    try:
        # 使用异步方式获取项目列表，避免阻塞
        projects = await asyncio.get_event_loop().run_in_executor(
            None, lambda: list(project_manager.projects.values())
        )
        return projects
    except Exception as e:
        logger.error(f"get_projects failed: {e}")
        return []

@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """获取单个项目详情"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_project failed for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.put("/api/projects/{project_id}/category")
async def update_project_category(project_id: str, video_category: str = Form(...)):
    """更新项目的视频分类"""
    try:
        # 验证分类是否有效
        if video_category not in [category.value for category in VideoCategory]:
            raise HTTPException(status_code=400, detail="无效的视频分类")
        
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 更新项目分类
        project.video_category = video_category
        project.updated_at = datetime.now().isoformat()
        
        # 保存项目
        project_manager.save_projects()
        
        return {"message": "项目分类更新成功", "video_category": video_category}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_project_category failed for {project_id}: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.post("/api/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    srt_file: Optional[UploadFile] = File(None),
    project_name: str = Form(...),
    video_category: str = Form("default")
):
    """上传文件并创建项目"""
    # 验证文件类型
    if not video_file.filename or not video_file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="不支持的视频格式")
    
    # 创建项目ID
    project_id = str(uuid.uuid4())
    project_dir = Path("./uploads") / project_id
    input_dir = project_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    
    # 保存视频文件到input子目录
    video_extension = video_file.filename.split('.')[-1]
    video_path = input_dir / f"input.{video_extension}"
    with open(video_path, "wb") as f:
        content = await video_file.read()
        f.write(content)
    
    # 保存字幕文件到input子目录
    if srt_file:
        srt_path = input_dir / "input.srt"
        with open(srt_path, "wb") as f:
            content = await srt_file.read()
            f.write(content)
    
    # 创建项目记录（video_path相对于项目根目录）
    relative_video_path = f"uploads/{project_id}/input/input.{video_extension}"
    project = project_manager.create_project(project_name, relative_video_path, project_id, video_category)
    
    return project

async def process_project_background(project_id: str, start_step: int = 1):
    """后台处理项目"""
    try:
        # 更新状态为处理中
        project_manager.update_project(project_id, status="processing")
        processing_status[project_id] = {
            "status": "processing",
            "current_step": start_step,
            "total_steps": 6,
            "step_name": f"从步骤{start_step}开始处理",
            "progress": ((start_step - 1) / 6) * 100
        }
        
        # 获取项目信息
        project = project_manager.get_project(project_id)
        if not project:
            return
        
        # 定义进度回调函数
        def update_progress(current_step, total_steps, step_name, progress):
            processing_status[project_id].update({
                "status": "processing",
                "current_step": current_step,
                "total_steps": total_steps,
                "step_name": step_name,
                "progress": progress
            })
        
        # 创建处理器并运行
        processor = AutoClipsProcessor(project_id)
        
        # 根据起始步骤选择处理方式
        try:
            if start_step == 1:
                # 从头开始运行完整流水线
                result = processor.run_full_pipeline(update_progress)
            else:
                # 从指定步骤开始运行
                result = processor.run_from_step(start_step, update_progress)
        except Exception as e:
            logger.error(f"处理器运行失败: {str(e)}")
            result = {'success': False, 'error': str(e)}
        
        if result.get('success'):
            # 读取final_results.json并提取clips和collections数据
            try:
                final_results_path = Path(f"uploads/{project_id}/output/metadata/final_results.json")
                if final_results_path.exists():
                    with open(final_results_path, 'r', encoding='utf-8') as f:
                        final_results = json.load(f)
                    
                    # 提取clips数据
                    clips = final_results.get('step3_scoring', [])
                    collections = final_results.get('step5_collections', [])
                    
                    # 修复clips数据：将generated_title映射为title字段
                    for clip in clips:
                        if 'generated_title' in clip and clip['generated_title']:
                            clip['title'] = clip['generated_title']
                        elif 'title' not in clip or clip['title'] is None:
                            # 如果没有generated_title，使用outline作为fallback
                            clip['title'] = clip.get('outline', f"片段 {clip.get('id', '')}")
                    
                    # 更新项目状态，包含clips和collections数据
                    project_manager.update_project(
                        project_id, 
                        status="completed",
                        clips=clips,
                        collections=collections
                    )
                else:
                    # 如果没有final_results.json，只更新状态
                    project_manager.update_project(project_id, status="completed")
            except Exception as e:
                logger.error(f"读取final_results.json失败: {e}")
                # 即使读取失败，也要更新项目状态
                project_manager.update_project(project_id, status="completed")
            
            processing_status[project_id].update({
                "status": "completed",
                "current_step": 6,
                "total_steps": 6,
                "step_name": "处理完成",
                "progress": 100.0
            })
        else:
            # 处理失败
            error_msg = result.get('error', '处理过程中发生未知错误')
            project_manager.update_project(project_id, status="error", error_message=error_msg)
            processing_status[project_id] = {
                "status": "error",
                "current_step": processing_status[project_id].get("current_step", 0),
                "total_steps": 6,
                "step_name": "处理失败",
                "progress": 0,
                "error_message": error_msg
            }
    
    except Exception as e:
        # 处理异常
        error_msg = f"处理失败: {str(e)}"
        project_manager.update_project(project_id, status="error", error_message=error_msg)
        processing_status[project_id] = {
            "status": "error",
            "current_step": processing_status[project_id].get("current_step", 0),
            "total_steps": 6,
            "step_name": "处理失败",
            "progress": 0,
            "error_message": error_msg
        }

async def process_project_background_with_lock(project_id: str, start_step: int = 1):
    """带资源锁的后台处理项目"""
    try:
        await process_project_background(project_id, start_step)
    finally:
        # 无论成功还是失败，都要释放处理锁
        async with project_manager.processing_lock:
            if project_manager.current_processing_count > 0:
                project_manager.current_processing_count -= 1
        logger.info(f"项目 {project_id} 处理完成，当前并发处理数: {project_manager.current_processing_count}")

@app.post("/api/projects/{project_id}/process")
async def start_processing(project_id: str, background_tasks: BackgroundTasks):
    """开始处理项目"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.status != "uploading":
        raise HTTPException(status_code=400, detail="项目状态不允许处理")
    
    # 检查并发处理限制
    async with project_manager.processing_lock:
        if project_manager.current_processing_count >= project_manager.max_concurrent_processing:
            raise HTTPException(status_code=429, detail="系统正在处理其他项目，请稍后再试")
        
        project_manager.current_processing_count += 1
    
    # 添加后台任务
    background_tasks.add_task(process_project_background_with_lock, project_id)
    
    return {"message": "开始处理项目"}

@app.post("/api/projects/{project_id}/retry")
async def retry_project_processing(project_id: str, background_tasks: BackgroundTasks):
    """重试处理项目"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if project.status != "error":
        raise HTTPException(status_code=400, detail="只有失败的项目才能重试")
    
    # 获取失败时的步骤，从该步骤开始重试
    failed_step = 1
    if project_id in processing_status:
        failed_step = processing_status[project_id].get("current_step", 1)
    elif hasattr(project, 'current_step') and project.current_step:
        failed_step = project.current_step
    
    # 清除之前的错误信息，但保持当前步骤信息
    project_manager.update_project(project_id, status="uploading", error_message=None)
    
    # 清除处理状态
    if project_id in processing_status:
        del processing_status[project_id]
    
    # 检查并发处理限制
    async with project_manager.processing_lock:
        if project_manager.current_processing_count >= project_manager.max_concurrent_processing:
            raise HTTPException(status_code=429, detail="系统正在处理其他项目，请稍后再试")
        
        project_manager.current_processing_count += 1
    
    # 添加后台任务从失败步骤开始重新处理
    background_tasks.add_task(process_project_background_with_lock, project_id, failed_step)
    
    return {"message": f"开始从步骤 {failed_step} 重试处理项目"}

@app.get("/api/system/status")
async def get_system_status():
    """获取系统状态"""
    return {
        "current_processing_count": project_manager.current_processing_count,
        "max_concurrent_processing": project_manager.max_concurrent_processing,
        "total_projects": len(project_manager.projects),
        "processing_projects": [
            project_id for project_id, status in processing_status.items() 
            if status.get("status") == "processing"
        ]
    }

@app.post("/api/projects/{project_id}/collections")
async def create_collection(project_id: str, collection_data: dict):
    """创建新合集"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 验证请求数据
        if not collection_data.get("collection_title"):
            raise HTTPException(status_code=400, detail="合集标题不能为空")
        
        if not collection_data.get("clip_ids") or not isinstance(collection_data["clip_ids"], list):
            raise HTTPException(status_code=400, detail="必须选择至少一个片段")
        
        # 验证片段ID是否存在
        valid_clip_ids = [clip.id for clip in project.clips]
        for clip_id in collection_data["clip_ids"]:
            if clip_id not in valid_clip_ids:
                raise HTTPException(status_code=400, detail=f"片段ID {clip_id} 不存在")
        
        # 创建新合集
        collection_id = str(uuid.uuid4())
        new_collection = Collection(
            id=collection_id,
            collection_title=collection_data["collection_title"],
            collection_summary=collection_data.get("collection_summary", ""),
            clip_ids=collection_data["clip_ids"],
            collection_type="manual",
            created_at=datetime.now().isoformat()
        )
        
        # 添加到项目中
        project.collections.append(new_collection)
        
        # 保存项目
        project_manager.save_projects()
        
        # 更新项目的合集元数据文件
        try:
            metadata_dir = Path("./uploads") / project_id / "output" / "metadata"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            
            collections_metadata_file = metadata_dir / "collections_metadata.json"
            collections_metadata = []
            
            # 如果文件已存在，读取现有数据
            if collections_metadata_file.exists():
                with open(collections_metadata_file, 'r', encoding='utf-8') as f:
                    collections_metadata = json.load(f)
            
            # 添加新合集到元数据
            collection_metadata = {
                "id": collection_id,
                "collection_title": new_collection.collection_title,
                "collection_summary": new_collection.collection_summary,
                "clip_ids": new_collection.clip_ids,
                "collection_type": new_collection.collection_type,
                "created_at": new_collection.created_at
            }
            collections_metadata.append(collection_metadata)
            
            # 保存更新后的元数据
            with open(collections_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(collections_metadata, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"保存合集元数据失败: {e}")
        
        return new_collection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建合集失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建合集失败: {str(e)}")

@app.delete("/api/projects/{project_id}/collections/{collection_id}")
async def delete_collection(project_id: str, collection_id: str):
    """删除合集"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 查找指定的合集
        collection_index = None
        for i, coll in enumerate(project.collections):
            if coll.id == collection_id:
                collection_index = i
                break
        
        if collection_index is None:
            raise HTTPException(status_code=404, detail="合集不存在")
        
        # 从项目中删除合集
        deleted_collection = project.collections.pop(collection_index)
        
        # 保存项目
        project_manager.save_projects()
        
        # 删除合集元数据文件中的记录
        try:
            metadata_dir = Path("./uploads") / project_id / "output" / "metadata"
            collections_metadata_file = metadata_dir / "collections_metadata.json"
            
            if collections_metadata_file.exists():
                with open(collections_metadata_file, 'r', encoding='utf-8') as f:
                    collections_metadata = json.load(f)
                
                # 过滤掉被删除的合集
                collections_metadata = [c for c in collections_metadata if c.get("id") != collection_id]
                
                # 保存更新后的元数据
                with open(collections_metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(collections_metadata, f, ensure_ascii=False, indent=2)
                    
        except Exception as e:
            logger.warning(f"删除合集元数据失败: {e}")
        
        # 删除合集生成的视频文件（如果存在）
        try:
            collection_video_path = Path(f"./uploads/{project_id}/output/collections/{collection_id}.mp4")
            if collection_video_path.exists():
                collection_video_path.unlink()
                logger.info(f"已删除合集视频文件: {collection_video_path}")
        except Exception as e:
            logger.warning(f"删除合集视频文件失败: {e}")
        
        return {"message": "合集删除成功", "deleted_collection": deleted_collection.collection_title}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除合集失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除合集失败: {str(e)}")

@app.post("/api/projects/{project_id}/collections/{collection_id}/generate")
async def generate_collection_video(project_id: str, collection_id: str, background_tasks: BackgroundTasks):
    """生成合集视频"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 查找指定的合集
    collection = None
    for coll in project.collections:
        if coll.id == collection_id:
            collection = coll
            break
    
    if not collection:
        raise HTTPException(status_code=404, detail="合集不存在")
    
    # 添加后台任务生成合集视频
    background_tasks.add_task(generate_collection_video_background, project_id, collection_id)
    
    return {"message": "开始生成合集视频"}

async def generate_collection_video_background(project_id: str, collection_id: str):
    """后台生成合集视频"""
    try:
        from src.utils.video_processor import VideoProcessor
        import subprocess
        
        project = project_manager.get_project(project_id)
        if not project:
            return
        
        # 查找指定的合集
        collection = None
        for coll in project.collections:
            if coll.id == collection_id:
                collection = coll
                break
        
        if not collection:
            return
        
        # 获取合集中的所有切片视频路径
        clips_dir = Path(f"./uploads/{project_id}/output/clips")
        collection_clips_dir = Path(f"./uploads/{project_id}/output/collections")
        collection_clips_dir.mkdir(exist_ok=True)
        
        clip_paths = []
        for clip_id in collection.clip_ids:
            # 查找对应的切片视频文件
            clip_files = list(clips_dir.glob(f"{clip_id}_*.mp4"))
            if clip_files:
                clip_paths.append(str(clip_files[0]))
        
        if not clip_paths:
            logger.error(f"合集 {collection_id} 中没有找到有效的切片视频")
            return
        
        # 生成合集视频文件路径
        output_path = collection_clips_dir / f"{collection_id}.mp4"
        
        # 创建临时文件列表
        temp_list_file = collection_clips_dir / f"{collection_id}_list.txt"
        with open(temp_list_file, 'w', encoding='utf-8') as f:
            for clip_path in clip_paths:
                f.write(f"file '{clip_path}'\n")
        
        # 使用ffmpeg合并视频
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(temp_list_file),
            '-c', 'copy',
            '-y',  # 覆盖输出文件
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 清理临时文件
        if temp_list_file.exists():
            temp_list_file.unlink()
        
        if result.returncode == 0:
            logger.info(f"合集视频生成成功: {output_path}")
        else:
            logger.error(f"合集视频生成失败: {result.stderr}")
            
    except Exception as e:
        logger.error(f"生成合集视频时发生错误: {str(e)}")

@app.get("/api/projects/{project_id}/status")
async def get_processing_status(project_id: str):
    """获取处理状态"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 返回处理状态
    if project_id in processing_status:
        return processing_status[project_id]
    else:
        # 如果没有处理状态记录，根据项目状态返回默认状态
        if project.status == "completed":
            return {
                "status": "completed",
                "current_step": 6,
                "total_steps": 6,
                "step_name": "处理完成",
                "progress": 100.0
            }
        elif project.status == "error":
            return {
                "status": "error",
                "current_step": 0,
                "total_steps": 6,
                "step_name": "处理失败",
                "progress": 0,
                "error_message": project.error_message or "处理过程中发生错误"
            }
        else:
            return {
                "status": "processing",
                "current_step": 0,
                "total_steps": 6,
                "step_name": "准备处理",
                "progress": 0
            }

@app.get("/api/projects/{project_id}/logs")
async def get_project_logs(project_id: str, lines: int = 50):
    """获取项目处理日志"""
    try:
        project = project_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        log_file = "auto_clips.log"
        if not os.path.exists(log_file):
            return {"logs": []}
        
        # 读取日志文件的最后N行
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
        
        # 获取最后N行
        recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        # 解析日志行
        logs = []
        for line in recent_lines:
            line = line.strip()
            if line:
                # 解析日志格式: 时间戳 - 模块 - 级别 - 消息
                parts = line.split(' - ', 3)
                if len(parts) >= 4:
                    timestamp = parts[0]
                    module = parts[1]
                    level = parts[2]
                    message = parts[3]
                    logs.append({
                        "timestamp": timestamp,
                        "module": module,
                        "level": level,
                        "message": message
                    })
                else:
                    # 如果格式不匹配，直接作为消息
                    logs.append({
                        "timestamp": "",
                        "module": "",
                        "level": "INFO",
                        "message": line
                    })
        
        return {"logs": logs}
    except Exception as e:
        logger.error(f"get_project_logs failed for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/download")
async def download_project_video(project_id: str, clip_id: str = None, collection_id: str = None):
    """下载项目视频文件"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    if clip_id:
        # 下载切片视频
        clip_files = list(CLIPS_DIR.glob(f"{clip_id}_*.mp4"))
        if not clip_files:
            raise HTTPException(status_code=404, detail="切片视频不存在")
        file_path = clip_files[0]
        filename = f"clip_{clip_id}.mp4"
    elif collection_id:
        # 下载合集视频
        file_path = COLLECTIONS_DIR / f"{collection_id}.mp4"
        filename = f"collection_{collection_id}.mp4"
    else:
        # 下载原始视频
        file_path = Path(project.video_path)
        filename = f"project_{project_id}.mp4"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    success = project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"message": "项目删除成功"}

@app.get("/api/projects/{project_id}/files/{file_path:path}")
async def get_project_file(project_id: str, file_path: str):
    """获取项目文件"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 构建文件路径
    full_file_path = Path("./uploads") / project_id / file_path
    
    if not full_file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 检查文件是否在项目目录内（安全检查）
    try:
        full_file_path.resolve().relative_to(Path("./uploads").resolve() / project_id)
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")
    
    return FileResponse(path=full_file_path)

@app.get("/api/projects/{project_id}/clips/{clip_id}")
async def get_clip_video(project_id: str, clip_id: str):
    """根据clipId获取切片视频文件"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 查找clips目录下以clip_id开头的mp4文件
    clips_dir = Path("./uploads") / project_id / "output" / "clips"
    if not clips_dir.exists():
        raise HTTPException(status_code=404, detail="切片目录不存在")
    
    # 查找匹配的文件
    matching_files = list(clips_dir.glob(f"{clip_id}_*.mp4"))
    if not matching_files:
        raise HTTPException(status_code=404, detail="切片视频文件不存在")
    
    # 返回第一个匹配的文件
    video_file = matching_files[0]
    return FileResponse(
        path=video_file, 
        media_type='video/mp4',
        headers={
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'no-cache'
        }
    )

# 设置相关API
@app.get("/api/settings")
async def get_settings():
    """获取系统配置"""
    try:
        settings_file = Path("./data/settings.json")
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        else:
            # 返回默认配置
            settings = {
                "dashscope_api_key": DASHSCOPE_API_KEY or "",
                "model_name": "qwen-plus",
                "chunk_size": 5000,
                "min_score_threshold": 0.7,
                "max_clips_per_collection": 5
            }
        return settings
    except Exception as e:
        logger.error(f"获取设置失败: {e}")
        raise HTTPException(status_code=500, detail="获取设置失败")

@app.post("/api/settings")
async def update_settings(settings: ApiSettings):
    """更新系统配置"""
    try:
        settings_file = Path("./data/settings.json")
        settings_file.parent.mkdir(exist_ok=True)
        
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings.dict(), f, ensure_ascii=False, indent=2)
        
        # 更新环境变量
        os.environ["DASHSCOPE_API_KEY"] = settings.dashscope_api_key
        
        return {"message": "配置更新成功"}
    except Exception as e:
        logger.error(f"更新设置失败: {e}")
        raise HTTPException(status_code=500, detail="更新设置失败")

@app.post("/api/settings/test-api-key")
async def test_api_key(request: dict):
    """测试API密钥"""
    try:
        api_key = request.get("api_key")
        if not api_key:
            return {"success": False, "error": "API密钥不能为空"}
        
        # 创建临时LLM客户端测试连接
        try:
            from src.utils.llm_client import LLMClient
            llm_client = LLMClient(api_key=api_key)
            # 发送一个简单的测试请求
            test_response = llm_client.call_llm("测试连接", "请回复'连接成功'")
            if test_response and "连接成功" in test_response:
                return {"success": True}
            else:
                return {"success": True}  # 即使回复不完全匹配也认为连接成功
        except Exception as e:
            return {"success": False, "error": f"API密钥测试失败: {str(e)}"}
    except Exception as e:
        logger.error(f"测试API密钥失败: {e}")
        return {"success": False, "error": "测试过程中发生错误"}

# ==================== 上传相关API ====================

@app.post("/api/upload/bilibili/credential")
async def set_bilibili_credential(credential: BilibiliCredential):
    """设置B站登录凭证"""
    try:
        project_manager.upload_manager.set_bilibili_credential(
            sessdata=credential.sessdata,
            bili_jct=credential.bili_jct,
            buvid3=credential.buvid3
        )
        
        # 验证凭证
        is_valid = await project_manager.upload_manager.verify_platform_credential(Platform.BILIBILI)
        
        if is_valid:
            return {"success": True, "message": "B站凭证设置成功"}
        else:
            return {"success": False, "error": "B站凭证验证失败"}
            
    except Exception as e:
        logger.error(f"设置B站凭证失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/upload/bilibili/verify")
async def verify_bilibili_credential():
    """验证B站登录凭证"""
    try:
        is_valid = await project_manager.upload_manager.verify_platform_credential(Platform.BILIBILI)
        return {"success": True, "valid": is_valid}
    except Exception as e:
        logger.error(f"验证B站凭证失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/upload/bilibili/categories")
async def get_bilibili_categories():
    """获取B站分区列表"""
    try:
        categories = project_manager.upload_manager.get_platform_categories(Platform.BILIBILI)
        return {"success": True, "categories": categories}
    except Exception as e:
        logger.error(f"获取B站分区失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/upload/create")
async def create_upload_task(upload_request: UploadRequest):
    """创建上传任务"""
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 验证平台
        if upload_request.platform.lower() == "bilibili":
            platform = Platform.BILIBILI
        else:
            raise ValueError(f"不支持的平台: {upload_request.platform}")
        
        # 验证视频文件是否存在
        if not os.path.exists(upload_request.video_path):
            raise FileNotFoundError(f"视频文件不存在: {upload_request.video_path}")
        
        # 创建上传任务
        task = await project_manager.upload_manager.create_upload_task(
            task_id=task_id,
            platform=platform,
            video_path=upload_request.video_path,
            title=upload_request.title,
            desc=upload_request.desc,
            tags=upload_request.tags,
            cover_path=upload_request.cover_path,
            tid=upload_request.tid,
            auto_start=True
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "上传任务创建成功"
        }
        
    except Exception as e:
        logger.error(f"创建上传任务失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/upload/tasks/{task_id}", response_model=UploadTaskResponse)
async def get_upload_task_status(task_id: str):
    """获取上传任务状态"""
    try:
        task_status = project_manager.upload_manager.get_task_status(task_id)
        
        if not task_status:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return UploadTaskResponse(**task_status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取上传任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/tasks")
async def get_all_upload_tasks():
    """获取所有上传任务"""
    try:
        tasks = project_manager.upload_manager.get_all_tasks()
        return {"success": True, "tasks": tasks}
    except Exception as e:
        logger.error(f"获取上传任务列表失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/upload/tasks/{task_id}/cancel")
async def cancel_upload_task(task_id: str):
    """取消上传任务"""
    try:
        success = await project_manager.upload_manager.cancel_upload(task_id)
        
        if success:
            return {"success": True, "message": "任务已取消"}
        else:
            return {"success": False, "error": "取消任务失败"}
            
    except Exception as e:
        logger.error(f"取消上传任务失败: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/upload/clips/{clip_id}")
async def upload_clip_to_platform(
    clip_id: str,
    platform: str = Form(...),
    title: str = Form(...),
    desc: str = Form(""),
    tags: str = Form(""),  # 逗号分隔的标签
    tid: int = Form(21)
):
    """上传指定切片到平台"""
    try:
        # 查找切片文件
        clip_file = None
        for project in project_manager.projects.values():
            for clip in project.clips:
                if clip.id == clip_id:
                    # 构建切片文件路径
                    clip_filename = f"{clip_id}.mp4"
                    clip_file = CLIPS_DIR / clip_filename
                    break
            if clip_file:
                break
        
        if not clip_file or not clip_file.exists():
            raise FileNotFoundError(f"切片文件不存在: {clip_id}")
        
        # 解析标签
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # 创建上传请求
        upload_request = UploadRequest(
            platform=platform,
            video_path=str(clip_file),
            title=title,
            desc=desc,
            tags=tag_list,
            tid=tid
        )
        
        # 创建上传任务
        result = await create_upload_task(upload_request)
        return result
        
    except Exception as e:
        logger.error(f"上传切片失败: {e}")
        return {"success": False, "error": str(e)}

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # 确保必要的目录存在
    Path("./uploads").mkdir(exist_ok=True)
    Path("./data").mkdir(exist_ok=True)
    Path("./output").mkdir(exist_ok=True)
    
    # 加载配置文件并设置环境变量
    try:
        settings_file = Path("./data/settings.json")
        if settings_file.exists():
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                if settings.get("dashscope_api_key"):
                    os.environ["DASHSCOPE_API_KEY"] = settings["dashscope_api_key"]
                    logger.info("已从配置文件加载 DASHSCOPE_API_KEY")
                else:
                    logger.warning("配置文件中未找到有效的 DASHSCOPE_API_KEY")
        else:
            logger.warning("配置文件不存在，请在前端设置 API 密钥")
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
    
    # 启动服务器
    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )