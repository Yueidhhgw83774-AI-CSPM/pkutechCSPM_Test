"""简单的测试执行脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

# 运行pytest
import pytest

if __name__ == "__main__":
    # 运行测试
    exit_code = pytest.main([
        "test_clients.py",
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ])

    print(f"\n测试执行完成,退出码: {exit_code}")
    sys.exit(exit_code)
