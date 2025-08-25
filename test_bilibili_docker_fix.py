#!/usr/bin/env python3
"""
测试脚本 - 验证B站下载器容器环境适配
"""

import sys
import os
import json
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

def test_container_detection():
    """测试容器环境检测"""
    print("=== 测试容器环境检测 ===")
    
    try:
        from src.utils.bilibili_downloader import BilibiliDownloader
        
        # 测试基本初始化
        downloader = BilibiliDownloader()
        print(f"容器环境检测结果: {downloader.is_container}")
        print(f"跳过浏览器cookies: {downloader.skip_browser_cookies}")
        print(f"cookies文件路径: {downloader.cookies_file}")
        
        # 测试带配置的初始化
        settings = {
            'bilibili_cookies_file': '/test/cookies.txt',
            'skip_browser_cookies_in_container': True
        }
        
        downloader_with_config = BilibiliDownloader(settings=settings)
        print(f"配置传递测试 - cookies文件: {downloader_with_config.cookies_file}")
        print(f"配置传递测试 - 跳过浏览器cookies: {downloader_with_config.skip_browser_cookies}")
        
        return True
        
    except Exception as e:
        print(f"容器环境检测测试失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    
    try:
        from src.config import config_manager
        
        # 测试bilibili配置获取
        bilibili_config = config_manager.get_bilibili_config()
        print(f"Bilibili配置: {bilibili_config}")
        
        return True
        
    except Exception as e:
        print(f"配置加载测试失败: {e}")
        return False

def test_env_file_creation():
    """测试环境文件创建"""
    print("\n=== 测试环境文件 ===")
    
    env_example_path = Path("./env.example")
    settings_example_path = Path("./data/settings.example.json")
    
    # 检查env.example文件
    if env_example_path.exists():
        print("✓ env.example 文件存在")
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'BILIBILI_COOKIES_FILE' in content:
                print("✓ env.example 包含B站配置")
            else:
                print("✗ env.example 缺少B站配置")
    else:
        print("✗ env.example 文件不存在")
    
    # 检查settings.example.json文件
    if settings_example_path.exists():
        print("✓ settings.example.json 文件存在")
        try:
            with open(settings_example_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if 'bilibili_cookies_file' in config_data:
                    print("✓ settings.example.json 包含B站配置")
                else:
                    print("✗ settings.example.json 缺少B站配置")
        except Exception as e:
            print(f"✗ settings.example.json 解析失败: {e}")
    else:
        print("✗ settings.example.json 文件不存在")
    
    return True

def test_url_validation():
    """测试URL验证"""
    print("\n=== 测试URL验证 ===")
    
    try:
        from src.utils.bilibili_downloader import BilibiliDownloader
        
        downloader = BilibiliDownloader()
        
        test_urls = [
            "https://www.bilibili.com/video/BV1234567890",
            "https://bilibili.com/video/BV1234567890",
            "https://b23.tv/abc123",
            "https://www.bilibili.com/video/av12345",
            "https://invalid-url.com/video"
        ]
        
        for url in test_urls:
            is_valid = downloader.validate_bilibili_url(url)
            status = "✓" if is_valid else "✗"
            print(f"{status} {url}: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"URL验证测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("B站下载器Docker环境适配测试\n")
    
    tests = [
        test_container_detection,
        test_config_loading,
        test_env_file_creation,
        test_url_validation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"测试执行失败: {e}")
            results.append(False)
    
    print(f"\n=== 测试结果汇总 ===")
    print(f"通过测试: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1

if __name__ == "__main__":
    exit(main())