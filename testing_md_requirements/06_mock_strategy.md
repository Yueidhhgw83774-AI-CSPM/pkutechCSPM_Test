# モック戦略

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトのテストにおけるモック戦略を説明します。

## 2. モック対象の分類

### 2.1 モック対象マトリクス

| 対象 | ユニットテスト | 統合テスト | E2Eテスト |
|------|---------------|-----------|----------|
| LLM API | モック | モック | 実際（またはモック） |
| OpenSearch | モック | 実際（テスト環境） | 実際 |
| AWS SDK | モック（moto） | モック（moto） | 実際（テスト環境） |
| ファイルシステム | モック（tmp_path） | 実際 | 実際 |
| 外部HTTP API | モック | モック | 実際 |
| 時間/日付 | モック | 実際 | 実際 |

## 3. LLM モック戦略

### 3.1 基本的なLLMモック

```python
from unittest.mock import AsyncMock, MagicMock, patch


class MockLLMResponse:
    """LLMレスポンスのモックヘルパークラス"""

    @staticmethod
    def simple_response(content: str = "Mocked response"):
        """シンプルなテキストレスポンス"""
        mock = MagicMock()
        mock.content = content
        return mock

    @staticmethod
    def tool_call_response(tool_name: str, tool_args: dict):
        """ツール呼び出しを含むレスポンス"""
        mock = MagicMock()
        mock.content = ""
        mock.tool_calls = [{
            "name": tool_name,
            "args": tool_args,
            "id": f"call_{tool_name}"
        }]
        return mock

    @staticmethod
    def streaming_response(chunks: list[str]):
        """ストリーミングレスポンス"""
        async def stream():
            for chunk in chunks:
                mock_chunk = MagicMock()
                mock_chunk.content = chunk
                yield mock_chunk
        return stream()


# 使用例
@pytest.fixture
def mock_llm():
    """LLMモックフィクスチャ"""
    with patch("langchain_openai.ChatOpenAI") as mock_class:
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # デフォルトレスポンス設定
        mock_instance.ainvoke.return_value = MockLLMResponse.simple_response()

        yield mock_instance
```

### 3.2 LangChain/LangGraphエージェントのモック

```python
@pytest.fixture
def mock_langgraph_agent():
    """
    LangGraphエージェントのモック

    用途:
        - エージェント実行フローのテスト
        - 状態遷移の検証
    """
    with patch("langgraph.graph.StateGraph") as mock_graph:
        mock_compiled = AsyncMock()

        # invoke結果のモック
        mock_compiled.ainvoke.return_value = {
            "messages": [MagicMock(content="Agent response")],
            "status": "completed"
        }

        mock_graph.return_value.compile.return_value = mock_compiled
        yield mock_compiled


# 使用例
class TestPolicyAgent:
    async def test_agent_execution(self, mock_langgraph_agent):
        """エージェント実行のテスト"""
        mock_langgraph_agent.ainvoke.return_value = {
            "messages": [MagicMock(content="Generated policy: ...")],
            "status": "success",
            "policy_content": "policies:\n  - name: test"
        }

        result = await run_policy_agent(
            item_data={"uid": "test"},
            target_cloud="aws"
        )

        assert result["status"] == "success"
```

### 3.3 LLMファクトリのモック

```python
@pytest.fixture
def mock_llm_factory():
    """
    LLMファクトリのモック

    用途:
        - 異なるLLMプロバイダーのテスト
        - モデル選択ロジックのテスト
    """
    with patch("app.core.llm_factory.create_llm") as mock_factory:
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MockLLMResponse.simple_response()
        mock_factory.return_value = mock_llm
        yield mock_factory


# 使用例
class TestLLMSelection:
    async def test_openai_model_selection(self, mock_llm_factory):
        """OpenAIモデル選択のテスト"""
        await some_function_using_llm()

        mock_llm_factory.assert_called_once()
        call_args = mock_llm_factory.call_args
        assert call_args.kwargs.get("provider") == "openai"
```

## 4. OpenSearch モック戦略

### 4.1 基本的なOpenSearchモック

```python
class MockOpenSearchClient:
    """OpenSearchクライアントのモックヘルパー"""

    @staticmethod
    def create_mock():
        """基本的なモッククライアント作成"""
        mock = AsyncMock()

        # 検索結果のデフォルト
        mock.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        # インデックス操作
        mock.index.return_value = {"result": "created", "_id": "mock-id"}
        mock.delete.return_value = {"result": "deleted"}
        mock.update.return_value = {"result": "updated"}

        # バルク操作
        mock.bulk.return_value = {"errors": False, "items": []}

        return mock

    @staticmethod
    def with_search_results(hits: list[dict]):
        """検索結果を設定したモック"""
        mock = MockOpenSearchClient.create_mock()
        mock.search.return_value = {
            "hits": {
                "total": {"value": len(hits)},
                "hits": [
                    {"_id": f"doc-{i}", "_source": hit}
                    for i, hit in enumerate(hits)
                ]
            }
        }
        return mock


@pytest.fixture
def mock_opensearch():
    """OpenSearchモックフィクスチャ"""
    with patch("app.core.clients.get_opensearch_client") as mock_getter:
        mock_client = MockOpenSearchClient.create_mock()
        mock_getter.return_value = mock_client
        yield mock_client
```

### 4.2 検索結果のカスタマイズ

```python
@pytest.fixture
def mock_opensearch_with_policies(mock_opensearch):
    """ポリシーデータを含むOpenSearchモック"""
    policies = [
        {
            "name": "s3-encryption",
            "resource": "s3",
            "status": "active"
        },
        {
            "name": "ec2-security-group",
            "resource": "ec2",
            "status": "active"
        }
    ]

    mock_opensearch.search.return_value = {
        "hits": {
            "total": {"value": len(policies)},
            "hits": [
                {"_id": f"policy-{i}", "_source": p}
                for i, p in enumerate(policies)
            ]
        }
    }

    return mock_opensearch
```

