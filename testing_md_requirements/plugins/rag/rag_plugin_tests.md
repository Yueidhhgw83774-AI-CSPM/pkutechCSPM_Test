# rag_plugin テストケース

## 1. 概要

`rag_plugin` はCloud Custodianドキュメント特化の強化版RAG（Retrieval-Augmented Generation）検索システムを提供するプラグインです。
OpenSearchベクトル検索とLLMを組み合わせた質問応答機能を提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `RAGClient.initialize` | RAGクライアントの初期化（OpenSearch、Embedding、VectorStore、ChatModel） |
| `RAGClient.search_documents` | ベクトル検索によるドキュメント検索 |
| `RAGClient.search_with_scores` | スコア付きドキュメント検索 |
| `RAGClient._get_opensearch_auth_config` | OpenSearch認証設定取得（AWS IAM / Basic認証） |
| `RAGClient.check_health` | RAGクライアントのヘルスチェック |
| `RAGClient.get_index_info` | インデックス情報取得 |
| `EnhancedRAGSearch.search` | 基本検索機能（フィルター対応） |
| `EnhancedRAGSearch.qa_search` | 質問応答機能（LLMによる回答生成） |
| `EnhancedRAGSearch.get_health` | システムヘルスチェック |
| `RAGManager.get_instance` | シングルトンインスタンス取得 |
| `RAGManager.initialize` | RAG管理システムの初期化 |
| `router.search_documents` | 検索APIエンドポイント |
| `router.qa_search` | QA APIエンドポイント |

### 1.2 カバレッジ目標: 85%

> **注記**: RAGシステムはLLM統合とベクトル検索を含む複雑なシステムであり、OpenSearch、OpenAI Embeddings、ChatGPTなど複数の外部サービスに依存します。これらは全てモックでカバーします。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象（クライアント） | `app/rag/rag_client.py` |
| テスト対象（検索システム） | `app/rag/enhanced_rag_search.py` |
| テスト対象（ルーター） | `app/rag/router.py` |
| テスト対象（モデル） | `app/rag/models.py` |
| テスト対象（マネージャー） | `app/core/rag_manager.py` |
| テストコード | `test/unit/rag/test_rag_client.py` |
| テストコード | `test/unit/rag/test_enhanced_rag_search.py` |
| テストコード | `test/unit/rag/test_router.py` |
| テストコード | `test/unit/rag/test_rag_manager.py` |

### 1.4 補足情報

#### グローバル変数
- `_global_rag_manager` (rag_manager.py:124): グローバルRAGマネージャーインスタンス
- `RAGManager._instance` (rag_manager.py:20): シングルトンインスタンス
- `RAGManager._lock` (rag_manager.py:21): 非同期ロック

#### 主要分岐
- rag_client.py:44-45: 初期化済みチェック
- rag_client.py:52-54: OpenSearchクライアント存在チェック
- rag_client.py:58-60: Embedding機能存在チェック
- rag_client.py:125-170: AWS OpenSearch vs 自前OpenSearchの認証設定分岐
- rag_client.py:131-138: AWS IAM認証のリージョン推定ロジック
- rag_client.py:161-170: IAM認証失敗時のBasic認証フォールバック
- enhanced_rag_search.py:57-83: フィルター条件構築
- enhanced_rag_search.py:268-275: ヘルスステータス判定（healthy/degraded/unhealthy）
- rag_manager.py:33-37: シングルトン取得のダブルチェックロック
- rag_manager.py:43-49: 初期化のダブルチェックロック

#### 外部依存
- boto3: AWS認証情報取得
- langchain_community: OpenSearchVectorSearch
- langchain_openai: ChatOpenAI, OpenAIEmbeddings
- opensearchpy: AsyncOpenSearch
- requests_aws4auth: AWS4Auth

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|----------|
| RAG-001 | RAGClient初期化成功 | 有効な設定 | _initialized=True |
| RAG-002 | 初期化済みの場合は即時True | 既に初期化済み | True（再初期化なし） |
| RAG-003 | VectorStore初期化成功 | OpenSearch設定 | vectorstore設定完了 |
| RAG-004 | ChatModel初期化成功 | LLM設定 | chat_model設定完了 |
| RAG-005 | AWS OpenSearch認証設定（IAM） | AWS環境 | AWS4Auth返却 |
| RAG-006 | AWS OpenSearch認証設定（Basic認証フォールバック） | IAM失敗時 | user/password認証 |
| RAG-007 | 自前OpenSearch認証設定 | ローカル環境 | Basic認証+CA証明書 |
| RAG-008 | ドキュメント検索成功 | 有効なクエリ | Documentリスト |
| RAG-009 | スコア付き検索成功 | 有効なクエリ | (Document, score)リスト |
| RAG-010 | フィルター付き検索成功 | クエリ+フィルター | フィルター適用済み結果 |
| RAG-011 | ChatModel取得成功 | 初期化済み | ChatModelインスタンス |
| RAG-012 | ヘルスチェック成功 | 初期化済み | 全項目True |
| RAG-013 | インデックス情報取得成功 | 有効なインデックス | document_count, index_size含む |
| RAG-014 | EnhancedRAGSearch初期化成功 | 有効な設定 | _initialized=True |
| RAG-015 | フィルター構築（cloud指定） | cloud="aws" | term filterあり |
| RAG-016 | フィルター構築（複数条件） | cloud+section_type | bool mustクエリ |
| RAG-017 | フィルター構築（フィルターなし） | None | None返却 |
| RAG-046 | フィルター構築（空フィルター） | SearchFilters() | None返却 |
| RAG-018 | ドキュメント変換成功 | Documentリスト | DocumentResultリスト |
| RAG-019 | ドキュメント変換（スコア付き） | Documentリスト+スコア | scoreフィールド設定 |
| RAG-020 | 基本検索成功 | RAGSearchRequest | RAGSearchResponse |
| RAG-021 | フィルター専用検索成功 | query, cloud | section_type="filter"で検索 |
| RAG-022 | アクション専用検索成功 | query, cloud | section_type="action"で検索 |
| RAG-023 | コード例検索成功 | query, cloud | has_code_example=Trueで検索 |
| RAG-024 | QA検索成功 | RAGQARequest | answer含むRAGQAResponse |
| RAG-025 | QA検索（ソースなし） | include_sources=False | sources=None |
| RAG-026 | システムヘルスチェック（healthy） | 全接続正常 | status="healthy" |
| RAG-027 | システムヘルスチェック（degraded） | OpenSearchのみ接続 | status="degraded" |
| RAG-028 | インデックス情報取得（EnhancedRAGSearch） | 初期化済み | RAGIndexInfoResponse |
| RAG-029 | RAGManager.get_instance成功 | 初回呼び出し | 新規インスタンス |
| RAG-030 | RAGManager.get_instance（既存） | 2回目呼び出し | 同一インスタンス |
| RAG-031 | RAGManager.initialize成功 | 有効な設定 | True |
| RAG-032 | RAGManager初期化済み確認 | 初期化後 | is_initialized()=True |
| RAG-033 | RAGManager.health_check成功 | 初期化済み | status="healthy" |
| RAG-034 | グローバルRAGマネージャー取得 | - | RAGManagerインスタンス |
| RAG-035 | グローバルRAGシステム初期化 | - | True |
| RAG-036 | 検索エンドポイント成功 | POST /rag/search | 200, RAGSearchResponse |
| RAG-037 | フィルター検索エンドポイント成功 | GET /rag/search/filters | 200 |
| RAG-038 | アクション検索エンドポイント成功 | GET /rag/search/actions | 200 |
| RAG-039 | コード例検索エンドポイント成功 | GET /rag/search/code-examples | 200 |
| RAG-040 | QAエンドポイント成功 | POST /rag/qa | 200, RAGQAResponse |
| RAG-041 | ヘルスエンドポイント成功 | GET /rag/health | 200, RAGHealthResponse |
| RAG-042 | インデックス情報エンドポイント成功 | GET /rag/index/info | 200 |
| RAG-043 | AWS EC2検索エンドポイント成功 | GET /rag/search/aws/ec2 | 200 |
| RAG-044 | AWS S3検索エンドポイント成功 | GET /rag/search/aws/s3 | 200 |
| RAG-045 | セキュリティ検索エンドポイント成功 | GET /rag/search/security | 200 |

### 2.1 RAGClient テスト

