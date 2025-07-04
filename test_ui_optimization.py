#!/usr/bin/env python3
"""
测试UI优化 - 验证合集页面的按钮修改
"""

import requests
import json
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"

def test_ui_optimization():
    """测试UI优化是否正确应用"""
    
    print("=== 测试UI优化 ===")
    
    # 1. 检查前端文件是否存在
    print("1. 检查前端文件...")
    
    frontend_files = [
        "frontend/src/components/CollectionCard.tsx",
        "frontend/src/components/CollectionPreviewModal.tsx",
        "frontend/src/pages/ProjectDetailPage.tsx"
    ]
    
    for file_path in frontend_files:
        if Path(file_path).exists():
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
    
    # 2. 检查后端API是否正常
    print("\n2. 检查后端API...")
    try:
        response = requests.get(f"{BASE_URL}/api/projects")
        if response.status_code == 200:
            print("✅ 后端API正常")
            projects = response.json()
            print(f"   当前项目数量: {len(projects)}")
        else:
            print(f"❌ 后端API异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 后端连接失败: {e}")
    
    # 3. 检查合集功能
    print("\n3. 检查合集功能...")
    try:
        response = requests.get(f"{BASE_URL}/api/projects")
        if response.status_code == 200:
            projects = response.json()
            total_collections = 0
            for project in projects:
                total_collections += len(project.get('collections', []))
            print(f"✅ 合集功能正常，总合集数: {total_collections}")
        else:
            print("❌ 无法获取项目列表")
    except Exception as e:
        print(f"❌ 合集功能检查失败: {e}")
    
    # 4. 检查文件修改内容
    print("\n4. 检查文件修改内容...")
    
    # 检查CollectionCard.tsx
    collection_card_path = "frontend/src/components/CollectionCard.tsx"
    if Path(collection_card_path).exists():
        with open(collection_card_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否隐藏了下载按钮
        if "下载" not in content or "DownloadOutlined" not in content:
            print("✅ CollectionCard.tsx - 下载按钮已隐藏")
        else:
            print("❌ CollectionCard.tsx - 下载按钮未完全隐藏")
            
        # 检查导出按钮文案
        if "导出完整视频" in content:
            print("✅ CollectionCard.tsx - 导出按钮文案已修改为'导出完整视频'")
        else:
            print("❌ CollectionCard.tsx - 导出按钮文案未修改")
    
    # 检查CollectionPreviewModal.tsx
    preview_modal_path = "frontend/src/components/CollectionPreviewModal.tsx"
    if Path(preview_modal_path).exists():
        with open(preview_modal_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否隐藏了下载合集按钮
        if "下载合集" not in content:
            print("✅ CollectionPreviewModal.tsx - 下载合集按钮已隐藏")
        else:
            print("❌ CollectionPreviewModal.tsx - 下载合集按钮未隐藏")
            
        # 检查导出按钮文案
        if "导出完整视频" in content:
            print("✅ CollectionPreviewModal.tsx - 导出按钮文案已修改为'导出完整视频'")
        else:
            print("❌ CollectionPreviewModal.tsx - 导出按钮文案未修改")
            
        # 检查添加切片按钮尺寸
        if "size=\"middle\"" in content and "height: '36px'" in content:
            print("✅ CollectionPreviewModal.tsx - 添加切片按钮尺寸已增大")
        else:
            print("❌ CollectionPreviewModal.tsx - 添加切片按钮尺寸未修改")
    
    # 检查ProjectDetailPage.tsx
    detail_page_path = "frontend/src/pages/ProjectDetailPage.tsx"
    if Path(detail_page_path).exists():
        with open(detail_page_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查创建合集按钮尺寸
        if "height: '40px'" in content:
            print("✅ ProjectDetailPage.tsx - 创建合集按钮尺寸已增大")
        else:
            print("❌ ProjectDetailPage.tsx - 创建合集按钮尺寸未修改")
    
    print("\n=== UI优化测试完成 ===")
    print("请手动检查以下功能：")
    print("1. 合集卡片中是否隐藏了'下载'按钮")
    print("2. 合集卡片中的'生成'按钮是否改为'导出完整视频'")
    print("3. 合集预览模态框中是否隐藏了'下载合集'按钮")
    print("4. 合集预览模态框中的'导出合集视频'按钮是否改为'导出完整视频'")
    print("5. 添加切片按钮是否变大了")
    print("6. 创建合集按钮是否变大了")

if __name__ == "__main__":
    test_ui_optimization() 