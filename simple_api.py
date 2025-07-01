#!/usr/bin/env python3
"""简化版B站上传API服务器"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 创建FastAPI应用
app = FastAPI(
    title="Simple Bilibili Upload API",
    description="简化版B站上传API",
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

@app.get("/")
async def root():
    """根路径"""
    return {"message": "Simple Bilibili Upload API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.get("/api/upload/bilibili/categories")
async def get_bilibili_categories():
    """获取B站分区列表"""
    categories = [
        {"tid": 1, "name": "动画"},
        {"tid": 3, "name": "音乐"},
        {"tid": 4, "name": "游戏"},
        {"tid": 5, "name": "娱乐"},
        {"tid": 11, "name": "电视剧"},
        {"tid": 13, "name": "番剧"},
        {"tid": 17, "name": "单机游戏"},
        {"tid": 21, "name": "日常"},
        {"tid": 22, "name": "鬼畜"},
        {"tid": 23, "name": "电影"},
        {"tid": 24, "name": "纪录片"},
        {"tid": 36, "name": "知识"},
        {"tid": 119, "name": "鬼畜调教"},
        {"tid": 129, "name": "舞蹈"},
        {"tid": 155, "name": "时尚"},
        {"tid": 160, "name": "生活"},
        {"tid": 181, "name": "影视杂谈"},
        {"tid": 188, "name": "科技"},
    ]
    return {"success": True, "data": categories}

@app.get("/api/upload/bilibili/credentials/verify")
async def verify_bilibili_credentials():
    """验证B站登录凭证"""
    return {"success": True, "valid": False, "message": "未设置凭证"}

@app.get("/api/upload/tasks")
async def get_all_tasks():
    """获取所有上传任务"""
    return {"success": True, "data": []}

if __name__ == "__main__":
    print("🚀 启动简化版B站上传API服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)