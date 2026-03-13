# jobs/utils ストレージ統合・再エクスポート テストケース (#17g)

## 1. 概要

`app/jobs/utils/store_operations.py` および `app/jobs/utils/custodian_output.py` のテスト仕様書。Custodianスキャン結果のOpenSearchへの保存操作と、分割モジュールの再エクスポートファサードを検証する。

### 1.1 主要機能

| 関数 | ファイル | 行範囲 | 説明 |
|------|---------|--------|------|
| `store_custodian_output_to_opensearch()` | store_operations.py | L12-78 | メイン保存エントリーポイント（v2保存に委譲） |
| `store_scan_history_v2()` | store_operations.py | L81-278 | スキャン履歴のcspm-scan-history-v2保存 |
| `store_scan_result_v2()` | store_operations.py | L281-343 | v2ドキュメントのバッチ保存 |
| `custodian_output.py` | custodian_output.py | 全体 | 分割モジュールの再エクスポートファサード |

### 1.2 カバレッジ目標: 85%

> **注記**: `store_scan_history_v2` は278行の大規模関数で、`ResultProcessor` / `ResultFormatter` との連携が中心。これらの外部依存は全てモックし、本モジュール固有の分岐ロジック（account_id取得の3段階フォールバック、エラー/正常時のサマリー切り替え、OpenSearch保存結果判定）に集中する。`custodian_output.py` は純粋な再エクスポートのため、インポート検証のみ。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/utils/store_operations.py` (343行) |
| テスト対象2 | `app/jobs/utils/custodian_output.py` (78行) |
| テストコード | `test/unit/jobs/utils/test_store_operations.py` |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存先 | 用途 | モック要否 |
|--------|------|-----------|
| `get_opensearch_client` | OpenSearchクライアント取得 | 要（動的import、モック） |
| `TaskLogger` | ログ出力 | 要（モック） |
| `_extract_violation_documents_from_output` | 違反ドキュメント抽出 | 要（モック、#17bで検証済） |
| `_extract_v2_documents_from_output` | v2ドキュメント抽出 | 要（モック、#17bで検証済） |
| `_sanitize_resource_for_opensearch` | リソースサニタイズ | 要（モック、#17aで検証済） |
| `_get_custodian_version` | Custodianバージョン取得 | 要（モック、#17aで検証済） |
| `_generate_policy_fingerprint` | ポリシーフィンガープリント | 要（モック、#17aで検証済） |
| `extract_metadata_from_output_dir` | メタデータ抽出 | 要（モック、#17eで検証済） |
| `ResultProcessor` | スキャン結果処理 | 要（動的import、モック） |
| `ResultFormatter` | エラーサマリー生成 | 要（動的import、モック） |
| `OpenSearchV2Indexer` | v2インデックス操作 | 要（動的import、モック） |

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `store_custodian_output_to_opensearch` | 5 | L41 クライアントNone, L54 違反データ空, L62 skip_result_v2, L69 v2保存例外, L76 外部例外 |
| `store_scan_history_v2` | 7 | L120 account_id from metadata, L125 from history_data, L130 from custodian output, L135 抽出例外, L144 has_errors分岐, L269 保存結果判定, L276 外部例外 |
| `store_scan_result_v2` | 5 | L314 インデックス存在確認, L316 インデックス作成失敗, L327 ドキュメント空, L335 部分エラー, L341 外部例外 |

---

## 2. 正常系テストケース

| ID | テスト名 | 対象関数 | 期待結果 |
|----|---------|---------|---------|
| SO-001 | メイン保存正常（v2委譲） | store_custodian_output_to_opensearch | v2_stored_count を返す |
| SO-002 | skip_result_v2=True → 0 | store_custodian_output_to_opensearch | 0 |
| SO-003 | 違反データなし → 0 | store_custodian_output_to_opensearch | 0 |
| SO-004 | 履歴保存正常（エラーなし） | store_scan_history_v2 | True, status="completed" |
| SO-005 | 履歴保存（エラーあり） | store_scan_history_v2 | True, status="partial_failure" |
| SO-006 | account_id: scan_metadataから取得 | store_scan_history_v2 | scan_metadata の値を使用 |
| SO-007 | account_id: history_dataから取得 | store_scan_history_v2 | history_data の値を使用 |
| SO-008 | account_id: custodian出力フォールバック | store_scan_history_v2 | extract_metadata の値を使用 |
| SO-009 | v2ドキュメント保存正常 | store_scan_result_v2 | stored_count |
| SO-010 | インデックス未存在→作成→保存 | store_scan_result_v2 | stored_count |
| SO-011 | v2ドキュメント空 → 0 | store_scan_result_v2 | 0 |
| SO-012 | v2保存で部分エラー → 成功件数のみ返却 | store_scan_result_v2 | stored_count（成功分のみ） |
| SO-013 | 再エクスポート検証 | custodian_output | __all__ の全関数がインポート可能 |

### 2.1 store_custodian_output_to_opensearch テスト

```python
# test/unit/jobs/utils/test_store_operations.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestStoreCustodianOutput:
    """store_custodian_output_to_opensearch のテスト"""

    @pytest.mark.asyncio
    async def test_successful_v2_storage(self):
        """SO-001: v2保存に委譲して正常に保存件数を返す

        store_operations.py:L12-68 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        mock_client = AsyncMock()

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_violation_documents_from_output",
                   return_value=[{"doc": "violation1"}, {"doc": "violation2"}]), \
             patch("app.jobs.utils.store_operations.store_scan_result_v2",
                   new_callable=AsyncMock, return_value=5):

            result = await store_custodian_output_to_opensearch(
                "/output/dir", "job-001", "aws", "123456789"
            )

        # Assert
        assert result == 5

    @pytest.mark.asyncio
    async def test_skip_result_v2(self):
        """SO-002: skip_result_v2=True → v2保存スキップで0を返す

        store_operations.py:L62-74 の skip_result_v2 分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        mock_client = AsyncMock()

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_violation_documents_from_output",
                   return_value=[{"doc": "violation1"}]):

            result = await store_custodian_output_to_opensearch(
                "/output/dir", "job-002", "aws", skip_result_v2=True
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_no_violation_documents(self):
        """SO-003: 違反データなし → 早期リターンで0

        store_operations.py:L54-56 の空データ分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        mock_client = AsyncMock()

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_violation_documents_from_output",
                   return_value=[]):

            result = await store_custodian_output_to_opensearch(
                "/output/dir", "job-003", "aws"
            )

        # Assert
        assert result == 0
```

### 2.2 store_scan_history_v2 テスト

```python
class TestStoreScanHistoryV2:
    """store_scan_history_v2 のテスト"""

    def _create_mock_history_data(self, has_errors=False, account_id=None):
        """テスト用の history_data を生成するヘルパー"""
        data = {
            "basic_statistics": {"total_violations": 10},
            "policy_results": [{"name": "test-policy", "violations": 5}],
            "insights": ["insight1"],
            "scan_errors_summary": {
                "total_errors": 3 if has_errors else 0,
                "errors_by_type": {"permission": 2, "timeout": 1} if has_errors else {},
                "failed_policies": ["policy-x"] if has_errors else [],
            },
            "resource_overview": {"total_resources": 100},
        }
        if account_id:
            data["account_id"] = account_id
        return data

    def _create_base_patches(self, mock_client, history_data, account_id_source="metadata"):
        """共通パッチを生成するヘルパー

        account_id_source: "metadata" | "history" | "fallback"
        """
        mock_processor = MagicMock()
        mock_processor.process_scan_for_history_v2 = AsyncMock(return_value=history_data)
        mock_processor.result_formatter = MagicMock()
        mock_processor.result_formatter.create_execution_summary.return_value = {"summary": "exec"}
        mock_processor.result_formatter.create_insights_summary.return_value = {"summary": "insights"}
        mock_processor.result_formatter.create_policy_executions.return_value = []

        scan_metadata = {"cloud_provider": "aws"}
        if account_id_source == "metadata":
            scan_metadata["account_id"] = "acct-from-metadata"
        # "history": scan_metadataにaccount_id無し → history_dataから取得（L125-127）
        # "fallback": 両方にaccount_id無し → extract_metadata_from_output_dir（L130-134）

        return mock_processor, scan_metadata

    @pytest.mark.asyncio
    async def test_successful_history_no_errors(self):
        """SO-004: エラーなし時の正常な履歴保存

        store_operations.py:L81-274 の正常パス（has_errors=False）をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "created"}

        history_data = self._create_mock_history_data(has_errors=False)
        mock_processor, scan_metadata = self._create_base_patches(mock_client, history_data)

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp-001"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9.30"):

            result = await store_scan_history_v2(
                "job-004", "/output/dir", scan_metadata, "aws"
            )

        # Assert
        assert result is True
        # OpenSearch indexが呼ばれたことを確認
        mock_client.index.assert_called_once()
        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["index"] == "cspm-scan-history-v2"
        assert call_kwargs["body"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_successful_history_with_errors(self):
        """SO-005: エラーあり時の履歴保存（partial_failure）

        store_operations.py:L144-170 の has_errors=True 分岐をカバー。
        ResultFormatter による専用エラーサマリー生成パスを検証。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "updated"}

        history_data = self._create_mock_history_data(has_errors=True)
        mock_processor, scan_metadata = self._create_base_patches(mock_client, history_data)

        mock_error_formatter = MagicMock()
        mock_error_formatter.create_error_execution_summary.return_value = {"error": "exec"}
        mock_error_formatter.create_error_insights_summary.return_value = {"error": "insights"}

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.tasks.new_custodian_scan.results.result_formatter.ResultFormatter",
                   return_value=mock_error_formatter), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp-005"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9.30"):

            result = await store_scan_history_v2(
                "job-005", "/output/dir", scan_metadata, "aws"
            )

        # Assert
        assert result is True
        call_kwargs = mock_client.index.call_args[1]
        assert call_kwargs["body"]["status"] == "partial_failure"
        assert call_kwargs["body"]["error_summary"]["has_errors"] is True
        # エラー時は ResultFormatter の専用メソッドが呼ばれることを検証
        mock_error_formatter.create_error_execution_summary.assert_called_once()
        mock_error_formatter.create_error_insights_summary.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_id_from_scan_metadata(self):
        """SO-006: account_idをscan_metadataから取得（優先度1）

        store_operations.py:L120-122 の最優先パスをカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "created"}

        history_data = self._create_mock_history_data()
        mock_processor, scan_metadata = self._create_base_patches(
            mock_client, history_data, account_id_source="metadata"
        )

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp-006"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9.30"):

            result = await store_scan_history_v2(
                "job-006", "/output/dir", scan_metadata, "aws"
            )

        # Assert
        assert result is True
        body = mock_client.index.call_args[1]["body"]
        assert body["scan_scope"]["target_account_id"] == "acct-from-metadata"

    @pytest.mark.asyncio
    async def test_account_id_from_history_data(self):
        """SO-007: account_idをhistory_dataから取得（優先度2）

        store_operations.py:L125-127 のフォールバックパスをカバー。
        scan_metadataにaccount_idが無い場合。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "created"}

        history_data = self._create_mock_history_data(account_id="acct-from-history")
        mock_processor, _ = self._create_base_patches(
            mock_client, history_data, account_id_source="history"
        )
        # scan_metadataにaccount_id無し
        scan_metadata = {"cloud_provider": "aws"}

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp-007"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9.30"):

            result = await store_scan_history_v2(
                "job-007", "/output/dir", scan_metadata, "aws"
            )

        # Assert
        assert result is True
        body = mock_client.index.call_args[1]["body"]
        assert body["scan_scope"]["target_account_id"] == "acct-from-history"

    @pytest.mark.asyncio
    async def test_account_id_fallback_to_custodian_output(self):
        """SO-008: account_idをCustodian出力からフォールバック取得（優先度3）

        store_operations.py:L130-134 のフォールバックパスをカバー。
        scan_metadata・history_data両方にaccount_idが無い場合。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "created"}

        # account_id無しのhistory_data
        history_data = self._create_mock_history_data()
        mock_processor, _ = self._create_base_patches(
            mock_client, history_data, account_id_source="fallback"
        )
        scan_metadata = {"cloud_provider": "aws"}

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations.extract_metadata_from_output_dir",
                   return_value={"account_id": "acct-from-custodian"}), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp-008"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9.30"):

            result = await store_scan_history_v2(
                "job-008", "/output/dir", scan_metadata, "aws"
            )

        # Assert
        assert result is True
        body = mock_client.index.call_args[1]["body"]
        assert body["scan_scope"]["target_account_id"] == "acct-from-custodian"
