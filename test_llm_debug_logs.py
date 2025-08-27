#!/usr/bin/env python3
"""
测试LLM调试日志功能
用于验证新增的详细日志记录是否正常工作
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.llm_factory import LLMFactory

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_llm_debug_logs():
    """测试LLM调试日志功能"""
    print("=" * 60)
    print("🧪 测试LLM调试日志功能")
    print("=" * 60)
    
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("❌ 未找到API密钥，请设置DASHSCOPE_API_KEY或SILICONFLOW_API_KEY环境变量")
        return
    
    try:
        # 创建LLM客户端（使用默认配置）
        client = LLMFactory.get_default_client()
        print(f"✅ 成功创建LLM客户端: {type(client).__name__}")
        
        # 测试1: 简单调用
        print("\n📝 测试1: 简单文本调用")
        test_prompt = "请简单回复'测试成功'"
        response = client.call_with_retry(test_prompt)
        print(f"📤 响应: {response[:100]}...")
        
        # 测试2: 带结构化输入的调用
        print("\n📝 测试2: 带结构化输入的调用")
        test_prompt_2 = "请根据输入数据生成一个简单的JSON响应，包含一个name字段"
        test_input = {"text": "这是测试数据", "type": "test"}
        response_2 = client.call_with_retry(test_prompt_2, test_input)
        print(f"📤 响应: {response_2[:100]}...")
        
        # 测试3: JSON解析功能
        print("\n📝 测试3: JSON解析功能")
        json_prompt = """请返回以下JSON格式的数据：
```json
[
    {"name": "测试项目1", "value": 10},
    {"name": "测试项目2", "value": 20}
]
```"""
        json_response = client.call_with_retry(json_prompt)
        print(f"📤 JSON响应: {json_response[:200]}...")
        
        # 尝试解析JSON
        try:
            parsed_json = client.parse_json_response(json_response)
            print(f"✅ JSON解析成功: {parsed_json}")
        except Exception as e:
            print(f"❌ JSON解析失败: {e}")
        
        print("\n🎉 LLM调试日志测试完成！")
        print("请查看上面的日志输出，确认包含以下信息:")
        print("- 🚀 [LLM调用开始] 模型信息")
        print("- 📝 [提示词长度] 和 📊 [输入数据] 统计")
        print("- ⏱️ [API调用] 时间信息")
        print("- ✅ [API调用成功] 响应统计")
        print("- 🔍 [JSON解析开始] 等解析过程日志")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_debug_logs()