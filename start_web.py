#!/usr/bin/env python3
"""
PDF翻译工具 - Web服务器启动脚本

使用方法:
    python start_web.py

或者手动启动:
    cd /Users/max/Documents/pdf_trans_tools
    PYTHONPATH=src python -m pdf_trans_tools.web
"""
import os
import sys

# 确保在正确的工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 设置 PYTHONPATH
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
if 'PYTHONPATH' not in os.environ:
    os.environ['PYTHONPATH'] = src_path
elif src_path not in os.environ['PYTHONPATH']:
    os.environ['PYTHONPATH'] = src_path + os.pathsep + os.environ['PYTHONPATH']

# 启动服务器
from pdf_trans_tools.web import run_server

if __name__ == "__main__":
    print("=" * 60)
    print("PDF翻译工具 Web界面")
    print("=" * 60)
    print()
    print("启动服务器: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print()
    run_server(host="127.0.0.1", port=5000, debug=True)
