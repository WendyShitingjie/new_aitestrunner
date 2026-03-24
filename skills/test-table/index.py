#!/usr/bin/env python3
"""
JDBC 测试表生成器 - Skill 入口脚本
"""
import sys
import os

# 添加 scripts 目录到路径
script_dir = os.path.join(os.path.dirname(__file__), 'scripts')
sys.path.insert(0, script_dir)

# 导入主脚本
from index import main

if __name__ == '__main__':
    main()
