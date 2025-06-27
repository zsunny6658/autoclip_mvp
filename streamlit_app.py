#!/usr/bin/env python3
"""
Streamlit应用启动脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 导入并运行Streamlit应用
    from app import main
    main() 