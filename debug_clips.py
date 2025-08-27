#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试片段数据结构
"""
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def debug_clips_data():
    """调试片段数据结构"""
    # 查找step4_titles.json文件
    metadata_dirs = [
        "./metadata",
        "./data/metadata",
        "./output/metadata",
        "."
    ]
    
    clips_file = None
    for metadata_dir in metadata_dirs:
        possible_path = os.path.join(metadata_dir, "step4_titles.json")
        if os.path.exists(possible_path):
            clips_file = possible_path
            break
    
    if not clips_file:
        # 尝试在当前目录及子目录中查找
        import glob
        matches = glob.glob("./**/step4_titles.json", recursive=True)
        if matches:
            clips_file = matches[0]
    
    if not clips_file:
        print("❌ 未找到step4_titles.json文件")
        return
    
    print(f"📄 找到片段文件: {clips_file}")
    
    try:
        with open(clips_file, 'r', encoding='utf-8') as f:
            clips_data = json.load(f)
        
        print(f"✅ 成功加载片段数据，共 {len(clips_data)} 个片段")
        
        # 显示前几个片段的详细信息
        print("\n🔍 前5个片段的详细信息:")
        for i, clip in enumerate(clips_data[:5]):
            print(f"\n--- 片段 {i+1} ---")
            print(f"  ID: {clip.get('id', 'N/A')}")
            print(f"  Outline: {clip.get('outline', 'N/A')}")
            print(f"  Generated Title: {clip.get('generated_title', 'N/A')}")
            print(f"  Final Score: {clip.get('final_score', 'N/A')}")
            print(f"  Recommend Reason: {clip.get('recommend_reason', 'N/A')[:50]}..." if clip.get('recommend_reason') else "  Recommend Reason: N/A")
        
        # 统计信息
        has_generated_title = sum(1 for clip in clips_data if clip.get('generated_title'))
        has_outline = sum(1 for clip in clips_data if clip.get('outline'))
        
        print(f"\n📊 统计信息:")
        print(f"  总片段数: {len(clips_data)}")
        print(f"  有generated_title的片段: {has_generated_title}")
        print(f"  有outline的片段: {has_outline}")
        
        # 收集所有标题用于比较
        all_generated_titles = [clip.get('generated_title') for clip in clips_data if clip.get('generated_title')]
        all_outlines = [clip.get('outline') for clip in clips_data if clip.get('outline')]
        
        print(f"\n📋 标题样本:")
        print(f"  Generated Titles (前5个): {all_generated_titles[:5]}")
        print(f"  Outlines (前5个): {all_outlines[:5]}")
        
    except Exception as e:
        print(f"❌ 读取片段数据时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_clips_data()