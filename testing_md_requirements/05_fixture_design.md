# フィクスチャ設計

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトで使用するテストフィクスチャの設計を説明します。

## 2. フィクスチャ一覧

### 2.1 カテゴリ別フィクスチャ

| カテゴリ | フィクスチャ名 | スコープ | 説明 |
|---------|---------------|---------|------|
| HTTP | `async_client` | function | 非同期HTTPクライアント |
| HTTP | `authenticated_client` | function | 認証済みクライアント |
| 認証 | `test_auth_token` | function | テスト用JWTトークン |
| 認証 | `mock_jwt_verification` | function | JWT検証モック |
| LLM | `mock_llm_response` | function | LLMレスポンスモック |
| LLM | `mock_llm_streaming` | function | ストリーミングモック |
| DB | `mock_opensearch_client` | function | OpenSearchモック |
| DB | `opensearch_client` | module | 実OpenSearchクライアント |
| DB | `test_index` | function | テスト用インデックス |
| データ | `sample_policy_yaml` | function | サンプルポリシー |
| データ | `sample_recommendation_data` | function | サンプル推奨事項 |
| データ | `sample_chat_request` | function | サンプルリクエスト |

## 3. HTTPクライアント フィクスチャ

### 3.1 async_client

```python
@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    非同期HTTPテストクライアント

    用途:
        - FastAPIエンドポイントのテスト
        - HTTPリクエスト/レスポンスの検証

    使用例:
        async def test_health_check(async_client):
            response = await async_client.get("/api/health")
            assert response.status_code == 200
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

### 3.2 authenticated_client

```python
@pytest.fixture
async def authenticated_client(
    async_client: AsyncClient,
    test_auth_token: str
) -> AsyncClient:
    """
    認証済みHTTPクライアント

    用途:
        - 認証が必要なエンドポイントのテスト
        - 権限チェックの検証

    使用例:
        async def test_protected_endpoint(authenticated_client):
            response = await authenticated_client.get("/api/protected")
            assert response.status_code == 200
    """
    async_client.headers.update({
        "Authorization": f"Bearer {test_auth_token}"
    })
    return async_client
```

## 4. 認証 フィクスチャ

### 4.1 test_auth_token

```python
@pytest.fixture
def test_auth_token() -> str:
    """
    テスト用JWTトークン

    用途:
        - 認証ヘッダーの設定
        - トークン解析のテスト

    注意:
        - 実際のJWT形式ではなくテスト用の固定値
        - mock_jwt_verification と併用する
    """
    return "test-jwt-token-for-testing"
```

### 4.2 mock_jwt_verification

```python
@pytest.fixture
def mock_jwt_verification():
    """
    JWT検証のモック

    用途:
        - 認証をバイパスしたテスト
        - 特定のユーザー/ロールでのテスト

    使用例:
        async def test_admin_only(async_client, mock_jwt_verification):
            mock_jwt_verification.return_value = {
                "sub": "admin-user",
                "roles": ["admin"]
            }
            response = await async_client.get("/api/admin")
            assert response.status_code == 200
    """
    with patch("app.core.auth.verify_token") as mock:
        mock.return_value = {
            "sub": "test-user",
            "roles": ["user"],
            "exp": 9999999999
        }
        yield mock
```

### 4.3 カスタムロールでのテスト

```python
@pytest.fixture
def admin_user_token(mock_jwt_verification):
    """管理者ユーザーとしてのテスト"""
    mock_jwt_verification.return_value = {
        "sub": "admin-user",
        "roles": ["admin", "user"],
        "exp": 9999999999
    }
    return mock_jwt_verification


@pytest.fixture
def readonly_user_token(mock_jwt_verification):
    """読み取り専用ユーザーとしてのテスト"""
    mock_jwt_verification.return_value = {
        "sub": "readonly-user",
        "roles": ["readonly"],
        "exp": 9999999999
    }
    return mock_jwt_verification
```

## 5. LLM フィクスチャ

### 5.1 mock_llm_response

```python
@pytest.fixture
def mock_llm_response():
    """
    LLMレスポンスのモック

    用途:
        - LLM呼び出しを含むロジックのテスト
        - 固定レスポンスでの動作検証

    使用例:
        async def test_policy_generation(mock_llm_response):
            mock_llm_response.ainvoke.return_value.content = "generated policy"
            result = await generate_policy("request")
            assert "generated policy" in result
    """
    mock_response = MagicMock()
    mock_response.content = "This is a mocked LLM response."

    with patch("langchain_openai.ChatOpenAI") as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = mock_response
        mock_openai.return_value = mock_instance
        yield mock_instance
```

### 5.2 mock_llm_with_tools

```python
@pytest.fixture
def mock_llm_with_tools():
    """
    ツール呼び出しを含むLLMモック

    用途:
        - LangChainエージェントのテスト
        - ツール実行フローの検証
    """
    mock_response = MagicMock()
    mock_response.content = ""
    mock_response.tool_calls = [
        {
            "name": "validate_policy",
            "args": {"policy_content": "test policy"},
            "id": "call_123"
        }
    ]

    with patch("langchain_openai.ChatOpenAI") as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.ainvoke.return_value = mock_response
        mock_openai.return_value = mock_instance
        yield mock_instance
