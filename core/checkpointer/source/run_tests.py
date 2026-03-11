#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行 checkpointer 测试并捕获输出
"""
import sys
import subprocess

def run_tests():
    """运行测试并捕获输出"""
    print("=" * 80)
    print("开始运行 checkpointer 测试")
    print("=" * 80)

    cmd = [
        sys.executable,
        "-m", "pytest",
        "test_checkpointer.py",
        "-v",
        "--tb=short",
        "--no-header"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=r"C:\pythonProject\python_ai_cspm\TestReport\checkpointer\source"
        )

        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\n返回码: {result.returncode}")

        return result.returncode
    except Exception as e:
        print(f"运行测试时出错: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
