#!/usr/bin/env python3
"""
系统测试脚本
验证项目的各个组件是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        from src.config import config_manager
        print("✅ config_manager 导入成功")
    except Exception as e:
        print(f"❌ config_manager 导入失败: {e}")
        return False
    
    try:
        from src.utils.project_manager import project_manager
        print("✅ project_manager 导入成功")
    except Exception as e:
        print(f"❌ project_manager 导入失败: {e}")
        return False
    
    try:
        from src.utils.llm_client import LLMClient
        print("✅ LLMClient 导入成功")
    except Exception as e:
        print(f"❌ LLMClient 导入失败: {e}")
        return False
    
    try:
        from src.main import AutoClipsProcessor
        print("✅ AutoClipsProcessor 导入成功")
    except Exception as e:
        print(f"❌ AutoClipsProcessor 导入失败: {e}")
        return False
    
    return True

def test_config():
    """测试配置管理"""
    print("\n🔍 测试配置管理...")
    
    try:
        from src.config import config_manager
        
        # 测试配置导出
        config = config_manager.export_config()
        print("✅ 配置导出成功")
        
        # 测试API密钥更新
        config_manager.update_api_key("test_key")
        print("✅ API密钥更新成功")
        
        return True
    except Exception as e:
        print(f"❌ 配置管理测试失败: {e}")
        return False

def test_project_manager():
    """测试项目管理"""
    print("\n🔍 测试项目管理...")
    
    try:
        from src.utils.project_manager import project_manager
        
        # 测试项目列表
        projects = project_manager.list_projects()
        print(f"✅ 项目列表获取成功，当前项目数: {len(projects)}")
        
        # 测试项目创建
        test_project_id = project_manager.create_project("测试项目")
        print(f"✅ 测试项目创建成功: {test_project_id}")
        
        # 测试项目验证
        exists = project_manager.validate_project_exists(test_project_id)
        print(f"✅ 项目验证成功: {exists}")
        
        # 测试项目删除
        success = project_manager.delete_project(test_project_id)
        print(f"✅ 测试项目删除成功: {success}")
        
        return True
    except Exception as e:
        print(f"❌ 项目管理测试失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    print("\n🔍 测试目录结构...")
    
    required_dirs = [
        "src",
        "src/pipeline", 
        "src/utils",
        "frontend",
        "uploads",
        "data",
        "temp",
        "tests"
    ]
    
    required_files = [
        "main.py",
        "app.py", 
        "backend_server.py",
        "start.py",
        "streamlit_app.py",
        "requirements.txt",
        "README.md",
        "src/main.py",
        "src/config.py"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ 目录存在: {dir_path}")
        else:
            print(f"❌ 目录缺失: {dir_path}")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ 文件存在: {file_path}")
        else:
            print(f"❌ 文件缺失: {file_path}")
            all_good = False
    
    return all_good

def test_pipeline_modules():
    """测试流水线模块"""
    print("\n🔍 测试流水线模块...")
    
    pipeline_modules = [
        "step1_outline",
        "step2_timeline", 
        "step3_scoring",
        "step4_title",
        "step5_clustering",
        "step6_video"
    ]
    
    all_good = True
    
    for module_name in pipeline_modules:
        try:
            module = __import__(f"src.pipeline.{module_name}", fromlist=["*"])
            print(f"✅ {module_name} 模块导入成功")
        except Exception as e:
            print(f"❌ {module_name} 模块导入失败: {e}")
            all_good = False
    
    return all_good

def test_utils_modules():
    """测试工具模块"""
    print("\n🔍 测试工具模块...")
    
    utils_modules = [
        "project_manager",
        "api_key_manager",
        "error_handler", 
        "llm_client",
        "video_processor",
        "text_processor"
    ]
    
    all_good = True
    
    for module_name in utils_modules:
        try:
            module = __import__(f"src.utils.{module_name}", fromlist=["*"])
            print(f"✅ {module_name} 模块导入成功")
        except Exception as e:
            print(f"❌ {module_name} 模块导入失败: {e}")
            all_good = False
    
    return all_good

def main():
    """主测试函数"""
    print("🚀 开始系统测试...\n")
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理", test_config),
        ("项目管理", test_project_manager),
        ("目录结构", test_directory_structure),
        ("流水线模块", test_pipeline_modules),
        ("工具模块", test_utils_modules)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查相关模块。")
        return 1

if __name__ == "__main__":
    exit(main()) 