```

### 2.3 store_scan_result_v2 テスト

```python
class TestStoreScanResultV2:
    """store_scan_result_v2 のテスト"""

    @pytest.mark.asyncio
    async def test_successful_v2_storage(self):
        """SO-009: v2ドキュメントの正常保存

        store_operations.py:L281-339 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        mock_indexer = AsyncMock()
        mock_indexer.check_index_exists.return_value = True
        mock_indexer.store_v2_documents.return_value = {"successful": 10, "errors": []}

        # Act
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   return_value=mock_indexer), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_v2_documents_from_output",
                   return_value=[{"doc": f"v2-{i}"} for i in range(10)]):

            result = await store_scan_result_v2(
                "/output/dir", "job-009", "aws", "123456789"
            )

        # Assert
        assert result == 10

    @pytest.mark.asyncio
    async def test_index_not_exists_create_then_store(self):
        """SO-010: インデックス未存在→作成→保存

        store_operations.py:L314-320 のインデックス作成分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        mock_indexer = AsyncMock()
        mock_indexer.check_index_exists.return_value = False
        mock_indexer.create_v2_index.return_value = True
        mock_indexer.store_v2_documents.return_value = {"successful": 3, "errors": []}

        # Act
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   return_value=mock_indexer), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_v2_documents_from_output",
                   return_value=[{"doc": "v2-1"}]):

            result = await store_scan_result_v2(
                "/output/dir", "job-010", "aws"
            )

        # Assert
        assert result == 3
        mock_indexer.create_v2_index.assert_called_once_with("cspm-scan-result-v2")

    @pytest.mark.asyncio
    async def test_no_v2_documents(self):
        """SO-011: v2ドキュメント空 → 0を返す

        store_operations.py:L327-329 の空データ分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        mock_indexer = AsyncMock()
        mock_indexer.check_index_exists.return_value = True

        # Act
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   return_value=mock_indexer), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_v2_documents_from_output",
                   return_value=[]):

            result = await store_scan_result_v2(
                "/output/dir", "job-011", "aws"
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_v2_storage_partial_errors(self):
        """SO-012: v2保存で部分エラー → 成功件数のみ返却しwarningログ出力

        store_operations.py:L335-336 の部分エラー分岐をカバー。
        一部ドキュメントの保存に失敗した場合でも成功件数を返す。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        mock_indexer = AsyncMock()
        mock_indexer.check_index_exists.return_value = True
        mock_indexer.store_v2_documents.return_value = {
            "successful": 8,
            "errors": [{"doc_id": "err-1", "error": "mapping conflict"}]
        }

        # Act
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   return_value=mock_indexer), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger, \
             patch("app.jobs.utils.store_operations._extract_v2_documents_from_output",
                   return_value=[{"doc": f"v2-{i}"} for i in range(10)]):

            result = await store_scan_result_v2(
                "/output/dir", "job-012", "aws"
            )

        # Assert
        assert result == 8
        # warningログが出力されることを確認
        mock_logger_instance = MockLogger.return_value
        warning_calls = [
            c for c in mock_logger_instance.method_calls
            if c[0] == "warning"
        ]
        assert len(warning_calls) > 0, "部分エラー時にwarningログが出力されるべき"
