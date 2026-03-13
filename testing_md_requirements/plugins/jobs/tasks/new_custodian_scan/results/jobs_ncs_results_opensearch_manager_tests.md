# jobs/tasks/new_custodian_scan/results OpenSearch管理 テストケース

## 1. 概要

`results/` サブディレクトリのOpenSearch管理ファイル（`opensearch_manager.py`）のテスト仕様書。OpenSearchへの結果保存・データ取得・推奨事項マッピング・UUID/severity抽出を担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `OpenSearchManager` | `opensearch_manager.py` | 506 | OpenSearchへの結果保存・インデックス検索・推奨事項マッピング管理 |

### 1.2 カバレッジ目標: 85%

> **注記**: 全公開メソッド（`_create_region_metadata`を除く）がasyncのため、pytest-asyncio必須。外部依存（OpenSearchクライアント、store_operations、account_id_extractor）はすべてモック。store_scan_result_v2は遅延importのため個別パッチが必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/results/opensearch_manager.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py` |

### 1.4 補足情報

#### 依存関係

```
opensearch_manager.py (OpenSearchManager)
  ──→ TaskLogger（ログ）
  ──→ app.core.clients.get_opensearch_client（OpenSearchクライアント取得）
  ──→ app.jobs.utils.store_operations.store_custodian_output_to_opensearch（保存処理）
  ──→ app.jobs.utils.store_operations.store_scan_result_v2（遅延import、result-v2保存）
  ──→ app.jobs.utils.account_id_extractor.extract_account_id_with_fallback（アカウントID抽出）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| async保存メソッド | AsyncMockでOpenSearchクライアント・store_operationsをモック |
| `_create_region_metadata` | 同期メソッドのため直接呼び出し（モック不要） |
| 遅延import（store_scan_result_v2） | `{STORE_OPS_MODULE}.store_scan_result_v2`をAsyncMockでパッチ |

#### 主要分岐マップ

| メソッド | 行番号 | 条件 | 分岐数 |
|---------|--------|------|--------|
| `store_multi_region_results` | L55, L62, L67, L73, L75-86 | forループ, custodian_output_dir有無, account_id有効性, 遅延import(store_scan_result_v2), try/except | 5 |
| `_store_single_region_result` | L113, L118, L122-145 | error有無, output_dir有無, try/except | 3 |
| `_create_region_metadata` | L182, L192, L202, L215, L220 | scan_statistics, has_error, detailed_errors, policy_errors, missing_resources | 5 |
| `extract_account_id_from_opensearch` | L257, L260 | hits>0, account_id有効, try/except | 3 |
| `get_recommendation_mappings` | L278, L297 | client有無, uuid有無, try/except | 3 |
| `get_recommendation_title_from_policy_name` | L322, L328, L346, L350 | policy-prefix, client有無, hits有無, fallback | 4 |
| `_get_title_from_scan_result` | L368, L393, L396, L400, L403 | client有無, hits有無, title有無, description有無, 文字数 | 5 |
| `extract_recommendation_uuid` | L444, L451 | hits>0, uuid有無, try/except | 3 |
| `extract_severity` | L494, L500 | hits>0, severity有無, try/except | 3 |

---

## 2. 正常系テストケース

### OpenSearchManager 基本操作 (OSM)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OSM-001 | 初期化 | job_id | job_id保持・logger生成 |
| OSM-002 | store_multi_region_results custodian_output_dir無し | region_results, None | 各リージョン保存合計 |
| OSM-003 | store_multi_region_results custodian_output_dir有り（metadata account_id） | account_id有効 | リージョン+result-v2合計 |
| OSM-004 | store_multi_region_results custodian_output_dir有り（fallback account_id） | account_id="unknown" | extract_account_id_with_fallback呼び出し |
| OSM-005 | _store_single_region_result 正常 | 正常result | store_custodian呼び出し・件数返却 |
| OSM-006 | _store_single_region_result エラーリージョンスキップ | error有り | 0返却 |
| OSM-007 | _store_single_region_result output_dir無しスキップ | output_dir無し | 0返却 |
| OSM-008 | _create_region_metadata 基本 | stats無し,error無し | 基本フィールドのみ |
| OSM-009 | _create_region_metadata scan_statistics有り | stats有り | 統計フィールド追加 |
| OSM-010 | _create_region_metadata エラー詳細有り | has_error+detailed_errors | error_details追加 |
| OSM-011 | _create_region_metadata policy_errors有り | policy_errors | error_details.policy_errors追加 |
| OSM-012 | _create_region_metadata missing_resources有り | missing_resources | error_details.missing_resources追加 |
| OSM-013 | _create_region_metadata エラーだがdetailed_errors空 | has_error,詳細空 | error_details基本のみ |
| OSM-014 | extract_account_id_from_opensearch ヒット有り | 1件ヒット | account_id返却 |
| OSM-015 | extract_account_id_from_opensearch ヒット無し | 0件 | "unknown" |
| OSM-016 | extract_account_id_from_opensearch account_id空 | account_id=None | "unknown" |
| OSM-017 | get_recommendation_mappings 正常 | 複数ヒット | UUID→{title,severity}マッピング |
| OSM-018 | get_recommendation_mappings client None | None返却 | {} |
| OSM-019 | get_recommendation_mappings uuid無しスキップ | uuid欠落hit | マッピングに含まれない |
| OSM-020 | get_recommendation_title_from_policy_name recommendations検索成功 | policy-a-4 | タイトル返却 |
| OSM-021 | get_recommendation_title_from_policy_name fallback | recommendationsに無し | _get_title_from_scan_result呼び出し |
| OSM-022 | get_recommendation_title_from_policy_name 非policyプレフィックス | "custom-rule" | "" |
| OSM-023 | get_recommendation_title_from_policy_name client None | None返却 | "" |
| OSM-024 | _get_title_from_scan_result title有り | title存在 | title返却 |
| OSM-025 | _get_title_from_scan_result description代替 | title無し,description有り | description返却 |
| OSM-026 | _get_title_from_scan_result description切り詰め | 51文字以上 | 50文字+"..." |
| OSM-027 | _get_title_from_scan_result 該当無し | 0件ヒット | "" |
| OSM-028 | _get_title_from_scan_result client None | None返却 | "" |
| OSM-029 | extract_recommendation_uuid ヒット有り | uuid存在 | uuid返却 |
| OSM-030 | extract_recommendation_uuid ヒット無し | 0件 | "unknown-{policy_name}" |
| OSM-030A | extract_recommendation_uuid uuid=None | ヒット有り,uuid空 | "unknown-{policy_name}" |
| OSM-031 | extract_severity ヒット有り | severity存在 | severity返却 |
| OSM-032 | extract_severity ヒット無し | 0件 | "Medium" |
| OSM-032A | extract_severity severity=None | ヒット有り,severity空 | "Medium" |

