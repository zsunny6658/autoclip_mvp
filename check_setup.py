#!/usr/bin/env python3
"""
项目启动检查脚本
验证所有必要的文件和配置是否正确
"""
import os
import sys
import json
from pathlib import Path
import subprocess

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python版本过低，需要Python 3.8+")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def check_node_version():
    """检查Node.js版本"""
    print("📦 检查Node.js版本...")
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Node.js版本: {version}")
            return True
        else:
            print("❌ Node.js未安装或无法访问")
            return False
    except FileNotFoundError:
        print("❌ Node.js未安装")
        return False

def check_directories():
    """检查必要的目录"""
    print("📁 检查项目目录...")
    required_dirs = [
        'frontend',
        'src',
        'data',
        'uploads',
        'prompt',
        'tests'
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            missing_dirs.append(dir_name)
        else:
            print(f"✅ 目录存在: {dir_name}")
    
    if missing_dirs:
        print(f"❌ 缺少目录: {', '.join(missing_dirs)}")
        return False
    
    return True

def check_files():
    """检查必要的文件"""
    print("📄 检查项目文件...")
    required_files = [
        'backend_server.py',
        'main.py',
        'start_dev.sh',
        'requirements.txt',
        '.gitignore',
        'README.md',
        'frontend/package.json',
        'frontend/vite.config.ts',
        'src/main.py',
        'src/config.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ 文件存在: {file_path}")
    
    if missing_files:
        print(f"❌ 缺少文件: {', '.join(missing_files)}")
        return False
    
    return True

def check_virtual_environment():
    """检查虚拟环境"""
    print("🔧 检查虚拟环境...")
    venv_path = Path('venv')
    if not venv_path.exists():
        print("❌ 虚拟环境不存在，请运行: python3 -m venv venv")
        return False
    
    # 检查是否激活
    if 'VIRTUAL_ENV' not in os.environ:
        print("⚠️  虚拟环境未激活，请运行: source venv/bin/activate")
        return False
    
    print("✅ 虚拟环境已激活")
    return True

def check_dependencies():
    """检查Python依赖"""
    print("📦 检查Python依赖...")
    
    # 定义必需的依赖包
    required_packages = [
        'fastapi',
        'uvicorn', 
        'dashscope',
        'pydub',
        'pysrt',
        'pydantic',
        'aiofiles',
        'requests',
        'aiohttp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("✅ 所有Python依赖已安装")
    return True

def check_frontend_dependencies():
    """检查前端依赖"""
    print("🎨 检查前端依赖...")
    node_modules = Path('frontend/node_modules')
    if not node_modules.exists():
        print("❌ 前端依赖未安装，请运行: cd frontend && npm install")
        return False
    
    print("✅ 前端依赖已安装")
    return True

def check_config():
    """检查配置文件"""
    print("⚙️  检查配置文件...")
    settings_file = Path('data/settings.json')
    if not settings_file.exists():
        print("❌ 配置文件不存在，请创建 data/settings.json")
        print("示例配置:")
        print("""
{
  "dashscope_api_key": "your-api-key-here",
  "model_name": "qwen-plus",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
        """)
        return False
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        if 'dashscope_api_key' not in config or not config['dashscope_api_key']:
            print("❌ API密钥未配置")
            return False
        
        print("✅ 配置文件正确")
        return True
    except json.JSONDecodeError:
        print("❌ 配置文件格式错误")
        return False

def check_uploads_directory():
    """检查上传目录"""
    print("📁 检查上传目录...")
    uploads_dir = Path('uploads')
    if not uploads_dir.exists():
        uploads_dir.mkdir(parents=True)
        print("✅ 创建上传目录")
    
    tmp_dir = uploads_dir / 'tmp'
    if not tmp_dir.exists():
        tmp_dir.mkdir(parents=True)
        print("✅ 创建临时目录")
    
    print("✅ 上传目录结构正确")
    return True

def check_docker():
    """检查Docker安装和状态"""
    print("🐳 检查Docker...") 
    try:
        # 检查Docker命令
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker已安装: {version}")
        else:
            print("❌ Docker未安装")
            return False
        
        # 检查Docker服务状态
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker服务正常运行")
        else:
            print("❌ Docker服务未运行，请启动Docker")
            return False
            
        return True
    except FileNotFoundError:
        print("❌ Docker未安装")
        return False
    except Exception as e:
        print(f"❌ Docker检查失败: {e}")
        return False

def check_docker_compose():
    """检查Docker Compose安装和版本"""
    print("🛠️  检查Docker Compose...")
    
    # 检查docker-compose命令
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker Compose已安装: {version}")
            return True
    except FileNotFoundError:
        pass
    
    # 检查docker compose命令（Docker v2+）
    try:
        result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ Docker Compose已安装: {version}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Docker Compose未安装")
    print("安装指南: https://docs.docker.com/compose/install/")
    return False

def check_docker_files():
    """检查Docker相关文件"""
    print("📄 检查Docker文件...")
    
    docker_files = [
        'Dockerfile',
        'docker-compose.yml', 
        'docker-compose.prod.yml',
        '.dockerignore'
    ]
    
    all_exist = True
    for file_path in docker_files:
        if Path(file_path).exists():
            print(f"✅ 文件存在: {file_path}")
        else:
            if file_path == '.dockerignore':
                print(f"⚠️  可选文件不存在: {file_path}")
            else:
                print(f"❌ 文件不存在: {file_path}")
                all_exist = False
    
    return all_exist

def check_env_file():
    """检查环境变量文件"""
    print("🌍 检查环境变量文件...")
    
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if env_file.exists():
        print("✅ .env 文件存在")
        
        # 检查关键API密钥
        try:
            with open('.env', 'r') as f:
                content = f.read()
                if 'DASHSCOPE_API_KEY=' in content or 'SILICONFLOW_API_KEY=' in content:
                    print("✅ API密钥配置已设置")
                else:
                    print("⚠️  API密钥未配置")
        except Exception as e:
            print(f"⚠️  读取.env文件失败: {e}")
        return True
    elif env_example.exists():
        print("⚠️  .env 文件不存在，但找到 env.example")
        print("请运行: cp env.example .env 并编辑配置")
        return False
    else:
        print("❌ .env 和 env.example 文件都不存在")
        return False

def validate_docker_compose_files():
    """验证Docker Compose文件语法"""
    print("⚙️  验证Docker Compose文件...")
    
    compose_files = ['docker-compose.yml', 'docker-compose.prod.yml']
    all_valid = True
    
    for compose_file in compose_files:
        if not Path(compose_file).exists():
            continue
            
        try:
            # 尝试使用docker-compose
            result = subprocess.run(
                ['docker-compose', '-f', compose_file, 'config'], 
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✅ {compose_file} 语法正确")
                continue
        except FileNotFoundError:
            pass
        
        try:
            # 尝试使用docker compose
            result = subprocess.run(
                ['docker', 'compose', '-f', compose_file, 'config'], 
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"✅ {compose_file} 语法正确")
            else:
                print(f"❌ {compose_file} 语法错误")
                all_valid = False
        except FileNotFoundError:
            print(f"⚠️  无法验证 {compose_file}，Docker Compose不可用")
            all_valid = False
    
    return all_valid

def main():
    """主检查函数"""
    print("🔍 开始项目启动检查...")
    print("=" * 50)
    
    checks = [
        check_python_version,
        check_node_version,
        check_directories,
        check_files,
        check_virtual_environment,
        check_dependencies,
        check_frontend_dependencies,
        check_config,
        check_uploads_directory,
        check_docker,
        check_docker_compose,
        check_docker_files,
        check_env_file,
        validate_docker_compose_files
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ 检查失败: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有检查通过！项目可以正常启动")
        print("\n🚀 启动命令:")
        print("  本地开发:")
        print("    ./start_dev.sh")
        print("    或")
        print("    python backend_server.py")
        print("    cd frontend && npm run dev")
        print("\n  Docker部署:")
        print("    开发环境: ./docker-deploy.sh")
        print("    生产环境: ./docker-deploy-prod.sh")
        print("    测试配置: ./test-docker.sh")
    else:
        print("⚠️  请修复上述问题后重新运行检查")
        print("\n📈 建议操作:")
        if not Path('.env').exists():
            print("  1. 创建环境变量文件: cp env.example .env")
            print("  2. 编辑 .env 文件并设置 API 密钥")
        if passed < total - 2:  # 如果失败较多
            print("  3. 检查系统依赖安装")
            print("  4. 检查项目文件完整性")
        print("  5. 重新运行: python check_setup.py")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 