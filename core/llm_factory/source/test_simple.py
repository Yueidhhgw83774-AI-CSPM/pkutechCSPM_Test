"""簡単なテストでmockが正常に動作するかを確認する"""
import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# プロジェクトルートディレクトリをインポートする
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


def test_mock_works(mock_chat_openai, mock_settings_env):
    """mockの動作が正常かどうかを検証する"""
    # モジュールをインポートする
    from app.core.llm_factory import LLMFactory

    # メソッドを呼び出す
    result = LLMFactory.create_llm(model_name="gpt-5.1-chat")

    # mockの呼び出しが行われたことを確認する
    print(f"Mock called: {mock_chat_openai.called}")
    print(f"Mock call_args: {mock_chat_openai.call_args}")

    assert mock_chat_openai.called, "Mock was not called!"
    assert mock_chat_openai.call_args is not None, "Mock call_args is None!"
