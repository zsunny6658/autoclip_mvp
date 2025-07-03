#!/usr/bin/env python3
"""
测试合集视频下载功能修复
"""

import requests
import json
import time
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
PROJECT_ID = "a19838d9-6b06-4c57-898c-0b4ed600e160"  # 6.22-004 项目
COLLECTION_ID = "1"  # 投资趋势洞察 合集

def test_collection_download():
    """测试合集视频下载功能"""
    
    print("=== 测试合集视频下载功能 ===")
    
    # 1. 检查项目是否存在
    print(f"1. 检查项目 {PROJECT_ID}...")
    response = requests.get(f"{BASE_URL}/api/projects/{PROJECT_ID}")
    if response.status_code != 200:
        print(f"❌ 项目不存在: {response.status_code}")
        return False
    
    project = response.json()
    print(f"✅ 项目存在: {project['name']}")
    
    # 2. 检查合集是否存在
    print(f"2. 检查合集 {COLLECTION_ID}...")
    collection = None
    for coll in project['collections']:
        if coll['id'] == COLLECTION_ID:
            collection = coll
            break
    
    if not collection:
        print(f"❌ 合集不存在")
        return False
    
    print(f"✅ 合集存在: {collection['collection_title']}")
    
    # 3. 检查合集视频文件是否存在
    print(f"3. 检查合集视频文件...")
    collection_dir = Path(f"./uploads/{PROJECT_ID}/output/collections")
    safe_title = collection['collection_title'].replace('/', '_').replace('\\', '_')
    video_file = collection_dir / f"{safe_title}.mp4"
    
    if video_file.exists():
        print(f"✅ 视频文件存在: {video_file}")
        print(f"   文件大小: {video_file.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print(f"❌ 视频文件不存在: {video_file}")
        return False
    
    # 4. 测试下载接口
    print(f"4. 测试下载接口...")
    download_url = f"{BASE_URL}/api/projects/{PROJECT_ID}/download?collection_id={COLLECTION_ID}"
    
    try:
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            print(f"✅ 下载接口正常")
            print(f"   响应头: {dict(response.headers)}")
            
            # 保存测试文件
            test_file = Path(f"test_download_{COLLECTION_ID}.mp4")
            with open(test_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 测试文件下载成功: {test_file}")
            print(f"   文件大小: {test_file.stat().st_size / 1024 / 1024:.2f} MB")
            
            # 清理测试文件
            test_file.unlink()
            print(f"✅ 测试文件已清理")
            
            return True
        else:
            print(f"❌ 下载接口失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 下载测试异常: {e}")
        return False

def list_collections():
    """列出所有项目中的合集"""
    print("=== 列出所有合集 ===")
    
    response = requests.get(f"{BASE_URL}/api/projects")
    if response.status_code != 200:
        print(f"❌ 获取项目列表失败: {response.status_code}")
        return
    
    projects = response.json()
    
    for project in projects:
        print(f"\n项目: {project['name']} (ID: {project['id']})")
        if project['collections']:
            for coll in project['collections']:
                print(f"  - 合集: {coll['collection_title']} (ID: {coll['id']})")
                
                # 检查视频文件
                collection_dir = Path(f"./uploads/{project['id']}/output/collections")
                safe_title = coll['collection_title'].replace('/', '_').replace('\\', '_')
                video_file = collection_dir / f"{safe_title}.mp4"
                
                if video_file.exists():
                    size_mb = video_file.stat().st_size / 1024 / 1024
                    print(f"    ✅ 视频文件: {video_file.name} ({size_mb:.2f} MB)")
                else:
                    print(f"    ❌ 视频文件不存在")
        else:
            print("  - 无合集")

if __name__ == "__main__":
    print("开始测试合集视频下载功能...")
    
    # 列出所有合集
    list_collections()
    
    print("\n" + "="*50)
    
    # 如果提供了具体的项目ID和合集ID，则进行测试
    if PROJECT_ID != "test_project" and COLLECTION_ID != "test_collection":
        success = test_collection_download()
        if success:
            print("\n🎉 测试通过！合集视频下载功能正常工作")
        else:
            print("\n❌ 测试失败！请检查错误信息")
    else:
        print("请修改脚本中的 PROJECT_ID 和 COLLECTION_ID 进行具体测试") 