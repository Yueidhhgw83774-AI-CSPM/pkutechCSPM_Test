# TestReport/plugins/rag/rag_plugin/source/conftest.py
"""
RAG Plugin テストの共通フィクスチャとモック

Jobs Router / Custodian Scan の成功パターンを適用
"""

import pytest
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

# プロジェクトルート設定（env_loader を使用）
try:
    from env_loader import PROJECT_ROOT
except ImportError:
    _here = Path(__file__).resolve()
    for _p in [_here, *_here.parents]:
        if (_p / "env_loader.py").exists():
            sys.path.insert(0, str(_p))
            from env_loader import PROJECT_ROOT
            break
    else:
        raise ImportError("env_loader.py が見つかりません")

project_root = PROJECT_ROOT / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))


# ============================================================================
# JWT認証モック
# ============================================================================

@pytest.fixture
def mock_jwt_auth():
    """JWT認証をバイパスするモック"""
    with patch('app.core.auth.get_current_active_user') as mock_auth:
        from app.models.auth import User
        mock_user = User(username="test_user", email="test@example.com", full_name="Test User", disabled=False)
        mock_auth.return_value = mock_user
        yield mock_auth


# ============================================================================
# OpenSearch / Embedding モック
# ============================================================================

@pytest.fixture
def mock_opensearch_client():
    """OpenSearchクライアントのモック"""
    client = AsyncMock()
    client.index = AsyncMock(return_value={"result": "created", "_id": "test-id"})
    client.search = AsyncMock(return_value={
        "hits": {
            "total": {"value": 3},
            "hits": [
                {
                    "_id": "doc1",
                    "_score": 0.95,
                    "_source": {
                        "content": "Test document 1",
                        "cloud": "aws",
                        "section_type": "filter"
                    }
                },
                {
                    "_id": "doc2",
                    "_score": 0.85,
                    "_source": {
                        "content": "Test document 2",
                        "cloud": "aws",
                        "section_type": "action"
                    }
                }
            ]
        }
    })
    client.count = AsyncMock(return_value={"count": 1000})
    client.indices = AsyncMock()
    client.indices.stats = AsyncMock(return_value={
        "indices": {
            "custodian-docs": {
                "total": {
                    "store": {"size_in_bytes": 1024000}
                }
            }
        }
    })
    return client


@pytest.fixture
def mock_embedding_function():
    """Embedding関数のモック"""
    mock_emb = MagicMock()
    mock_emb.embed_query = MagicMock(return_value=[0.1, 0.2, 0.3] * 512)  # 1536次元
    mock_emb.embed_documents = MagicMock(return_value=[[0.1, 0.2, 0.3] * 512])
    return mock_emb


@pytest.fixture
def mock_vectorstore():
    """VectorStoreのモック"""
    from langchain_core.documents import Document
    
    mock_vs = MagicMock()
    
    # similarity_searchのモック（同期関数）
    mock_vs.similarity_search = MagicMock(return_value=[
        Document(
            page_content="Test document 1",
            metadata={"cloud": "aws", "section_type": "filter", "source": "test1.md"}
        ),
        Document(
            page_content="Test document 2",
            metadata={"cloud": "aws", "section_type": "action", "source": "test2.md"}
        )
    ])
    
    # similarity_search_with_scoreのモック（同期関数）
    mock_vs.similarity_search_with_score = MagicMock(return_value=[
        (Document(
            page_content="Test document 1",
            metadata={"cloud": "aws", "section_type": "filter"}
        ), 0.95),
        (Document(
            page_content="Test document 2",
            metadata={"cloud": "aws", "section_type": "action"}
        ), 0.85)
    ])
    
    return mock_vs


@pytest.fixture
def mock_chat_model():
    """ChatModelのモック"""
    from langchain_core.messages import AIMessage
    
    mock_chat = MagicMock()
    mock_chat.invoke = MagicMock(return_value=AIMessage(content="This is a test answer from LLM."))
    mock_chat.ainvoke = AsyncMock(return_value=AIMessage(content="This is a test answer from LLM."))
    return mock_chat


# ============================================================================
# RAGClient モック
# ============================================================================

@pytest.fixture
def mock_rag_client(mock_opensearch_client, mock_embedding_function, mock_vectorstore, mock_chat_model):
    """RAGClientのモック"""
    with patch('app.rag.rag_client.get_opensearch_client', new_callable=AsyncMock) as mock_get_os, \
         patch('app.rag.rag_client.get_embedding_function') as mock_get_emb:
        
        mock_get_os.return_value = mock_opensearch_client
        mock_get_emb.return_value = mock_embedding_function
        
        from app.rag.rag_client import RAGClient
        
        client = RAGClient()
        client._initialized = True
        client.opensearch_client = mock_opensearch_client
        client.embedding_function = mock_embedding_function
        client.vectorstore = mock_vectorstore
        client.chat_model = mock_chat_model
        
        yield client