```

### 2.4 custodian_output 再エクスポート検証

```python
class TestCustodianOutputReExport:
    """custodian_output.py の再エクスポート検証"""

    def test_all_exports_importable(self):
        """SO-013: __all__ に定義された全関数がインポート可能

        custodian_output.py の再エクスポートファサードが
        全分割モジュールの関数を正しく公開していることを検証。
        """
        # Arrange / Act
        import app.jobs.utils.custodian_output as co

        # Assert
        for name in co.__all__:
            assert hasattr(co, name), f"{name} が custodian_output からインポートできません"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 対象関数 | 期待結果 |
|----|---------|---------|---------|
| SO-E01 | クライアントNone → 0 | store_custodian_output_to_opensearch | 0 |
| SO-E02 | v2保存例外 → 0 | store_custodian_output_to_opensearch | 0 |
| SO-E03 | 外部例外 → 0 | store_custodian_output_to_opensearch | 0 |
| SO-E04 | 履歴保存例外 → False | store_scan_history_v2 | False |
| SO-E05 | OpenSearch保存結果が非成功 → False | store_scan_history_v2 | False |
| SO-E06 | account_idフォールバック例外 → "unknown" | store_scan_history_v2 | True（account_id="unknown"で継続） |
| SO-E07 | インデックス作成失敗 → 0 | store_scan_result_v2 | 0 |
| SO-E08 | v2保存例外 → 0 | store_scan_result_v2 | 0 |
| SO-E09 | 履歴v2クライアントNone → False | store_scan_history_v2 | False |

