"""FastAPI应用 - B站上传API接口"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
from pathlib import Path

from src.upload.upload_manager import UploadManager
from src.upload.bilibili_uploader import BilibiliUploader

# 创建FastAPI应用
app = FastAPI(
    title="Auto Clips Upload API",
    description="自动切片工具上传API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局上传管理器
upload_manager = UploadManager()

# Pydantic模型
class BilibiliCredentials(BaseModel):
    sessdata: str
    bili_jct: str
    buvid3: str
    dedeuserid: str
    ac_time_value: str

class UploadTaskRequest(BaseModel):
    video_path: str
    title: str
    description: str = ""
    category_id: int = 21  # 默认日常分区
    tags: List[str] = []
    cover_path: Optional[str] = None

class TaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    message: str = ""

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Auto Clips Upload API", "version": "1.0.0"}

@app.get("/api/upload/bilibili/categories")
async def get_bilibili_categories():
    """获取B站分区列表"""
    try:
        uploader = BilibiliUploader()
        categories = uploader.get_video_categories()
        return {"success": True, "data": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/bilibili/credentials")
async def set_bilibili_credentials(credentials: BilibiliCredentials):
    """设置B站登录凭证"""
    try:
        success = await upload_manager.set_platform_credentials(
            "bilibili",
            {
                "SESSDATA": credentials.sessdata,
                "bili_jct": credentials.bili_jct,
                "buvid3": credentials.buvid3,
                "DedeUserID": credentials.dedeuserid,
                "ac_time_value": credentials.ac_time_value
            }
        )
        return {"success": success, "message": "凭证设置成功" if success else "凭证设置失败"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/bilibili/credentials/verify")
async def verify_bilibili_credentials():
    """验证B站登录凭证"""
    try:
        is_valid = await upload_manager.verify_platform_credential("bilibili")
        return {"success": True, "valid": is_valid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload/bilibili/upload")
async def create_upload_task(task_request: UploadTaskRequest, background_tasks: BackgroundTasks):
    """创建B站上传任务"""
    try:
        # 检查视频文件是否存在
        video_path = Path(task_request.video_path)
        if not video_path.exists():
            raise HTTPException(status_code=400, detail=f"视频文件不存在: {task_request.video_path}")
        
        # 创建上传任务
        task = await upload_manager.create_upload_task(
            platform="bilibili",
            video_path=task_request.video_path,
            title=task_request.title,
            description=task_request.description,
            category_id=task_request.category_id,
            tags=task_request.tags,
            cover_path=task_request.cover_path
        )
        
        # 在后台启动上传
        background_tasks.add_task(upload_manager.start_upload, task.task_id)
        
        return {
            "success": True,
            "task_id": task.task_id,
            "message": "上传任务创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取上传任务状态"""
    try:
        task = await upload_manager.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return {
            "success": True,
            "data": {
                "task_id": task.task_id,
                "status": task.status,
                "progress": task.progress,
                "platform": task.platform,
                "title": task.title,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "error_message": task.error_message
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/upload/tasks")
async def get_all_tasks():
    """获取所有上传任务"""
    try:
        tasks = await upload_manager.get_all_tasks()
        return {
            "success": True,
            "data": [
                {
                    "task_id": task.task_id,
                    "status": task.status,
                    "progress": task.progress,
                    "platform": task.platform,
                    "title": task.title,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "error_message": task.error_message
                }
                for task in tasks
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/upload/tasks/{task_id}")
async def cancel_upload_task(task_id: str):
    """取消上传任务"""
    try:
        success = await upload_manager.cancel_upload(task_id)
        return {
            "success": success,
            "message": "任务取消成功" if success else "任务取消失败"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)