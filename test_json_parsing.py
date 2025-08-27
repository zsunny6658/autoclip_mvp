#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试LLM响应解析功能
"""
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.llm_factory import LLMFactory

def test_json_parsing():
    """测试JSON解析功能"""
    # 创建LLM客户端
    llm_client = LLMFactory.get_default_client()
    
    # 测试用例1: 正常的JSON响应
    print("=== 测试用例1: 正常的JSON响应 ===")
    normal_response = '''[
  {
    "collection_title": "投资理财启示",
    "collection_summary": "通过生活化案例分享投资理念，兼具实用与共鸣。",
    "clips": ["散户如何解套？", "北交所中免种业还能涨吗？"]
  }
]'''
    
    try:
        result = llm_client.parse_json_response(normal_response)
        print(f"✅ 解析成功: {result}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")
    
    # 测试用例2: 包含Markdown代码块的响应
    print("\n=== 测试用例2: 包含Markdown代码块的响应 ===")
    markdown_response = '''```json
[
  {
    "collection_title": "职场技能提升",
    "collection_summary": "探讨职场技能与个人成长的实用建议。",
    "clips": ["董秘的职业发展路径", "大学生如何提升财商"]
  }
]
```'''
    
    try:
        result = llm_client.parse_json_response(markdown_response)
        print(f"✅ 解析成功: {result}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")
    
    # 测试用例3: 包含额外文本的响应
    print("\n=== 测试用例3: 包含额外文本的响应 ===")
    extra_text_response = '''根据您的要求，我将视频切片进行了主题聚类，结果如下：

```json
[
  {
    "collection_title": "文化差异趣谈",
    "collection_summary": "从饮食到语言，展现跨文化交流的趣味视角。",
    "clips": ["日本饮食文化解析", "欧美与亚洲的语言差异"]
  }
]
```

以上是聚类结果，请查看。'''
    
    try:
        result = llm_client.parse_json_response(extra_text_response)
        print(f"✅ 解析成功: {result}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")
    
    # 测试用例4: 空响应
    print("\n=== 测试用例4: 空响应 ===")
    empty_response = ""
    
    try:
        result = llm_client.parse_json_response(empty_response)
        print(f"解析结果: {result}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")
    
    # 测试用例5: 无效JSON
    print("\n=== 测试用例5: 无效JSON ===")
    invalid_response = '''[
  {
    "collection_title": "投资理财启示",
    "collection_summary": "通过生活化案例分享投资理念，兼具实用与共鸣。",
    "clips": ["散户如何解套？", "北交所中免种业还能涨吗？"
  }
]'''  # 缺少闭合括号
    
    try:
        result = llm_client.parse_json_response(invalid_response)
        print(f"✅ 解析成功: {result}")
    except Exception as e:
        print(f"❌ 解析失败: {e}")

if __name__ == "__main__":
    test_json_parsing()