```

## 6. データベース フィクスチャ

### 6.1 mock_opensearch_client

```python
@pytest.fixture
def mock_opensearch_client():
    """
    OpenSearchクライアントのモック

    用途:
        - DBアクセスを含むロジックのユニットテスト
        - 検索結果の固定化
    """
    with patch("app.core.clients.get_opensearch_client") as mock:
        mock_client = AsyncMock()

        # 検索結果のデフォルト設定
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 0},
                "hits": []
            }
        }

        mock.return_value = mock_client
        yield mock_client
```

### 6.2 opensearch_client（統合テスト用）

```python
@pytest.fixture(scope="module")
async def opensearch_client():
    """
    実際のOpenSearchクライアント（テスト環境用）

    用途:
        - 統合テストでの実DB操作
        - インデックス操作の検証

    注意:
        - テスト環境のOpenSearchが必要
        - `pytest -m opensearch` で実行
    """
    client = AsyncOpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        http_auth=("admin", "admin"),
        use_ssl=True,
        verify_certs=False,
    )

    # 接続確認
    assert await client.ping(), "OpenSearch connection failed"

    yield client

    await client.close()
```

### 6.3 test_index

```python
@pytest.fixture
async def test_index(opensearch_client) -> AsyncGenerator[str, None]:
    """
    テスト用一時インデックス

    用途:
        - インデックス操作のテスト
        - データ投入・検索のテスト

    特徴:
        - ユニークな名前で作成
        - テスト終了後に自動削除
    """
    import uuid
    index_name = f"test_{uuid.uuid4().hex[:8]}"

    # マッピング定義
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "content": {"type": "text"},
                "timestamp": {"type": "date"}
            }
        }
    }

    await opensearch_client.indices.create(index=index_name, body=mapping)

    yield index_name

    # クリーンアップ
    await opensearch_client.indices.delete(index=index_name, ignore=[404])
```

## 7. テストデータ フィクスチャ

### 7.1 sample_policy_yaml

```python
@pytest.fixture
def sample_policy_yaml() -> str:
    """
    サンプルのCloud Custodianポリシー

    用途:
        - ポリシー解析のテスト
        - バリデーションのテスト
    """
    return """
policies:
  - name: s3-encryption-check
    resource: s3
    description: S3バケットの暗号化をチェック
    filters:
      - type: value
        key: BucketEncryption
        value: absent
    actions:
      - type: notify
        subject: "S3 Bucket without encryption found"
"""
```

### 7.2 sample_recommendation_data

```python
@pytest.fixture
def sample_recommendation_data() -> dict:
    """
    サンプルの推奨事項データ

    用途:
        - ポリシー生成APIのテスト
        - データ変換のテスト
    """
    return {
        "uid": "rec-001",
        "title": "S3バケットの暗号化を有効化",
        "description": "セキュリティのためにS3バケットのサーバーサイド暗号化を有効にしてください",
        "severity": "high",
        "resource_type": "s3",
        "cloud_provider": "aws",
        "compliance_standards": ["CIS AWS 2.1.1"],
        "remediation_steps": [
            "AWSコンソールでS3バケットを開く",
            "プロパティタブを選択",
            "デフォルト暗号化を有効化"
        ]
    }
```

### 7.3 ファクトリ関数

```python
@pytest.fixture
def recommendation_factory():
    """
    推奨事項データのファクトリ

    用途:
        - カスタムデータでのテスト
        - 複数パターンのテスト

    使用例:
        def test_with_custom_data(recommendation_factory):
            rec = recommendation_factory(severity="low", resource_type="ec2")
            assert rec["severity"] == "low"
    """
    def _create(
        uid: str = None,
        title: str = "Test Recommendation",
        severity: str = "medium",
        resource_type: str = "s3",
        **kwargs
    ) -> dict:
        import uuid
        return {
            "uid": uid or f"rec-{uuid.uuid4().hex[:8]}",
            "title": title,
            "description": f"Description for {title}",
            "severity": severity,
            "resource_type": resource_type,
            "cloud_provider": "aws",
            **kwargs
        }

    return _create
```

## 8. フィクスチャ設計のベストプラクティス

### 8.1 スコープの選択基準

```python
# function: 各テストで独立したデータが必要
@pytest.fixture(scope="function")
def unique_data():
    return {"id": uuid.uuid4()}

# module: セットアップコストが高く、状態を変更しない
@pytest.fixture(scope="module")
async def db_client():
    client = await create_client()
    yield client
    await client.close()

# session: アプリ全体で共有可能
@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()
```

### 8.2 依存関係の明示化

```python
# 良い例: 依存関係が明確
@pytest.fixture
def authenticated_request(async_client, auth_token, request_data):
    return async_client, auth_token, request_data

# 悪い例: 暗黙の依存
@pytest.fixture
def bad_fixture():
    return global_client.get_something()  # グローバル依存
```

### 8.3 クリーンアップの保証

```python
@pytest.fixture
async def resource_with_cleanup():
    """リソースの確実なクリーンアップ"""
    resource = await create_resource()
    try:
        yield resource
    finally:
        # 例外が発生してもクリーンアップを実行
        await cleanup_resource(resource)
```
