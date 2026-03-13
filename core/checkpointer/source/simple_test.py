#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""シンプルなテストスクリプト - テストを直接実行する"""
import sys
import os

# 環境の設定
os.chdir(r"C:\pythonProject\python_ai_cspm\TestReport\checkpointer\source")
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
sys.path.insert(0, PROJECT_ROOT)

print("=" * 80)
print("checkpointer 测试执行")
print("=" * 80)

# Mock が必要なモジュール
from unittest.mock import MagicMock
sys.modules['psycopg_pool'] = MagicMock()
sys.modules['psycopg_pool'].AsyncConnectionPool = MagicMock
sys.modules['langgraph.checkpoint.postgres'] = MagicMock()
sys.modules['langgraph.checkpoint.postgres.aio'] = MagicMock()
sys.modules['langgraph.checkpoint.postgres.aio'].AsyncPostgresSaver = MagicMock
print("✓ Mock 模块已创建\n")

# テストを実行する
import pytest
sys.exit(pytest.main(['-v', '--tb=short', 'test_checkpointer.py']))