### 2.1 基本操作・保存テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

OSM_MODULE = "app.jobs.tasks.new_custodian_scan.results.opensearch_manager"
STORE_OPS_MODULE = "app.jobs.utils.store_operations"


class TestOpenSearchManagerInit:
    """OpenSearchManager初期化テスト"""

    def test_init(self, opensearch_manager):
        """OSM-001: 初期化

        opensearch_manager.py:L22-30 をカバー。
        """
        # Assert
        assert opensearch_manager.job_id == "test-job-id"
        assert opensearch_manager.logger is not None


@pytest.mark.asyncio
class TestStoreMultiRegionResults:
    """マルチリージョン結果保存テスト"""

    async def test_without_custodian_output_dir(
        self, opensearch_manager, mock_store_ops, mock_account_extractor
    ):
        """OSM-002: store_multi_region_results custodian_output_dir無し

        opensearch_manager.py:L54-59 のforループのみ実行、L62の分岐不成立をカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "output_dir": "/out/us-east-1"},
            {"region": "eu-west-1", "output_dir": "/out/eu-west-1"},
        ]
        mock_store_ops.return_value = 3

        # Act
        result = await opensearch_manager.store_multi_region_results(
            region_results, {"account_id": "123456"}, "AWS"
        )

        # Assert
        assert result == 6  # 3 * 2リージョン
        assert mock_store_ops.call_count == 2
        # 各リージョン呼び出しでskip_result_v2=Trueが伝播されることを確認
        for call in mock_store_ops.call_args_list:
            assert call[1]["skip_result_v2"] is True

    async def test_with_output_dir_metadata_account(
        self, opensearch_manager, mock_store_ops,
        mock_account_extractor, mock_store_scan_result_v2
    ):
        """OSM-003: store_multi_region_results custodian_output_dir有り（metadata account_id）

        opensearch_manager.py:L62-84 のcustodian_output_dir有り分岐をカバー。
        account_idがscan_metadataから取得される（L66-67条件不成立→L70-71）。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "output_dir": "/out/us-east-1"}]
        scan_metadata = {"account_id": "123456"}
        mock_store_ops.return_value = 3
        mock_store_scan_result_v2.return_value = 5

        # Act
        result = await opensearch_manager.store_multi_region_results(
            region_results, scan_metadata, "AWS",
            custodian_output_dir="/out"
        )

        # Assert
        assert result == 8  # 3(リージョン) + 5(result-v2)
        mock_store_scan_result_v2.assert_called_once()
        # metadata由来のaccount_idが使用されたことを確認
        call_kwargs = mock_store_scan_result_v2.call_args[1]
        assert call_kwargs["account_id"] == "123456"

    async def test_with_output_dir_fallback_account(
        self, opensearch_manager, mock_store_ops,
        mock_account_extractor, mock_store_scan_result_v2
    ):
        """OSM-004: store_multi_region_results custodian_output_dir有り（fallback account_id）

        opensearch_manager.py:L67-69 のaccount_id=="unknown"→extract_account_id_with_fallback
        呼び出しをカバー。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "output_dir": "/out/us-east-1"}]
        scan_metadata = {"account_id": "unknown"}
        mock_store_ops.return_value = 3
        mock_store_scan_result_v2.return_value = 5
        mock_account_extractor.return_value = "789012"

        # Act
        result = await opensearch_manager.store_multi_region_results(
            region_results, scan_metadata, "AWS",
            custodian_output_dir="/out"
        )

        # Assert
        assert result == 8
        # フォールバック呼び出しを確認（custodian_output_dir引数）
        mock_account_extractor.assert_any_call("/out", "test-job-id")


@pytest.mark.asyncio
class TestStoreSingleRegionResult:
    """単一リージョン結果保存テスト"""

    async def test_normal(
        self, opensearch_manager, mock_store_ops, mock_account_extractor
    ):
        """OSM-005: _store_single_region_result 正常

        opensearch_manager.py:L122-143 の正常保存フローをカバー。
        """
        # Arrange
        result = {"region": "us-east-1", "output_dir": "/out/us-east-1"}
        mock_store_ops.return_value = 3

        # Act
        count = await opensearch_manager._store_single_region_result(
            result, {"total_regions": 1}, "AWS"
        )

        # Assert
        assert count == 3
        mock_store_ops.assert_called_once()

    async def test_error_region_skip(self, opensearch_manager):
        """OSM-006: _store_single_region_result エラーリージョンスキップ

        opensearch_manager.py:L113-115 の"error"チェックでスキップをカバー。
        """
        # Arrange
        result = {"region": "us-east-1", "error": "timeout"}

        # Act
        count = await opensearch_manager._store_single_region_result(
            result, {}, "AWS"
        )

        # Assert
        assert count == 0

    async def test_no_output_dir_skip(self, opensearch_manager):
        """OSM-007: _store_single_region_result output_dir無しスキップ

        opensearch_manager.py:L118-120 のoutput_dir無しチェックでスキップをカバー。
        """
        # Arrange
        result = {"region": "us-east-1", "violations_count": 3}

        # Act
        count = await opensearch_manager._store_single_region_result(
            result, {}, "AWS"
        )

        # Assert
        assert count == 0
```

### 2.2 メタデータ構築テスト

```python
class TestCreateRegionMetadata:
    """リージョンメタデータ構築テスト"""

    def test_basic(self, opensearch_manager):
        """OSM-008: _create_region_metadata 基本

        opensearch_manager.py:L167-178 の基本フィールド構築をカバー。
        scan_statistics無し、error無し。
        """
        # Arrange
        base_metadata = {
            "cloud_provider": "aws", "total_regions": 3,
            "completed_regions": 2, "failed_regions": 1,
            "scan_start_time": "2024-01-01T00:00:00Z",
            "scan_end_time": "2024-01-01T00:10:00Z"
        }
        result = {"violations_count": 5, "return_code": 0}

        # Act
        metadata = opensearch_manager._create_region_metadata(
            base_metadata, result, "us-east-1"
        )

        # Assert
        assert metadata["region"] == "us-east-1"
        assert metadata["violations_count"] == 5
        assert metadata["cloud_provider"] == "aws"
        assert "total_scanned" not in metadata
        assert "error_details" not in metadata

    def test_with_scan_statistics(self, opensearch_manager):
        """OSM-009: _create_region_metadata scan_statistics有り

        opensearch_manager.py:L182-188 のscan_statistics分岐をカバー。
        """
        # Arrange
        result = {
            "violations_count": 3,
            "scan_statistics": {
                "total_scanned": 100, "compliance_rate": 97.0,
                "resource_type": "aws.ec2",
                "scan_details": {"compliant_resources": 97}
            }
        }

        # Act
        metadata = opensearch_manager._create_region_metadata(
            {}, result, "us-east-1"
        )

        # Assert
        assert metadata["total_scanned"] == 100
        assert metadata["compliance_rate"] == 97.0
        assert metadata["resource_type"] == "aws.ec2"
        assert metadata["compliant_resources"] == 97

    def test_with_error_details(self, opensearch_manager):
        """OSM-010: _create_region_metadata エラー詳細有り

        opensearch_manager.py:L192-228 のhas_error+detailed_errors分岐をカバー。
        full_tracebackは1000文字で切り詰め。
        """
        # Arrange
        result = {
            "violations_count": 0,
            "execution_status": {
                "has_error": True,
                "error_type": "PolicyExecutionError",
                "detailed_errors": [{
                    "error_message": "Resource not found",
                    "full_traceback": "Traceback..." + "x" * 1500,
                    "suggested_fix": "Check resource ARN",
                    "log_size": 2048,
                    "policy_name": "policy-a-1"
                }]
            }
        }

        # Act
        metadata = opensearch_manager._create_region_metadata(
            {}, result, "us-east-1"
        )

        # Assert
        assert metadata["error_details"]["has_error"] is True
        assert metadata["error_details"]["error_type"] == "PolicyExecutionError"
        assert metadata["error_details"]["error_message"] == "Resource not found"
        assert len(metadata["error_details"]["full_traceback"]) <= 1000
        assert metadata["error_details"]["policy_name"] == "policy-a-1"

    def test_with_policy_errors(self, opensearch_manager):
        """OSM-011: _create_region_metadata policy_errors有り

        opensearch_manager.py:L214-216 のpolicy_errors分岐をカバー。
        """
        # Arrange
        result = {
            "violations_count": 0,
            "execution_status": {
                "has_error": True, "error_type": "PolicyError",
                "policy_errors": [{"policy": "p1", "error": "invalid"}]
            }
        }

        # Act
        metadata = opensearch_manager._create_region_metadata(
            {}, result, "us-east-1"
        )

        # Assert
        assert metadata["error_details"]["policy_errors"] == [
            {"policy": "p1", "error": "invalid"}
        ]

    def test_with_missing_resources(self, opensearch_manager):
        """OSM-012: _create_region_metadata missing_resources有り

        opensearch_manager.py:L219-221 のmissing_resources分岐をカバー。
        """
        # Arrange
        result = {
            "violations_count": 0,
            "execution_status": {
                "has_error": True, "error_type": "ResourceError",
                "missing_resources": ["ec2:instance", "s3:bucket"]
            }
        }

        # Act
        metadata = opensearch_manager._create_region_metadata(
            {}, result, "us-east-1"
        )

        # Assert
        assert metadata["error_details"]["missing_resources"] == [
            "ec2:instance", "s3:bucket"
        ]

    def test_error_without_detailed_errors(self, opensearch_manager):
        """OSM-013: _create_region_metadata エラーだがdetailed_errors空

        opensearch_manager.py:L192-198 のhas_error=True但しdetailed_errors空をカバー。
        基本エラー情報のみ設定される。
        """
        # Arrange
        result = {
            "violations_count": 0,
            "execution_status": {
                "has_error": True, "error_type": "UnknownError"
            }
        }

        # Act
        metadata = opensearch_manager._create_region_metadata(
            {}, result, "us-east-1"
        )

        # Assert
        assert metadata["error_details"]["has_error"] is True
        assert metadata["error_details"]["error_type"] == "UnknownError"
        assert "error_message" not in metadata["error_details"]
```

### 2.3 OpenSearch検索テスト

```python
@pytest.mark.asyncio
class TestExtractAccountIdFromOpensearch:
    """OpenSearchからのアカウントID抽出テスト"""

    async def test_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-014: extract_account_id_from_opensearch ヒット有り

        opensearch_manager.py:L257-261 のヒット有り→account_id返却をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {"account_id": "123456789012"}}]
            }
        }

        # Act
        result = await opensearch_manager.extract_account_id_from_opensearch()

        # Assert
        assert result == "123456789012"

    async def test_not_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-015: extract_account_id_from_opensearch ヒット無し

        opensearch_manager.py:L257 の条件不成立（0件ヒット）→L263 "unknown"をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []}
        }

        # Act
        result = await opensearch_manager.extract_account_id_from_opensearch()

        # Assert
        assert result == "unknown"

    async def test_account_id_empty(self, opensearch_manager, mock_opensearch_client):
        """OSM-016: extract_account_id_from_opensearch account_id空

        opensearch_manager.py:L260 のaccount_id falsy→L263 "unknown"をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {"account_id": None}}]
            }
        }

        # Act
        result = await opensearch_manager.extract_account_id_from_opensearch()

        # Assert
        assert result == "unknown"


