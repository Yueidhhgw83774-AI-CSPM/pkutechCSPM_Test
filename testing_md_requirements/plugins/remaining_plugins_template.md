# 残りのプラグインテストケーステンプレート

## 概要

以下のプラグインのテストケース基本構造を定義します。詳細なテストケースは必要に応じて拡充してください。

---

## 1. chat_dashboard プラグイン

### カバレッジ目標: 70%

### 主要エンドポイント
- POST /chat/cspm_dashboard - CSPMダッシュボードチャット

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| CHAT-001 | 正常系 | 有効なチャットリクエスト | status 200 |
| CHAT-002 | 正常系 | コンテキスト付きチャット | コンテキスト反映 |
| CHAT-E01 | 異常系 | 空のメッセージ | status 422 |
| CHAT-E02 | 異常系 | LLMエラー | エラーメッセージ |

```python
# test/unit/chat_dashboard/test_router.py
class TestChatDashboard:
    @pytest.mark.asyncio
    async def test_chat_success(self, async_client, mock_llm):
        response = await async_client.post(
            "/api/chat/cspm_dashboard",
            json={"message": "セキュリティ状況を教えて"}
        )
        assert response.status_code == 200
```

---

## 2. mcp_plugin プラグイン

### カバレッジ目標: 75%

### 主要エンドポイント
- POST /mcp/execute - MCPツール実行
- GET /mcp/tools - 利用可能ツール一覧

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| MCP-001 | 正常系 | ツール実行成功 | ツール結果 |
| MCP-002 | 正常系 | ツール一覧取得 | ツールリスト |
| MCP-E01 | 異常系 | 無効なツール名 | status 404 |
| MCP-E02 | 異常系 | パラメータ不足 | status 422 |

---

## 3. report_plugin プラグイン

### カバレッジ目標: 70%

### 主要エンドポイント
- POST /report/generate - レポート生成
- GET /report/{id} - レポート取得

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| RPT-001 | 正常系 | PDF生成成功 | PDFデータ |
| RPT-002 | 正常系 | レポート取得 | レポートデータ |
| RPT-E01 | 異常系 | 無効なフォーマット | status 422 |
| RPT-E02 | 異常系 | データ不足 | エラーメッセージ |

---

## 4. rag プラグイン

### カバレッジ目標: 60%

### 主要エンドポイント
- POST /rag/search - セマンティック検索
- POST /rag/index - ドキュメントインデックス

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| RAG-001 | 正常系 | 検索成功 | 検索結果 |
| RAG-002 | 正常系 | インデックス成功 | インデックスID |
| RAG-E01 | 異常系 | OpenSearch未接続 | status 503 |

---

## 5. doc_reader_plugin プラグイン

### カバレッジ目標: 60%

### 主要エンドポイント
- POST /docreader/parse - ドキュメント解析
- GET /docreader/documents - ドキュメント一覧

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| DOC-001 | 正常系 | PDF解析成功 | 解析結果 |
| DOC-002 | 正常系 | テキスト抽出 | テキストデータ |
| DOC-E01 | 異常系 | 無効なファイル形式 | status 415 |

---

## 6. custodian_scan プラグイン

### カバレッジ目標: 65%

### 主要エンドポイント
- POST /custodian/scan - スキャン実行
- GET /custodian/results - スキャン結果取得

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| SCAN-001 | 正常系 | スキャン開始成功 | ジョブID |
| SCAN-002 | 正常系 | 結果取得成功 | スキャン結果 |
| SCAN-E01 | 異常系 | 無効なポリシー | status 400 |
| SCAN-E02 | 異常系 | AWS認証エラー | status 401 |

---

## 7. logchecker プラグイン

### カバレッジ目標: 60%

### 主要機能
- ログ解析
- パターンマッチング
- アラート生成

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| LOG-001 | 正常系 | ログ解析成功 | 解析結果 |
| LOG-002 | 正常系 | パターン検出 | マッチ結果 |
| LOG-E01 | 異常系 | 無効なログ形式 | エラーメッセージ |

---

## 8. aws_plugin プラグイン

### カバレッジ目標: 60%

### 主要機能
- AWS API呼び出し
- リソース情報取得
- 設定変更

### テストケース概要

| ID | カテゴリ | テスト名 | 期待結果 |
|----|---------|---------|---------|
| AWS-001 | 正常系 | リソース一覧取得 | リソースリスト |
| AWS-002 | 正常系 | 設定取得 | 設定データ |
| AWS-E01 | 異常系 | 認証エラー | status 401 |
| AWS-E02 | 異常系 | 権限不足 | status 403 |

---

## 共通フィクスチャテンプレート

```python
# test/unit/plugins/conftest.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_plugin_service():
    """プラグインサービスの汎用モック"""
    service = AsyncMock()
    return service

@pytest.fixture
def sample_request_data():
    """サンプルリクエストデータ"""
    return {"key": "value"}
```

---

## テスト実行例

```bash
# 特定プラグインのテスト
pytest test/unit/chat_dashboard/ -v
pytest test/unit/mcp_plugin/ -v
pytest test/unit/report_plugin/ -v

# 全プラグインのテスト
pytest test/unit/ -v --ignore=test/unit/core/
```