```python
# test/unit/rag/test_rag_client.py
"""RAGClientのテスト

注意: opensearch_client, embedding_function, vectorstore, chat_modelは
conftest.pyのモックを使用します。
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.documents import Document


class TestRAGClientInitialization:
    """RAGClient初期化テスト"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_opensearch_client, mock_embedding_function):
        """RAG-001: RAGClient初期化成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.get_opensearch_client", new_callable=AsyncMock) as mock_get_os:
            mock_get_os.return_value = mock_opensearch_client
            with patch("app.rag.rag_client.get_embedding_function") as mock_get_emb:
                mock_get_emb.return_value = mock_embedding_function
                with patch.object(RAGClient, "_initialize_vectorstore", new_callable=AsyncMock):
                    with patch.object(RAGClient, "_initialize_chat_model"):
                        client = RAGClient()

                        # Act
                        result = await client.initialize()

                        # Assert
                        assert result is True
                        assert client._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_already_initialized(self):
        """RAG-002: 初期化済みの場合は即時True"""
        # Arrange
        from app.rag.rag_client import RAGClient
        client = RAGClient()
        client._initialized = True

        # Act
        result = await client.initialize()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_initialize_vectorstore_success(self, mock_embedding_function):
        """RAG-003: VectorStore初期化成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.OpenSearchVectorSearch") as mock_vs:
            mock_vs.return_value = MagicMock()
            client = RAGClient()
            client.embedding_function = mock_embedding_function

            with patch.object(client, "_get_opensearch_auth_config") as mock_auth:
                mock_auth.return_value = (("user", "pass"), {
                    "use_ssl": True,
                    "verify_certs": True,
                    "ssl_assert_hostname": True,
                    "ca_certs": None
                })

                # Act
                await client._initialize_vectorstore()

                # Assert
                assert client.vectorstore is not None
                mock_vs.assert_called_once()

    def test_initialize_chat_model_success(self):
        """RAG-004: ChatModel初期化成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.get_chat_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm
            client = RAGClient()

            # Act
            client._initialize_chat_model()

            # Assert
            assert client.chat_model is mock_llm
            mock_get_llm.assert_called_once_with(streaming=False)


class TestRAGClientAuthConfig:
    """RAGClient認証設定テスト"""

    def test_aws_opensearch_iam_auth(self):
        """RAG-005: AWS OpenSearch認証設定（IAM）"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = True
            with patch("app.rag.rag_client.boto3.Session") as mock_session_cls:
                mock_session = MagicMock()
                mock_credentials = MagicMock()
                mock_credentials.access_key = "AKIAIOSFODNN7EXAMPLE"
                mock_credentials.secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                mock_credentials.token = "session-token"
                mock_session.get_credentials.return_value = mock_credentials
                mock_session_cls.return_value = mock_session

                with patch("app.rag.rag_client.AWS4Auth") as mock_aws4auth:
                    mock_aws4auth.return_value = MagicMock()
                    with patch("app.rag.rag_client.settings") as mock_settings:
                        mock_settings.OPENSEARCH_URL = "https://search-test.ap-northeast-1.es.amazonaws.com"

                        client = RAGClient()

                        # Act
                        auth, ssl_config = client._get_opensearch_auth_config()

                        # Assert
                        mock_aws4auth.assert_called_once()
                        assert ssl_config["use_ssl"] is True
                        assert ssl_config["verify_certs"] is True

    def test_aws_opensearch_basic_auth_fallback(self):
        """RAG-006: AWS OpenSearch認証設定（Basic認証フォールバック）"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = True
            with patch("app.rag.rag_client.boto3.Session") as mock_session_cls:
                mock_session_cls.side_effect = Exception("IAM auth failed")
                with patch("app.rag.rag_client.settings") as mock_settings:
                    mock_settings.OPENSEARCH_URL = "https://search-test.ap-northeast-1.es.amazonaws.com"
                    mock_settings.OPENSEARCH_USER = "admin"
                    mock_settings.OPENSEARCH_PASSWORD = "password"

                    client = RAGClient()

                    # Act
                    auth, ssl_config = client._get_opensearch_auth_config()

                    # Assert
                    assert auth == ("admin", "password")
                    assert ssl_config["use_ssl"] is True

    def test_local_opensearch_basic_auth(self):
        """RAG-007: 自前OpenSearch認証設定"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = False
            with patch("app.rag.rag_client.settings") as mock_settings:
                mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                mock_settings.OPENSEARCH_USER = "admin"
                mock_settings.OPENSEARCH_PASSWORD = "password"
                mock_settings.OPENSEARCH_CA_CERTS_PATH = "/path/to/ca.crt"

                with patch("app.rag.rag_client.certifi.where") as mock_certifi:
                    mock_certifi.return_value = "/default/ca.crt"
                    client = RAGClient()

                    # Act
                    auth, ssl_config = client._get_opensearch_auth_config()

                    # Assert
                    assert auth == ("admin", "password")
                    assert ssl_config["ca_certs"] == "/path/to/ca.crt"


class TestRAGClientSearch:
    """RAGClient検索テスト"""

    @pytest.mark.asyncio
    async def test_search_documents_success(self):
        """RAG-008: ドキュメント検索成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        mock_documents = [
            Document(page_content="Test content 1", metadata={"source": "test1"}),
            Document(page_content="Test content 2", metadata={"source": "test2"})
        ]

        client = RAGClient()
        client._initialized = True
        client.vectorstore = MagicMock()
        client.vectorstore.similarity_search.return_value = mock_documents

        # Act
        results = await client.search_documents("test query", k=5)

        # Assert
        assert len(results) == 2
        assert results[0].page_content == "Test content 1"
        client.vectorstore.similarity_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_scores_success(self):
        """RAG-009: スコア付き検索成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        mock_results = [
            (Document(page_content="Test content 1", metadata={}), 0.95),
            (Document(page_content="Test content 2", metadata={}), 0.85)
        ]

        client = RAGClient()
        client._initialized = True
        client.vectorstore = MagicMock()
        client.vectorstore.similarity_search_with_score.return_value = mock_results

        # Act
        results = await client.search_with_scores("test query", k=5)

        # Assert
        assert len(results) == 2
        assert results[0][1] == 0.95

    @pytest.mark.asyncio
    async def test_search_with_filters(self):
        """RAG-010: フィルター付き検索成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        client = RAGClient()
        client._initialized = True
        client.vectorstore = MagicMock()
        client.vectorstore.similarity_search.return_value = []

        filters = {"term": {"metadata.cloud": "aws"}}

        # Act
        await client.search_documents("test", k=5, filters=filters)

        # Assert
        call_kwargs = client.vectorstore.similarity_search.call_args.kwargs
        assert call_kwargs["filter"] == filters

    @pytest.mark.asyncio
    async def test_get_chat_model_success(self):
        """RAG-011: ChatModel取得成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        mock_model = MagicMock()
        client = RAGClient()
        client._initialized = True
        client.chat_model = mock_model

        # Act
        result = await client.get_chat_model()

        # Assert
        assert result is mock_model


class TestRAGClientHealth:
    """RAGClientヘルスチェックテスト"""

    @pytest.mark.asyncio
    async def test_check_health_success(self):
        """RAG-012: ヘルスチェック成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        client = RAGClient()
        client._initialized = True
        client.opensearch_client = AsyncMock()
        client.opensearch_client.ping.return_value = True
        client.opensearch_client.indices.exists.return_value = True
        client.embedding_function = MagicMock()
        client.vectorstore = MagicMock()
        client.chat_model = MagicMock()
        client.index_name = "test-index"

        # Act
        health = await client.check_health()

        # Assert
        assert health["initialized"] is True
        assert health["opensearch_connected"] is True
        assert health["embedding_available"] is True
        assert health["vectorstore_available"] is True
        assert health["chat_model_available"] is True
        assert health["index_exists"] is True

    @pytest.mark.asyncio
    async def test_get_index_info_success(self):
        """RAG-013: インデックス情報取得成功"""
        # Arrange
        from app.rag.rag_client import RAGClient

        client = RAGClient()
        client.opensearch_client = AsyncMock()
        client.index_name = "test-index"
        client.opensearch_client.indices.stats.return_value = {
            "indices": {
                "test-index": {
                    "total": {
                        "docs": {"count": 1000},
                        "store": {"size_in_bytes": 1024000}
                    }
                }
            }
        }
        client.opensearch_client.indices.get_mapping.return_value = {
            "test-index": {"mappings": {"properties": {}}}
        }

        # Act
        info = await client.get_index_info()

        # Assert
        assert info["index_name"] == "test-index"
        assert info["document_count"] == 1000
        assert info["index_size"] == 1024000
```