### 3.1 異常系テスト

```python
class TestStoreOperationsErrors:
    """store_operations エラーテスト"""

    @pytest.mark.asyncio
    async def test_output_client_none(self):
        """SO-E01: OpenSearchクライアントNone → 0

        store_operations.py:L41-43 のクライアントNullチェックをカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None), \
             patch("app.jobs.utils.store_operations.TaskLogger"):
            result = await store_custodian_output_to_opensearch(
                "/output/dir", "job-e01", "aws"
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_output_v2_store_exception(self):
        """SO-E02: v2保存で例外 → 0

        store_operations.py:L69-71 のv2保存例外分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        mock_client = AsyncMock()

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.utils.store_operations._extract_violation_documents_from_output",
                   return_value=[{"doc": "v1"}]), \
             patch("app.jobs.utils.store_operations.store_scan_result_v2",
                   new_callable=AsyncMock, side_effect=RuntimeError("v2 storage failed")):

            result = await store_custodian_output_to_opensearch(
                "/output/dir", "job-e02", "aws"
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_output_outer_exception(self):
        """SO-E03: 外部例外 → 0

        store_operations.py:L76-78 の最外部exceptをカバー。
        get_opensearch_client自体が例外を投げるケース。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, side_effect=RuntimeError("connection refused")), \
             patch("app.jobs.utils.store_operations.TaskLogger"):
            result = await store_custodian_output_to_opensearch(
                "/output/dir", "job-e03", "aws"
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_history_v2_exception(self):
        """SO-E04: store_scan_history_v2 で外部例外 → False

        store_operations.py:L276-278 の最外部exceptをカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        # Act
        # ResultProcessor のインスタンス化時に例外が発生するケース
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   side_effect=RuntimeError("processor initialization failed")):

            result = await store_scan_history_v2(
                "job-e04", "/output/dir", {"cloud_provider": "aws"}, "aws"
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_history_v2_save_not_success(self):
        """SO-E05: OpenSearch保存結果が"created"/"updated"以外 → False

        store_operations.py:L272-274 の非成功レスポンス分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "noop"}

        mock_processor = MagicMock()
        mock_processor.process_scan_for_history_v2 = AsyncMock(return_value={
            "basic_statistics": {},
            "policy_results": [],
            "insights": [],
            "scan_errors_summary": {"total_errors": 0},
            "resource_overview": {},
        })
        mock_processor.result_formatter = MagicMock()
        mock_processor.result_formatter.create_execution_summary.return_value = {}
        mock_processor.result_formatter.create_insights_summary.return_value = {}
        mock_processor.result_formatter.create_policy_executions.return_value = []

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9"):

            result = await store_scan_history_v2(
                "job-e05", "/output/dir", {"account_id": "acct"}, "aws"
            )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_history_v2_account_id_fallback_exception(self):
        """SO-E06: account_idフォールバック取得で例外 → "unknown"で継続

        store_operations.py:L135-136 のフォールバック例外分岐をカバー。
        scan_metadata・history_data両方にaccount_idが無く、
        extract_metadata_from_output_dirも例外を投げるケース。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "created"}

        mock_processor = MagicMock()
        mock_processor.process_scan_for_history_v2 = AsyncMock(return_value={
            "basic_statistics": {},
            "policy_results": [],
            "insights": [],
            "scan_errors_summary": {"total_errors": 0},
            "resource_overview": {},
        })
        mock_processor.result_formatter = MagicMock()
        mock_processor.result_formatter.create_execution_summary.return_value = {}
        mock_processor.result_formatter.create_insights_summary.return_value = {}
        mock_processor.result_formatter.create_policy_executions.return_value = []

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations.extract_metadata_from_output_dir",
                   side_effect=RuntimeError("metadata extraction failed")), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9"):

            result = await store_scan_history_v2(
                "job-e06", "/output/dir", {}, "aws"
            )

        # Assert
        assert result is True
        body = mock_client.index.call_args[1]["body"]
        # フォールバック例外時は "unknown" のまま
        assert body["scan_scope"]["target_account_id"] == "unknown"

    @pytest.mark.asyncio
    async def test_result_v2_index_creation_failure(self):
        """SO-E07: v2インデックス作成失敗 → 0

        store_operations.py:L316-318 のインデックス作成失敗分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        mock_indexer = AsyncMock()
        mock_indexer.check_index_exists.return_value = False
        mock_indexer.create_v2_index.return_value = False

        # Act
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   return_value=mock_indexer), \
             patch("app.jobs.utils.store_operations.TaskLogger"):

            result = await store_scan_result_v2(
                "/output/dir", "job-e07", "aws"
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_result_v2_outer_exception(self):
        """SO-E08: store_scan_result_v2 で外部例外 → 0

        store_operations.py:L341-343 の最外部exceptをカバー。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        # Act
        # OpenSearchV2Indexer のインスタンス化時に例外が発生するケース
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   side_effect=RuntimeError("indexer initialization failed")), \
             patch("app.jobs.utils.store_operations.TaskLogger"):

            result = await store_scan_result_v2(
                "/output/dir", "job-e08", "aws"
            )

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    async def test_history_v2_client_none(self):
        """SO-E09: store_scan_history_v2 で OpenSearchクライアントがNone → False

        store_operations.py:L259 で get_opensearch_client() が None を返した場合、
        L262 の os_client.index(...) で AttributeError が発生し、
        L276 の except ブロックで False を返す。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        mock_processor = MagicMock()
        mock_processor.process_scan_for_history_v2 = AsyncMock(return_value={
            "basic_statistics": {},
            "policy_results": [],
            "insights": [],
            "scan_errors_summary": {"total_errors": 0},
            "resource_overview": {},
        })
        mock_processor.result_formatter = MagicMock()
        mock_processor.result_formatter.create_execution_summary.return_value = {}
        mock_processor.result_formatter.create_insights_summary.return_value = {}
        mock_processor.result_formatter.create_policy_executions.return_value = []

        # Act
        # get_opensearch_client が None を返す → os_client.index() で AttributeError
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None), \
             patch("app.jobs.utils.store_operations.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9"):

            result = await store_scan_history_v2(
                "job-e09", "/output/dir", {"account_id": "acct"}, "aws"
            )

        # Assert
        assert result is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SO-SEC-01a | エラーログにAPIキー非露出（store_output 外側except L77） | APIキーを含む例外 | store_custodian_output_to_opensearch 外側exceptのログにAPIキーが含まれない |
| SO-SEC-01d | エラーログにAPIキー非露出（store_output 内側except L70） | APIキーを含む例外 | store_custodian_output_to_opensearch 内側v2_errorのログにAPIキーが含まれない |
| SO-SEC-01b | エラーログにAPIキー非露出（history_v2） | APIキーを含む例外 | store_scan_history_v2 のログにAPIキーが含まれない |
| SO-SEC-01c | エラーログにAPIキー非露出（result_v2） | APIキーを含む例外 | store_scan_result_v2 のログにAPIキーが含まれない |
| SO-SEC-02 | ログインジェクション耐性 | CRLFを含むjob_id | クラッシュせず処理完了 |
| SO-SEC-03 | scan_metadata内の機密情報がログに露出しない | 機密情報を含むmetadata | logger出力に機密情報が含まれないことを確認 |

```python
@pytest.mark.security
class TestStoreOperationsSecurity:
    """store_operations セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SO-SEC-01a: store_operations.py:L77 で str(e) を"
               "そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_error_log_store_output_outer(self):
        """SO-SEC-01a: store_custodian_output_to_opensearch 外側except(L77)のAPIキー非露出

        store_operations.py:L76-78 の外側 except Exception as e で
        get_opensearch_client 自体が例外を投げるケース。
        L77 の logger.error(f"...{str(e)}") によりAPIキーが露出する。

        [EXPECTED_TO_FAIL] str(e) をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError(f"Auth failed: key={fake_key}")), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger:

            await store_custodian_output_to_opensearch(
                "/output/dir", "job-sec01a", "aws"
            )

        # Assert
        # 全ログ出力にAPIキーが含まれないことを検証
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call}"
            )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SO-SEC-01d: store_operations.py:L70 で str(v2_error) を"
               "そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_error_log_store_output_inner(self):
        """SO-SEC-01d: store_custodian_output_to_opensearch 内側except(L70)のAPIキー非露出

        store_operations.py:L69-71 の内側 except Exception as v2_error で
        store_scan_result_v2 が例外を投げるケース。
        L70 の logger.error(f"...{str(v2_error)}") によりAPIキーが露出する。

        [EXPECTED_TO_FAIL] str(v2_error) をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"
        mock_client = AsyncMock()

        # Act
        # クライアント取得成功 → 違反データあり → store_scan_result_v2 で例外（L69の内側try）
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger, \
             patch("app.jobs.utils.store_operations._extract_violation_documents_from_output",
                   return_value=[{"doc": "v1"}]), \
             patch("app.jobs.utils.store_operations.store_scan_result_v2",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError(f"Auth failed: key={fake_key}")):

            await store_custodian_output_to_opensearch(
                "/output/dir", "job-sec01d", "aws"
            )

        # Assert
        # 全ログ出力にAPIキーが含まれないことを検証
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call}"
            )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SO-SEC-01b: store_operations.py:L277 で str(e) を"
               "そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_error_log_history_v2(self):
        """SO-SEC-01b: store_scan_history_v2 のエラーログにAPIキー非露出

        store_operations.py:L277 の logger.error(f"...{str(e)}") により、
        例外メッセージにAPIキー等が含まれる場合にログに露出する。

        [EXPECTED_TO_FAIL] str(e) をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"

        # Act
        # ResultProcessor インスタンス化で例外（APIキー含む）が発生するケース
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger, \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   side_effect=RuntimeError(f"Auth failed: key={fake_key}")):

            await store_scan_history_v2(
                "job-sec01b", "/output/dir", {}, "aws"
            )

        # Assert
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call}"
            )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SO-SEC-01c: store_operations.py:L342 で str(e) を"
               "そのままログに含めるため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_error_log_result_v2(self):
        """SO-SEC-01c: store_scan_result_v2 のエラーログにAPIキー非露出

        store_operations.py:L342 の logger.error(f"...{str(e)}") により、
        例外メッセージにAPIキー等が含まれる場合にログに露出する。

        [EXPECTED_TO_FAIL] str(e) をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_result_v2

        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"

        # Act
        # OpenSearchV2Indexer インスタンス化で例外（APIキー含む）が発生するケース
        with patch("app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer",
                   side_effect=RuntimeError(f"Auth failed: key={fake_key}")), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger:

            await store_scan_result_v2(
                "/output/dir", "job-sec01c", "aws"
            )

        # Assert
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call}"
            )

    @pytest.mark.asyncio
    async def test_log_injection_resilience(self):
        """SO-SEC-02: CRLFを含むjob_idでクラッシュしない

        store_operations.py:L36 の TaskLogger にCRLFを含む
        job_idが渡された場合でも処理を完了することを確認。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_custodian_output_to_opensearch

        malicious_job_id = "job\r\nInjected-Header: malicious"

        # Act - 例外が発生しないこと
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger:
            result = await store_custodian_output_to_opensearch(
                "/output/dir", malicious_job_id, "aws"
            )

        # Assert
        assert result == 0
        # TaskLoggerに渡されたjob_idにCRLFが含まれてもクラッシュしないことを確認
        # 注: 現行実装はCRLFのサニタイズを行わないため、ログフレームワーク側の
        #      インジェクション耐性に依存する。ここではクラッシュ回避のみを検証。

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SO-SEC-03: store_operations.py:L122/L127/L134 で account_id を"
               "そのままログに出力するため、account_idに機密情報が紛れ込んだ場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_scan_metadata_secrets_not_in_log(self):
        """SO-SEC-03: scan_metadata内の機密情報がログに露出しない

        store_operations.py:L122 の logger.info(f"...account_id取得: {account_id}")
        により、account_idの値がそのままログに出力される。

        [EXPECTED_TO_FAIL] account_id をそのままログに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.store_operations import store_scan_history_v2

        sensitive_account_id = "987654321012"  # 12桁のAWSアカウントID形式
        mock_client = AsyncMock()
        mock_client.index.return_value = {"result": "created"}

        mock_processor = MagicMock()
        mock_processor.process_scan_for_history_v2 = AsyncMock(return_value={
            "basic_statistics": {},
            "policy_results": [],
            "insights": [],
            "scan_errors_summary": {"total_errors": 0},
            "resource_overview": {},
        })
        mock_processor.result_formatter = MagicMock()
        mock_processor.result_formatter.create_execution_summary.return_value = {}
        mock_processor.result_formatter.create_insights_summary.return_value = {}
        mock_processor.result_formatter.create_policy_executions.return_value = []

        # Act
        with patch("app.core.clients.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.store_operations.TaskLogger") as MockLogger, \
             patch("app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor",
                   return_value=mock_processor), \
             patch("app.jobs.utils.store_operations._generate_policy_fingerprint",
                   return_value="fp"), \
             patch("app.jobs.utils.store_operations._get_custodian_version",
                   return_value="0.9"):

            await store_scan_history_v2(
                "job-sec03", "/output/dir",
                {"account_id": sensitive_account_id}, "aws"
            )

        # Assert
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert sensitive_account_id not in call_str, (
                f"ログにaccount_id機密情報が露出: {call}"
            )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

> **注記**: `store_operations.py` はモジュールレベルで `TaskLogger`、`_extract_violation_documents_from_output`、`_extract_v2_documents_from_output`、`_sanitize_resource_for_opensearch`、`_get_custodian_version`、`_generate_policy_fingerprint`、`extract_metadata_from_output_dir` をインポート（L2-9）する。これらは `app.jobs.utils.store_operations.関数名` でパッチ可能。一方 `get_opensearch_client`、`ResultProcessor`、`ResultFormatter`、`OpenSearchV2Indexer` は関数内の動的importであるため、パッチターゲットはソースモジュール（`app.core.clients`、`app.jobs.tasks.new_custodian_scan.result_processor`、`app.jobs.tasks.new_custodian_scan.results.result_formatter`、`app.jobs.utils.opensearch_v2_indexer`）を指定する。conftest.py は `test/unit/jobs/utils/conftest.py`（#17aで定義）を共有する。

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

_TARGET_MODULES = (
    "app.jobs.utils.store_operations",
    "app.jobs.utils.custodian_output",
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

> **注記**: conftest.py は #17a〜#17h と共有予定。実装時には既存の `_TARGET_MODULES` タプルに `"app.jobs.utils.store_operations"` と `"app.jobs.utils.custodian_output"` を追加する形で統合する。

---

## 6. テスト実行例

```bash
# ストレージ操作テストのみ実行
pytest test/unit/jobs/utils/test_store_operations.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_store_operations.py::TestStoreScanHistoryV2 -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_store_operations.py \
  --cov=app.jobs.utils.store_operations \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_store_operations.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 13 | SO-001 〜 SO-013 |
| 異常系 | 9 | SO-E01 〜 SO-E09 |
| セキュリティ | 6 | SO-SEC-01a/b/c/d, SO-SEC-02, SO-SEC-03 |
| **合計** | **28** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestStoreCustodianOutput` | SO-001〜SO-003 | 3 |
| `TestStoreScanHistoryV2` | SO-004〜SO-008 | 5 |
| `TestStoreScanResultV2` | SO-009〜SO-012 | 4 |
| `TestCustodianOutputReExport` | SO-013 | 1 |
| `TestStoreOperationsErrors` | SO-E01〜SO-E09 | 9 |
| `TestStoreOperationsSecurity` | SO-SEC-01a/b/c/d, SO-SEC-02, SO-SEC-03 | 6 |

### 7.1 予想失敗テスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| SO-SEC-01a | store_operations.py:L77 で `str(e)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する（外側except） | ログ出力から `str(e)` を除去するか、マスク処理を導入する |
| SO-SEC-01d | store_operations.py:L70 で `str(v2_error)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する（内側except） | 同上 |
| SO-SEC-01b | store_operations.py:L277 で `str(e)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する | 同上 |
| SO-SEC-01c | store_operations.py:L342 で `str(e)` をそのままログに含めるため、例外メッセージにAPIキーが含まれる場合にログに露出する | 同上 |
| SO-SEC-03 | store_operations.py:L122/L127/L134 で `account_id` をそのままログに出力するため、機密情報が紛れ込んだ場合にログに露出する | ログ出力で account_id をマスク（例: 先頭4桁のみ表示）する |

### xfail 解除手順

1. `store_operations.py` の `logger.error(f"...{str(e)}")` パターン（L70, L77, L277, L342）で例外メッセージをマスクまたは汎用メッセージに置換
2. `store_operations.py` の `logger.info(f"...{account_id}")` パターン（L122, L127, L134）で account_id をマスク処理
3. 上記修正後、SO-SEC-01a/b/c/d および SO-SEC-03 の `@pytest.mark.xfail(...)` デコレータを削除
4. テスト実行で PASS を確認

### 注意事項

- `pytest-asyncio` パッケージが必要（全async関数）
- OpenSearchクライアント・ResultProcessor・ResultFormatter・OpenSearchV2Indexer は全てモック化
- モジュールレベルimport（L2-9）の関数は `app.jobs.utils.store_operations.関数名` でパッチ
- 動的import（関数内 `from ... import`）はローカル変数にバインドされるため、**ソースモジュール**をパッチする必要がある：
  - `get_opensearch_client` → `app.core.clients.get_opensearch_client`
  - `ResultProcessor` → `app.jobs.tasks.new_custodian_scan.result_processor.ResultProcessor`
  - `ResultFormatter` → `app.jobs.tasks.new_custodian_scan.results.result_formatter.ResultFormatter`
  - `OpenSearchV2Indexer` → `app.jobs.utils.opensearch_v2_indexer.OpenSearchV2Indexer`
- `store_scan_history_v2` 内の `ExecutionError` クラス定義（L152-157）はテスト不要（内部ヘルパー）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `store_scan_history_v2` の history_document 構築（L187-256）は70行の大規模辞書リテラル | 全フィールドの個別検証は冗長 | 主要フィールド（status, scan_scope.target_account_id, error_summary.has_errors）のみ検証 |
| 2 | `ResultProcessor.process_scan_for_history_v2` の戻り値構造が複雑 | モックデータの正確な再現が困難 | ヘルパーメソッドで最小限のモックデータを生成 |
| 3 | `store_scan_history_v2` 内のインラインクラス `ExecutionError`（L152-157）はテスト対象外 | エラーオブジェクト生成ロジックの検証漏れ | `ResultFormatter.create_error_execution_summary` がモック経由で呼ばれることを検証 |
| 4 | `custodian_output.py` は純粋な再エクスポートのためロジックテストなし | インポート互換性のみ検証 | SO-013 で `__all__` の全関数がインポート可能であることを確認 |
| 5 | `str(e)` / `str(v2_error)` がログに直接含まれる（L70, L77, L277, L342） | 機密情報がログに露出するリスク | SO-SEC-01a/b/c/d で各経路を個別に記録（`xfail`）。マスク処理の導入を推奨 |
| 6 | `account_id` がログに直接出力される（L122, L127, L134） | アカウントIDがログに露出 | SO-SEC-03 で記録（`xfail`）。マスク処理の導入を推奨 |
