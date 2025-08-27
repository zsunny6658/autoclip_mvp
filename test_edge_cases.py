#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试各种边界情况下的片段匹配
"""
import json
import re
import unicodedata
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def remove_punctuation(text):
    """移除常见的中文和英文标点符号"""
    # 简化版标点符号移除
    import string
    # 中文标点符号
    chinese_punctuation = '，。！？；：""''（）【】《》、'
    # 英文标点符号
    english_punctuation = string.punctuation
    # 所有标点符号
    all_punctuation = chinese_punctuation + english_punctuation + ' \\t\\n\\r'
    
    # 逐个移除标点符号
    for punct in all_punctuation:
        text = text.replace(punct, '')
    return text.strip()

def normalize_text(text):
    """标准化文本用于比较"""
    # 移除标点符号和多余空格，转换为小写
    text = remove_punctuation(text)
    return text.strip().lower()

def test_matching_strategies(clip_title, clips_with_titles):
    """测试多种匹配策略"""
    print(f"\n  测试标题: '{clip_title}'")
    
    # 清理LLM返回的标题
    cleaned_clip_title = clip_title.strip()
    # 去除可能的引号
    if cleaned_clip_title.startswith('"') and cleaned_clip_title.endswith('"'):
        cleaned_clip_title = cleaned_clip_title[1:-1]
    if cleaned_clip_title.startswith("'") and cleaned_clip_title.endswith("'"):
        cleaned_clip_title = cleaned_clip_title[1:-1]
    
    # 处理Unicode字符
    cleaned_clip_title = unicodedata.normalize('NFKC', cleaned_clip_title)
    
    print(f"  清理后标题: '{cleaned_clip_title}'")
    
    for i, clip in enumerate(clips_with_titles):
        generated_title = clip.get('generated_title', clip['outline'])
        outline = clip['outline']
        
        # 清理实际的标题
        cleaned_generated_title = generated_title.strip()
        cleaned_outline = outline.strip()
        
        # 处理Unicode字符
        cleaned_generated_title = unicodedata.normalize('NFKC', cleaned_generated_title)
        cleaned_outline = unicodedata.normalize('NFKC', cleaned_outline)
        
        print(f"\n    片段{i}:")
        print(f"      Generated: '{generated_title}'")
        print(f"      Outline: '{outline}'")
        
        # 策略1: 精确匹配（忽略首尾空格）
        if (cleaned_clip_title.strip() == cleaned_generated_title.strip() or 
            cleaned_clip_title.strip() == cleaned_outline.strip()):
            print(f"      ✅ 策略1(精确匹配)成功")
            return clip
        
        # 策略2: 去除标点符号后匹配
        no_punct_clip_title = remove_punctuation(cleaned_clip_title)
        no_punct_generated_title = remove_punctuation(cleaned_generated_title)
        no_punct_outline = remove_punctuation(cleaned_outline)
        
        print(f"      去标点 - LLM: '{no_punct_clip_title}', Generated: '{no_punct_generated_title}', Outline: '{no_punct_outline}'")
        
        if (no_punct_clip_title == no_punct_generated_title or 
            no_punct_clip_title == no_punct_outline):
            print(f"      ✅ 策略2(去标点匹配)成功")
            return clip
        
        # 策略3: 包含匹配
        if (no_punct_clip_title in no_punct_generated_title or 
            no_punct_generated_title in no_punct_clip_title or
            no_punct_clip_title in no_punct_outline or 
            no_punct_outline in no_punct_clip_title):
            print(f"      ✅ 策略3(包含匹配)成功")
            print(f"        包含关系详情: '{no_punct_clip_title}' in '{no_punct_generated_title}' = {no_punct_clip_title in no_punct_generated_title}")
            print(f"        包含关系详情: '{no_punct_generated_title}' in '{no_punct_clip_title}' = {no_punct_generated_title in no_punct_clip_title}")
            print(f"        包含关系详情: '{no_punct_clip_title}' in '{no_punct_outline}' = {no_punct_clip_title in no_punct_outline}")
            print(f"        包含关系详情: '{no_punct_outline}' in '{no_punct_clip_title}' = {no_punct_outline in no_punct_clip_title}")
            return clip
        
        # 策略4: 模糊匹配
        normalized_clip_title = normalize_text(cleaned_clip_title)
        normalized_generated_title = normalize_text(cleaned_generated_title)
        normalized_outline = normalize_text(cleaned_outline)
        
        print(f"      模糊 - LLM: '{normalized_clip_title}', Generated: '{normalized_generated_title}', Outline: '{normalized_outline}'")
        
        if (normalized_clip_title == normalized_generated_title or 
            normalized_clip_title == normalized_outline):
            print(f"      ✅ 策略4(模糊匹配)成功")
            return clip
    
    print(f"      ❌ 所有策略都失败")
    return None

def test_edge_cases():
    """测试各种边界情况"""
    print("=== 测试边界情况 ===")
    
    # 测试用例
    test_cases = [
        # 情况1: 标点符号差异
        {
            "name": "标点符号差异",
            "llm_title": "散户如何解套？",
            "actual_clips": [
                {"id": "1", "outline": "散户如何解套", "generated_title": "散户如何解套？"}
            ]
        },
        # 情况2: 引号问题
        {
            "name": "引号问题",
            "llm_title": '"北交所中免种业还能涨吗？"',
            "actual_clips": [
                {"id": "2", "outline": "北交所中免种业还能涨吗", "generated_title": "北交所中免种业还能涨吗？"}
            ]
        },
        # 情况3: Unicode字符问题
        {
            "name": "Unicode字符问题",
            "llm_title": "董秘的职业发展路径",  # 假设这里有Unicode问题
            "actual_clips": [
                {"id": "3", "outline": "董秘的职业发展路径", "generated_title": "董秘的职业发展路径"}
            ]
        },
        # 情况4: 包含关系
        {
            "name": "包含关系",
            "llm_title": "职场技能",
            "actual_clips": [
                {"id": "4", "outline": "职场技能提升：从新手到专家", "generated_title": "职场技能提升"}
            ]
        },
        # 情况5: 空格问题
        {
            "name": "空格问题",
            "llm_title": " 大学生如何提升财商 ",
            "actual_clips": [
                {"id": "5", "outline": "大学生如何提升财商", "generated_title": "大学生如何提升财商"}
            ]
        }
    ]
    
    for i, case in enumerate(test_cases):
        print(f"\n--- 测试情况 {i+1}: {case['name']} ---")
        result = test_matching_strategies(case['llm_title'], case['actual_clips'])
        if result:
            print(f"  ✅ 匹配成功，片段ID: {result['id']}")
        else:
            print(f"  ❌ 匹配失败")

if __name__ == "__main__":
    test_edge_cases()