#!/usr/bin/env python3
"""
bilitool 安装脚本
自动检测环境并安装 bilitool 依赖
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_bilitool_installed():
    """检查 bilitool 是否已安装"""
    try:
        import bilitool
        return True, bilitool.__version__
    except ImportError:
        return False, None

def check_virtual_env():
    """检查是否在虚拟环境中"""
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def install_with_pip():
    """使用 pip 安装 bilitool"""
    print("尝试使用 pip 安装 bilitool...")
    
    # 尝试不同的安装方法
    install_commands = [
        "pip install bilitool",
        "pip3 install bilitool",
        "python -m pip install bilitool",
        "python3 -m pip install bilitool"
    ]
    
    for cmd in install_commands:
        print(f"执行: {cmd}")
        success, stdout, stderr = run_command(cmd, check=False)
        
        if success:
            print("✅ bilitool 安装成功！")
            return True
        else:
            print(f"❌ 安装失败: {stderr}")
    
    return False

def install_with_user_flag():
    """使用 --user 标志安装"""
    print("尝试使用 --user 标志安装...")
    
    cmd = "pip3 install --user bilitool"
    print(f"执行: {cmd}")
    success, stdout, stderr = run_command(cmd, check=False)
    
    if success:
        print("✅ bilitool 安装成功（用户目录）！")
        return True
    else:
        print(f"❌ 安装失败: {stderr}")
        return False

def install_with_break_system_packages():
    """使用 --break-system-packages 标志安装（不推荐）"""
    print("⚠️  尝试使用 --break-system-packages 标志安装（不推荐）...")
    
    response = input("这可能会影响系统Python环境，是否继续？(y/N): ")
    if response.lower() != 'y':
        return False
    
    cmd = "pip3 install --break-system-packages bilitool"
    print(f"执行: {cmd}")
    success, stdout, stderr = run_command(cmd, check=False)
    
    if success:
        print("✅ bilitool 安装成功！")
        return True
    else:
        print(f"❌ 安装失败: {stderr}")
        return False

def create_virtual_env():
    """创建虚拟环境"""
    print("创建虚拟环境...")
    
    venv_path = Path.cwd() / "venv"
    
    if venv_path.exists():
        print(f"虚拟环境已存在: {venv_path}")
        return True, venv_path
    
    # 创建虚拟环境
    cmd = f"python3 -m venv {venv_path}"
    print(f"执行: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print(f"✅ 虚拟环境创建成功: {venv_path}")
        return True, venv_path
    else:
        print(f"❌ 虚拟环境创建失败: {stderr}")
        return False, None

def install_in_venv(venv_path):
    """在虚拟环境中安装 bilitool"""
    print("在虚拟环境中安装 bilitool...")
    
    # 确定激活脚本路径
    if platform.system() == "Windows":
        activate_script = venv_path / "Scripts" / "activate"
        pip_cmd = str(venv_path / "Scripts" / "pip")
    else:
        activate_script = venv_path / "bin" / "activate"
        pip_cmd = str(venv_path / "bin" / "pip")
    
    # 安装 bilitool
    cmd = f"{pip_cmd} install bilitool"
    print(f"执行: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ bilitool 在虚拟环境中安装成功！")
        print(f"\n要使用虚拟环境，请运行:")
        if platform.system() == "Windows":
            print(f"  {venv_path}\\Scripts\\activate")
        else:
            print(f"  source {activate_script}")
        return True
    else:
        print(f"❌ 安装失败: {stderr}")
        return False

def check_pipx():
    """检查 pipx 是否可用"""
    success, stdout, stderr = run_command("pipx --version", check=False)
    return success

def install_with_pipx():
    """使用 pipx 安装 bilitool"""
    print("使用 pipx 安装 bilitool...")
    
    cmd = "pipx install bilitool"
    print(f"执行: {cmd}")
    success, stdout, stderr = run_command(cmd)
    
    if success:
        print("✅ bilitool 通过 pipx 安装成功！")
        return True
    else:
        print(f"❌ 安装失败: {stderr}")
        return False

def main():
    print("🚀 bilitool 安装脚本")
    print("=" * 50)
    
    # 检查是否已安装
    installed, version = check_bilitool_installed()
    if installed:
        print(f"✅ bilitool 已安装，版本: {version}")
        return
    
    print("❌ bilitool 未安装")
    print(f"Python 版本: {sys.version}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    # 检查虚拟环境
    in_venv = check_virtual_env()
    print(f"虚拟环境: {'是' if in_venv else '否'}")
    
    print("\n选择安装方法:")
    print("1. 创建虚拟环境并安装（推荐）")
    print("2. 使用 pipx 安装")
    print("3. 使用 pip 直接安装")
    print("4. 使用 --user 标志安装")
    print("5. 使用 --break-system-packages 安装（不推荐）")
    print("6. 显示手动安装说明")
    
    choice = input("\n请选择 (1-6): ").strip()
    
    if choice == "1":
        # 虚拟环境安装
        success, venv_path = create_virtual_env()
        if success:
            install_in_venv(venv_path)
    
    elif choice == "2":
        # pipx 安装
        if check_pipx():
            install_with_pipx()
        else:
            print("❌ pipx 未安装")
            print("请先安装 pipx:")
            if platform.system() == "Darwin":  # macOS
                print("  brew install pipx")
            else:
                print("  python3 -m pip install --user pipx")
    
    elif choice == "3":
        # 直接安装
        install_with_pip()
    
    elif choice == "4":
        # 用户目录安装
        install_with_user_flag()
    
    elif choice == "5":
        # 强制安装
        install_with_break_system_packages()
    
    elif choice == "6":
        # 手动安装说明
        print("\n📖 手动安装说明:")
        print("\n方法1: 使用虚拟环境（推荐）")
        print("  python3 -m venv venv")
        if platform.system() == "Windows":
            print("  venv\\Scripts\\activate")
        else:
            print("  source venv/bin/activate")
        print("  pip install bilitool")
        
        print("\n方法2: 使用 pipx")
        if platform.system() == "Darwin":  # macOS
            print("  brew install pipx")
        else:
            print("  python3 -m pip install --user pipx")
        print("  pipx install bilitool")
        
        print("\n方法3: 用户目录安装")
        print("  pip3 install --user bilitool")
        
        print("\n方法4: 强制安装（不推荐）")
        print("  pip3 install --break-system-packages bilitool")
    
    else:
        print("❌ 无效选择")
    
    # 再次检查安装结果
    print("\n" + "=" * 50)
    installed, version = check_bilitool_installed()
    if installed:
        print(f"🎉 安装成功！bilitool 版本: {version}")
        print("\n现在可以运行测试:")
        print("  python3 test_bilibili_upload.py")
    else:
        print("❌ 安装失败，请参考手动安装说明")

if __name__ == "__main__":
    main()