@pytest.mark.asyncio
class TestGetRecommendationMappings:
    """推奨事項マッピング取得テスト"""

    async def test_normal(self, opensearch_manager, mock_opensearch_client):
        """OSM-017: get_recommendation_mappings 正常

        opensearch_manager.py:L293-304 のマッピング構築ループをカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {
                    "uuid": "uuid-1", "title": "Title1",
                    "severity": "High", "recommendationId": "A-1"
                }},
                {"_source": {
                    "uuid": "uuid-2", "title": "Title2",
                    "severity": "Low", "recommendationId": "B-2"
                }}
            ]}
        }

        # Act
        mappings = await opensearch_manager.get_recommendation_mappings()

        # Assert
        assert len(mappings) == 2
        assert mappings["uuid-1"]["title"] == "Title1"
        assert mappings["uuid-2"]["severity"] == "Low"

    async def test_client_none(self, opensearch_manager):
        """OSM-018: get_recommendation_mappings client None

        opensearch_manager.py:L278-279 のclient無し→空辞書返却をカバー。
        """
        # Arrange
        with patch(f"{OSM_MODULE}.get_opensearch_client", return_value=None):
            # Act
            mappings = await opensearch_manager.get_recommendation_mappings()

        # Assert
        assert mappings == {}

    async def test_uuid_missing_skip(self, opensearch_manager, mock_opensearch_client):
        """OSM-019: get_recommendation_mappings uuid無しスキップ

        opensearch_manager.py:L297 のuuid無し→スキップをカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {"title": "No UUID", "severity": "High"}},
                {"_source": {"uuid": "uuid-1", "title": "Has UUID"}}
            ]}
        }

        # Act
        mappings = await opensearch_manager.get_recommendation_mappings()

        # Assert
        assert len(mappings) == 1
        assert "uuid-1" in mappings