@pytest.fixture
def mock_enhanced_rag_search(mock_rag_client):
    """EnhancedRAGSearchのモック"""
    from app.rag.enhanced_rag_search import EnhancedRAGSearch
    from app.rag.models import RAGSearchResponse, RAGQAResponse, DocumentResult, SearchFilters
    
    mock_search = MagicMock(spec=EnhancedRAGSearch)
    mock_search._initialized = True
    mock_search.rag_client = mock_rag_client
    
    # searchメソッドのモック - 动态返回query
    async def mock_search(request):
        return RAGSearchResponse(
            query=request.query,  # 使用请求的query
            results=[
                DocumentResult(
                    content="Test document 1",
                    metadata={"cloud": "aws", "section_type": "filter"},
                    score=0.95
                )
            ],
            total_results=1,
            k=request.k
        )
    mock_search.search = AsyncMock(side_effect=mock_search)
    
    # search_filters_onlyメソッドのモック
    mock_search.search_filters_only = AsyncMock(return_value=RAGSearchResponse(
        query="test query",
        results=[
            DocumentResult(
                content="Filter document",
                metadata={"cloud": "aws", "section_type": "filter"},
                score=0.95
            )
        ],
        total_results=1,
        k=5,
        filters_applied=SearchFilters(cloud="aws", section_type="filter")
    ))
    
    # search_actions_onlyメソッドのモック
    mock_search.search_actions_only = AsyncMock(return_value=RAGSearchResponse(
        query="test query",
        results=[
            DocumentResult(
                content="Action document",
                metadata={"cloud": "aws", "section_type": "action"},
                score=0.95
            )
        ],
        total_results=1,
        k=5,
        filters_applied=SearchFilters(cloud="aws", section_type="action")
    ))
    
    # search_code_examplesメソッドのモック (旧名)
    mock_search.search_code_examples = AsyncMock(return_value=RAGSearchResponse(
        query="test query",
        results=[
            DocumentResult(
                content="Code example",
                metadata={"cloud": "aws", "has_code_example": True},
                score=0.95
            )
        ],
        total_results=1,
        k=5,
        filters_applied=SearchFilters(cloud="aws", has_code_example=True)
    ))
    
    # search_with_code_examplesメソッドのモック (新名)
    mock_search.search_with_code_examples = AsyncMock(return_value=RAGSearchResponse(
        query="test query",
        results=[
            DocumentResult(
                content="Code example",
                metadata={"cloud": "aws", "has_code_example": True},
                score=0.95
            )
        ],
        total_results=1,
        k=5,
        filters_applied=SearchFilters(cloud="aws", has_code_example=True)
    ))
    
    # qa_searchメソッドのモック
    mock_search.qa_search = AsyncMock(return_value=RAGQAResponse(
        question="test query",
        answer="This is a test answer.",
        source_count=1,
        sources=[
            DocumentResult(
                content="Source document",
                metadata={"cloud": "aws"},
                score=0.95
            )
        ]
    ))
    
    # get_healthメソッドのモック
    from app.rag.models import RAGHealthResponse
    from datetime import datetime
    mock_search.get_health = AsyncMock(return_value=RAGHealthResponse(
        status="healthy",
        opensearch_connected=True,
        embedding_available=True,
        index_exists=True,
        total_documents=1000,
        last_check_time=datetime.now().isoformat()
    ))
    
    # get_index_infoメソッドのモック
    from app.rag.models import RAGIndexInfoResponse
    mock_search.get_index_info = AsyncMock(return_value=RAGIndexInfoResponse(
        index_name="custodian-docs",
        document_count=1000,
        index_size="1.0 MB",
        mapping_info={"properties": {"content": {"type": "text"}}}
    ))
    
    yield mock_search


# ============================================================================
# Test App フィクスチャ（Jobs Router の成功パターンを適用）
# ============================================================================

@pytest.fixture
async def test_app(mock_jwt_auth, mock_enhanced_rag_search):
    """テスト用FastAPIアプリケーション"""
    from fastapi import FastAPI
    import sys
    
    app = FastAPI()
    
    # ルーターモジュールを強制リロード
    if 'app.rag.router' in sys.modules:
        del sys.modules['app.rag.router']
    
    with patch.dict('sys.modules', {'weasyprint': MagicMock()}):
        # get_enhanced_rag_searchをモック
        with patch('app.core.rag_manager.get_enhanced_rag_search', new_callable=AsyncMock) as mock_get_rag:
            mock_get_rag.return_value = mock_enhanced_rag_search
            
            # Import router
            from app.rag import router as rag_router_module
            
            # Get the router
            rag_router = rag_router_module.router
            
            # Mount router
            app.include_router(rag_router)
            
            yield app


@pytest.fixture
async def authenticated_client(test_app, mock_jwt_auth):
    """認証済みHTTPクライアント"""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
        headers={"Authorization": "Bearer test_token"}
    ) as client:
        yield client


# ============================================================================
# テストデータフィクスチャ
# ============================================================================

