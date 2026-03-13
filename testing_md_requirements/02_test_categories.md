# テストカテゴリ分類

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトのテストカテゴリとその詳細を定義します。

## 2. ユニットテスト

### 2.1 対象範囲

| 対象 | 説明 | 例 |
|------|------|-----|
| ビジネスロジック | コア機能のロジック | ポリシー検証、YAML解析 |
| ユーティリティ関数 | 汎用処理関数 | 文字列処理、日付変換 |
| データモデル | Pydanticモデル | バリデーション、シリアライズ |
| ツール関数 | LangChainツール | validate_policy, search_rag |

### 2.2 テスト方法

```python
# ユニットテストの基本構造
import pytest
from unittest.mock import patch, AsyncMock

class TestPolicyValidation:
    """ポリシー検証のユニットテスト"""

    def test_valid_yaml_policy(self):
        """正常なYAMLポリシーを検証する"""
        # Arrange（準備）
        policy = """
        policies:
          - name: s3-encryption
            resource: s3
        """

        # Act（実行）
        result = parse_policy(policy)

        # Assert（検証）
        assert result is not None
        assert "policies" in result

    def test_invalid_yaml_raises_error(self):
        """不正なYAMLでエラーを発生させる"""
        # Arrange
        invalid_policy = "policies: [invalid yaml"

        # Act & Assert
        with pytest.raises(YAMLParseError):
            parse_policy(invalid_policy)
```

### 2.3 モック方針

| 依存 | モック方法 | 理由 |
|------|-----------|------|
| LLM API | AsyncMock | 外部依存・コスト |
| OpenSearch | MagicMock | 外部依存 |
| AWS SDK | moto / MagicMock | 外部依存 |
| ファイルシステム | tmp_path fixture | 隔離性 |

### 2.4 ディレクトリ構造

```
test/
├── unit/
│   ├── __init__.py
│   ├── cspm_plugin/           # CSPMプラグインのユニットテスト
│   │   ├── test_policy_validation.py
│   │   ├── test_refinement.py
│   │   └── test_agent_executor.py
│   ├── mcp_plugin/            # MCPプラグインのユニットテスト
│   │   ├── test_url_validator.py
│   │   └── test_subagents.py
│   └── core/                  # コアサービスのユニットテスト
│       ├── test_llm_factory.py
│       └── test_config.py
```

## 3. 統合テスト

### 3.1 対象範囲

| 対象 | 説明 | 例 |
|------|------|-----|
| APIエンドポイント | HTTPリクエスト/レスポンス | POST /api/cspm/chat/refine |
| データベース連携 | OpenSearch操作 | インデックス作成、検索 |
| サービス間連携 | 内部サービス呼び出し | 認証→ジョブ→レポート |
| 認証フロー | JWT生成・検証 | ログイン、トークンリフレッシュ |

### 3.2 テスト方法

```python
# 統合テストの基本構造
import pytest
from httpx import AsyncClient
from app.main import app

class TestCSPMIntegration:
    """CSPMエンドポイントの統合テスト"""

    @pytest.fixture
    async def client(self):
        """非同期HTTPクライアント"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_refine_policy_success(self, client, mock_llm_response):
        """ポリシー修正が成功する"""
        # Arrange
        request_data = {
            "prompt": "S3バケットの暗号化チェックを追加",
            "policy_context": "policies:\n  - name: test"
        }

        # Act
        response = await client.post(
            "/api/cspm/chat/refine",
            json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    @pytest.mark.asyncio
    async def test_refine_policy_unauthorized(self, client):
        """認証なしでエラーを返す"""
        # Act
        response = await client.post(
            "/api/cspm/chat/refine",
            json={"prompt": "test"}
        )

        # Assert
        assert response.status_code == 401
```

### 3.3 テストデータベース

```python
# OpenSearchテスト用フィクスチャ
@pytest.fixture
async def test_opensearch_client():
    """テスト用OpenSearchクライアント"""
    from opensearchpy import AsyncOpenSearch

    client = AsyncOpenSearch(
        hosts=[{"host": "localhost", "port": 9200}],
        http_auth=("admin", "admin"),
        use_ssl=True,
        verify_certs=False,
    )

    # テスト用インデックス作成
    test_index = "test_cspm_policies"
    if not await client.indices.exists(index=test_index):
        await client.indices.create(index=test_index)

    yield client

    # クリーンアップ
    await client.indices.delete(index=test_index, ignore=[404])
    await client.close()
```

### 3.4 ディレクトリ構造