@pytest.mark.asyncio
class TestGetRecommendationTitleFromPolicyName:
    """ポリシー名からの推奨事項タイトル取得テスト"""

    async def test_found_in_recommendations(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-020: get_recommendation_title_from_policy_name recommendations検索成功

        opensearch_manager.py:L322-347 のpolicy-プレフィックス→推奨事項検索→タイトル返却をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {"title": "Enable MFA", "uuid": "u1"}}
            ]}
        }

        # Act
        title = await opensearch_manager.get_recommendation_title_from_policy_name(
            "policy-a-4"
        )

        # Assert
        assert title == "Enable MFA"

    async def test_fallback_to_scan_result(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-021: get_recommendation_title_from_policy_name fallback

        opensearch_manager.py:L346-350 のrecommendationsに無し→_get_title_from_scan_result
        フォールバックをカバー。
        """
        # Arrange — recommendationsは空、scan_resultにtitleあり
        mock_opensearch_client.search.side_effect = [
            {"hits": {"hits": []}},  # recommendations検索: 空
            {"hits": {"hits": [{"_source": {
                "custodian_metadata": {"policy": {"metadata": {"title": "Fallback Title"}}}
            }}]}}  # scan_result検索: ヒット
        ]

        # Act
        title = await opensearch_manager.get_recommendation_title_from_policy_name(
            "policy-b-2"
        )

        # Assert
        assert title == "Fallback Title"

    async def test_non_policy_prefix(self, opensearch_manager):
        """OSM-022: get_recommendation_title_from_policy_name 非policyプレフィックス

        opensearch_manager.py:L324-325 のpolicy-で始まらない→空文字返却をカバー。
        """
        # Act
        title = await opensearch_manager.get_recommendation_title_from_policy_name(
            "custom-rule-1"
        )

        # Assert
        assert title == ""

    async def test_client_none(self, opensearch_manager):
        """OSM-023: get_recommendation_title_from_policy_name client None

        opensearch_manager.py:L328-329 のclient無し→空文字返却をカバー。
        """
        # Arrange
        with patch(f"{OSM_MODULE}.get_opensearch_client", return_value=None):
            # Act
            title = await opensearch_manager.get_recommendation_title_from_policy_name(
                "policy-a-1"
            )

        # Assert
        assert title == ""


@pytest.mark.asyncio
class TestGetTitleFromScanResult:
    """スキャン結果からのタイトル取得テスト"""

    async def test_title_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-024: _get_title_from_scan_result title有り

        opensearch_manager.py:L393-397 のtitle取得成功をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": [{"_source": {
                "custodian_metadata": {
                    "policy": {"metadata": {"title": "Test Title"}}
                }
            }}]}
        }

        # Act
        title = await opensearch_manager._get_title_from_scan_result("policy-a-1")

        # Assert
        assert title == "Test Title"

    async def test_description_fallback(self, opensearch_manager, mock_opensearch_client):
        """OSM-025: _get_title_from_scan_result description代替

        opensearch_manager.py:L399-403 のtitle無し→description使用をカバー。
        50文字以下の場合はそのまま返却。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": [{"_source": {
                "custodian_metadata": {
                    "policy": {"metadata": {}, "description": "Short description"}
                }
            }}]}
        }

        # Act
        title = await opensearch_manager._get_title_from_scan_result("policy-a-1")

        # Assert
        assert title == "Short description"

    async def test_description_truncation(self, opensearch_manager, mock_opensearch_client):
        """OSM-026: _get_title_from_scan_result description切り詰め

        opensearch_manager.py:L403 の50文字超→切り詰め+"..."をカバー。
        """
        # Arrange
        long_desc = "A" * 60  # 60文字
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": [{"_source": {
                "custodian_metadata": {
                    "policy": {"metadata": {}, "description": long_desc}
                }
            }}]}
        }

        # Act
        title = await opensearch_manager._get_title_from_scan_result("policy-a-1")

        # Assert
        assert title == "A" * 50 + "..."
        assert len(title) == 53

    async def test_not_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-027: _get_title_from_scan_result 該当無し

        opensearch_manager.py:L405 の0件ヒット→空文字返却をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": []}
        }

        # Act
        title = await opensearch_manager._get_title_from_scan_result("policy-a-1")

        # Assert
        assert title == ""

    async def test_client_none(self, opensearch_manager):
        """OSM-028: _get_title_from_scan_result client None

        opensearch_manager.py:L368-369 のclient無し→空文字返却をカバー。
        """
        # Arrange
        with patch(f"{OSM_MODULE}.get_opensearch_client", return_value=None):
            # Act
            title = await opensearch_manager._get_title_from_scan_result("policy-a-1")

        # Assert
        assert title == ""