### 2.2 EnhancedRAGSearch テスト

```python
# test/unit/rag/test_enhanced_rag_search.py
"""EnhancedRAGSearchのテスト"""
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.documents import Document

from app.rag.models import (
    RAGSearchRequest, RAGQARequest, SearchFilters, DocumentResult
)


class TestEnhancedRAGSearchInitialization:
    """EnhancedRAGSearch初期化テスト"""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """RAG-014: EnhancedRAGSearch初期化成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        with patch.object(EnhancedRAGSearch, "__init__", lambda x: None):
            search = EnhancedRAGSearch()
            search.rag_client = MagicMock()
            search.rag_client.initialize = AsyncMock(return_value=True)
            search._initialized = False

            # Act
            result = await search.initialize()

            # Assert
            assert result is True
            assert search._initialized is True


class TestEnhancedRAGSearchFilters:
    """EnhancedRAGSearchフィルター構築テスト"""

    def test_build_filters_cloud_only(self):
        """RAG-015: フィルター構築（cloud指定）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        filters = SearchFilters(cloud="aws")

        # Act
        result = search._build_filters(filters)

        # Assert
        assert result is not None
        assert "bool" in result
        assert {"term": {"metadata.cloud": "aws"}} in result["bool"]["must"]

    def test_build_filters_multiple_conditions(self):
        """RAG-016: フィルター構築（複数条件）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        filters = SearchFilters(cloud="aws", section_type="filter", has_code_example=True)

        # Act
        result = search._build_filters(filters)

        # Assert
        assert len(result["bool"]["must"]) == 3

    def test_build_filters_none(self):
        """RAG-017: フィルター構築（フィルターなし）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()

        # Act
        result = search._build_filters(None)

        # Assert
        assert result is None

    def test_build_filters_empty(self):
        """RAG-046: フィルター構築（空フィルター）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        filters = SearchFilters()  # 全てNone

        # Act
        result = search._build_filters(filters)

        # Assert
        assert result is None


class TestEnhancedRAGSearchDocumentConversion:
    """EnhancedRAGSearchドキュメント変換テスト"""

    def test_documents_to_results_success(self):
        """RAG-018: ドキュメント変換成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        documents = [
            Document(page_content="Content 1", metadata={"source": "test1", "cloud": "aws"}),
            Document(page_content="Content 2", metadata={"source": "test2", "cloud": "azure"})
        ]
        search = EnhancedRAGSearch()

        # Act
        results = search._documents_to_results(documents)

        # Assert
        assert len(results) == 2
        assert results[0].content == "Content 1"
        assert results[0].metadata["cloud"] == "aws"

    def test_documents_to_results_with_scores(self):
        """RAG-019: ドキュメント変換（スコア付き）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        documents = [
            Document(page_content="Content 1", metadata={}),
            Document(page_content="Content 2", metadata={})
        ]
        scores = [0.95, 0.85]
        search = EnhancedRAGSearch()

        # Act
        results = search._documents_to_results(documents, scores)

        # Assert
        assert results[0].score == 0.95
        assert results[1].score == 0.85


class TestEnhancedRAGSearchSearch:
    """EnhancedRAGSearch検索テスト"""

    @pytest.mark.asyncio
    async def test_search_success(self):
        """RAG-020: 基本検索成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        mock_documents = [
            Document(page_content="Test", metadata={"cloud": "aws"})
        ]

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(return_value=mock_documents)

        request = RAGSearchRequest(query="test query", k=5)

        # Act
        response = await search.search(request)

        # Assert
        assert response.query == "test query"
        assert response.total_results == 1
        assert response.execution_time_ms is not None

    @pytest.mark.asyncio
    async def test_search_filters_only(self):
        """RAG-021: フィルター専用検索成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(return_value=[])

        # Act
        response = await search.search_filters_only("test", cloud="aws", k=5)

        # Assert
        assert response.filters_applied.section_type == "filter"
        assert response.filters_applied.cloud == "aws"

    @pytest.mark.asyncio
    async def test_search_actions_only(self):
        """RAG-022: アクション専用検索成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(return_value=[])

        # Act
        response = await search.search_actions_only("test", cloud="gcp", k=3)

        # Assert
        assert response.filters_applied.section_type == "action"

    @pytest.mark.asyncio
    async def test_search_with_code_examples(self):
        """RAG-023: コード例検索成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(return_value=[])

        # Act
        response = await search.search_with_code_examples("test", k=5)

        # Assert
        assert response.filters_applied.has_code_example is True


class TestEnhancedRAGSearchQA:
    """EnhancedRAGSearch QA検索テスト"""

    @pytest.mark.asyncio
    async def test_qa_search_success(self):
        """RAG-024: QA検索成功"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        mock_documents = [
            Document(page_content="EC2の説明", metadata={"source": "ec2.md"})
        ]
        mock_model = MagicMock()

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(return_value=mock_documents)
        search.rag_client.get_chat_model = AsyncMock(return_value=mock_model)

        with patch("app.rag.enhanced_rag_search.PromptTemplate") as mock_prompt:
            with patch("app.rag.enhanced_rag_search.StrOutputParser") as mock_parser:
                mock_chain = MagicMock()
                mock_chain.invoke.return_value = "EC2はAWSの仮想サーバーです。"

                # RunnablePassthroughのモック
                with patch("app.rag.enhanced_rag_search.RunnablePassthrough"):
                    # チェーン構築のモック（|演算子）
                    mock_prompt.from_template.return_value.__or__ = MagicMock(return_value=mock_chain)

                    request = RAGQARequest(
                        question="EC2とは何ですか？",
                        context_limit=3,
                        include_sources=True
                    )

                    # Act
                    response = await search.qa_search(request)

                    # Assert
                    assert response.question == "EC2とは何ですか？"
                    assert response.source_count == 1
                    assert response.sources is not None

    @pytest.mark.asyncio
    async def test_qa_search_without_sources(self):
        """RAG-025: QA検索（ソースなし）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        mock_documents = [Document(page_content="Test", metadata={})]
        mock_model = MagicMock()

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(return_value=mock_documents)
        search.rag_client.get_chat_model = AsyncMock(return_value=mock_model)

        with patch("app.rag.enhanced_rag_search.PromptTemplate") as mock_prompt:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = "Answer"
            mock_prompt.from_template.return_value.__or__ = MagicMock(return_value=mock_chain)

            request = RAGQARequest(
                question="Test?",
                include_sources=False
            )

            # Act
            response = await search.qa_search(request)

            # Assert
            assert response.sources is None


class TestEnhancedRAGSearchHealth:
    """EnhancedRAGSearchヘルスチェックテスト"""

    @pytest.mark.asyncio
    async def test_get_health_healthy(self):
        """RAG-026: システムヘルスチェック（healthy）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search.rag_client = MagicMock()
        search.rag_client.check_health = AsyncMock(return_value={
            "opensearch_connected": True,
            "embedding_available": True,
            "index_exists": True
        })
        search.rag_client.get_index_info = AsyncMock(return_value={
            "document_count": 1000
        })

        # Act
        response = await search.get_health()

        # Assert
        assert response.status == "healthy"
        assert response.opensearch_connected is True
        assert response.total_documents == 1000

    @pytest.mark.asyncio
    async def test_get_health_degraded(self):
        """RAG-027: システムヘルスチェック（degraded）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search.rag_client = MagicMock()
        search.rag_client.check_health = AsyncMock(return_value={
            "opensearch_connected": True,
            "embedding_available": False,
            "index_exists": False
        })
        search.rag_client.get_index_info = AsyncMock(side_effect=Exception("Index not found"))

        # Act
        response = await search.get_health()

        # Assert
        assert response.status == "degraded"

    @pytest.mark.asyncio
    async def test_get_index_info_success(self):
        """RAG-028: インデックス情報取得（EnhancedRAGSearch）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.get_index_info = AsyncMock(return_value={
            "index_name": "test-index",
            "document_count": 500,
            "index_size": 1024000,
            "mapping_info": {}
        })

        # Act
        response = await search.get_index_info()

        # Assert
        assert response.index_name == "test-index"
        assert response.document_count == 500
        assert "MB" in response.index_size
```

