"""シンプルなテスト実行スクリプト"""
import sys
from pathlib import Path

# プロジェクトルートディレクトリをパスに追加する
project_root = Path(__file__).parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

# pytestを実行する
import pytest

if __name__ == "__main__":
    # テストを実行する
    exit_code = pytest.main([
        "test_clients.py",
        "-v",
        "--tb=short",
        "-p", "no:warnings"
    ])

    print(f"\n测试执行完成,退出码: {exit_code}")
    sys.exit(exit_code)