```
test/
├── integration/
│   ├── __init__.py
│   ├── test_cspm_api.py         # CSPM APIの統合テスト
│   ├── test_auth_flow.py        # 認証フローの統合テスト
│   ├── test_job_lifecycle.py    # ジョブライフサイクルテスト
│   └── test_opensearch_ops.py   # OpenSearch操作テスト
```

## 4. E2Eテスト

### 4.1 対象範囲

| 対象 | 説明 | 例 |
|------|------|-----|
| ユーザーフロー | 完全なシナリオ | ログイン→スキャン→レポート |
| 外部連携 | 実際の外部サービス | AWS、OpenSearch |
| パフォーマンス | 応答時間、スループット | 大量データ処理 |

### 4.2 テスト方法

```python
# E2Eテストの基本構造
import pytest
from httpx import AsyncClient

class TestE2ECSPMFlow:
    """CSPMの完全なフローをテスト"""

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_policy_generation_flow(self, e2e_client, e2e_auth_token):
        """
        完全なポリシー生成フロー:
        1. 推奨事項取得
        2. ポリシー生成
        3. ポリシー検証
        4. 保存
        """
        headers = {"Authorization": f"Bearer {e2e_auth_token}"}

        # Step 1: 推奨事項取得
        rec_response = await e2e_client.get(
            "/api/recommendations",
            headers=headers
        )
        assert rec_response.status_code == 200
        recommendation = rec_response.json()["items"][0]

        # Step 2: ポリシー生成
        gen_response = await e2e_client.post(
            "/api/cspm/chat/agent",
            json={"recommendation_data": recommendation, "target_cloud": "aws"},
            headers=headers
        )
        assert gen_response.status_code == 200
        policy = gen_response.json()["policy_content"]

        # Step 3: ポリシー検証
        val_response = await e2e_client.post(
            "/api/cspm/validate_policy_with_tool",
            json={"policy_content": policy},
            headers=headers
        )
        assert val_response.status_code == 200
        assert val_response.json()["isValid"] is True
```

### 4.3 実行条件

| 条件 | 要件 |
|------|------|
| 環境 | テスト/ステージング環境 |
| 認証 | 有効なテストアカウント |
| 外部サービス | 接続可能な状態 |
| データ | テスト用初期データ |

### 4.4 ディレクトリ構造

```
test/
├── e2e/
│   ├── __init__.py
│   ├── conftest.py              # E2E用フィクスチャ
│   ├── test_cspm_flow.py        # CSPMフローE2Eテスト
│   ├── test_auth_flow.py        # 認証フローE2Eテスト
│   └── test_report_flow.py      # レポート生成フローE2Eテスト
```

## 5. テストマーカー

### 5.1 定義済みマーカー

```python
# conftest.py または pyproject.toml で定義

# pytest マーカー定義
pytest_markers = [
    "unit: ユニットテスト",
    "integration: 統合テスト",
    "e2e: E2Eテスト",
    "slow: 実行時間が長いテスト",
    "llm: LLM連携が必要なテスト",
    "opensearch: OpenSearch接続が必要なテスト",
    "aws: AWS接続が必要なテスト",
]
```

### 5.2 使用方法

```python
# テストにマーカーを付与
@pytest.mark.unit
def test_parse_yaml():
    """ユニットテスト"""
    pass

@pytest.mark.integration
@pytest.mark.opensearch
async def test_search_index():
    """OpenSearch連携の統合テスト"""
    pass

@pytest.mark.e2e
@pytest.mark.slow
async def test_full_flow():
    """時間のかかるE2Eテスト"""
    pass
```

### 5.3 実行フィルタリング

```bash
# ユニットテストのみ実行
pytest -m unit

# 統合テスト除くすべて
pytest -m "not integration"

# OpenSearch不要なテストのみ
pytest -m "not opensearch"

# E2Eテストを除外（高速実行）
pytest -m "not e2e and not slow"
```

## 6. テストカテゴリ別チェックリスト

### 6.1 ユニットテスト作成時

- [ ] 外部依存が全てモック化されている
- [ ] 1テストで1つの動作のみ検証している
- [ ] 境界値・エッジケースが考慮されている
- [ ] エラーケースがテストされている
- [ ] テストが独立して実行可能

### 6.2 統合テスト作成時

- [ ] APIエンドポイントの全メソッドがカバーされている
- [ ] 正常系・異常系の両方がテストされている
- [ ] 認証・認可が検証されている
- [ ] テストデータのクリーンアップが実装されている

### 6.3 E2Eテスト作成時

- [ ] ユーザーシナリオに基づいている
- [ ] 前提条件が明確
- [ ] タイムアウト設定が適切
- [ ] 失敗時のデバッグ情報が十分