### 2.3 RAGManager テスト

```python
# test/unit/rag/test_rag_manager.py
"""RAGManagerのテスト"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestRAGManagerSingleton:
    """RAGManagerシングルトンテスト"""

    @pytest.mark.asyncio
    async def test_get_instance_creates_new(self):
        """RAG-029: RAGManager.get_instance成功"""
        # Arrange
        from app.core.rag_manager import RAGManager
        RAGManager._instance = None  # リセット

        # Act
        instance = await RAGManager.get_instance()

        # Assert
        assert instance is not None
        assert isinstance(instance, RAGManager)

    @pytest.mark.asyncio
    async def test_get_instance_returns_same(self):
        """RAG-030: RAGManager.get_instance（既存）"""
        # Arrange
        from app.core.rag_manager import RAGManager
        RAGManager._instance = None  # リセット

        # Act
        instance1 = await RAGManager.get_instance()
        instance2 = await RAGManager.get_instance()

        # Assert
        assert instance1 is instance2


class TestRAGManagerInitialization:
    """RAGManager初期化テスト"""

    @pytest.mark.asyncio
    async def test_initialize_success(self):
        """RAG-031: RAGManager.initialize成功"""
        # Arrange
        from app.core.rag_manager import RAGManager

        with patch("app.core.rag_manager.EnhancedRAGSearch") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.initialize = AsyncMock(return_value=True)
            mock_rag_cls.return_value = mock_rag

            manager = RAGManager()

            # Act
            result = await manager.initialize()

            # Assert
            assert result is True
            assert manager._initialized is True

    def test_is_initialized(self):
        """RAG-032: RAGManager初期化済み確認"""
        # Arrange
        from app.core.rag_manager import RAGManager
        manager = RAGManager()
        manager._initialized = True

        # Act
        result = manager.is_initialized()

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """RAG-033: RAGManager.health_check成功"""
        # Arrange
        from app.core.rag_manager import RAGManager

        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = MagicMock()
        manager.enhanced_rag_search.get_health = AsyncMock(return_value=MagicMock(status="healthy"))

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "healthy"
        assert result["initialized"] is True


class TestGlobalRAGManager:
    """グローバルRAGマネージャーテスト"""

    @pytest.mark.asyncio
    async def test_get_global_rag_manager(self):
        """RAG-034: グローバルRAGマネージャー取得"""
        # Arrange
        import app.core.rag_manager as rag_module
        rag_module._global_rag_manager = None

        with patch.object(rag_module.RAGManager, "get_instance", new_callable=AsyncMock) as mock_get:
            mock_manager = MagicMock()
            mock_get.return_value = mock_manager

            # Act
            result = await rag_module.get_global_rag_manager()

            # Assert
            assert result is mock_manager

    @pytest.mark.asyncio
    async def test_initialize_global_rag_system(self):
        """RAG-035: グローバルRAGシステム初期化"""
        # Arrange
        import app.core.rag_manager as rag_module

        with patch.object(rag_module, "get_global_rag_manager", new_callable=AsyncMock) as mock_get:
            mock_manager = MagicMock()
            mock_manager.initialize = AsyncMock(return_value=True)
            mock_get.return_value = mock_manager

            # Act
            result = await rag_module.initialize_global_rag_system()

            # Assert
            assert result is True
```

### 2.4 ルーター テスト

```python
# test/unit/rag/test_router.py
"""RAGルーターのテスト

注意: appとclientフィクスチャはconftest.pyで定義済み。
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.rag.models import (
    RAGSearchResponse, RAGQAResponse, RAGHealthResponse,
    RAGIndexInfoResponse, DocumentResult
)


class TestRAGRouterSearch:
    """RAGルーター検索エンドポイントテスト"""

    @pytest.mark.asyncio
    async def test_search_documents_success(self, client):
        """RAG-036: 検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(
            query="test",
            results=[],
            total_results=0,
            execution_time_ms=10.5
        )

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.post(
                "/rag/search",
                json={"query": "test query", "k": 5}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "test"

    @pytest.mark.asyncio
    async def test_search_filters_endpoint(self, client):
        """RAG-037: フィルター検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(
            query="test",
            results=[],
            total_results=0
        )

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search_filters_only = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/search/filters?query=test&cloud=aws&k=5")

            # Assert
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_actions_endpoint(self, client):
        """RAG-038: アクション検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(query="test", results=[], total_results=0)

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search_actions_only = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/search/actions?query=test")

            # Assert
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_search_code_examples_endpoint(self, client):
        """RAG-039: コード例検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(query="test", results=[], total_results=0)

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search_with_code_examples = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/search/code-examples?query=test")

            # Assert
            assert response.status_code == 200


class TestRAGRouterQA:
    """RAGルーターQAエンドポイントテスト"""

    @pytest.mark.asyncio
    async def test_qa_search_endpoint(self, client):
        """RAG-040: QAエンドポイント成功"""
        # Arrange
        mock_response = RAGQAResponse(
            question="What is EC2?",
            answer="EC2 is AWS virtual server.",
            source_count=3,
            execution_time_ms=150.0
        )

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.qa_search = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.post(
                "/rag/qa",
                json={"question": "What is EC2?", "context_limit": 3}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data


class TestRAGRouterHealth:
    """RAGルーターヘルスエンドポイントテスト"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """RAG-041: ヘルスエンドポイント成功"""
        # Arrange
        mock_response = RAGHealthResponse(
            status="healthy",
            opensearch_connected=True,
            embedding_available=True,
            index_exists=True,
            last_check_time="2026-02-03 12:00:00"
        )

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.get_health = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/health")

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_index_info_endpoint(self, client):
        """RAG-042: インデックス情報エンドポイント成功"""
        # Arrange
        mock_response = RAGIndexInfoResponse(
            index_name="test-index",
            document_count=1000,
            index_size="10.5 MB",
            mapping_info={}
        )

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.get_index_info = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/index/info")

            # Assert
            assert response.status_code == 200


class TestRAGRouterHelpers:
    """RAGルーターヘルパーエンドポイントテスト"""

    @pytest.mark.asyncio
    async def test_aws_ec2_search_endpoint(self, client):
        """RAG-043: AWS EC2検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(query="EC2", results=[], total_results=0)

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/search/aws/ec2")

            # Assert
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_aws_s3_search_endpoint(self, client):
        """RAG-044: AWS S3検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(query="S3", results=[], total_results=0)

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/search/aws/s3")

            # Assert
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_security_search_endpoint(self, client):
        """RAG-045: セキュリティ検索エンドポイント成功"""
        # Arrange
        mock_response = RAGSearchResponse(query="セキュリティ", results=[], total_results=0)

        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/search/security")

            # Assert
            assert response.status_code == 200
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|----------|
| RAG-E01 | RAGClient初期化失敗（OpenSearchなし） | OpenSearchクライアントなし | False |
| RAG-E02 | RAGClient初期化失敗（Embeddingなし） | Embedding機能なし | False |
| RAG-E03 | RAGClient初期化失敗（例外発生） | 初期化中に例外 | False |
| RAG-E04 | VectorStore初期化例外 | OpenSearch接続失敗 | 例外伝播 |
| RAG-E05 | ChatModel初期化例外 | LLM初期化失敗 | 例外伝播 |
| RAG-E06 | AWS認証設定失敗（IAMなし+Basicなし） | 認証情報なし | Exception |
| RAG-E07 | 自前OpenSearch認証設定失敗 | user/passwordなし | Exception |
| RAG-E08 | ドキュメント検索失敗（未初期化） | _initialized=False | RuntimeError |
| RAG-E09 | ドキュメント検索例外 | VectorStore例外 | 例外伝播 |
| RAG-E10 | スコア付き検索失敗（未初期化） | _initialized=False | RuntimeError |
| RAG-E11 | ChatModel取得失敗（未初期化） | chat_model=None | RuntimeError |
| RAG-E12 | ヘルスチェック例外処理 | OpenSearch接続失敗 | error含むdict |
| RAG-E13 | インデックス情報取得失敗（未初期化） | opensearch_client=None | RuntimeError |
| RAG-E14 | インデックス情報取得例外 | インデックスなし | 例外伝播 |
| RAG-E15 | EnhancedRAGSearch初期化失敗 | RAGClient初期化失敗 | False |
| RAG-E16 | 検索失敗（未初期化） | _initialized=False | RuntimeError |
| RAG-E17 | 検索例外 | RAGClient例外 | 例外伝播 |
| RAG-E18 | QA検索失敗（未初期化） | _initialized=False | RuntimeError |
| RAG-E19 | QA検索例外 | LLM呼び出し失敗 | 例外伝播 |
| RAG-E20 | ヘルスチェック例外処理 | RAGClient例外 | status="unhealthy" |
| RAG-E21 | インデックス情報取得失敗（未初期化） | _initialized=False | RuntimeError |
| RAG-E22 | RAGManager初期化失敗 | EnhancedRAGSearch失敗 | False |
| RAG-E23 | RAGManager初期化例外 | 予期しない例外 | False |
| RAG-E24 | RAGManager.get_enhanced_rag_search失敗 | 初期化失敗 | RuntimeError |
| RAG-E25 | RAGManager.health_check（未初期化） | _initialized=False | status="uninitialized" |
| RAG-E26 | RAGManager.health_check例外 | 例外発生 | status="error" |
| RAG-E27 | グローバルRAGシステム初期化失敗 | 初期化例外 | False |
| RAG-E28 | 検索エンドポイント503 | RAGシステム利用不可 | 503 |
| RAG-E29 | 検索エンドポイント500 | 検索例外 | 500 |
| RAG-E30 | QAエンドポイント500 | QA検索例外 | 500 |
| RAG-E31 | インデックス情報エンドポイント500 | 情報取得例外 | 500 |

### 3.1 RAGClient 異常系テスト

```python
# test/unit/rag/test_rag_client.py（続き）
from botocore.exceptions import NoCredentialsError


