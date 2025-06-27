#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复项目数据脚本
用于将final_results.json中的clips和collections数据更新到projects.json中
"""

import json
from pathlib import Path

def fix_project_data(project_id: str):
    """修复指定项目的数据"""
    
    # 读取final_results.json
    final_results_path = Path(f"uploads/{project_id}/output/metadata/final_results.json")
    if not final_results_path.exists():
        print(f"❌ 项目 {project_id} 的final_results.json不存在")
        return False
    
    try:
        with open(final_results_path, 'r', encoding='utf-8') as f:
            final_results = json.load(f)
        
        # 提取clips和collections数据
        # 使用step4_titles因为它包含generated_title字段
        clips = final_results.get('step4_titles', [])
        collections = final_results.get('step5_collections', [])
        
        # 修复clips数据：确保generated_title字段正确存在
        for clip in clips:
            # 确保generated_title字段存在且正确
            if 'generated_title' not in clip:
                clip['generated_title'] = None
            
            # 如果没有title字段，使用outline作为fallback
            if 'title' not in clip or clip['title'] is None:
                clip['title'] = clip.get('outline', f"片段 {clip.get('id', '')}")
        
        print(f"✅ 找到 {len(clips)} 个clips和 {len(collections)} 个collections")
        
        # 读取projects.json
        projects_file = Path("data/projects.json")
        if not projects_file.exists():
            print("❌ projects.json不存在")
            return False
        
        with open(projects_file, 'r', encoding='utf-8') as f:
            projects_data = json.load(f)
        
        # 找到目标项目并更新
        project_found = False
        for project in projects_data:
            if project['id'] == project_id:
                project['clips'] = clips
                project['collections'] = collections
                project_found = True
                print(f"✅ 已更新项目 {project_id} 的数据")
                break
        
        if not project_found:
            print(f"❌ 在projects.json中未找到项目 {project_id}")
            return False
        
        # 保存更新后的projects.json
        with open(projects_file, 'w', encoding='utf-8') as f:
            json.dump(projects_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 项目 {project_id} 数据修复完成")
        return True
        
    except Exception as e:
        print(f"❌ 修复项目数据失败: {e}")
        return False

if __name__ == "__main__":
    # 修复指定项目
    project_id = "a5140373-4cf7-4687-8156-5716f5d370a2"
    print(f"🔧 开始修复项目 {project_id} 的数据...")
    
    success = fix_project_data(project_id)
    
    if success:
        print("\n🎉 数据修复完成！现在前端应该能正确显示clips和collections了。")
        print("💡 建议重启前端服务以确保数据更新生效。")
    else:
        print("\n❌ 数据修复失败，请检查错误信息。")