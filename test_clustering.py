#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试聚类过程和片段匹配
"""
import json
import re
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def normalize_text(text):
    """标准化文本用于比较"""
    # 移除标点符号和多余空格，转换为小写
    return re.sub(r'[^\w\s]', '', text).strip().lower()

def debug_validate_collections(collections_data, clips_with_titles):
    """模拟_validate_collections方法的匹配过程"""
    print("=== 模拟验证合集数据 ===")
    print(f"合集数量: {len(collections_data)}")
    print(f"片段数量: {len(clips_with_titles)}")
    
    validated_collections = []
    
    for i, collection in enumerate(collections_data):
        print(f"\n--- 验证合集 {i} ---")
        print(f"合集标题: {collection.get('collection_title', 'N/A')}")
        
        # 验证必需字段
        required_fields = ['collection_title', 'collection_summary', 'clips']
        missing_fields = [key for key in required_fields if key not in collection]
        
        if missing_fields:
            print(f"⚠️ 缺少必需字段: {missing_fields}")
            continue
        
        # 验证片段列表
        clip_titles = collection['clips']
        print(f"片段标题数量: {len(clip_titles)}")
        print(f"片段标题列表: {clip_titles}")
        
        valid_clip_ids = []
        
        for j, clip_title in enumerate(clip_titles):
            print(f"\n  [片段 {j}] 查找片段标题: '{clip_title}'")
            
            # 清理LLM返回的标题
            cleaned_clip_title = clip_title.strip()
            # 去除可能的引号
            if cleaned_clip_title.startswith('"') and cleaned_clip_title.endswith('"'):
                cleaned_clip_title = cleaned_clip_title[1:-1]
            if cleaned_clip_title.startswith("'") and cleaned_clip_title.endswith("'"):
                cleaned_clip_title = cleaned_clip_title[1:-1]
            
            print(f"  清理后标题: '{cleaned_clip_title}'")
            
            # 根据标题找到对应的片段ID
            found_clip = None
            
            for k, clip in enumerate(clips_with_titles):
                generated_title = clip.get('generated_title', clip['outline'])
                outline = clip['outline']
                
                # 清理实际的标题
                cleaned_generated_title = generated_title.strip()
                cleaned_outline = outline.strip()
                
                print(f"    比较 {k}: '{cleaned_clip_title}' vs '{cleaned_generated_title}' | '{cleaned_outline}'")
                
                # 精确匹配
                if (cleaned_clip_title == cleaned_generated_title or 
                    cleaned_clip_title == cleaned_outline):
                    found_clip = clip
                    print(f"    ✅ 精确匹配成功! 片段ID: {clip['id']}")
                    break
                
                # 模糊匹配
                normalized_clip_title = normalize_text(cleaned_clip_title)
                normalized_generated_title = normalize_text(cleaned_generated_title)
                normalized_outline = normalize_text(cleaned_outline)
                
                print(f"    模糊比较 {k}: '{normalized_clip_title}' vs '{normalized_generated_title}' | '{normalized_outline}'")
                
                if (normalized_clip_title == normalized_generated_title or 
                    normalized_clip_title == normalized_outline):
                    found_clip = clip
                    print(f"    💡 模糊匹配成功! 片段ID: {clip['id']}")
                    break
            
            if found_clip:
                valid_clip_ids.append(found_clip['id'])
                print(f"  ✅ [片段 {j} 匹配成功] 找到匹配片段 ID: {found_clip['id']}")
            else:
                print(f"  ❌ [片段 {j} 匹配失败] 未找到匹配的片段: '{clip_title}'")
        
        if len(valid_clip_ids) < 2:
            print(f"⚠️ 有效片段少于2个 ({len(valid_clip_ids)}个)，跳过该合集")
            continue
        
        validated_collection = {
            'id': str(i + 1),
            'collection_title': collection['collection_title'],
            'collection_summary': collection['collection_summary'],
            'clip_ids': valid_clip_ids
        }
        
        print(f"✅ 合集 {i} 验证通过，标题: '{validated_collection['collection_title']}', 片段数: {len(valid_clip_ids)}")
        validated_collections.append(validated_collection)
    
    print(f"\n=== 验证完成 ===")
    print(f"最终有效合集数量: {len(validated_collections)}")
    return validated_collections

def test_with_sample_data():
    """使用示例数据测试"""
    # 模拟LLM返回的合集数据
    collections_data = [
        {
            "collection_title": "投资理财启示",
            "collection_summary": "通过生活化案例分享投资理念，兼具实用与共鸣。",
            "clips": ["散户如何解套？", "北交所中免种业还能涨吗？"]
        }
    ]
    
    # 模拟实际的片段数据
    clips_with_titles = [
        {
            "id": "clip_1",
            "outline": "散户如何解套",
            "generated_title": "散户如何解套？",
            "final_score": 0.95
        },
        {
            "id": "clip_2",
            "outline": "北交所中免种业还能涨吗",
            "generated_title": "北交所中免种业还能涨吗？",
            "final_score": 0.92
        },
        {
            "id": "clip_3",
            "outline": "职场技能提升",
            "generated_title": "职场技能提升：从新手到专家",
            "final_score": 0.88
        }
    ]
    
    print("=== 使用示例数据测试 ===")
    print("LLM返回的合集数据:")
    print(json.dumps(collections_data, ensure_ascii=False, indent=2))
    
    print("\n实际片段数据:")
    print(json.dumps(clips_with_titles, ensure_ascii=False, indent=2))
    
    # 执行验证
    result = debug_validate_collections(collections_data, clips_with_titles)
    
    print("\n验证结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    test_with_sample_data()