class TestRAGClientErrors:
    """RAGClientエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_initialize_no_opensearch(self):
        """RAG-E01: RAGClient初期化失敗（OpenSearchなし）"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.get_opensearch_client", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            client = RAGClient()

            # Act
            result = await client.initialize()

            # Assert
            assert result is False
            assert client._initialized is False

    @pytest.mark.asyncio
    async def test_initialize_no_embedding(self, mock_opensearch_client):
        """RAG-E02: RAGClient初期化失敗（Embeddingなし）"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.get_opensearch_client", new_callable=AsyncMock) as mock_get_os:
            mock_get_os.return_value = mock_opensearch_client
            with patch("app.rag.rag_client.get_embedding_function") as mock_get_emb:
                mock_get_emb.return_value = None
                client = RAGClient()

                # Act
                result = await client.initialize()

                # Assert
                assert result is False

    @pytest.mark.asyncio
    async def test_initialize_exception(self):
        """RAG-E03: RAGClient初期化失敗（例外発生）"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.get_opensearch_client", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            client = RAGClient()

            # Act
            result = await client.initialize()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_vectorstore_exception(self):
        """RAG-E04: VectorStore初期化例外"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.OpenSearchVectorSearch") as mock_vs:
            mock_vs.side_effect = Exception("VectorStore init failed")
            client = RAGClient()
            client.embedding_function = MagicMock()

            with patch.object(client, "_get_opensearch_auth_config") as mock_auth:
                mock_auth.return_value = (("user", "pass"), {"use_ssl": True, "verify_certs": True, "ssl_assert_hostname": True, "ca_certs": None})

                # Act & Assert
                with pytest.raises(Exception, match="VectorStore init failed"):
                    await client._initialize_vectorstore()

    def test_initialize_chat_model_exception(self):
        """RAG-E05: ChatModel初期化例外"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.get_chat_llm") as mock_get_llm:
            mock_get_llm.side_effect = Exception("LLM init failed")
            client = RAGClient()

            # Act & Assert
            with pytest.raises(Exception, match="LLM init failed"):
                client._initialize_chat_model()

    def test_aws_auth_no_credentials(self):
        """RAG-E06: AWS認証設定失敗（IAMなし+Basicなし）"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = True
            with patch("app.rag.rag_client.boto3.Session") as mock_session_cls:
                mock_session_cls.side_effect = Exception("No IAM")
                with patch("app.rag.rag_client.settings") as mock_settings:
                    mock_settings.OPENSEARCH_URL = "https://search.es.amazonaws.com"
                    mock_settings.OPENSEARCH_USER = None
                    mock_settings.OPENSEARCH_PASSWORD = None

                    client = RAGClient()

                    # Act & Assert
                    with pytest.raises(Exception, match="IAM認証失敗"):
                        client._get_opensearch_auth_config()

    def test_local_opensearch_no_credentials(self):
        """RAG-E07: 自前OpenSearch認証設定失敗"""
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = False
            with patch("app.rag.rag_client.settings") as mock_settings:
                mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                mock_settings.OPENSEARCH_USER = None
                mock_settings.OPENSEARCH_PASSWORD = None

                client = RAGClient()

                # Act & Assert
                with pytest.raises(Exception, match="OPENSEARCH_USERとOPENSEARCH_PASSWORDが必要"):
                    client._get_opensearch_auth_config()

    @pytest.mark.asyncio
    async def test_search_not_initialized(self):
        """RAG-E08: ドキュメント検索失敗（未初期化）"""
        # Arrange
        from app.rag.rag_client import RAGClient
        client = RAGClient()
        client._initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await client.search_documents("test")

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """RAG-E09: ドキュメント検索例外"""
        # Arrange
        from app.rag.rag_client import RAGClient

        client = RAGClient()
        client._initialized = True
        client.vectorstore = MagicMock()
        client.vectorstore.similarity_search.side_effect = Exception("Search failed")

        # Act & Assert
        with pytest.raises(Exception, match="Search failed"):
            await client.search_documents("test")

    @pytest.mark.asyncio
    async def test_search_with_scores_not_initialized(self):
        """RAG-E10: スコア付き検索失敗（未初期化）"""
        # Arrange
        from app.rag.rag_client import RAGClient
        client = RAGClient()
        client._initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await client.search_with_scores("test")

    @pytest.mark.asyncio
    async def test_get_chat_model_not_initialized(self):
        """RAG-E11: ChatModel取得失敗（未初期化）"""
        # Arrange
        from app.rag.rag_client import RAGClient
        client = RAGClient()
        client._initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await client.get_chat_model()

    @pytest.mark.asyncio
    async def test_check_health_exception(self):
        """RAG-E12: ヘルスチェック例外処理"""
        # Arrange
        from app.rag.rag_client import RAGClient

        client = RAGClient()
        client._initialized = True
        client.opensearch_client = AsyncMock()
        client.opensearch_client.ping.side_effect = Exception("Connection failed")

        # Act
        health = await client.check_health()

        # Assert
        assert "error" in health

    @pytest.mark.asyncio
    async def test_get_index_info_not_initialized(self):
        """RAG-E13: インデックス情報取得失敗（未初期化）"""
        # Arrange
        from app.rag.rag_client import RAGClient
        client = RAGClient()
        client.opensearch_client = None

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await client.get_index_info()

    @pytest.mark.asyncio
    async def test_get_index_info_exception(self):
        """RAG-E14: インデックス情報取得例外"""
        # Arrange
        from app.rag.rag_client import RAGClient

        client = RAGClient()
        client.opensearch_client = AsyncMock()
        client.index_name = "test-index"
        client.opensearch_client.indices.stats.side_effect = Exception("Index not found")

        # Act & Assert
        with pytest.raises(Exception, match="Index not found"):
            await client.get_index_info()
```

### 3.2 EnhancedRAGSearch 異常系テスト

```python
# test/unit/rag/test_enhanced_rag_search.py（続き）

class TestEnhancedRAGSearchErrors:
    """EnhancedRAGSearchエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """RAG-E15: EnhancedRAGSearch初期化失敗"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search.rag_client = MagicMock()
        search.rag_client.initialize = AsyncMock(return_value=False)

        # Act
        result = await search.initialize()

        # Assert
        assert result is False
        assert search._initialized is False

    @pytest.mark.asyncio
    async def test_search_not_initialized(self):
        """RAG-E16: 検索失敗（未初期化）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch
        from app.rag.models import RAGSearchRequest

        search = EnhancedRAGSearch()
        search._initialized = False
        request = RAGSearchRequest(query="test")

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await search.search(request)

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """RAG-E17: 検索例外"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch
        from app.rag.models import RAGSearchRequest

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(side_effect=Exception("Search error"))

        request = RAGSearchRequest(query="test")

        # Act & Assert
        with pytest.raises(Exception, match="Search error"):
            await search.search(request)

    @pytest.mark.asyncio
    async def test_qa_search_not_initialized(self):
        """RAG-E18: QA検索失敗（未初期化）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch
        from app.rag.models import RAGQARequest

        search = EnhancedRAGSearch()
        search._initialized = False
        request = RAGQARequest(question="test?")

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await search.qa_search(request)

    @pytest.mark.asyncio
    async def test_qa_search_exception(self):
        """RAG-E19: QA検索例外"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch
        from app.rag.models import RAGQARequest

        search = EnhancedRAGSearch()
        search._initialized = True
        search.rag_client = MagicMock()
        search.rag_client.search_documents = AsyncMock(side_effect=Exception("QA error"))

        request = RAGQARequest(question="test?")

        # Act & Assert
        with pytest.raises(Exception, match="QA error"):
            await search.qa_search(request)

    @pytest.mark.asyncio
    async def test_get_health_exception(self):
        """RAG-E20: ヘルスチェック例外処理"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search.rag_client = MagicMock()
        search.rag_client.check_health = AsyncMock(side_effect=Exception("Health check failed"))

        # Act
        response = await search.get_health()

        # Assert
        assert response.status == "unhealthy"
        assert "error" in response.details

    @pytest.mark.asyncio
    async def test_get_index_info_not_initialized(self):
        """RAG-E21: インデックス情報取得失敗（未初期化）"""
        # Arrange
        from app.rag.enhanced_rag_search import EnhancedRAGSearch

        search = EnhancedRAGSearch()
        search._initialized = False

        # Act & Assert
        with pytest.raises(RuntimeError, match="初期化されていません"):
            await search.get_index_info()