## 5. AWS SDK モック戦略

### 5.1 motoを使用したモック

```python
import pytest
from moto import mock_s3, mock_ec2
import boto3


@pytest.fixture
def aws_credentials():
    """AWS認証情報のモック設定"""
    import os
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "ap-northeast-1"


@pytest.fixture
def mock_s3_client(aws_credentials):
    """S3クライアントのモック"""
    with mock_s3():
        client = boto3.client("s3", region_name="ap-northeast-1")

        # テスト用バケット作成
        client.create_bucket(
            Bucket="test-bucket",
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"}
        )

        yield client


@pytest.fixture
def mock_ec2_client(aws_credentials):
    """EC2クライアントのモック"""
    with mock_ec2():
        client = boto3.client("ec2", region_name="ap-northeast-1")
        yield client


# 使用例
class TestAWSOperations:
    def test_s3_list_buckets(self, mock_s3_client):
        """S3バケット一覧取得のテスト"""
        response = mock_s3_client.list_buckets()
        buckets = [b["Name"] for b in response["Buckets"]]
        assert "test-bucket" in buckets
```

### 5.2 非同期AWSクライアントのモック

```python
@pytest.fixture
def mock_async_s3():
    """非同期S3クライアントのモック"""
    with patch("aioboto3.Session") as mock_session:
        mock_client = AsyncMock()

        # list_objects_v2のモック
        mock_client.list_objects_v2.return_value = {
            "Contents": [
                {"Key": "file1.txt", "Size": 100},
                {"Key": "file2.txt", "Size": 200}
            ]
        }

        # get_objectのモック
        mock_body = AsyncMock()
        mock_body.read.return_value = b"file content"
        mock_client.get_object.return_value = {"Body": mock_body}

        mock_session.return_value.client.return_value.__aenter__.return_value = mock_client
        yield mock_client
```

## 6. 外部HTTP APIモック

### 6.1 responsesを使用したモック

```python
import responses
import pytest


@pytest.fixture
def mock_external_api():
    """外部APIのモック"""
    with responses.RequestsMock() as rsps:
        yield rsps


# 使用例
class TestExternalAPIIntegration:
    def test_fetch_external_data(self, mock_external_api):
        """外部API呼び出しのテスト"""
        mock_external_api.add(
            responses.GET,
            "https://api.example.com/data",
            json={"status": "ok", "data": []},
            status=200
        )

        result = fetch_external_data()
        assert result["status"] == "ok"
```

### 6.2 httpxを使用した非同期モック

```python
from pytest_httpx import HTTPXMock


@pytest.fixture
def mock_httpx(httpx_mock: HTTPXMock):
    """httpxのモック"""
    return httpx_mock


# 使用例
class TestAsyncHTTP:
    async def test_async_api_call(self, mock_httpx):
        """非同期API呼び出しのテスト"""
        mock_httpx.add_response(
            method="POST",
            url="https://api.example.com/endpoint",
            json={"result": "success"}
        )

        result = await async_api_call()
        assert result["result"] == "success"
```

## 7. 時間・日付のモック

### 7.1 freezegunを使用したモック

```python
from freezegun import freeze_time
import pytest


@freeze_time("2024-01-15 10:30:00")
def test_timestamp_generation():
    """タイムスタンプ生成のテスト"""
    from datetime import datetime
    now = datetime.now()
    assert now.year == 2024
    assert now.month == 1
    assert now.day == 15


@pytest.fixture
def frozen_time():
    """時間を固定するフィクスチャ"""
    with freeze_time("2024-01-15 10:30:00") as frozen:
        yield frozen


# 使用例
class TestTimeSensitiveFeature:
    def test_expiration_check(self, frozen_time):
        """有効期限チェックのテスト"""
        token = create_token(expires_in=3600)  # 1時間後

        # 時間を進める
        frozen_time.tick(delta=timedelta(hours=2))

        assert is_token_expired(token) is True
```

## 8. モック設計のベストプラクティス

### 8.1 モックの範囲を最小限に

```python
# 良い例: 必要な部分のみモック
@patch("app.services.policy.validate_yaml")
def test_policy_creation(mock_validate):
    mock_validate.return_value = True
    result = create_policy("valid yaml")
    assert result.is_valid

# 悪い例: 広範囲のモック
@patch("app.services")  # サービス全体をモック - 避けるべき
def test_bad_example(mock_services):
    pass
```

### 8.2 モックの検証

```python
def test_llm_called_with_correct_prompt(mock_llm):
    """LLMが正しいプロンプトで呼び出されたか検証"""
    await generate_policy("S3暗号化チェック")

    # 呼び出し回数の検証
    assert mock_llm.ainvoke.call_count == 1

    # 引数の検証
    call_args = mock_llm.ainvoke.call_args
    messages = call_args[0][0]  # 最初の位置引数
    assert "S3暗号化" in str(messages)
```

### 8.3 モックのリセット

```python
@pytest.fixture(autouse=True)
def reset_mocks(mock_llm, mock_opensearch):
    """各テスト後にモックをリセット"""
    yield
    mock_llm.reset_mock()
    mock_opensearch.reset_mock()
```

## 9. モッククラス一覧

| クラス名 | 用途 | ファイル |
|---------|------|---------|
| `MockLLMResponse` | LLMレスポンス生成 | `conftest.py` |
| `MockOpenSearchClient` | OpenSearchクライアント | `conftest.py` |
| `MockAWSClient` | AWSサービスクライアント | `conftest.py` |
| `MockHTTPResponse` | HTTPレスポンス | `conftest.py` |