@pytest.fixture
def sample_documents():
    """サンプルドキュメント"""
    from langchain_core.documents import Document
    return [
        Document(
            page_content="EC2 instance must have tags",
            metadata={
                "cloud": "aws",
                "service": "ec2",
                "section_type": "filter",
                "source": "aws-ec2.md",
                "has_code_example": True
            }
        ),
        Document(
            page_content="Stop untagged EC2 instances",
            metadata={
                "cloud": "aws",
                "service": "ec2",
                "section_type": "action",
                "source": "aws-ec2-actions.md",
                "has_code_example": False
            }
        ),
        Document(
            page_content="S3 bucket encryption filter",
            metadata={
                "cloud": "aws",
                "service": "s3",
                "section_type": "filter",
                "source": "aws-s3.md",
                "has_code_example": True
            }
        )
    ]


@pytest.fixture
def sample_search_request():
    """サンプル検索リクエスト"""
    from app.rag.models import RAGSearchRequest, SearchFilters
    return RAGSearchRequest(
        query="ec2 instance tags",
        k=5,
        filters=SearchFilters(cloud="aws", section_type="filter")
    )


@pytest.fixture
def sample_qa_request():
    """サンプルQAリクエスト"""
    from app.rag.models import RAGQARequest, SearchFilters
    return RAGQARequest(
        question="How to stop untagged EC2 instances?",
        context_limit=3,
        filters=SearchFilters(cloud="aws"),
        include_sources=True
    )


# ============================================================================
# pytest設定
# ============================================================================

def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running test")


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """テスト環境のセットアップ"""
    os.environ["TESTING"] = "true"
    os.environ["OPENAI_API_KEY"] = "test-key"
    
    yield
    
    os.environ.pop("TESTING", None)
    os.environ.pop("OPENAI_API_KEY", None)


# ============================================================================
# テストレポート生成
# ============================================================================

class TestResultCollector:
    """テスト結果を収集してレポートを生成"""
    def __init__(self):
        self.results = {"normal": [], "error": [], "security": [], "performance": [], "integration": []}

    def add_result(self, nodeid: str, outcome: str, duration: float):
        test_name = nodeid.split("::")[-1]
        # テストカテゴリを判定
        if "Security" in nodeid:
            cat = "security"
        elif "Error" in nodeid:
            cat = "error"
        elif "Performance" in nodeid:
            cat = "performance"
        elif "Integration" in nodeid:
            cat = "integration"
        else:
            cat = "normal"
        self.results[cat].append({"test_id": test_name, "outcome": outcome, "duration": duration})

    def generate_markdown_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        
        lines = [
            f"# RAG Plugin テストレポート\n",
            f"**生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**通過率**: {passed}/{total} ({(passed/total*100 if total > 0 else 0.0):.1f}%)\n",
            f"\n---\n"
        ]
        
        # カテゴリ別の結果
        for cat, label in [
            ("normal", "正常系テスト"), 
            ("error", "異常系テスト"), 
            ("security", "セキュリティテスト"),
            ("performance", "パフォーマンステスト"),
            ("integration", "統合テスト")
        ]:
            r = self.results[cat]
            if not r:
                continue
            p = sum(1 for x in r if x["outcome"] == "passed")
            f = len(r) - p
            lines.append(f"\n## {label}: {p}/{len(r)}\n")
            lines.append(f"- ✅ 成功: {p}")
            lines.append(f"- ❌ 失敗: {f}\n")
            
            # 失敗したテストのリスト
            if f > 0:
                lines.append(f"\n### 失敗したテスト\n")
                for test in r:
                    if test["outcome"] != "passed":
                        lines.append(f"- `{test['test_id']}` ({test['duration']:.3f}s)")
        
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def generate_json_report(self, output_path: Path):
        total = sum(len(v) for v in self.results.values())
        passed = sum(1 for cat in self.results.values() for r in cat if r["outcome"] == "passed")
        report = {
            "summary": {
                "total": total, 
                "passed": passed,
                "failed": total - passed,
                "pass_rate": round(passed/total*100 if total > 0 else 0.0, 2)
            }, 
            "categories": self.results,
            "generated_at": datetime.now().isoformat()
        }
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """各テストの実行結果を収集"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call":
        collector = getattr(item.session.config, '_test_collector', None)
        if collector:
            collector.add_result(item.nodeid, rep.outcome, rep.duration)


def pytest_sessionstart(session):
    """テストセッション開始時にコレクターを初期化"""
    session.config._test_collector = TestResultCollector()


def pytest_sessionfinish(session, exitstatus):
    """テストセッション終了時にレポートを生成"""
    collector = getattr(session.config, '_test_collector', None)
    if not collector:
        return
    
    # レポートディレクトリを作成
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # レポートを生成
    collector.generate_markdown_report(reports_dir / "TestReport_rag_plugin.md")
    collector.generate_json_report(reports_dir / "TestReport_rag_plugin.json")