```

### 3.3 RAGManager 異常系テスト

```python
# test/unit/rag/test_rag_manager.py（続き）

class TestRAGManagerErrors:
    """RAGManagerエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_initialize_failure(self):
        """RAG-E22: RAGManager初期化失敗"""
        # Arrange
        from app.core.rag_manager import RAGManager

        with patch("app.core.rag_manager.EnhancedRAGSearch") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.initialize = AsyncMock(return_value=False)
            mock_rag_cls.return_value = mock_rag

            manager = RAGManager()

            # Act
            result = await manager.initialize()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_initialize_exception(self):
        """RAG-E23: RAGManager初期化例外"""
        # Arrange
        from app.core.rag_manager import RAGManager

        with patch("app.core.rag_manager.EnhancedRAGSearch") as mock_rag_cls:
            mock_rag_cls.side_effect = Exception("Unexpected error")

            manager = RAGManager()

            # Act
            result = await manager.initialize()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_get_enhanced_rag_search_failure(self):
        """RAG-E24: RAGManager.get_enhanced_rag_search失敗"""
        # Arrange
        from app.core.rag_manager import RAGManager

        manager = RAGManager()
        manager._initialized = False

        with patch.object(manager, "initialize", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = False

            # Act & Assert
            with pytest.raises(RuntimeError, match="初期化されていません"):
                await manager.get_enhanced_rag_search()

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self):
        """RAG-E25: RAGManager.health_check（未初期化）"""
        # Arrange
        from app.core.rag_manager import RAGManager

        manager = RAGManager()
        manager._initialized = False

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "uninitialized"

    @pytest.mark.asyncio
    async def test_health_check_exception(self):
        """RAG-E26: RAGManager.health_check例外"""
        # Arrange
        from app.core.rag_manager import RAGManager

        manager = RAGManager()
        manager._initialized = True
        manager.enhanced_rag_search = MagicMock()
        manager.enhanced_rag_search.get_health = AsyncMock(side_effect=Exception("Error"))

        # Act
        result = await manager.health_check()

        # Assert
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_initialize_global_rag_system_failure(self):
        """RAG-E27: グローバルRAGシステム初期化失敗"""
        # Arrange
        import app.core.rag_manager as rag_module

        with patch.object(rag_module, "get_global_rag_manager", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Init failed")

            # Act
            result = await rag_module.initialize_global_rag_system()

            # Assert
            assert result is False
```

### 3.4 ルーター 異常系テスト

```python
# test/unit/rag/test_router.py（続き）

class TestRAGRouterErrors:
    """RAGルーターエラーハンドリングテスト"""

    @pytest.mark.asyncio
    async def test_search_503_unavailable(self, client):
        """RAG-E28: 検索エンドポイント503"""
        # Arrange
        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("RAG system unavailable")

            # Act
            response = client.post(
                "/rag/search",
                json={"query": "test"}
            )

            # Assert
            assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_search_500_error(self, client):
        """RAG-E29: 検索エンドポイント500"""
        # Arrange
        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.search = AsyncMock(side_effect=Exception("Search failed"))
            mock_get.return_value = mock_rag

            # Act
            response = client.post(
                "/rag/search",
                json={"query": "test"}
            )

            # Assert
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_qa_500_error(self, client):
        """RAG-E30: QAエンドポイント500"""
        # Arrange
        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.qa_search = AsyncMock(side_effect=Exception("QA failed"))
            mock_get.return_value = mock_rag

            # Act
            response = client.post(
                "/rag/qa",
                json={"question": "test?"}
            )

            # Assert
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_index_info_500_error(self, client):
        """RAG-E31: インデックス情報エンドポイント500"""
        # Arrange
        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_rag = MagicMock()
            mock_rag.get_index_info = AsyncMock(side_effect=Exception("Index info failed"))
            mock_get.return_value = mock_rag

            # Act
            response = client.get("/rag/index/info")

            # Assert
            assert response.status_code == 500
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|----------|
| RAG-SEC-01 | AWS認証情報のログ出力防止 | IAM認証実行 | SecretAccessKeyがログに出力されない |
| RAG-SEC-02 | OpenSearch認証情報のログ出力防止 | Basic認証設定 | パスワードがログに出力されない |
| RAG-SEC-03 | クエリインジェクション防止 | 悪意あるクエリ文字列 | エスケープ処理またはエラー |
| RAG-SEC-04 | 検索クエリ長制限 | 1000文字超のクエリ | バリデーションエラー |
| RAG-SEC-05 | フィルター値検証 | 不正なcloud値 | バリデーションエラー |
| RAG-SEC-06 | SSL/TLS強制 | OpenSearch接続 | use_ssl=True, verify_certs=True |
| RAG-SEC-07 | エラーメッセージの情報漏洩防止 | 認証エラー | 詳細な認証情報を含まない |
| RAG-SEC-08 | 認証バイパス防止（空認証情報） | 空のuser/password | 認証エラー |
| RAG-SEC-09 | OpenSearchクエリDSLインジェクション防止 | 悪意あるDSL構文 | 安全に処理 |
| RAG-SEC-10 | メタデータフィルターインジェクション防止 | 悪意あるフィルター値 | バリデーションエラー |

### OWASP Top 10 カバレッジ

| OWASP Category | テストID | カバー内容 |
|----------------|----------|-----------|
| A01:2021 – Broken Access Control | RAG-SEC-08 | 認証バイパス防止 |
| A02:2021 – Cryptographic Failures | RAG-SEC-06 | SSL/TLS強制 |
| A03:2021 – Injection | RAG-SEC-03 | クエリインジェクション防止 |
| A04:2021 – Insecure Design | RAG-SEC-04, RAG-SEC-05 | 入力値バリデーション |
| A05:2021 – Security Misconfiguration | RAG-SEC-06 | SSL設定確認 |
| A07:2021 – Auth Failures | RAG-SEC-01, RAG-SEC-02 | 認証情報漏洩防止 |
| A09:2021 – Security Logging | RAG-SEC-01, RAG-SEC-02, RAG-SEC-07 | 認証情報のログ出力防止 |

```python
# test/unit/rag/test_security.py
"""RAGセキュリティテスト"""
import pytest
import logging
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.security
class TestRAGSecurity:
    """RAGセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_aws_credentials_not_logged(self, caplog):
        """RAG-SEC-01: AWS認証情報のログ出力防止

        IAM認証時にSecretAccessKeyがログに出力されないことを確認。
        """
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = True
            with patch("app.rag.rag_client.boto3.Session") as mock_session_cls:
                mock_session = MagicMock()
                mock_credentials = MagicMock()
                mock_credentials.access_key = "AKIAIOSFODNN7EXAMPLE"
                mock_credentials.secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
                mock_credentials.token = "session-token-secret"
                mock_session.get_credentials.return_value = mock_credentials
                mock_session_cls.return_value = mock_session

                with patch("app.rag.rag_client.AWS4Auth"):
                    with patch("app.rag.rag_client.settings") as mock_settings:
                        mock_settings.OPENSEARCH_URL = "https://search.es.amazonaws.com"

                        client = RAGClient()

                        with caplog.at_level(logging.DEBUG):
                            # Act
                            try:
                                client._get_opensearch_auth_config()
                            except Exception:
                                pass

                            # Assert
                            log_output = caplog.text
                            assert "wJalrXUtnFEMI" not in log_output
                            assert "session-token-secret" not in log_output

    def test_opensearch_password_not_logged(self, caplog):
        """RAG-SEC-02: OpenSearch認証情報のログ出力防止

        Basic認証時にパスワードがログに出力されないことを確認。
        """
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = False
            with patch("app.rag.rag_client.settings") as mock_settings:
                mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                mock_settings.OPENSEARCH_USER = "admin"
                mock_settings.OPENSEARCH_PASSWORD = "super-secret-password-123"
                mock_settings.OPENSEARCH_CA_CERTS_PATH = None

                with patch("app.rag.rag_client.certifi.where") as mock_certifi:
                    mock_certifi.return_value = "/ca.crt"
                    client = RAGClient()

                    with caplog.at_level(logging.DEBUG):
                        # Act
                        client._get_opensearch_auth_config()

                        # Assert
                        log_output = caplog.text
                        assert "super-secret-password-123" not in log_output

    @pytest.mark.asyncio
    async def test_query_injection_prevention(self):
        """RAG-SEC-03: クエリインジェクション防止

        悪意あるクエリ文字列が安全に処理されることを確認。
        OpenSearchVectorSearchは内部でクエリをサニタイズ。
        """
        # Arrange
        from app.rag.rag_client import RAGClient

        malicious_queries = [
            "'; DROP TABLE documents; --",
            '{"$ne": null}',
            "<script>alert('xss')</script>",
            "test\n\n{\"query\": {\"match_all\": {}}}",
        ]

        client = RAGClient()
        client._initialized = True
        client.vectorstore = MagicMock()
        client.vectorstore.similarity_search.return_value = []

        for query in malicious_queries:
            # Act
            results = await client.search_documents(query, k=5)

            # Assert
            # クエリが渡されてもエラーにならず、VectorStoreに委譲される
            assert isinstance(results, list)
            call_args = client.vectorstore.similarity_search.call_args
            assert call_args[0][0] == query  # クエリがそのまま渡される

    def test_query_length_validation(self):
        """RAG-SEC-04: 検索クエリ長制限

        1000文字を超えるクエリはバリデーションエラー。
        """
        # Arrange
        from app.rag.models import RAGSearchRequest
        from pydantic import ValidationError

        long_query = "a" * 1001  # 1001文字

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            RAGSearchRequest(query=long_query)

        assert "max_length" in str(exc_info.value) or "1000" in str(exc_info.value)

    def test_filter_value_validation(self):
        """RAG-SEC-05: フィルター値検証

        不正なcloud値はバリデーションエラー。
        """
        # Arrange
        from app.rag.models import SearchFilters
        from pydantic import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError):
            SearchFilters(cloud="invalid_cloud")

    def test_ssl_enforced(self):
        """RAG-SEC-06: SSL/TLS強制

        OpenSearch接続でSSL/TLSが強制されることを確認。
        """
        # Arrange
        from app.rag.rag_client import RAGClient

        # AWS OpenSearch
        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = True
            with patch("app.rag.rag_client.boto3.Session") as mock_session_cls:
                mock_session = MagicMock()
                mock_credentials = MagicMock()
                mock_credentials.access_key = "key"
                mock_credentials.secret_key = "secret"
                mock_credentials.token = None
                mock_session.get_credentials.return_value = mock_credentials
                mock_session_cls.return_value = mock_session

                with patch("app.rag.rag_client.AWS4Auth"):
                    with patch("app.rag.rag_client.settings") as mock_settings:
                        mock_settings.OPENSEARCH_URL = "https://search.es.amazonaws.com"

                        client = RAGClient()

                        # Act
                        _, ssl_config = client._get_opensearch_auth_config()

                        # Assert
                        assert ssl_config["use_ssl"] is True
                        assert ssl_config["verify_certs"] is True

        # ローカルOpenSearch
        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = False
            with patch("app.rag.rag_client.settings") as mock_settings:
                mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                mock_settings.OPENSEARCH_USER = "admin"
                mock_settings.OPENSEARCH_PASSWORD = "password"
                mock_settings.OPENSEARCH_CA_CERTS_PATH = "/ca.crt"

                client = RAGClient()

                # Act
                _, ssl_config = client._get_opensearch_auth_config()

                # Assert
                assert ssl_config["use_ssl"] is True
                assert ssl_config["verify_certs"] is True

    @pytest.mark.asyncio
    async def test_error_message_no_sensitive_info(self, client):
        """RAG-SEC-07: エラーメッセージの情報漏洩防止

        認証エラー時に詳細な認証情報を含まないことを確認。
        """
        # Arrange
        with patch("app.rag.router.get_rag_search", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection failed: auth error with password=secret")

            # Act
            response = client.post(
                "/rag/search",
                json={"query": "test"}
            )

            # Assert
            # 503エラーが返される
            assert response.status_code == 503
            data = response.json()
            # 詳細なエラーメッセージは含まれない（機密情報が漏洩しないこと）
            detail = data.get("detail", "").lower()
            assert "password" not in detail
            assert "secret" not in detail
            assert "token" not in detail
            assert "key" not in detail

    def test_empty_credentials_rejected(self):
        """RAG-SEC-08: 認証バイパス防止（空認証情報）

        空のuser/passwordでの認証試行が拒否されることを確認。
        """
        # Arrange
        from app.rag.rag_client import RAGClient

        with patch("app.rag.rag_client.is_aws_opensearch_service") as mock_is_aws:
            mock_is_aws.return_value = False
            with patch("app.rag.rag_client.settings") as mock_settings:
                mock_settings.OPENSEARCH_URL = "https://localhost:9200"
                mock_settings.OPENSEARCH_USER = ""  # 空文字列
                mock_settings.OPENSEARCH_PASSWORD = ""  # 空文字列

                client = RAGClient()

                # Act & Assert
                with pytest.raises(Exception, match="OPENSEARCH_USERとOPENSEARCH_PASSWORDが必要"):
                    client._get_opensearch_auth_config()

    @pytest.mark.asyncio
    async def test_opensearch_dsl_injection_prevention(self):
        """RAG-SEC-09: OpenSearchクエリDSLインジェクション防止

        OpenSearch DSL構文を含む悪意あるクエリが安全に処理されることを確認。
        """
        # Arrange
        from app.rag.rag_client import RAGClient

        dsl_injection_payloads = [
            '{"bool": {"must_not": {"match_all": {}}}}',
            'test\n\n{"query": {"match_all": {}}}',
            '{"script": {"source": "ctx._source.admin=true"}}',
        ]

        client = RAGClient()
        client._initialized = True
        client.vectorstore = MagicMock()
        client.vectorstore.similarity_search.return_value = []

        for payload in dsl_injection_payloads:
            # Act
            results = await client.search_documents(payload, k=5)

            # Assert
            # DSLインジェクション試行がエラーにならず、文字列として処理される
            assert isinstance(results, list)
            call_args = client.vectorstore.similarity_search.call_args
            assert call_args[0][0] == payload

    def test_filter_metadata_injection_prevention(self):
        """RAG-SEC-10: メタデータフィルターインジェクション防止

        フィルター値を通じたインジェクション試行がバリデーションエラーになることを確認。
        """
        # Arrange
        from app.rag.models import SearchFilters
        from pydantic import ValidationError

        malicious_filter_values = [
            '"; DROP TABLE; --',
            '{"admin": true}',
        ]

        for malicious_value in malicious_filter_values:
            # Act & Assert
            # cloud値はLiteral["aws", "azure", "gcp"]のためバリデーションエラー
            with pytest.raises(ValidationError):
                SearchFilters(cloud=malicious_value)
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_rag_module` | テスト間のモジュール状態リセット | function | Yes |
| `app` | テスト用FastAPIアプリケーション | function | No |
| `client` | テスト用HTTPクライアント | function | No |
| `mock_opensearch_client` | AsyncOpenSearchのモック | function | No |
| `mock_embedding_function` | OpenAIEmbeddingsのモック | function | No |
| `mock_vectorstore` | OpenSearchVectorSearchのモック | function | No |
| `mock_chat_model` | ChatOpenAI（AIMessage返却） | function | No |
| `sample_documents` | サンプルDocumentリスト（検索テスト用） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/rag/conftest.py
"""RAGテスト用共通フィクスチャ"""
import sys
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.documents import Document


@pytest.fixture(autouse=True)
def reset_rag_module():
    """テストごとにモジュールのグローバル状態をリセット

    RAGManager._instanceとグローバル_global_rag_managerを
    リセットしてテスト間の独立性を保証。
    """
    yield

    # グローバルRAGマネージャーをリセット
    import app.core.rag_manager as rag_module
    rag_module._global_rag_manager = None
    rag_module.RAGManager._instance = None

    # モジュールキャッシュをクリア（app.ragとapp.core.rag_managerのみ）
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.rag") or key == "app.core.rag_manager"
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def app():
    """テスト用FastAPIアプリケーション"""
    from app.rag.router import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """テスト用HTTPクライアント"""
    return TestClient(app)


@pytest.fixture
def mock_opensearch_client():
    """AsyncOpenSearchのモック"""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.indices.exists.return_value = True
    mock.indices.stats.return_value = {
        "indices": {
            "test-index": {
                "total": {
                    "docs": {"count": 100},
                    "store": {"size_in_bytes": 10240}
                }
            }
        }
    }
    mock.indices.get_mapping.return_value = {
        "test-index": {"mappings": {"properties": {}}}
    }
    return mock


@pytest.fixture
def mock_embedding_function():
    """OpenAIEmbeddingsのモック"""
    mock = MagicMock()
    mock.embed_query.return_value = [0.1] * 1536  # OpenAI embeddingの次元数
    mock.embed_documents.return_value = [[0.1] * 1536]
    return mock


@pytest.fixture
def mock_vectorstore():
    """OpenSearchVectorSearchのモック"""
    mock = MagicMock()
    mock.similarity_search.return_value = []
    mock.similarity_search_with_score.return_value = []
    return mock


@pytest.fixture
def mock_chat_model():
    """ChatOpenAIのモック"""
    from langchain_core.messages import AIMessage
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="Test response")
    return mock


@pytest.fixture
def sample_documents():
    """サンプルDocumentリスト"""
    return [
        Document(
            page_content="EC2インスタンスのフィルター機能について説明します。",
            metadata={
                "source": "aws/ec2.md",
                "cloud": "aws",
                "resource_name": "aws.ec2",
                "section_type": "filter",
                "has_code_example": True
            }
        ),
        Document(
            page_content="S3バケットのアクション機能について説明します。",
            metadata={
                "source": "aws/s3.md",
                "cloud": "aws",
                "resource_name": "aws.s3",
                "section_type": "action",
                "has_code_example": False
            }
        ),
        Document(
            page_content="Azure VMのセキュリティ設定について説明します。",
            metadata={
                "source": "azure/vm.md",
                "cloud": "azure",
                "resource_name": "azure.vm",
                "section_type": "filter",
                "has_permissions": True
            }
        )
    ]
```

---

## 6. テスト実行例

```bash
# rag関連テストのみ実行
pytest test/unit/rag/ -v

# 特定のテストファイルのみ実行
pytest test/unit/rag/test_rag_client.py -v

# 特定のテストクラスのみ実行
pytest test/unit/rag/test_enhanced_rag_search.py::TestEnhancedRAGSearchSearch -v

# カバレッジ付きで実行
pytest test/unit/rag/ --cov=app.rag --cov=app.core.rag_manager --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/rag/ -m "security" -v

# 非同期テストのみ実行
pytest test/unit/rag/ -m "asyncio" -v

# エラーハンドリングテストのみ実行
pytest test/unit/rag/test_rag_client.py::TestRAGClientErrors -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 46 | RAG-001 〜 RAG-046 |
| 異常系 | 31 | RAG-E01 〜 RAG-E31 |
| セキュリティ | 10 | RAG-SEC-01 〜 RAG-SEC-10 |
| **合計** | **87** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestRAGClientInitialization` | RAG-001〜RAG-004 | 4 |
| `TestRAGClientAuthConfig` | RAG-005〜RAG-007 | 3 |
| `TestRAGClientSearch` | RAG-008〜RAG-011 | 4 |
| `TestRAGClientHealth` | RAG-012〜RAG-013 | 2 |
| `TestEnhancedRAGSearchInitialization` | RAG-014 | 1 |
| `TestEnhancedRAGSearchFilters` | RAG-015〜RAG-017, RAG-046 | 4 |
| `TestEnhancedRAGSearchDocumentConversion` | RAG-018〜RAG-019 | 2 |
| `TestEnhancedRAGSearchSearch` | RAG-020〜RAG-023 | 4 |
| `TestEnhancedRAGSearchQA` | RAG-024〜RAG-025 | 2 |
| `TestEnhancedRAGSearchHealth` | RAG-026〜RAG-028 | 3 |
| `TestRAGManagerSingleton` | RAG-029〜RAG-030 | 2 |
| `TestRAGManagerInitialization` | RAG-031〜RAG-033 | 3 |
| `TestGlobalRAGManager` | RAG-034〜RAG-035 | 2 |
| `TestRAGRouterSearch` | RAG-036〜RAG-039 | 4 |
| `TestRAGRouterQA` | RAG-040 | 1 |
| `TestRAGRouterHealth` | RAG-041〜RAG-042 | 2 |
| `TestRAGRouterHelpers` | RAG-043〜RAG-045 | 3 |
| `TestRAGClientErrors` | RAG-E01〜RAG-E14 | 14 |
| `TestEnhancedRAGSearchErrors` | RAG-E15〜RAG-E21 | 7 |
| `TestRAGManagerErrors` | RAG-E22〜RAG-E27 | 6 |
| `TestRAGRouterErrors` | RAG-E28〜RAG-E31 | 4 |
| `TestRAGSecurity` | RAG-SEC-01〜RAG-SEC-10 | 10 |

### 実装失敗が予想されるテスト

以下のテストは実装との整合性確認が必要です：

| テストID | リスク | 対策 |
|----------|--------|------|
| RAG-024 | LangChainのチェーン構築のモックが複雑で失敗する可能性 | 実装を確認してモック構造を調整 |
| RAG-SEC-03 | OpenSearchVectorSearchのクエリサニタイズ動作を確認が必要 | 実装を確認 |
| RAG-SEC-07 | エラーメッセージに含まれる機密情報の範囲が広い | access_key, session_tokenなども検証対象 |
| RAG-SEC-08 | 空文字列の認証情報チェック実装依存 | 実装を確認 |

### 注意事項

- テスト実行には `pytest-asyncio` パッケージが必要です:
  ```bash
  uv add --dev pytest-asyncio
  ```
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録してください：
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "security: セキュリティ関連テスト",
  ]
  ```
- 外部サービス（OpenSearch、OpenAI）への接続は全てモック化
- RAGManager はシングルトンのため、テスト間で状態をリセットする必要あり

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実際のOpenSearch/OpenAI接続をテストしない | 実環境での動作は別途統合テストが必要 | モックでカバー、統合テストは別途実施 |
| 2 | LangChainのバージョン依存 | チェーン構築APIが変更される可能性 | LangChain 1.x API に準拠 |
| 3 | ベクトル検索の精度テスト不可 | 検索品質は統合テストで確認 | 機能テストのみカバー |
| 4 | AWS IAM認証のリージョン推定ロジック | URLパターンが変更されると失敗 | 正規表現パターンの更新が必要 |
| 5 | シングルトンのテスト隔離 | 並列テスト実行時に競合の可能性 | autouse fixtureでリセット |
| 6 | ルーター依存関数の完全なテスト不足 | `get_rag_search()`のロジックが未検証 | 統合テストでカバー |
