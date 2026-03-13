# jobs/utils OpenSearch V2 インデクサー テストケース (#17h-1)

## 1. 概要

`app/jobs/utils/opensearch_v2_indexer.py` のテスト仕様書。CSPM v2スキャン結果のOpenSearchインデックス管理（作成・削除・バッチ保存・更新・ドキュメントID生成）を検証する。

### 1.1 主要機能

| 名前 | 行範囲 | 説明 |
|------|--------|------|
| `OpenSearchV2Indexer.__init__` | L24-32 | 初期化（job_id任意、デフォルトUUID生成） |
| `_get_v2_index_mapping` | L34-131 | v2インデックスのマッピング定義取得 |
| `_get_v2_index_settings` | L133-159 | インデックス設定取得（カスタム設定マージ対応） |
| `check_index_exists` | L161-195 | インデックス存在確認 |
| `create_v2_index` | L197-255 | v2インデックス作成（既存時スキップ） |
| `delete_v2_index` | L257-302 | v2インデックス削除（未存在時True） |
| `store_v2_documents` | L304-429 | バッチドキュメント保存（バルクAPI使用） |
| `update_v2_document` | L431-487 | 単一ドキュメント更新（upsert） |
| `_generate_scan_based_document_id` | L489-531 | スキャンIDベースのドキュメントID生成 |
| `_generate_document_id` | L533-578 | 旧形式ドキュメントID生成（後方互換性） |
| `create_cspm_v2_index` | L582-597 | 便利関数（create_v2_indexに委譲） |
| `store_cspm_v2_documents` | L600-617 | 便利関数（store_v2_documentsに委譲） |

### 1.2 カバレッジ目標: 85%

> **注記**: `_get_v2_index_mapping` はL34-131の大規模辞書リテラル（マッピング定義）であり、構造検証のみ実施。`store_v2_documents` はバッチ処理ループ・バルクAPI応答解析を含む最も複雑なメソッド。便利関数（`create_cspm_v2_index` / `store_cspm_v2_documents`）は委譲のみのため最小限の検証。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/utils/opensearch_v2_indexer.py` (616行) |
| テストコード | `test/unit/jobs/utils/test_opensearch_v2_indexer.py` |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存先 | import行 | パッチターゲット | 用途 |
|--------|---------|----------------|------|
| `get_opensearch_client` | L17（モジュールレベル） | `app.jobs.utils.opensearch_v2_indexer.get_opensearch_client` | OpenSearchクライアント取得 |
| `TaskLogger` | L18（モジュールレベル） | `app.jobs.utils.opensearch_v2_indexer.TaskLogger` | ログ出力 |
| `OpenSearchExceptions` | L15（モジュールレベル） | `app.jobs.utils.opensearch_v2_indexer.OpenSearchExceptions` | 例外クラス群 |

> **注記**: 外部依存は全てモジュールレベルimportのため、パッチターゲットは全て `app.jobs.utils.opensearch_v2_indexer.依存名` で統一。外部依存の動的importは存在しない（標準ライブラリ `uuid` の関数内importあり: L529, L576）。

### 1.5 主要分岐マップ（テスト対象: 33分岐）

| メソッド | 分岐数 | 主要条件 |
|---------|--------|---------|
| `check_index_exists` | 4 | L173 無効名（空文字/非文字列のみ拒否）, L179 client None, L188 ConnectionError, L192 Exception |
| `create_v2_index` | 6 | L212 無効名, L218 client None, L223 既存, L244 RequestError, L248 ConnectionError, L252 Exception |
| `delete_v2_index` | 5 | L269 無効名, L274 client None, L280 未存在, L295 ConnectionError, L299 Exception |
| `store_v2_documents` | 9 | L328 無効名, L334 無効docs, L341 client None, L348 index未存在, L369 無効doc形式, L389 bulk errors, L401 batch例外, L418 ConnectionError, L424 Exception |
| `update_v2_document` | 6 | L448 params不足, L455 非dict, L460 client None, L475 NotFoundError, L479 ConnectionError, L483 Exception |
| `_generate_scan_based_document_id` | 2 | L506 scan_id無し, L524 Exception |
| `_generate_document_id` | 1 | L571 Exception |

> **注記**: 上記33分岐は全てテストで網羅済み。以下の2分岐はテスト対象外として既知制限事項（Section 8 #2）に記録:
> - `store_v2_documents` L381: `if not bulk_body: continue`（全件非dict時にバッチスキップ）→ OVI-E11 は dict/非dict 混在入力のため `bulk_body` が空にならず、本分岐には未到達
> - `store_v2_documents` L408-409: `if batch_num < total_batches - 1: await asyncio.sleep(0.1)`（バッチ間スリープ）→ 単一バッチテストでは未到達

---

## 2. 正常系テストケース

| ID | テスト名 | 対象 | 期待結果 |
|----|---------|------|---------|
| OVI-001 | 初期化（デフォルトjob_id） | `__init__` | UUID形式のjob_idが生成される |
| OVI-002 | 初期化（カスタムjob_id） | `__init__` | 指定したjob_idが使用される |
| OVI-003 | マッピング定義構造 | `_get_v2_index_mapping` | mappings.properties に必須フィールド含む |
| OVI-004 | デフォルト設定 | `_get_v2_index_settings` | シャード数1、レプリカ1 |
| OVI-005 | カスタム設定マージ | `_get_v2_index_settings` | カスタム値でデフォルト上書き |
| OVI-006 | インデックス存在確認 True | `check_index_exists` | True |
| OVI-007 | インデックス存在確認 False | `check_index_exists` | False |
| OVI-008 | インデックス作成成功 | `create_v2_index` | True |
| OVI-009 | インデックス既存 → True | `create_v2_index` | True（作成スキップ） |
| OVI-010 | インデックス削除成功 | `delete_v2_index` | True |
| OVI-011 | 削除対象未存在 → True | `delete_v2_index` | True |
| OVI-012 | バッチ保存成功 | `store_v2_documents` | successful=ドキュメント数 |
| OVI-013 | バッチ保存 部分エラー | `store_v2_documents` | successful + failed == total_documents |
| OVI-014 | ドキュメント更新成功 | `update_v2_document` | True |
| OVI-015 | scan_based_document_id 正常 | `_generate_scan_based_document_id` | 正規化されたscan_id |
| OVI-016 | scan_based_document_id フォールバック | `_generate_scan_based_document_id` | job_idから正規化されたID |
| OVI-017 | 旧形式document_id 正常 | `_generate_document_id` | scan_policy_resource形式 |
| OVI-018 | create_cspm_v2_index 委譲 | `create_cspm_v2_index` | create_v2_indexに委譲しTrue |
| OVI-019 | store_cspm_v2_documents 委譲 | `store_cspm_v2_documents` | store_v2_documentsに委譲 |

### 2.1 初期化テスト

```python
# test/unit/jobs/utils/test_opensearch_v2_indexer.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestOpenSearchV2IndexerInit:
    """OpenSearchV2Indexer 初期化テスト"""

    def test_init_default_job_id(self):
        """OVI-001: デフォルトjob_idでUUIDが生成される

        opensearch_v2_indexer.py:L31 の uuid.uuid4() 分岐をカバー。
        """
        # Arrange & Act
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer()

        # Assert
        assert indexer.job_id is not None
        assert len(indexer.job_id) == 36  # UUID形式

    def test_init_custom_job_id(self):
        """OVI-002: カスタムjob_idが使用される

        opensearch_v2_indexer.py:L31 の job_id or ... 分岐をカバー。
        """
        # Arrange & Act
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="custom-job-123")

        # Assert
        assert indexer.job_id == "custom-job-123"
