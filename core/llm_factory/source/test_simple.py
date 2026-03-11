"""简单测试验证mock是否工作"""
import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# 导入项目根目录
project_root = Path(__file__).parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


def test_mock_works(mock_chat_openai, mock_settings_env):
    """验证mock是否正常工作"""
    # 导入模块
    from app.core.llm_factory import LLMFactory

    # 调用方法
    result = LLMFactory.create_llm(model_name="gpt-5.1-chat")

    # 验证mock被调用
    print(f"Mock called: {mock_chat_openai.called}")
    print(f"Mock call_args: {mock_chat_openai.call_args}")

    assert mock_chat_openai.called, "Mock was not called!"
    assert mock_chat_openai.call_args is not None, "Mock call_args is None!"
