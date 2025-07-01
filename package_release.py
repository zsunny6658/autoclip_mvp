#!/usr/bin/env python3
"""
自动打包脚本 - 整理基础版本文件
"""
import os
import shutil
import zipfile
import tarfile
from pathlib import Path
import json

class ReleasePackager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.release_dir = self.project_root / "release"
        self.version = "1.0.0"
        
        # 需要包含的文件和目录
        self.include_files = [
            # 根目录文件
            "README.md",
            "requirements.txt", 
            "backend_requirements.txt",
            ".gitignore",
            "start_dev.sh",
            "main.py",
            "app.py",
            "backend_server.py",
            "simple_api.py",
            "start.py",
            "run_tests.py",
            "fix_project_data.py",
            
            # 文档文件
            "BACKEND_ARCHITECTURE.md",
            "BILITOOL_INTEGRATION.md",
            "B站视频下载方案调研报告.md",
        ]
        
        self.include_dirs = [
            # 后端代码
            "src",
            "prompt",
            "data",
            "tests",
            
            # 前端代码
            "frontend",
            
            # 输出目录（只包含.gitkeep文件）
            "output",
            "uploads",
        ]
        
        # 需要排除的文件和目录
        self.exclude_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            "node_modules",
            "venv",
            "*.log",
            "temp",
            "uploads/*/",  # 排除用户上传的内容
            "output/clips/*",  # 排除生成的视频片段
            "output/collections/*",  # 排除生成的合集
            "output/metadata/*",  # 排除生成的元数据
        ]
    
    def clean_release_dir(self):
        """清理发布目录"""
        if self.release_dir.exists():
            shutil.rmtree(self.release_dir)
        self.release_dir.mkdir(exist_ok=True)
        print(f"✅ 清理发布目录: {self.release_dir}")
    
    def should_exclude(self, file_path: Path) -> bool:
        """检查文件是否应该被排除"""
        file_str = str(file_path)
        
        for pattern in self.exclude_patterns:
            if pattern.endswith('/*'):
                # 目录模式匹配
                dir_pattern = pattern[:-2]
                if dir_pattern in file_str and file_path.is_file():
                    return True
            elif '*' in pattern:
                # 通配符模式匹配
                import fnmatch
                if fnmatch.fnmatch(file_path.name, pattern):
                    return True
            else:
                # 精确匹配
                if pattern in file_str:
                    return True
        
        return False
    
    def copy_file(self, src: Path, dst: Path):
        """复制单个文件"""
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  📄 {src} -> {dst}")
        except Exception as e:
            print(f"  ❌ 复制失败 {src}: {e}")
    
    def copy_directory(self, src: Path, dst: Path):
        """复制目录（排除不需要的文件）"""
        if not src.exists():
            print(f"  ⚠️  目录不存在: {src}")
            return
        
        try:
            dst.mkdir(parents=True, exist_ok=True)
            
            for item in src.rglob('*'):
                if item.is_file():
                    rel_path = item.relative_to(src)
                    dst_file = dst / rel_path
                    
                    if not self.should_exclude(item):
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dst_file)
                        print(f"  📄 {rel_path}")
                    else:
                        print(f"  ⏭️  跳过: {rel_path}")
                        
        except Exception as e:
            print(f"  ❌ 复制目录失败 {src}: {e}")
    
    def create_package(self):
        """创建发布包"""
        print("🚀 开始创建发布包...")
        
        # 清理发布目录
        self.clean_release_dir()
        
        # 复制根目录文件
        print("\n📁 复制根目录文件:")
        for file_name in self.include_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                dst_file = self.release_dir / file_name
                self.copy_file(src_file, dst_file)
            else:
                print(f"  ⚠️  文件不存在: {file_name}")
        
        # 复制目录
        print("\n📁 复制目录:")
        for dir_name in self.include_dirs:
            src_dir = self.project_root / dir_name
            dst_dir = self.release_dir / dir_name
            
            if src_dir.exists():
                print(f"\n📂 复制目录: {dir_name}")
                self.copy_directory(src_dir, dst_dir)
            else:
                print(f"  ⚠️  目录不存在: {dir_name}")
        
        # 创建版本信息文件
        self.create_version_info()
        
        print(f"\n✅ 发布包创建完成: {self.release_dir}")
    
    def create_version_info(self):
        """创建版本信息文件"""
        version_info = {
            "version": self.version,
            "build_time": str(Path().cwd()),
            "files_count": self.count_files(),
            "total_size": self.get_total_size()
        }
        
        version_file = self.release_dir / "version.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        print(f"  📄 创建版本信息: version.json")
    
    def count_files(self) -> int:
        """统计文件数量"""
        count = 0
        for root, dirs, files in os.walk(self.release_dir):
            count += len(files)
        return count
    
    def get_total_size(self) -> int:
        """计算总大小（字节）"""
        total_size = 0
        for root, dirs, files in os.walk(self.release_dir):
            for file in files:
                file_path = Path(root) / file
                total_size += file_path.stat().st_size
        return total_size
    
    def create_zip_archive(self):
        """创建ZIP压缩包"""
        zip_name = f"auto_clips_basic_v{self.version}.zip"
        zip_path = self.project_root / zip_name
        
        print(f"\n📦 创建ZIP压缩包: {zip_name}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.release_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(self.release_dir)
                    zipf.write(file_path, arc_name)
        
        zip_size = zip_path.stat().st_size
        print(f"✅ ZIP压缩包创建完成: {zip_path} ({zip_size / 1024 / 1024:.1f} MB)")
        return zip_path
    
    def create_tar_archive(self):
        """创建TAR压缩包"""
        tar_name = f"auto_clips_basic_v{self.version}.tar.gz"
        tar_path = self.project_root / tar_name
        
        print(f"\n📦 创建TAR压缩包: {tar_name}")
        
        with tarfile.open(tar_path, 'w:gz') as tar:
            tar.add(self.release_dir, arcname='auto_clips_basic')
        
        tar_size = tar_path.stat().st_size
        print(f"✅ TAR压缩包创建完成: {tar_path} ({tar_size / 1024 / 1024:.1f} MB)")
        return tar_path
    
    def generate_file_list(self):
        """生成文件清单"""
        file_list = []
        
        for root, dirs, files in os.walk(self.release_dir):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.release_dir)
                file_size = file_path.stat().st_size
                file_list.append({
                    "path": str(rel_path),
                    "size": file_size,
                    "size_mb": file_size / 1024 / 1024
                })
        
        # 按路径排序
        file_list.sort(key=lambda x: x["path"])
        
        # 保存到文件
        list_file = self.project_root / f"file_list_v{self.version}.json"
        with open(list_file, 'w', encoding='utf-8') as f:
            json.dump(file_list, f, indent=2, ensure_ascii=False)
        
        print(f"📋 文件清单已生成: {list_file}")
        
        # 打印统计信息
        total_files = len(file_list)
        total_size = sum(f["size"] for f in file_list)
        print(f"📊 统计信息:")
        print(f"   - 文件总数: {total_files}")
        print(f"   - 总大小: {total_size / 1024 / 1024:.1f} MB")
        
        return file_list

def main():
    """主函数"""
    packager = ReleasePackager()
    
    try:
        # 创建发布包
        packager.create_package()
        
        # 生成文件清单
        packager.generate_file_list()
        
        # 创建压缩包
        zip_path = packager.create_zip_archive()
        tar_path = packager.create_tar_archive()
        
        print(f"\n🎉 发布包创建完成!")
        print(f"📦 ZIP包: {zip_path}")
        print(f"📦 TAR包: {tar_path}")
        print(f"📁 源码目录: {packager.release_dir}")
        
    except Exception as e:
        print(f"❌ 创建发布包失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 