```

### 2.2 マッピング・設定テスト

```python
class TestOpenSearchV2IndexerConfig:
    """OpenSearchV2Indexer マッピング・設定テスト"""

    def test_get_v2_index_mapping_structure(self):
        """OVI-003: マッピング定義に必須フィールドが含まれる

        opensearch_v2_indexer.py:L34-131 の辞書構造を検証。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

        # Act
        mapping = indexer._get_v2_index_mapping()

        # Assert
        props = mapping["mappings"]["properties"]
        # 基本情報フィールド
        assert "scan_id" in props
        assert "account_id" in props
        assert "cloud_provider" in props
        assert "timestamp" in props
        # nested構造
        assert props["policies"]["type"] == "nested"
        assert "scan_summary" in props

    def test_get_v2_index_settings_default(self):
        """OVI-004: デフォルト設定を返す

        opensearch_v2_indexer.py:L159 の return default_settings 分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

        # Act
        settings = indexer._get_v2_index_settings()

        # Assert
        assert settings["number_of_shards"] == 1
        assert settings["number_of_replicas"] == 1
        assert settings["index"]["codec"] == "best_compression"

    def test_get_v2_index_settings_custom_merge(self):
        """OVI-005: カスタム設定がデフォルトにマージされる

        opensearch_v2_indexer.py:L153-157 の custom_settings マージ分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")
        custom = {"number_of_replicas": 2, "custom_key": "value"}

        # Act
        settings = indexer._get_v2_index_settings(custom)

        # Assert
        assert settings["number_of_replicas"] == 2
        assert settings["custom_key"] == "value"
        # デフォルト値が残っている
        assert settings["number_of_shards"] == 1
```

### 2.3 インデックス操作テスト

```python
class TestOpenSearchV2IndexerOperations:
    """OpenSearchV2Indexer インデックス操作テスト"""

    @pytest.mark.asyncio
    async def test_check_index_exists_true(self):
        """OVI-006: インデックスが存在する場合Trueを返す

        opensearch_v2_indexer.py:L183-186 の正常系パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.check_index_exists("cspm-scan-result-v2")

        # Assert
        assert result is True
        mock_client.indices.exists.assert_called_once_with(index="cspm-scan-result-v2")

    @pytest.mark.asyncio
    async def test_check_index_exists_false(self):
        """OVI-007: インデックスが存在しない場合Falseを返す"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.check_index_exists("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_v2_index_success(self):
        """OVI-008: 新規インデックス作成成功

        opensearch_v2_indexer.py:L238-242 の正常作成パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is True
        mock_client.indices.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_v2_index_already_exists(self):
        """OVI-009: 既存インデックス → True（作成スキップ）

        opensearch_v2_indexer.py:L223-226 の既存インデックス分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is True
        mock_client.indices.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_v2_index_success(self):
        """OVI-010: インデックス削除成功

        opensearch_v2_indexer.py:L289-293 の正常削除パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.indices.delete.return_value = {"acknowledged": True}

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.delete_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is True
        mock_client.indices.delete.assert_called_once_with(index="cspm-scan-result-v2")

    @pytest.mark.asyncio
    async def test_delete_v2_index_not_exists(self):
        """OVI-011: 削除対象が存在しない → True

        opensearch_v2_indexer.py:L280-283 の未存在分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.delete_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is True
        mock_client.indices.delete.assert_not_called()
```

### 2.4 ドキュメント保存・更新テスト

```python
class TestOpenSearchV2IndexerDocuments:
    """OpenSearchV2Indexer ドキュメント保存・更新テスト"""

    @pytest.mark.asyncio
    async def test_store_v2_documents_success(self):
        """OVI-012: バッチ保存成功

        opensearch_v2_indexer.py:L398-399 のエラーなしバルク応答パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.bulk.return_value = {"errors": False, "items": []}

        docs = [
            {"scan_id": "scan-001", "doc_type": "v2"},
            {"scan_id": "scan-002", "doc_type": "v2"},
        ]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["successful"] == 2
        assert result["failed"] == 0
        assert result["total_documents"] == 2

    @pytest.mark.asyncio
    async def test_store_v2_documents_partial_errors(self):
        """OVI-013: バルク応答に部分エラーがある場合

        opensearch_v2_indexer.py:L389-397 のbulk errors解析分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.bulk.return_value = {
            "errors": True,
            "items": [
                {"index": {"_id": "scan-001", "result": "created"}},
                {"index": {"_id": "scan-002", "error": {"type": "mapper_parsing_exception"}}},
            ]
        }

        docs = [
            {"scan_id": "scan-001", "doc_type": "v2"},
            {"scan_id": "scan-002", "doc_type": "v2"},
        ]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["successful"] == 1
        assert result["failed"] == 1
        assert len(result["errors"]) >= 1
        # 整合性チェック: successful + failed == total_documents
        assert result["successful"] + result["failed"] == result["total_documents"], (
            f"整合性エラー: successful({result['successful']}) + "
            f"failed({result['failed']}) != total_documents({result['total_documents']})"
        )

    @pytest.mark.asyncio
    async def test_update_v2_document_success(self):
        """OVI-014: 単一ドキュメント更新成功

        opensearch_v2_indexer.py:L464-473 の正常更新パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.update.return_value = {"result": "updated"}

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.update_v2_document(
                "cspm-scan-result-v2", "doc-001", {"status": "updated"}
            )

        # Assert
        assert result is True
        mock_client.update.assert_called_once_with(
            index="cspm-scan-result-v2",
            id="doc-001",
            body={"doc": {"status": "updated"}, "doc_as_upsert": True}
        )
