#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试测试环境
"""
import sys
import os

print("=" * 80)
print("环境检查")
print("=" * 80)

print(f"Python 版本: {sys.version}")
print(f"Python 路径: {sys.executable}")
print(f"当前目录: {os.getcwd()}")
print(f"\nsys.path:")
for p in sys.path[:5]:
    print(f"  - {p}")

print("\n" + "=" * 80)
print("尝试导入模块")
print("=" * 80)

# 添加项目路径
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    print(f"✓ 已添加项目路径: {PROJECT_ROOT}")

# Mock psycopg_pool
from unittest.mock import MagicMock
if 'psycopg_pool' not in sys.modules:
    sys.modules['psycopg_pool'] = MagicMock()
    sys.modules['psycopg_pool'].AsyncConnectionPool = MagicMock
    print("✓ 已 mock psycopg_pool")

if 'langgraph.checkpoint.postgres' not in sys.modules:
    sys.modules['langgraph.checkpoint.postgres'] = MagicMock()
if 'langgraph.checkpoint.postgres.aio' not in sys.modules:
    sys.modules['langgraph.checkpoint.postgres.aio'] = MagicMock()
    sys.modules['langgraph.checkpoint.postgres.aio'].AsyncPostgresSaver = MagicMock
    print("✓ 已 mock langgraph.checkpoint.postgres")

# 尝试导入 config
try:
    from app.core import config
    print(f"✓ 成功导入 app.core.config")
    print(f"  settings 类型: {type(config.settings)}")
except Exception as e:
    print(f"✗ 导入 app.core.config 失败: {e}")
    import traceback
    traceback.print_exc()

# 尝试导入 checkpointer
try:
    from app.core import checkpointer
    print(f"✓ 成功导入 app.core.checkpointer")
    print(f"  模块路径: {checkpointer.__file__}")
except Exception as e:
    print(f"✗ 导入 app.core.checkpointer 失败: {e}")
    import traceback
    traceback.print_exc()

# 检查 pytest
try:
    import pytest
    print(f"\n✓ pytest 已安装: {pytest.__version__}")
except ImportError:
    print(f"\n✗ pytest 未安装")

print("\n" + "=" * 80)
print("尝试运行一个简单测试")
print("=" * 80)

try:
    from app.core.checkpointer import get_current_storage_mode
    result = get_current_storage_mode()
    print(f"✓ get_current_storage_mode() = '{result}'")
except Exception as e:
    print(f"✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
