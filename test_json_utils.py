#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.json_utils import JSONUtils

def test_json_fix():
    # 模拟用户提供的LLM响应（包含被截断的情况）
    response = '''[{"outline":"开场美食预告与互动","content":[\"提及今日推荐的酒品对比（新西兰长相思 vs 法国纯香酥）\",\"通过幽默对话引出食材介绍（如\\"好粗啊\\"\\"你喂它它成生气\\"）\"],"start_time":"00:00:01,300","end_time":"00:02:22,790"},{"outline":"食材来源与烹饪细节","conten...'''
    
    print("原始响应:")
    print(response)
    print("\n" + "="*50 + "\n")
    
    try:
        # 直接尝试解析
        parsed_result = JSONUtils.parse_json_response(response)
        print("解析成功!")
        print(f"解析结果类型: {type(parsed_result)}")
        print(f"解析结果长度: {len(parsed_result)}")
        print("\n解析结果:")
        import json
        print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"解析失败: {e}")

def test_full_response():
    # 测试完整的响应
    response = '''[{"outline":"开场美食预告与互动","content":[\"提及今日推荐的酒品对比（新西兰长相思 vs 法国纯香酥）\",\"通过幽默对话引出食材介绍（如\\"好粗啊\\"\\"你喂它它成生气\\"）\"],"start_time":"00:00:01,300","end_time":"00:02:22,790"},{"outline":"食材来源与烹饪细节","content":[\"讨论食材的特殊来源（如\\"萝卜刚坐飞机到\\"\\"龙虾肉搭配\\"）\",\"核心对比野生与养殖食材的差异（如\\"野生中心 vs 养殖中心\\"）\"],"start_time":"00:02:23,240","end_time":"00:04:39,600"},{"outline":"菜肴口感与调味解析","content":[\"分析主菜的惊艳口感（如\\"和牛肥嫩\\"\\"萝卜味浓\\"）\",\"调味方案的创意与搭配（如\\"柱侯酱+猪虫夏草\\"\\"蒜蓉粉丝的豪华版\\"）\"],"start_time":"00:04:44,049","end_time":"00:06:49,020"},{"outline":"食客体验与场景描述","content":[\"模拟食客的直接反应（如\\"一口闷\\"\\"那边倒\\"）\",\"引入视觉化场景（如\\"下着雨\\"\\"萝卜摆盘\\"）\"],"start_time":"00:06:49,020","end_time":"00:06:57,230"},{"outline":"餐饮文化联想与补充互动","content":[\"关联岭南饮食文化（如\\"顺德味道\\"\\"猪头酱\\"）\",\"幽默式社交场景（如\\"20万赞\\"\\"渔业甲鱼头\\"）\"],"start_time":"00:06:57,230","end_time":"00:08:16,650"},{"outline":"收尾甜点与整体总结","content":[\"推荐甜品作为搭配（如\\"杨枝甘露收尾\\"）\",\"隐晦总结视频内容（如\\"这期视频多少分\\"\\"拜拜拜拜\\"）\"],"start_time":"00:08:21,270","end_time":"00:08:34,730"}]'''

    print("完整响应:")
    print(response)
    print("\n" + "="*50 + "\n")
    
    try:
        # 直接尝试解析
        parsed_result = JSONUtils.parse_json_response(response)
        print("解析成功!")
        print(f"解析结果类型: {type(parsed_result)}")
        print(f"解析结果长度: {len(parsed_result)}")
        print("\n解析结果:")
        import json
        print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"解析失败: {e}")

def test_truncated_response():
    # 测试更真实的被截断响应
    response = '''[{"outline":"开场美食预告与互动","content":[\"提及今日推荐的酒品对比（新西兰长相思 vs 法国纯香酥）\",\"通过幽默对话引出食材介绍（如\\"好粗啊\\"\\"你喂它它成生气\\"）\"],"start_time":"00:00:01,300","end_time":"00:02:22,790"},{"outline":"食材来源与烹饪细节","content":[\"讨论食材的特殊来源（如\\"萝卜刚坐飞机到\\"\\"龙虾肉搭配\\"）\",\"核心对比野生与养殖食材的差异（如\\"野生中心 vs 养殖中心\\"）\"],"start_time":"00:02:23,240","end_time":"00:04:39,600"},{"outline":"菜肴口感与调味解析","content":[\"分析主菜的惊艳口感（如\\"和牛肥嫩\\"\\"萝卜味浓\\"）\",\"调味方案的创意与搭配（如\\"柱侯酱+猪虫夏草\\"\\"蒜蓉粉丝的豪华版\\"）\"],"start_time":"00:04:44,049","end_time":"00:06:49,020"},{"outline":"食客体验与场景描述","content":[\"模拟食客的直接反应（如\\"一口闷\\"\\"那边倒\\"）\",\"引入视觉化场景（如\\"下着雨\\"\\"萝卜摆盘\\"）\"],"start_time":"00:06:49,020","end_time":"00:06:57,230"},{"outline":"餐饮文化联想与补充互动","content":[\"关联岭南饮食文化（如\\"顺德味道\\"\\"猪头酱\\"）\",\"幽默式社交场景（如\\"20万赞\\"\\"渔业甲鱼头\\"）\"],"start_time":"00:06:57,230","end_time":"00:08:16,650"},{"outline":"收尾甜点与整体总结","content":[\"推荐甜品作为搭配（如\\"杨枝甘露收尾\\"）\",\"隐晦总结视频内容（如\\"这期视频多少分\\"conten...'''
    
    print("被截断的响应:")
    print(response)
    print("\n" + "="*50 + "\n")
    
    try:
        # 直接尝试解析
        parsed_result = JSONUtils.parse_json_response(response)
        print("解析成功!")
        print(f"解析结果类型: {type(parsed_result)}")
        print(f"解析结果长度: {len(parsed_result)}")
        print("\n解析结果:")
        import json
        print(json.dumps(parsed_result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"解析失败: {e}")

if __name__ == "__main__":
    print("测试被截断的响应:")
    test_json_fix()
    
    print("\n\n测试完整的响应:")
    test_full_response()
    
    print("\n\n测试更真实的被截断响应:")
    test_truncated_response()