```

### 2.5 ドキュメントID生成テスト

```python
class TestOpenSearchV2IndexerDocumentId:
    """OpenSearchV2Indexer ドキュメントID生成テスト"""

    def test_generate_scan_based_document_id_normal(self):
        """OVI-015: scan_idからドキュメントID生成（特殊文字正規化）

        opensearch_v2_indexer.py:L504-522 の正常パスをカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")
        doc = {"scan_id": "scan:2024/01/01 test"}

        # Act
        result = indexer._generate_scan_based_document_id(doc)

        # Assert
        # コロン・スラッシュ・スペースがアンダースコアに置換される
        assert result == "scan_2024_01_01_test"
        assert ":" not in result
        assert "/" not in result

    def test_generate_scan_based_document_id_fallback(self):
        """OVI-016: scan_id無しでフォールバック

        opensearch_v2_indexer.py:L506-509 のフォールバック分岐をカバー。
        L509: doc.get("job_id") or doc.get("timestamp", "unknown_scan")
        L513: replace(":", "_").replace("/", "_").replace(" ", "_") → ハイフンは保持される
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")
        doc = {"job_id": "fallback-job-123"}

        # Act
        result = indexer._generate_scan_based_document_id(doc)

        # Assert
        # ハイフンは置換対象外のため、入力値がそのまま返される
        assert result == "fallback-job-123"

    def test_generate_document_id_legacy(self):
        """OVI-017: 旧形式ドキュメントID生成

        opensearch_v2_indexer.py:L543-569 の正常パスをカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")
        doc = {
            "violation_context": {"scan_id": "scan-001", "policy_name": "my-policy"},
            "resource_identity": {"primary_id": "i-1234567890"}
        }

        # Act
        result = indexer._generate_document_id(doc)

        # Assert
        assert "scan_001" in result
        assert "my_policy" in result
        assert "i_1234567890" in result
```

### 2.6 便利関数テスト

```python
class TestOpenSearchV2IndexerConvenience:
    """便利関数テスト"""

    @pytest.mark.asyncio
    async def test_create_cspm_v2_index_delegates(self):
        """OVI-018: create_cspm_v2_index が create_v2_index に委譲する

        opensearch_v2_indexer.py:L596-597 の委譲パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.return_value = {"acknowledged": True}

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import create_cspm_v2_index

            # Act
            result = await create_cspm_v2_index("test-index", job_id="job-018")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_store_cspm_v2_documents_delegates(self):
        """OVI-019: store_cspm_v2_documents が store_v2_documents に委譲する

        opensearch_v2_indexer.py:L616-617 の委譲パスをカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.bulk.return_value = {"errors": False, "items": []}

        docs = [{"scan_id": "scan-019", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import store_cspm_v2_documents

            # Act
            result = await store_cspm_v2_documents(
                "test-index", docs, job_id="job-019"
            )

        # Assert
        assert result["successful"] == 1
        assert result["failed"] == 0
```

---

## 3. 異常系テストケース

| ID | テスト名 | 対象 | 期待結果 |
|----|---------|------|---------|
| OVI-E01 | 無効なインデックス名 → False | `check_index_exists` | False |
| OVI-E02 | クライアントNone → False | `check_index_exists` | False |
| OVI-E03 | ConnectionError → False | `check_index_exists` | False |
| OVI-E04 | 作成時 RequestError → False | `create_v2_index` | False |
| OVI-E05 | 空ドキュメントリスト → エラー | `store_v2_documents` | errors配列にメッセージ |
| OVI-E06 | バッチ内例外 → failed加算 | `store_v2_documents` | failed=バッチサイズ |
| OVI-E07 | 更新時 NotFoundError → False | `update_v2_document` | False |
| OVI-E08 | 更新時 パラメータ不足 → False | `update_v2_document` | False |
| OVI-E09 | 保存時 クライアントNone → エラー | `store_v2_documents` | errors配列にメッセージ |
| OVI-E10 | 保存時 インデックス未存在 → エラー | `store_v2_documents` | errors配列にメッセージ |
| OVI-E11 | 非dictドキュメント → successful整合性バグ（xfail） | `store_v2_documents` | successful==1 を期待するが L399 len(batch_docs) 加算で2になる |
| OVI-E12 | 削除時 ConnectionError → False | `delete_v2_index` | False |
| OVI-E13 | 作成時 ConnectionError → False | `create_v2_index` | False |
| OVI-E14 | 更新時 非dict → False | `update_v2_document` | False |
| OVI-E15 | 更新時 クライアントNone → False | `update_v2_document` | False |
| OVI-E16 | 更新時 ConnectionError → False | `update_v2_document` | False |
| OVI-E17 | 作成時 汎用Exception → False | `create_v2_index` | False |
| OVI-E18 | 削除時 汎用Exception → False | `delete_v2_index` | False |
| OVI-E19 | 更新時 汎用Exception → False | `update_v2_document` | False |
| OVI-E20 | 存在確認時 汎用Exception → False | `check_index_exists` | False |
| OVI-E21 | 作成時 無効名 → False | `create_v2_index` | False |
| OVI-E22 | 作成時 クライアントNone → False | `create_v2_index` | False |
| OVI-E23 | 削除時 無効名 → False | `delete_v2_index` | False |
| OVI-E24 | 削除時 クライアントNone → False | `delete_v2_index` | False |
| OVI-E25 | 保存時 外側ConnectionError → failed全件 | `store_v2_documents` | failed=total_documents |
| OVI-E26 | 保存時 外側汎用Exception → failed全件 | `store_v2_documents` | failed=total_documents |
| OVI-E27 | 保存時 無効名 → エラー | `store_v2_documents` | errors配列にメッセージ |
| OVI-E28 | scan_based_document_id 例外 → emergency ID | `_generate_scan_based_document_id` | `emergency_scan_` プレフィックス付きID |
| OVI-E29 | 旧形式document_id 例外 → emergency ID | `_generate_document_id` | `emergency_` プレフィックス付きID |

### 3.1 異常系テスト

```python
class TestOpenSearchV2IndexerErrors:
    """OpenSearchV2Indexer エラーテスト"""

    @pytest.mark.asyncio
    async def test_check_index_exists_invalid_name(self):
        """OVI-E01: 無効なインデックス名 → False

        opensearch_v2_indexer.py:L173-176 の入力検証分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.check_index_exists("")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_index_exists_client_none(self):
        """OVI-E02: クライアントNone → False

        opensearch_v2_indexer.py:L179-181 のクライアント未取得分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.check_index_exists("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_index_exists_connection_error(self):
        """OVI-E03: ConnectionError → False

        opensearch_v2_indexer.py:L188-191 のConnectionError分岐をカバー。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions
        mock_client = AsyncMock()
        mock_client.indices.exists.side_effect = real_exceptions.ConnectionError(
            "N/A", "Connection refused", Exception("refused")
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.check_index_exists("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_v2_index_request_error(self):
        """OVI-E04: RequestError → False

        opensearch_v2_indexer.py:L244-247 のRequestError分岐をカバー。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False
        # TransportError は 3引数: (status_code, error, info)
        mock_client.indices.create.side_effect = real_exceptions.RequestError(
            400, "resource_already_exists_exception", {}
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_store_v2_documents_empty_list(self):
        """OVI-E05: 空ドキュメントリスト → エラー

        opensearch_v2_indexer.py:L334-338 の無効documents分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", [])

        # Assert
        assert result["successful"] == 0
        assert len(result["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_store_v2_documents_batch_exception(self):
        """OVI-E06: バッチ保存中の例外 → failed加算

        opensearch_v2_indexer.py:L401-405 のバッチ内例外分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.bulk.side_effect = RuntimeError("bulk insert failed")

        docs = [{"scan_id": "scan-001", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["failed"] == 1
        assert len(result["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_update_v2_document_not_found(self):
        """OVI-E07: NotFoundError → False

        opensearch_v2_indexer.py:L475-478 のNotFoundError分岐をカバー。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions
        mock_client = AsyncMock()
        # TransportError は 3引数: (status_code, error, info)
        mock_client.update.side_effect = real_exceptions.NotFoundError(
            404, "document_missing_exception", {}
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.update_v2_document(
                "cspm-scan-result-v2", "doc-001", {"status": "updated"}
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_v2_document_missing_params(self):
        """OVI-E08: 必須パラメータ不足 → False

        opensearch_v2_indexer.py:L448-453 のパラメータ検証分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.update_v2_document("", "doc-001", {"status": "x"})

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_store_v2_documents_client_none(self):
        """OVI-E09: クライアントNone → エラー

        opensearch_v2_indexer.py:L341-345 のクライアント未取得分岐をカバー。
        """
        # Arrange
        docs = [{"scan_id": "scan-001", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["successful"] == 0
        assert len(result["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_store_v2_documents_index_not_exists(self):
        """OVI-E10: 保存先インデックス未存在 → エラー

        opensearch_v2_indexer.py:L348-352 のインデックス未存在分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False

        docs = [{"scan_id": "scan-001", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["successful"] == 0
        assert len(result["errors"]) >= 1

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="OVI-E11: opensearch_v2_indexer.py:L399 の "
               "`result['successful'] += len(batch_docs)` がバッチ全体サイズ"
               "（非dict含む）を加算するため、successful が実際のbulk送信件数"
               "（1件）ではなく 2 になる。",
        strict=True,
        raises=AssertionError,
    )
    async def test_store_v2_documents_non_dict_document(self):
        """OVI-E11: 非dictドキュメントが混在 → successful整合性バグ検出

        opensearch_v2_indexer.py:L369-372 の無効ドキュメント形式分岐をカバー。

        [EXPECTED_TO_FAIL] 実装 L399 の `result["successful"] += len(batch_docs)` は
        バッチ全体サイズ（非dict含む）を加算する。docs=[str, dict] の場合、
        bulk送信は1件のみだが successful=2 になる（期待値 successful=1）。
        修正案: `len(bulk_body) // 2`（実際にbulk送信した件数）に変更。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.bulk.return_value = {"errors": False, "items": []}

        # dictと文字列（無効）の混在リスト
        docs = [
            "invalid_string_doc",
            {"scan_id": "scan-valid", "doc_type": "v2"},
        ]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["failed"] == 1  # 非dict分が1件failになる
        assert any("無効なドキュメント形式" in err for err in result["errors"])
        # successful は bulk送信した dict の件数（1件）であるべき
        assert result["successful"] == 1, (
            f"successful={result['successful']} だが、bulk送信は1件のみのため 1 であるべき"
        )

    @pytest.mark.asyncio
    async def test_delete_v2_index_connection_error(self):
        """OVI-E12: 削除時 ConnectionError → False

        opensearch_v2_indexer.py:L295-298 のConnectionError分岐をカバー。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.indices.delete.side_effect = real_exceptions.ConnectionError(
            "N/A", "Connection refused", Exception("refused")
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.delete_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_v2_index_connection_error(self):
        """OVI-E13: 作成時 ConnectionError → False

        opensearch_v2_indexer.py:L248-251 のConnectionError分岐をカバー。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.side_effect = real_exceptions.ConnectionError(
            "N/A", "Connection refused", Exception("refused")
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_v2_document_non_dict(self):
        """OVI-E14: 更新時 非dict → False

        opensearch_v2_indexer.py:L455-457 の非dict検証分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act — document に文字列を渡す（非dict）
            result = await indexer.update_v2_document(
                "cspm-scan-result-v2", "doc-001", "not-a-dict"
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_v2_document_client_none(self):
        """OVI-E15: 更新時 クライアントNone → False

        opensearch_v2_indexer.py:L459-462 のクライアント未取得分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.update_v2_document(
                "cspm-scan-result-v2", "doc-001", {"status": "updated"}
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_v2_document_connection_error(self):
        """OVI-E16: 更新時 ConnectionError → False

        opensearch_v2_indexer.py:L479-481 のConnectionError分岐をカバー。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions
        mock_client = AsyncMock()
        mock_client.update.side_effect = real_exceptions.ConnectionError(
            "N/A", "Connection refused", Exception("refused")
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.update_v2_document(
                "cspm-scan-result-v2", "doc-001", {"status": "updated"}
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_v2_index_general_exception(self):
        """OVI-E17: 作成時 汎用Exception → False

        opensearch_v2_indexer.py:L252-255 の汎用Exception分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = False
        mock_client.indices.create.side_effect = RuntimeError("unexpected error")

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_v2_index_general_exception(self):
        """OVI-E18: 削除時 汎用Exception → False

        opensearch_v2_indexer.py:L299-302 の汎用Exception分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.indices.delete.side_effect = RuntimeError("unexpected error")

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.delete_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_update_v2_document_general_exception(self):
        """OVI-E19: 更新時 汎用Exception → False

        opensearch_v2_indexer.py:L483-487 の汎用Exception分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.update.side_effect = RuntimeError("unexpected error")

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.update_v2_document(
                "cspm-scan-result-v2", "doc-001", {"status": "updated"}
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_index_exists_general_exception(self):
        """OVI-E20: 存在確認時 汎用Exception → False

        opensearch_v2_indexer.py:L192-195 の汎用Exception分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.side_effect = RuntimeError("unexpected error")

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.check_index_exists("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_v2_index_invalid_name(self):
        """OVI-E21: 作成時 無効名 → False

        opensearch_v2_indexer.py:L212-215 の入力検証分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_create_v2_index_client_none(self):
        """OVI-E22: 作成時 クライアントNone → False

        opensearch_v2_indexer.py:L217-220 の クライアント未取得分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.create_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_v2_index_invalid_name(self):
        """OVI-E23: 削除時 無効名 → False

        opensearch_v2_indexer.py:L269-272 の入力検証分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.delete_v2_index("")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_v2_index_client_none(self):
        """OVI-E24: 削除時 クライアントNone → False

        opensearch_v2_indexer.py:L274-277 のクライアント未取得分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.delete_v2_index("cspm-scan-result-v2")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_store_v2_documents_outer_connection_error(self):
        """OVI-E25: 保存時 外側ConnectionError → failed全件

        opensearch_v2_indexer.py:L418-423 の外側ConnectionError分岐をカバー。
        get_opensearch_client自体がConnectionErrorを投げることで、
        L340の呼び出しから直接L418の外側exceptに到達する。

        注意: indices.existsにside_effectを設定するとcheck_index_exists内で
        捕捉されるため（L188）、外側exceptには到達しない。
        """
        # Arrange
        from opensearchpy import exceptions as real_exceptions

        docs = [{"scan_id": "scan-001", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock,
                   side_effect=real_exceptions.ConnectionError(
                       "N/A", "Connection refused", Exception("refused")
                   )):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["failed"] == result["total_documents"]
        assert len(result["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_store_v2_documents_outer_general_exception(self):
        """OVI-E26: 保存時 外側汎用Exception → failed全件

        opensearch_v2_indexer.py:L424-429 の外側汎用Exception分岐をカバー。
        get_opensearch_client自体がRuntimeErrorを投げることで、
        L340の呼び出しから直接L424の外側exceptに到達する。

        注意: indices.existsにside_effectを設定するとcheck_index_exists内で
        捕捉されるため（L192）、外側exceptには到達しない。
        """
        # Arrange
        docs = [{"scan_id": "scan-001", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("unexpected outer error")):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert
        assert result["failed"] == result["total_documents"]
        assert len(result["errors"]) >= 1

    @pytest.mark.asyncio
    async def test_store_v2_documents_invalid_name(self):
        """OVI-E27: 保存時 無効名 → エラー

        opensearch_v2_indexer.py:L328-332 の無効インデックス名分岐をカバー。
        """
        # Arrange
        docs = [{"scan_id": "scan-001", "doc_type": "v2"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("", docs)

        # Assert
        assert result["successful"] == 0
        assert len(result["errors"]) >= 1

    def test_generate_scan_based_document_id_exception(self):
        """OVI-E28: scan_based_document_id 例外 → emergency ID

        opensearch_v2_indexer.py:L524-531 の例外フォールバック分岐をカバー。
        docにAttributeError等を引き起こすオブジェクトを渡し、
        emergency_scan_ プレフィックス付きIDが返ることを検証する。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

        # doc.get() が AttributeError を発生させるオブジェクト
        # MagicMock の get をside_effectで例外にする
        from unittest.mock import MagicMock
        broken_doc = MagicMock()
        broken_doc.get.side_effect = AttributeError("broken")

        # Act
        result = indexer._generate_scan_based_document_id(broken_doc)

        # Assert — emergency_scan_ プレフィックスのフォールバックIDが返る
        assert result.startswith("emergency_scan_")

    def test_generate_document_id_exception(self):
        """OVI-E29: 旧形式document_id 例外 → emergency ID

        opensearch_v2_indexer.py:L571-578 の例外フォールバック分岐をカバー。
        docにAttributeError等を引き起こすオブジェクトを渡し、
        emergency_ プレフィックス付きIDが返ることを検証する。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

        # doc.get() が AttributeError を発生させるオブジェクト
        from unittest.mock import MagicMock
        broken_doc = MagicMock()
        broken_doc.get.side_effect = AttributeError("broken")

        # Act
        result = indexer._generate_document_id(broken_doc)

        # Assert — emergency_ プレフィックスのフォールバックIDが返る
        assert result.startswith("emergency_")
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OVI-SEC-01 | エラーログにAPIキー非露出（check_index_exists） | APIキーを含む例外 | ログにAPIキーが含まれない |
| OVI-SEC-02 | エラーログにAPIキー非露出（store_v2_documents バッチ内） | APIキーを含む例外 | ログにAPIキーが含まれない |
| OVI-SEC-03 | ドキュメントIDに機密情報が残存しない（既知制限） | 機密情報を含むscan_id | 正規化後のIDにAPIキーが残存（xfail） |
| OVI-SEC-04 | 危険なインデックス名が入力検証で拒否される（xfail） | パストラバーサル・ワイルドカード | L173 で拒否を期待するが、空文字/非文字列のみ拒否のため通過する |
| OVI-SEC-05 | バッチエラーのレスポンスに機密情報非露出 | APIキーを含む例外 | result["errors"]にAPIキーが含まれない |

```python
@pytest.mark.security
class TestOpenSearchV2IndexerSecurity:
    """OpenSearchV2Indexer セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="OVI-SEC-01: opensearch_v2_indexer.py:L193-194 で str(e) を"
               "そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_check_error_log(self):
        """OVI-SEC-01: check_index_exists のエラーログにAPIキー非露出

        opensearch_v2_indexer.py:L193-194 の logger.error({"error": str(e), ...})
        により、例外メッセージにAPIキー等が含まれる場合にログに露出する。

        [EXPECTED_TO_FAIL] str(e) をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"
        mock_client = AsyncMock()
        mock_client.indices.exists.side_effect = RuntimeError(
            f"Auth failed: key={fake_key}"
        )

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger") as MockLogger, \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            await indexer.check_index_exists("cspm-scan-result-v2")

        # Assert — MockLogger.return_value は indexer.logger と同一インスタンス
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call}"
            )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="OVI-SEC-02: opensearch_v2_indexer.py:L403-404 で str(e) を"
               "そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_store_batch_error_log(self):
        """OVI-SEC-02: store_v2_documents のバッチ内エラーログにAPIキー非露出

        opensearch_v2_indexer.py:L401-405 のバッチ内 except で
        f"バッチ{batch_num + 1}の保存中にエラーが発生: {str(e)}" が
        ログに記録されるため、APIキーが露出する。

        [EXPECTED_TO_FAIL] str(e) をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        # check_index_existsを正常通過させ、bulk呼び出しで例外を発生させる
        mock_client.bulk.side_effect = RuntimeError(
            f"Auth failed: key={fake_key}"
        )

        docs = [{"scan_id": "scan-001"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger") as MockLogger, \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert — MockLogger.return_value は indexer.logger と同一インスタンス
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call}"
            )

    @pytest.mark.xfail(
        reason="OVI-SEC-03: opensearch_v2_indexer.py:L513 の正規化は"
               "特殊文字置換のみで、内容フィルタリングを行わないため、"
               "scan_id内のAWSアクセスキー相当文字列が残存する。",
        strict=True,
        raises=AssertionError,
    )
    def test_document_id_sensitive_data_retention(self):
        """OVI-SEC-03: ドキュメントID生成で機密情報が残存する（既知制限）

        opensearch_v2_indexer.py:L489-531 の _generate_scan_based_document_id で
        scan_idに機密情報が含まれる場合、正規化後のIDにも残存する。
        正規化は特殊文字置換のみで、内容フィルタリングは行わない。

        [EXPECTED_TO_FAIL] scan_id の内容フィルタリングが未実装のため、
        AWSアクセスキー相当の文字列がドキュメントIDに残存する。
        """
        # Arrange
        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

        # scan_idにAWSアクセスキーが混入したケース
        aws_access_key = "AKIAIOSFODNN7EXAMPLE"
        doc = {"scan_id": f"scan:{aws_access_key}:2024"}

        # Act
        result = indexer._generate_scan_based_document_id(doc)

        # Assert — 機密情報がIDに残存しないことを期待（現状は残存する）
        assert aws_access_key not in result, (
            f"ドキュメントIDにAWSアクセスキーが残存: {result}"
        )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="OVI-SEC-04: opensearch_v2_indexer.py:L173 の入力検証は "
               "`not index_name or not isinstance(index_name, str)` のみで、"
               "パストラバーサル（../）やワイルドカード（*）を拒否しない。"
               "有効なクライアントが存在する場合、危険な名前がそのまま "
               "OpenSearch API に渡される。",
        strict=True,
        raises=AssertionError,
    )
    async def test_index_name_injection_rejected(self):
        """OVI-SEC-04: 危険なインデックス名が入力検証で拒否される

        opensearch_v2_indexer.py:L173 の入力検証が
        パストラバーサル（../）やワイルドカード（*）を含むインデックス名を
        拒否することを期待するテスト。

        [EXPECTED_TO_FAIL] L173 は `not index_name or not isinstance(index_name, str)` のみ。
        危険な文字列は非空文字列なので検証を通過し、有効なクライアント経由で
        OpenSearch API に到達する。修正案: 正規表現 `^[a-z0-9][a-z0-9._-]*$` で検証。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        dangerous_names = ["../admin-index", "*", "cspm-*"]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act & Assert — 危険なインデックス名が L173 で拒否されることを期待
            for name in dangerous_names:
                result = await indexer.check_index_exists(name)
                assert result is False, (
                    f"危険なインデックス名 {name!r} が入力検証を通過した"
                )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="OVI-SEC-05: opensearch_v2_indexer.py:L403 で "
               "f'バッチ{batch_num + 1}の保存中にエラーが発生: {str(e)}' が "
               "result['errors'] に格納され、APIレスポンス経由で外部に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_batch_error_no_credentials_in_response(self):
        """OVI-SEC-05: バッチ内例外のエラーメッセージがレスポンスに露出しない

        opensearch_v2_indexer.py:L401-405 のバッチ内 except で
        str(e) を含むメッセージが result["errors"] に格納される。
        このresultは呼び出し元にAPIレスポンスとして返されるため、
        例外メッセージに含まれる機密情報が外部に露出するリスクがある。

        [EXPECTED_TO_FAIL] str(e) がそのまま result["errors"] に含まれるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        fake_token = "FAKE-SECRET-TOKEN-99999"
        mock_client = AsyncMock()
        mock_client.indices.exists.return_value = True
        mock_client.bulk.side_effect = RuntimeError(f"token={fake_token}")

        docs = [{"scan_id": "scan-001"}]

        with patch("app.jobs.utils.opensearch_v2_indexer.TaskLogger"), \
             patch("app.jobs.utils.opensearch_v2_indexer.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            from app.jobs.utils.opensearch_v2_indexer import OpenSearchV2Indexer
            indexer = OpenSearchV2Indexer(job_id="test")

            # Act
            result = await indexer.store_v2_documents("cspm-scan-result-v2", docs)

        # Assert — result["errors"] にシークレットが含まれないことを期待
        for err in result["errors"]:
            assert fake_token not in err, (
                f"APIレスポンスにシークレットが露出: {err}"
            )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

> **注記**: `opensearch_v2_indexer.py` はモジュールレベルで `get_opensearch_client`（L17）、`TaskLogger`（L18）、`OpenSearchExceptions`（L15）をインポートする。これらは全て `app.jobs.utils.opensearch_v2_indexer.依存名` でパッチ可能。conftest.py は `test/unit/jobs/utils/conftest.py`（#17aで定義）を共有する。

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

_TARGET_MODULES = (
    "app.jobs.utils.opensearch_v2_indexer",
)


@pytest.fixture(autouse=True)
def reset_utils_module():
    """テストごとにモジュールのグローバル状態をリセット"""
    yield
    modules_to_remove = [
        key for key in sys.modules
        if key in _TARGET_MODULES
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

> **注記**: conftest.py は #17a〜#17h と共有予定。実装時には既存の `_TARGET_MODULES` タプルに `"app.jobs.utils.opensearch_v2_indexer"` を追加する形で統合する。

---

## 6. テスト実行例

```bash
# OpenSearch V2インデクサーテストのみ実行
pytest test/unit/jobs/utils/test_opensearch_v2_indexer.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_opensearch_v2_indexer.py::TestOpenSearchV2IndexerOperations -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_opensearch_v2_indexer.py \
  --cov=app.jobs.utils.opensearch_v2_indexer \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_opensearch_v2_indexer.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 19 | OVI-001 〜 OVI-019 |
| 異常系 | 29 | OVI-E01 〜 OVI-E29 |
| セキュリティ | 5 | OVI-SEC-01 〜 OVI-SEC-05 |
| **合計** | **53** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestOpenSearchV2IndexerInit` | OVI-001〜OVI-002 | 2 |
| `TestOpenSearchV2IndexerConfig` | OVI-003〜OVI-005 | 3 |
| `TestOpenSearchV2IndexerOperations` | OVI-006〜OVI-011 | 6 |
| `TestOpenSearchV2IndexerDocuments` | OVI-012〜OVI-014 | 3 |
| `TestOpenSearchV2IndexerDocumentId` | OVI-015〜OVI-017 | 3 |
| `TestOpenSearchV2IndexerConvenience` | OVI-018〜OVI-019 | 2 |
| `TestOpenSearchV2IndexerErrors` | OVI-E01〜OVI-E29 | 29 |
| `TestOpenSearchV2IndexerSecurity` | OVI-SEC-01〜OVI-SEC-05 | 5 |

### 7.1 予想失敗テスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| OVI-SEC-01 | opensearch_v2_indexer.py:L193-194 で `str(e)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する | ログ出力から `str(e)` を除去するか、マスク処理を導入する |
| OVI-SEC-02 | opensearch_v2_indexer.py:L403-404 で `str(e)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する | 同上 |
| OVI-SEC-03 | opensearch_v2_indexer.py:L513 の正規化は特殊文字置換のみで、内容フィルタリングを行わないため、scan_id内のAWSアクセスキー相当文字列がドキュメントIDに残存する | scan_idの入力サニタイズを導入する（ハッシュ化はscan_id検索を破壊するため非推奨） |
| OVI-SEC-04 | opensearch_v2_indexer.py:L173 の入力検証は `not index_name or not isinstance(index_name, str)` のみで、パストラバーサル（`../`）やワイルドカード（`*`）を拒否しない | 正規表現 `^[a-z0-9][a-z0-9._-]*$` 等でインデックス名を検証する |
| OVI-SEC-05 | opensearch_v2_indexer.py:L403 で `str(e)` を含むメッセージが `result["errors"]` に格納され、APIレスポンス経由で外部に露出する | `result["errors"]` に格納するメッセージを汎用文に置換し、詳細はログのみに記録する |
| OVI-E11 | opensearch_v2_indexer.py:L399 の `result["successful"] += len(batch_docs)` がバッチ全体サイズ（非dict含む）を加算するため、successful が実際のbulk送信件数より多くなる | `len(bulk_body) // 2`（実際にbulk送信した件数）に修正するか、個別カウントに変更 |

### xfail 解除手順

1. `opensearch_v2_indexer.py` の `logger.error(... {"error": str(e), ...})` パターン（L190, L194, L246, L250, L254, L297, L301, L403-404, L419, L425-426, L481, L484-485）で例外メッセージをマスクまたは汎用メッセージに置換 → OVI-SEC-01, OVI-SEC-02 解除
2. `result["errors"].append(...)` に格納するメッセージから `str(e)` を除去（内側 except L403、外側 except L421, L427 の3箇所）→ OVI-SEC-05 解除
3. `_generate_scan_based_document_id` に入力サニタイズを導入 → OVI-SEC-03 解除（ハッシュ化はscan_idによる検索を破壊するため非推奨。呼び出し側でのバリデーション強化を優先）
4. 全メソッド共通のインデックス名検証関数に正規表現（`^[a-z0-9][a-z0-9._-]*$` 等）を導入（L173, L212, L269, L328）→ OVI-SEC-04 解除
5. `store_v2_documents` L399 の `len(batch_docs)` を `len(bulk_body) // 2` に修正 → OVI-E11 解除
6. 上記修正後、対応する `@pytest.mark.xfail(...)` デコレータを削除
7. テスト実行で PASS を確認

### 注意事項

- `pytest-asyncio` パッケージが必要（全asyncメソッド）
- OpenSearchクライアントは全てモック化（`AsyncMock`）
- `OpenSearchExceptions` は実際の例外クラスを使用（`from opensearchpy import exceptions`）してハンドラの型マッチングを検証
- `TransportError` 系の例外（`RequestError`, `NotFoundError`, `ConnectionError`）は3引数: `(status_code, error, info)` で生成する
- モジュールレベルimport（L15-18）の依存は全て `app.jobs.utils.opensearch_v2_indexer.依存名` でパッチ
- `store_v2_documents` のバッチ間 `asyncio.sleep(0.1)`（L408-409）は単一バッチ（100件以下）のテストでは `batch_num < total_batches - 1` 条件により実行されないため、パッチ不要。複数バッチテストを追加する場合は `asyncio.sleep` のパッチが必要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_get_v2_index_mapping`（L34-131）は100行の大規模辞書リテラル | 全フィールドの個別検証は冗長 | 主要フィールド（scan_id, policies nested, scan_summary）の存在のみ検証 |
| 2 | `store_v2_documents` のバッチスキップ L381（`if not bulk_body: continue`）およびバッチ間スリープ L408-409（`if batch_num < total_batches - 1: await asyncio.sleep(0.1)`） | L381 は全テスト未到達。L408-409 は単一バッチのテストでは未実行 | L381: 到達には「バッチ内の全ドキュメントが非dict」の入力が必要だが、OVI-E11 は dict/非dict 混在入力のため `bulk_body` が空にならず未到達。L408-409: 条件 `batch_num < total_batches - 1` により単一バッチ（100件以下）テストではsleepに到達しない。いずれも複数バッチ・全件非dictテスト追加時にカバー可能 |
| 3 | `_generate_scan_based_document_id` / `_generate_document_id` の最終フォールバック（L529-531, L576-578）で `uuid.uuid4()` を使用 | 非決定的な出力のためアサーション困難 | OVI-E28/E29 でプレフィックス（`emergency_scan_` / `emergency_`）の存在のみ検証 |
| 4 | `str(e)` がログの `error` 辞書キーに直接含まれる（14箇所） | 機密情報がログに露出するリスク | OVI-SEC-01 が `check_index_exists` L192（汎用Exception）の代表経路を記録。同メソッドの ConnectionError（L188）も同一パターンだが省略。OVI-SEC-02 が `store_v2_documents` 内側except L403 の代表経路を記録。`create_v2_index`、`delete_v2_index`、`update_v2_document`、`store_v2_documents` 外側except（L419, L425）も同一パターンのため省略 |
| 5 | `_generate_scan_based_document_id` は scan_id の内容フィルタリングを行わない | scan_id に機密情報が含まれる場合、ドキュメントIDに残存 | OVI-SEC-03 で xfail として記録。入力サニタイズの導入を推奨 |
| 6 | `str(e)` が `result["errors"]` に格納され、APIレスポンスとして外部に露出する（内側except L403、外側except L421, L427 の3箇所） | 例外メッセージ内の機密情報がAPI経由で漏洩 | OVI-SEC-05 が内側except（L403）の代表経路を xfail として記録。外側except（L421, L427）も同一パターンだが省略。汎用メッセージへの置換を推奨 |
| 7 | `check_index_exists` L173 の入力検証は空文字・非文字列のみを拒否（`../`, `*` 等は通過）。`create_v2_index`（L212）、`delete_v2_index`（L269）、`store_v2_documents`（L328）も同一の不十分な検証パターン | パストラバーサルやワイルドカードが全メソッドの入力検証を通過する。特に `create_v2_index`/`delete_v2_index` は破壊的操作のため影響大 | OVI-SEC-04 で `check_index_exists` を代表として xfail 記録。他メソッドも同一パターンのため省略。正規表現バリデーション（`^[a-z0-9][a-z0-9._-]*$` 等）を共通検証関数として導入を推奨 |
| 8 | `store_v2_documents` L399 の `result["successful"] += len(batch_docs)` は非dictを含むバッチ全体を加算 | successful が実際にbulk送信した件数より多くなる可能性 | OVI-E11 で潜在バグとして記録。`len(bulk_body) // 2` に修正するか、個別カウントに変更を推奨 |