```

### 2.4 UUID・severity抽出テスト

```python
@pytest.mark.asyncio
class TestExtractRecommendationUuid:
    """推奨事項UUID抽出テスト"""

    async def test_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-029: extract_recommendation_uuid ヒット有り

        opensearch_manager.py:L444-452 のuuid取得成功をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {
                    "custodian_metadata": {
                        "policy": {"metadata": {"recommendation_uuid": "uuid-abc"}}
                    }
                }}]
            }
        }

        # Act
        uuid = await opensearch_manager.extract_recommendation_uuid("policy-a-1")

        # Assert
        assert uuid == "uuid-abc"

    async def test_not_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-030: extract_recommendation_uuid ヒット無し

        opensearch_manager.py:L454 の0件→"unknown-{policy_name}"返却をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []}
        }

        # Act
        uuid = await opensearch_manager.extract_recommendation_uuid("policy-a-1")

        # Assert
        assert uuid == "unknown-policy-a-1"

    async def test_uuid_none_in_hit(self, opensearch_manager, mock_opensearch_client):
        """OSM-030A: extract_recommendation_uuid uuid=None

        opensearch_manager.py:L451 のif recommendation_uuid条件不成立→L454をカバー。
        ヒット有りだがuuidフィールドがNone。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {
                    "custodian_metadata": {
                        "policy": {"metadata": {"recommendation_uuid": None}}
                    }
                }}]
            }
        }

        # Act
        uuid = await opensearch_manager.extract_recommendation_uuid("policy-a-1")

        # Assert
        assert uuid == "unknown-policy-a-1"


@pytest.mark.asyncio
class TestExtractSeverity:
    """severity抽出テスト"""

    async def test_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-031: extract_severity ヒット有り

        opensearch_manager.py:L494-501 のseverity取得成功をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {
                    "custodian_metadata": {
                        "policy": {"metadata": {"severity": "Critical"}}
                    }
                }}]
            }
        }

        # Act
        severity = await opensearch_manager.extract_severity("policy-a-1")

        # Assert
        assert severity == "Critical"

    async def test_not_found(self, opensearch_manager, mock_opensearch_client):
        """OSM-032: extract_severity ヒット無し

        opensearch_manager.py:L503 の0件→"Medium"デフォルト返却をカバー。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {"total": {"value": 0}, "hits": []}
        }

        # Act
        severity = await opensearch_manager.extract_severity("policy-a-1")

        # Assert
        assert severity == "Medium"

    async def test_severity_none_in_hit(self, opensearch_manager, mock_opensearch_client):
        """OSM-032A: extract_severity severity=None

        opensearch_manager.py:L500 のif severity条件不成立→L503をカバー。
        ヒット有りだがseverityフィールドがNone。
        """
        # Arrange
        mock_opensearch_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{"_source": {
                    "custodian_metadata": {
                        "policy": {"metadata": {"severity": None}}
                    }
                }}]
            }
        }

        # Act
        severity = await opensearch_manager.extract_severity("policy-a-1")

        # Assert
        assert severity == "Medium"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OSM-E01 | store_multi_region_results result-v2保存例外 | store_scan_result_v2例外 | エラーログ・result-v2分のカウント除外 |
