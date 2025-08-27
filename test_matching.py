#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试片段标题匹配逻辑
"""
import re
import json

def normalize_text(text):
    """标准化文本用于比较"""
    # 移除标点符号和多余空格，转换为小写
    return re.sub(r'[^\w\s]', '', text).strip().lower()

def test_matching():
    """测试匹配逻辑"""
    # 模拟LLM返回的标题
    llm_titles = [
        '散户如何解套？',
        '北交所中免种业还能涨吗？',
        '董秘的职业发展路径',
        '大学生如何提升财商'
    ]
    
    # 模拟实际的片段标题
    actual_clips = [
        {
            'id': '1',
            'outline': '散户如何解套',
            'generated_title': '散户如何解套？'
        },
        {
            'id': '2',
            'outline': '北交所中免种业还能涨吗',
            'generated_title': '北交所中免种业还能涨吗？'
        },
        {
            'id': '3',
            'outline': '董秘的职业发展路径',
            'generated_title': '董秘的职业发展路径'
        },
        {
            'id': '4',
            'outline': '大学生如何提升财商',
            'generated_title': '大学生如何提升财商'
        }
    ]
    
    print("=== 测试片段标题匹配 ===")
    print(f"LLM标题数量: {len(llm_titles)}")
    print(f"实际片段数量: {len(actual_clips)}")
    
    for i, llm_title in enumerate(llm_titles):
        print(f"\n--- 测试标题 {i+1}: '{llm_title}' ---")
        
        # 清理LLM返回的标题
        cleaned_llm_title = llm_title.strip()
        # 去除可能的引号
        if cleaned_llm_title.startswith('"') and cleaned_llm_title.endswith('"'):
            cleaned_llm_title = cleaned_llm_title[1:-1]
        if cleaned_llm_title.startswith("'") and cleaned_llm_title.endswith("'"):
            cleaned_llm_title = cleaned_llm_title[1:-1]
        
        print(f"清理后标题: '{cleaned_llm_title}'")
        
        found = False
        for j, clip in enumerate(actual_clips):
            generated_title = clip.get('generated_title', clip['outline'])
            outline = clip['outline']
            
            # 清理实际的标题
            cleaned_generated_title = generated_title.strip()
            cleaned_outline = outline.strip()
            
            print(f"  比较: '{cleaned_llm_title}' vs '{cleaned_generated_title}' | '{cleaned_outline}'")
            
            # 精确匹配
            if (cleaned_llm_title == cleaned_generated_title or 
                cleaned_llm_title == cleaned_outline):
                print(f"  ✅ 精确匹配成功! 片段ID: {clip['id']}")
                found = True
                break
            
            # 模糊匹配
            normalized_llm_title = normalize_text(cleaned_llm_title)
            normalized_generated_title = normalize_text(cleaned_generated_title)
            normalized_outline = normalize_text(cleaned_outline)
            
            print(f"  模糊比较: '{normalized_llm_title}' vs '{normalized_generated_title}' | '{normalized_outline}'")
            
            if (normalized_llm_title == normalized_generated_title or 
                normalized_llm_title == normalized_outline):
                print(f"  💡 模糊匹配成功! 片段ID: {clip['id']}")
                found = True
                break
        
        if not found:
            print(f"  ❌ 未找到匹配的片段")
            # 显示所有实际标题
            all_titles = [clip.get('generated_title', clip['outline']) for clip in actual_clips]
            print(f"  可用标题列表: {all_titles}")

if __name__ == "__main__":
    test_matching()