| OSM-E02 | _store_single_region_result 保存例外 | store_custodian例外 | 0返却 |
| OSM-E03 | extract_account_id_from_opensearch 例外 | client.search例外 | "unknown" |
| OSM-E04 | get_recommendation_mappings 例外 | client.search例外 | {} |
| OSM-E05 | get_recommendation_title_from_policy_name 例外 | client.search例外 | "" |
| OSM-E06 | _get_title_from_scan_result 例外 | client.search例外 | "" |
| OSM-E07 | extract_recommendation_uuid 例外 | client.search例外 | "error-{policy_name}" |
| OSM-E08 | extract_severity 例外 | client.search例外 | "Unknown" |

### 3.1 異常系テスト

```python
@pytest.mark.asyncio
class TestOpenSearchManagerErrors:
    """OpenSearchManager異常系テスト"""

    async def test_store_result_v2_exception(
        self, opensearch_manager, mock_store_ops,
        mock_account_extractor, mock_store_scan_result_v2
    ):
        """OSM-E01: store_multi_region_results result-v2保存例外

        opensearch_manager.py:L85-86 のresult-v2保存try/exceptをカバー。
        リージョン保存は成功するがresult-v2保存で例外発生。
        """
        # Arrange
        region_results = [{"region": "us-east-1", "output_dir": "/out/us-east-1"}]
        mock_store_ops.return_value = 3
        mock_store_scan_result_v2.side_effect = RuntimeError("v2 save failed")

        # Act
        result = await opensearch_manager.store_multi_region_results(
            region_results, {"account_id": "123456"}, "AWS",
            custodian_output_dir="/out"
        )

        # Assert — リージョン分のみカウント、result-v2は除外
        assert result == 3
        opensearch_manager.logger.error.assert_called()

    async def test_store_single_region_exception(
        self, opensearch_manager, mock_store_ops, mock_account_extractor
    ):
        """OSM-E02: _store_single_region_result 保存例外

        opensearch_manager.py:L145-147 のtry/exceptをカバー。
        """
        # Arrange
        result = {"region": "us-east-1", "output_dir": "/out/us-east-1"}
        mock_store_ops.side_effect = RuntimeError("store failed")

        # Act
        count = await opensearch_manager._store_single_region_result(
            result, {}, "AWS"
        )

        # Assert
        assert count == 0
        opensearch_manager.logger.error.assert_called()

    async def test_extract_account_id_exception(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-E03: extract_account_id_from_opensearch 例外

        opensearch_manager.py:L265-267 のtry/exceptをカバー。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError("timeout")

        # Act
        result = await opensearch_manager.extract_account_id_from_opensearch()

        # Assert
        assert result == "unknown"
        opensearch_manager.logger.warning.assert_called()

    async def test_recommendation_mappings_exception(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-E04: get_recommendation_mappings 例外

        opensearch_manager.py:L306-308 のtry/exceptをカバー。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError("timeout")

        # Act
        mappings = await opensearch_manager.get_recommendation_mappings()

        # Assert
        assert mappings == {}

    async def test_recommendation_title_exception(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-E05: get_recommendation_title_from_policy_name 例外

        opensearch_manager.py:L352-354 のtry/exceptをカバー。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError("timeout")

        # Act
        title = await opensearch_manager.get_recommendation_title_from_policy_name(
            "policy-a-1"
        )

        # Assert
        assert title == ""

    async def test_get_title_from_scan_result_exception(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-E06: _get_title_from_scan_result 例外

        opensearch_manager.py:L407-408 のtry/exceptをカバー。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError("timeout")

        # Act
        title = await opensearch_manager._get_title_from_scan_result("policy-a-1")

        # Assert
        assert title == ""

    async def test_extract_uuid_exception(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-E07: extract_recommendation_uuid 例外

        opensearch_manager.py:L456-458 のtry/exceptをカバー。
        例外時は"error-{policy_name}"を返却。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError("timeout")

        # Act
        uuid = await opensearch_manager.extract_recommendation_uuid("policy-a-1")

        # Assert
        assert uuid == "error-policy-a-1"
        opensearch_manager.logger.warning.assert_called()

    async def test_extract_severity_exception(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-E08: extract_severity 例外

        opensearch_manager.py:L505-507 のtry/exceptをカバー。
        例外時は"Unknown"を返却（正常時デフォルト"Medium"とは異なる）。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError("timeout")

        # Act
        severity = await opensearch_manager.extract_severity("policy-a-1")

        # Assert
        assert severity == "Unknown"
        opensearch_manager.logger.warning.assert_called()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OSM-SEC-01 | 例外メッセージにクレデンシャル非露出 | 機密情報含む例外 | return値に機密情報なし |
| OSM-SEC-02 | 攻撃的policy_name安全処理 | XSS/SQLi文字列 | 安全にクエリ構築 |
| OSM-SEC-03 | full_traceback切り詰め検証 | 1000文字超traceback | 1000文字で切り詰め |

```python
@pytest.mark.security
@pytest.mark.asyncio
class TestOpenSearchManagerSecurity:
    """OpenSearchManagerセキュリティテスト"""

    async def test_exception_no_credential_leak(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-SEC-01: 例外メッセージにクレデンシャル非露出

        opensearch_manager.py:L265-267 で例外時、return値は定型"unknown"のみで
        機密情報を含まない。logger.warningにstr(e)が出力されるがreturn値は安全。
        """
        # Arrange
        mock_opensearch_client.search.side_effect = ConnectionError(
            "Auth failed: password=SuperSecret123"
        )

        # Act
        result = await opensearch_manager.extract_account_id_from_opensearch()

        # Assert
        assert result == "unknown"
        assert "SuperSecret" not in result

    async def test_malicious_policy_name_safe(
        self, opensearch_manager, mock_opensearch_client
    ):
        """OSM-SEC-02: 攻撃的policy_name安全処理

        opensearch_manager.py:L323 のreplace()はプレーンテキスト操作。
        policy_nameはOpenSearchのtermクエリにDSL辞書構造で渡されるため、
        文字列連結によるインジェクションリスクがない。
        """
        # Arrange
        malicious_name = "policy-'; DROP INDEX recommendations; --"
        mock_opensearch_client.search.return_value = {
            "hits": {"hits": []}
        }

        # Act
        title = await opensearch_manager.get_recommendation_title_from_policy_name(
            malicious_name
        )

        # Assert — 例外なく処理完了
        assert isinstance(title, str)
        # 1回目のsearch呼び出し（recommendations検索）を検証
        first_call = mock_opensearch_client.search.call_args_list[0]
        query_body = first_call[1]["body"]
        # 攻撃文字列がtermクエリの辞書値として安全に渡されていることを確認
        # （文字列連結ではなくdict構造でパラメータ化されている）
        term_value = query_body["query"]["term"]["recommendationId.keyword"]
        expected = malicious_name.replace("policy-", "").upper()
        assert term_value == expected

    def test_traceback_truncation(self, opensearch_manager):
        """OSM-SEC-03: full_traceback切り詰め検証

        opensearch_manager.py:L207 の[:1000]で長大なトレースバックを切り詰め。
        機密情報を含む可能性のあるスタックトレースの格納量を制限。
        """
        # Arrange
        sensitive_traceback = "/app/secrets/db_creds.py:42\n" * 100  # 長大
        result = {
            "violations_count": 0,
            "execution_status": {
                "has_error": True,
                "detailed_errors": [{
                    "full_traceback": sensitive_traceback
                }]
            }
        }

        # Act
        metadata = opensearch_manager._create_region_metadata(
            {}, result, "us-east-1"
        )

        # Assert
        assert len(metadata["error_details"]["full_traceback"]) <= 1000
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_results_module` | テスト間のモジュール状態リセット（#16a conftest.pyで定義済み） | function | Yes |
| `opensearch_manager` | テスト用OpenSearchManagerインスタンス | function | No |
| `mock_opensearch_client` | get_opensearch_clientのAsyncMock | function | No |
| `mock_store_ops` | store_custodian_output_to_opensearchのAsyncMock | function | No |
| `mock_account_extractor` | extract_account_id_with_fallbackのMock | function | No |
| `mock_store_scan_result_v2` | store_scan_result_v2のAsyncMock（遅延import対応） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/results/conftest.py
# ※ 以下は #16a の conftest.py に追記する。
# ※ reset_results_module (autouse) と MODULE_BASE, pytest, patch 等の
#    import は既に定義済み。

import sys
from unittest.mock import AsyncMock

OSM_MODULE = "app.jobs.tasks.new_custodian_scan.results.opensearch_manager"
STORE_OPS_MODULE = "app.jobs.utils.store_operations"


@pytest.fixture
def opensearch_manager():
    """テスト用OpenSearchManagerインスタンス

    TaskLoggerをパッチして実__init__を通す。
    loggerをMagicMockに置換してログ検証を可能にする。
    """
    with patch(f"{OSM_MODULE}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.results.opensearch_manager import (
            OpenSearchManager
        )
        manager = OpenSearchManager("test-job-id")
        manager.logger = MagicMock()
        yield manager


@pytest.fixture
def mock_opensearch_client():
    """get_opensearch_clientのモック（AsyncMock）

    OpenSearch検索メソッドのテストで使用。
    search()等のメソッドがAsyncMockとして利用可能。
    """
    mock_client = AsyncMock()
    with patch(
        f"{OSM_MODULE}.get_opensearch_client", return_value=mock_client
    ):
        yield mock_client


@pytest.fixture
def mock_store_ops():
    """store_custodian_output_to_opensearchのモック（AsyncMock）

    _store_single_region_resultの保存処理テストで使用。
    """
    mock_fn = AsyncMock(return_value=3)
    with patch(
        f"{OSM_MODULE}.store_custodian_output_to_opensearch", mock_fn
    ):
        yield mock_fn


@pytest.fixture
def mock_account_extractor():
    """extract_account_id_with_fallbackのモック

    _store_single_region_resultおよびstore_multi_region_resultsの
    アカウントID抽出テストで使用。
    """
    mock_fn = MagicMock(return_value="123456789012")
    with patch(
        f"{OSM_MODULE}.extract_account_id_with_fallback", mock_fn
    ):
        yield mock_fn


@pytest.fixture
def mock_store_scan_result_v2():
    """store_scan_result_v2のモック（遅延import対応）

    opensearch_manager.py:L73 の遅延importに対応。
    store_operationsモジュールが既にsys.modulesにある場合、
    属性パッチで対応（トップレベルimportでモジュールはロード済み）。
    """
    mock_fn = AsyncMock(return_value=5)
    with patch(f"{STORE_OPS_MODULE}.store_scan_result_v2", mock_fn):
        yield mock_fn
```

---

## 6. テスト実行例

```bash
# OpenSearch管理テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py::TestCreateRegionMetadata -v
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py::TestGetRecommendationTitleFromPolicyName -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py \
  --cov=app.jobs.tasks.new_custodian_scan.results.opensearch_manager \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/results/test_results_opensearch_manager.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 34 | OSM-001〜OSM-030A, OSM-031〜OSM-032A |
| 異常系 | 8 | OSM-E01〜OSM-E08 |
| セキュリティ | 3 | OSM-SEC-01〜OSM-SEC-03 |
| **合計** | **45** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestOpenSearchManagerInit` | OSM-001 | 1 |
| `TestStoreMultiRegionResults` | OSM-002〜OSM-004 | 3 |
| `TestStoreSingleRegionResult` | OSM-005〜OSM-007 | 3 |
| `TestCreateRegionMetadata` | OSM-008〜OSM-013 | 6 |
| `TestExtractAccountIdFromOpensearch` | OSM-014〜OSM-016 | 3 |
| `TestGetRecommendationMappings` | OSM-017〜OSM-019 | 3 |
| `TestGetRecommendationTitleFromPolicyName` | OSM-020〜OSM-023 | 4 |
| `TestGetTitleFromScanResult` | OSM-024〜OSM-028 | 5 |
| `TestExtractRecommendationUuid` | OSM-029〜OSM-030A | 3 |
| `TestExtractSeverity` | OSM-031〜OSM-032A | 3 |
| `TestOpenSearchManagerErrors` | OSM-E01〜OSM-E08 | 8 |
| `TestOpenSearchManagerSecurity` | OSM-SEC-01〜OSM-SEC-03 | 3 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提

| 前提 | 対応内容 |
|------|---------|
| `pytest-asyncio` | asyncテスト実行に必要。`pip install pytest-asyncio` |
| `security`マーカー | `pyproject.toml` に定義済み（#16aで追加） |
| `reset_results_module` | `conftest.py` に #16a で定義済み |
| `store_operations`モジュール | トップレベルimportでsys.modulesにロード済み。mock_store_scan_result_v2はこれに依存 |

### 注意事項

- 全async公開メソッドが`@pytest.mark.asyncio`でマーク必須。`_create_region_metadata`のみ同期テスト
- OpenSearchクライアントはすべてAsyncMock（`client.search`がawait対象）
- `extract_recommendation_uuid`の例外時return値は`"error-{policy_name}"`、`extract_severity`の例外時は`"Unknown"`であり、正常時デフォルト（`"unknown-{policy_name}"`、`"Medium"`）とは異なる
- 内部メソッド`_get_title_from_scan_result`のexceptブロック（L407-408）はlogger呼び出しなしの`return ""`のみ。ログ検証アサーション不可
- `store_multi_region_results`はforループ内で`_store_single_region_result`を呼ぶため、OSM-002〜004ではmock_store_opsが実際のstore処理を代替

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | opensearch_managerの4つのトップレベルimport | テスト環境で依存パッケージが未インストールの場合、モジュールimportが失敗する | プロジェクト全体のuv sync実行を前提とする。または個別にsys.modulesモック注入 |
| 2 | store_scan_result_v2の遅延import（L73） | store_operationsモジュールがsys.modulesにロード済みであることが前提 | mock_store_scan_result_v2フィクスチャでSTORE_OPS_MODULEの属性をパッチ |
| 3 | get_opensearch_clientのawait | get_opensearch_clientはasync関数だが、テストではAsyncMockのreturn_valueで直接モッククライアントを返却 | awaitの結果としてmock_clientが返る設計。AsyncMockがawait対応を自動処理 |
| 4 | _create_region_metadataのfull_traceback切り詰め | L207の`[:1000]`はバイト数ではなく文字数。マルチバイト文字で切り詰め位置がずれる可能性 | テストではASCII文字列で検証。マルチバイト対応は実装側の課題 |
| 5 | OSM-021のside_effect複数回呼び出し | get_recommendation_title_from_policy_nameは内部で_get_title_from_scan_resultを呼び、それが再度client.searchを呼ぶ。side_effectリストで呼び出し順を制御 | side_effectに[recommendations結果, scan_result結果]を設定 |
| 6 | extract_severityとextract_recommendation_uuidの構造的類似 | 両メソッドはほぼ同一構造（検索→メタデータ抽出→デフォルト返却）だが例外時return値が異なる | 各メソッドを独立テストし、例外時return値の差異を明示的に検証 |
