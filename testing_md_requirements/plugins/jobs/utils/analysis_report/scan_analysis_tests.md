# jobs/utils スキャン分析 テストケース (#17f)

## 1. 概要

`app/jobs/utils/scan_analysis.py` のテスト仕様書。Cloud Custodianスキャン結果の包括的な分析と要約を検証する。

### 1.1 主要機能

| 関数 | 行範囲 | 説明 |
|------|--------|------|
| `_get_recommendation_mappings_for_job()` | L20-96 | 推奨事項UUIDマッピング取得（v2/v1フォールバック） |
| `_generate_comprehensive_policy_results()` | L99-253 | 全ポリシー結果生成（違反なし含む） |
| `_map_policy_names_to_recommendations()` | L256-296 | ポリシー名→推奨事項名マッピング |
| `summarize_index_content()` | L299-622 | 包括的サマリーJSON生成（公開API） |

### 1.2 カバレッジ目標: 80%

> **注記**: 621行の大規模モジュール。OpenSearch集計クエリの構築・解析が中心。`summarize_index_content` のインサイト生成ロジック（L540-607）は多数の条件分岐を含むが、主要パスのみカバーし、全組み合わせの網羅はE2Eテストに委ねる。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/utils/scan_analysis.py` (621行) |
| テストコード | `test/unit/jobs/utils/test_scan_analysis.py` |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存先 | 用途 | モック要否 |
|--------|------|-----------|
| `get_opensearch_client` | OpenSearchクライアント取得 | 要（モック） |
| `TaskLogger` | ログ出力 | 要（モック） |
| `TransportError` | OpenSearch例外型 | 不要（実型使用） |
| `json` | JSON変換 | 不要（標準ライブラリ） |

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `_get_recommendation_mappings_for_job` | 5 | L31 クライアントNone, L42/48 v2/v1フォールバック, L57 hits空, L61 UUIDs空, L85 uuid&title存在 |
| `_generate_comprehensive_policy_results` | 5 | L114 クライアントNone, L141/173 内部例外, L163 uuid&policy_name存在, L226 未スキャン推奨事項追加 |
| `_map_policy_names_to_recommendations` | 3 | L271 プレフィックス除去, L276 マッピング空, L285 ポリシー名一致 |
| `summarize_index_content` | 12+ | L343 クライアントNone, L345 無効index, L442-448 プロバイダ判定, L540 violations>0, L554/562/568/583/586/591/596/602/604 インサイト条件 |

---

## 2. 正常系テストケース

| ID | テスト名 | 対象関数 | 期待結果 |
|----|---------|---------|---------|
| SA-001 | 推奨事項マッピング正常取得 | _get_recommendation_mappings | UUID→詳細の辞書 |
| SA-002 | v2インデックス失敗→v1フォールバック | _get_recommendation_mappings | v1から取得成功 |
| SA-003 | job_hitsが空 → 空辞書 | _get_recommendation_mappings | {} |
| SA-004 | recommendation_uuidsが空 → 空辞書 | _get_recommendation_mappings | {} |
| SA-005 | 全ポリシー結果正常生成 | _generate_comprehensive | (results, mapping)タプル |
| SA-006 | 未スキャン推奨事項の追加 | _generate_comprehensive | 違反なしポリシーも含む |
| SA-007 | 違反数順ソート | _generate_comprehensive | 降順ソート |
| SA-008 | ポリシー名マッピング正常 | _map_policy_names | 推奨事項名に置換 |
| SA-009 | プレフィックス除去 | _map_policy_names | "cspm-scan-result-"除去 |
| SA-010 | マッピング空→元リスト返却 | _map_policy_names | 入力そのまま |
| SA-011 | サマリー正常生成 | summarize_index_content | JSON文字列（全項目） |
| SA-012 | クラウドプロバイダ判定：Azure | summarize_index_content | target_provider="Azure" |
| SA-013 | クラウドプロバイダ判定：GCP | summarize_index_content | target_provider="GCP" |
| SA-014 | インサイト生成：違反あり | summarize_index_content | insightsにメッセージ含む |
| SA-015 | インサイト：Critical重要度 | summarize_index_content | 緊急対応メッセージ |
| SA-016 | インサイト：単一リージョン | summarize_index_content | 単一リージョンメッセージ |
| SA-017 | severity_breakdown計算 | summarize_index_content | severity別集計 |

### 2.1 _get_recommendation_mappings_for_job テスト

```python
# test/unit/jobs/utils/test_scan_analysis.py
import pytest
import json
from unittest.mock import patch, AsyncMock
from opensearchpy import TransportError


class TestGetRecommendationMappings:
    """_get_recommendation_mappings_for_job のテスト"""

    @pytest.mark.asyncio
    async def test_successful_mapping(self):
        """SA-001: 正常にUUID→詳細マッピングを返す

        scan_analysis.py:L20-92 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        mock_client = AsyncMock()
        # ジョブ検索レスポンス
        mock_client.search.side_effect = [
            # v2インデックス検索結果
            {"hits": {"hits": [{"_source": {"target_recommendation_uuids": ["uuid-1", "uuid-2"]}}]}},
            # recommendations検索結果
            {"hits": {"hits": [
                {"_source": {"uuid": "uuid-1", "title": "EC2 Public Access", "severity": "High", "recommendationId": "rec-001"}},
                {"_source": {"uuid": "uuid-2", "title": "S3 Encryption", "severity": "Medium", "recommendationId": "rec-002"}},
            ]}},
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            result = await _get_recommendation_mappings_for_job("job-001")

        # Assert
        assert len(result) == 2
        assert result["uuid-1"]["title"] == "EC2 Public Access"
        assert result["uuid-1"]["severity"] == "High"
        assert result["uuid-2"]["recommendationId"] == "rec-002"

    @pytest.mark.asyncio
    async def test_v2_fallback_to_v1(self):
        """SA-002: v2インデックス検索失敗 → v1にフォールバック

        scan_analysis.py:L42-54 の try/except フォールバックをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        mock_client = AsyncMock()
        # v2で例外 → v1で成功 → recommendations検索
        mock_client.search.side_effect = [
            Exception("v2 index not found"),
            {"hits": {"hits": [{"_source": {"target_recommendation_uuids": ["uuid-1"]}}]}},
            {"hits": {"hits": [{"_source": {"uuid": "uuid-1", "title": "Test", "severity": "Low", "recommendationId": "rec-001"}}]}},
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            result = await _get_recommendation_mappings_for_job("job-002")

        # Assert
        assert len(result) == 1
        assert result["uuid-1"]["title"] == "Test"

    @pytest.mark.asyncio
    async def test_no_job_hits(self):
        """SA-003: ジョブヒットなし → 空辞書

        scan_analysis.py:L57-58 の空hits分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            result = await _get_recommendation_mappings_for_job("job-003")

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_no_recommendation_uuids(self):
        """SA-004: recommendation_uuidsが空 → 空辞書

        scan_analysis.py:L61-62 の空UUIDs分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {"hits": [{"_source": {"target_recommendation_uuids": []}}]}
        }

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            result = await _get_recommendation_mappings_for_job("job-004")

        # Assert
        assert result == {}
```

### 2.2 _generate_comprehensive_policy_results テスト

```python
class TestGenerateComprehensivePolicyResults:
    """_generate_comprehensive_policy_results のテスト"""

    @pytest.mark.asyncio
    async def test_successful_generation(self):
        """SA-005: 正常にポリシー結果を生成

        scan_analysis.py:L99-248 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _generate_comprehensive_policy_results

        mock_client = AsyncMock()
        # ポリシー検索結果
        mock_client.search.return_value = {
            "hits": {"hits": [{
                "_source": {
                    "policy_name": "check-ec2-public",
                    "resource_count": 5,
                    "custodian_metadata": {
                        "policy": {
                            "metadata": {"uuid": "uuid-1", "severity": "High", "recommendation_id": "rec-001"},
                            "description": "EC2パブリックアクセスチェック"
                        }
                    }
                }
            }]}
        }

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis._get_recommendation_mappings_for_job",
                   new_callable=AsyncMock, return_value={"uuid-1": {"title": "EC2 Public", "severity": "High", "recommendationId": "rec-001"}}):

            results, mapping = await _generate_comprehensive_policy_results("scan-005")

        # Assert
        assert len(results) >= 1
        assert results[0]["recommendation_uuid"] == "uuid-1"
        assert "check-ec2-public" in mapping

    @pytest.mark.asyncio
    async def test_adds_unscanned_recommendations(self):
        """SA-006: 未スキャン推奨事項を違反なしとして追加

        scan_analysis.py:L224-242 のuuid_to_detailsから追加する分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _generate_comprehensive_policy_results

        mock_client = AsyncMock()
        # スキャン結果は空
        mock_client.search.return_value = {"hits": {"hits": []}}

        # 推奨事項マッピングには1件あり
        mock_rec_mappings = {
            "uuid-extra": {"title": "Unscanned Policy", "severity": "Low", "recommendationId": "rec-extra"}
        }

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis._get_recommendation_mappings_for_job",
                   new_callable=AsyncMock, return_value=mock_rec_mappings):

            results, _ = await _generate_comprehensive_policy_results("scan-006")

        # Assert
        assert len(results) == 1
        assert results[0]["status"] == "適合"
        assert results[0]["violation_count"] == 0

    @pytest.mark.asyncio
    async def test_sorted_by_violation_count(self):
        """SA-007: 結果が違反数の降順でソートされる

        scan_analysis.py:L245 の sort() をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _generate_comprehensive_policy_results

        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {"policy_name": "low-violations", "resource_count": 1,
                    "custodian_metadata": {"policy": {"metadata": {"uuid": "uuid-lo", "severity": "Low", "recommendation_id": ""}, "description": ""}}}},
                {"_source": {"policy_name": "high-violations", "resource_count": 10,
                    "custodian_metadata": {"policy": {"metadata": {"uuid": "uuid-hi", "severity": "High", "recommendation_id": ""}, "description": ""}}}},
            ]}
        }

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis._get_recommendation_mappings_for_job",
                   new_callable=AsyncMock, return_value={}):

            results, _ = await _generate_comprehensive_policy_results("scan-007")

        # Assert
        assert results[0]["violation_count"] == 10
        assert results[1]["violation_count"] == 1
```

### 2.3 _map_policy_names_to_recommendations テスト

```python
class TestMapPolicyNames:
    """_map_policy_names_to_recommendations のテスト"""

    @pytest.mark.asyncio
    async def test_successful_mapping(self):
        """SA-008: ポリシー名を推奨事項名に正常マッピング

        scan_analysis.py:L279-296 のマッピングロジックをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _map_policy_names_to_recommendations

        violations = [{"policy_name": "check-ec2", "violation_count": 3}]
        mapping = {"check-ec2": {
            "title": "EC2 Public Access Check",
            "severity": "High",
            "recommendationId": "rec-001",
            "recommendation_id": "rec-001",
            "recommendation_uuid": "uuid-1"
        }}

        # Act
        with patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=([], mapping)):

            result = await _map_policy_names_to_recommendations(violations, "cspm-scan-result-job-008")

        # Assert
        assert result[0]["policy_name"] == "EC2 Public Access Check"
        assert result[0]["original_policy_name"] == "check-ec2"
        assert result[0]["severity"] == "High"

    @pytest.mark.asyncio
    async def test_prefix_stripping(self):
        """SA-009: "cspm-scan-result-"プレフィックスの除去

        scan_analysis.py:L271 のプレフィックス除去をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _map_policy_names_to_recommendations

        # Act
        with patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=([], {})) as mock_gen:

            await _map_policy_names_to_recommendations([], "cspm-scan-result-my-scan-id")

        # Assert
        # _generate_comprehensive_policy_resultsに "my-scan-id" が渡される
        mock_gen.assert_called_once_with("my-scan-id")

    @pytest.mark.asyncio
    async def test_empty_mapping_returns_original(self):
        """SA-010: マッピング空 → 元のリストをそのまま返す

        scan_analysis.py:L276-277 の空マッピング分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _map_policy_names_to_recommendations

        original = [{"policy_name": "original-policy", "violation_count": 1}]

        # Act
        with patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=([], {})):

            result = await _map_policy_names_to_recommendations(original, "job-010")

        # Assert
        assert result == original
```

### 2.4 summarize_index_content テスト

```python
class TestSummarizeIndexContent:
    """summarize_index_content のテスト"""

    def _create_mock_aggs_response(self, total_violations=10, cloud_resource="aws.ec2",
                                    policy_name="check-ec2", account_id="123456",
                                    region="us-east-1"):
        """テスト用のOpenSearch集計レスポンスを生成するヘルパー"""
        return {
            "aggregations": {
                "total_violations": {"value": total_violations},
                "total_policy_groups": {"value": 3},
                "cloud_providers": {"buckets": [
                    {"key": cloud_resource, "doc_count": total_violations}
                ]},
                "top_policies": {"buckets": [
                    {"key": policy_name, "doc_count": total_violations}
                ]},
                "target_account": {"buckets": [
                    {"key": account_id}
                ]},
                "regions": {"buckets": [
                    {"key": region, "doc_count": total_violations}
                ]},
                "time_stats": {
                    "min_as_string": "2025-01-01T00:00:00Z",
                    "max_as_string": "2025-01-31T23:59:59Z"
                },
                "scan_time_distribution": {"buckets": [
                    {"key_as_string": "2025-01-15T10:00:00Z", "doc_count": total_violations}
                ]}
            }
        }

    @pytest.mark.asyncio
    async def test_successful_summary(self):
        """SA-011: 正常なサマリーJSON生成

        scan_analysis.py:L299-610 の正常パス全体をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.return_value = self._create_mock_aggs_response()

        mock_all_results = [
            {"policy_name": "Check EC2", "recommendation_uuid": "uuid-1",
             "violation_count": 10, "severity": "High", "status": "違反あり"}
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock,
                   # NOTE: AsyncMock の side_effect に lambda を渡すと、Python 3.8+ では
                   # 戻り値が自動的にコルーチンとしてラップされるため await 可能になる
                   side_effect=lambda v, _: v), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=(mock_all_results, {})):

            result = await summarize_index_content("cspm-scan-result-v2", job_id="job-011")

        # Assert
        assert not result.startswith("Error:")
        summary = json.loads(result)
        assert "basic_statistics" in summary
        assert summary["basic_statistics"]["total_violations"] == 10
        assert summary["basic_statistics"]["cloud_provider"] == "AWS"

    @pytest.mark.asyncio
    async def test_cloud_provider_azure(self):
        """SA-012: Azureリソースプレフィックス → target_provider="Azure"

        scan_analysis.py:L445-446 のAzure判定をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.return_value = self._create_mock_aggs_response(
            cloud_resource="azure.vm"
        )

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock, side_effect=lambda v, _: v), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=([], {})):

            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        summary = json.loads(result)
        assert summary["basic_statistics"]["cloud_provider"] == "Azure"

    @pytest.mark.asyncio
    async def test_cloud_provider_gcp(self):
        """SA-013: GCPリソースプレフィックス → target_provider="GCP"

        scan_analysis.py:L447-448 のGCP判定をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.return_value = self._create_mock_aggs_response(
            cloud_resource="gcp.compute"
        )

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock, side_effect=lambda v, _: v), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=([], {})):

            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        summary = json.loads(result)
        assert summary["basic_statistics"]["cloud_provider"] == "GCP"

    @pytest.mark.asyncio
    async def test_insights_with_violations(self):
        """SA-014: 違反あり時のインサイト生成

        scan_analysis.py:L540-559 の基本インサイト生成をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.return_value = self._create_mock_aggs_response(
            total_violations=20
        )

        mock_all_results = [
            {"policy_name": "Top Policy", "recommendation_uuid": "uuid-1",
             "violation_count": 15, "severity": "High", "status": "違反あり"},
            {"policy_name": "Minor Policy", "recommendation_uuid": "uuid-2",
             "violation_count": 5, "severity": "Low", "status": "違反あり"},
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock, side_effect=lambda v, _: v), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=(mock_all_results, {})):

            result = await summarize_index_content("cspm-scan-result-v2", job_id="job-014")

        # Assert
        summary = json.loads(result)
        insights = summary["insights"]
        assert len(insights) >= 1
        # 最も多い違反のインサイトが含まれること
        assert any("Top Policy" in i for i in insights)

    @pytest.mark.asyncio
    async def test_insights_critical_severity(self):
        """SA-015: Critical重要度の違反 → 緊急対応メッセージ

        scan_analysis.py:L583-585 のCritical判定をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.return_value = self._create_mock_aggs_response(
            total_violations=5
        )

        mock_all_results = [
            {"policy_name": "Critical Policy", "recommendation_uuid": "uuid-c",
             "violation_count": 5, "severity": "Critical", "status": "違反あり"},
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock, side_effect=lambda v, _: v), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=(mock_all_results, {})):

            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        summary = json.loads(result)
        assert any("緊急対応" in i for i in summary["insights"])

    @pytest.mark.asyncio
    async def test_insights_single_region(self):
        """SA-016: 単一リージョンスキャン → 専用メッセージ

        scan_analysis.py:L602-603 の単一リージョン分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        response = self._create_mock_aggs_response(region="ap-northeast-1")
        # デフォルトで1件だが、将来のヘルパー変更に対して明示的に1件を保証
        response["aggregations"]["regions"]["buckets"] = [
            {"key": "ap-northeast-1", "doc_count": 5}
        ]
        mock_client.search.return_value = response

        mock_all_results = [
            {"policy_name": "Test", "recommendation_uuid": "uuid-r",
             "violation_count": 5, "severity": "Medium", "status": "違反あり"},
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock, side_effect=lambda v, _: v), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=(mock_all_results, {})):

            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        summary = json.loads(result)
        assert any("単一リージョン" in i for i in summary["insights"])

    @pytest.mark.asyncio
    async def test_severity_breakdown(self):
        """SA-017: severity_breakdown が正しく計算される

        scan_analysis.py:L471-485 のseverity集計をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.return_value = self._create_mock_aggs_response()

        # top_policiesに複数severity
        mock_mapped_policies = [
            {"policy_name": "P1", "violation_count": 5, "severity": "High"},
            {"policy_name": "P2", "violation_count": 3, "severity": "Medium"},
            {"policy_name": "P3", "violation_count": 2, "severity": "High"},
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis._map_policy_names_to_recommendations",
                   new_callable=AsyncMock, return_value=mock_mapped_policies), \
             patch("app.jobs.utils.scan_analysis._generate_comprehensive_policy_results",
                   new_callable=AsyncMock, return_value=([], {})):

            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        summary = json.loads(result)
        severity_breakdown = summary["severity_breakdown"]
        # High: 5+2=7, Medium: 3 → Highが先（降順）
        assert severity_breakdown[0]["severity"] == "High"
        assert severity_breakdown[0]["violation_count"] == 7
```

---

## 3. 異常系テストケース

| ID | テスト名 | 対象関数 | 期待結果 |
|----|---------|---------|---------|
| SA-E01 | クライアントNone → 空辞書 | _get_recommendation_mappings_for_job | {} |
| SA-E02 | 推奨事項検索で例外 → 空辞書 | _get_recommendation_mappings_for_job | {} |
| SA-E03 | クライアントNone → ([], {}) | _generate_comprehensive_policy_results | ([], {}) |
| SA-E04 | 内部例外（L173）→ 処理継続 | _generate_comprehensive_policy_results | ([], {})（空データで継続） |
| SA-E05 | 外部例外（L250）→ ([], {}) | _generate_comprehensive_policy_results | ([], {}) |
| SA-E06 | クライアントNone → Errorメッセージ | summarize_index_content | "Error: OpenSearch client..." |
| SA-E07 | 無効なindex_name → Errorメッセージ | summarize_index_content | "Error: index_name is required." |
| SA-E08 | TransportError 404 → Not found | summarize_index_content | "Error: Index...not found." |
| SA-E09 | TransportError 500 → transport error | summarize_index_content | "Error: OpenSearch transport error..." |
| SA-E10 | 汎用Exception → unexpected error | summarize_index_content | "Error: An unexpected error..." |

### 3.1 異常系テスト

```python
class TestScanAnalysisErrors:
    """scan_analysis エラーテスト"""

    @pytest.mark.asyncio
    async def test_recommendation_client_none(self):
        """SA-E01: OpenSearchクライアントNone → 空辞書

        scan_analysis.py:L31-32 のクライアントNullチェックをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            result = await _get_recommendation_mappings_for_job("job-e01")

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_recommendation_search_exception(self):
        """SA-E02: 推奨事項検索で例外 → 空辞書

        scan_analysis.py:L94-96 のexceptをカバー。
        v2ジョブ検索は成功するが、推奨事項検索（L70-73）で例外が発生するケース。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        mock_client = AsyncMock()
        # v2ジョブ検索は成功（1回目）、推奨事項検索（2回目）で例外
        mock_client.search.side_effect = [
            {"hits": {"hits": [{"_source": {"target_recommendation_uuids": ["uuid-1"]}}]}},
            Exception("Connection timeout on recommendations search"),
        ]

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client):
            result = await _get_recommendation_mappings_for_job("job-e02")

        # Assert
        assert result == {}

    @pytest.mark.asyncio
    async def test_comprehensive_client_none(self):
        """SA-E03: _generate_comprehensive_policy_results でクライアントNone

        scan_analysis.py:L114-115 のクライアントNullチェックをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _generate_comprehensive_policy_results

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None):
            results, mapping = await _generate_comprehensive_policy_results("scan-e03")

        # Assert
        assert results == []
        assert mapping == {}

    @pytest.mark.asyncio
    async def test_comprehensive_inner_exception(self):
        """SA-E04: _generate_comprehensive_policy_results の内部例外（L173）

        scan_analysis.py:L141-177 の内部try/exceptをカバー。
        os_client.search が例外を投げても、内部exceptで吸収され処理が継続する。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _generate_comprehensive_policy_results

        mock_client = AsyncMock()
        # ポリシー情報検索（L142）で例外 → 内部except（L173）で吸収
        mock_client.search.side_effect = RuntimeError("search failure")

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis._get_recommendation_mappings_for_job",
                   new_callable=AsyncMock, return_value={}), \
             patch("app.jobs.utils.scan_analysis.traceback"), \
             patch("builtins.print"):
            results, mapping = await _generate_comprehensive_policy_results("scan-e04")

        # Assert
        # 内部例外で吸収され、空のscan_policy_dataで処理継続
        # uuid_to_detailsも空なので結果は空リスト
        assert results == []
        assert mapping == {}

    @pytest.mark.asyncio
    async def test_comprehensive_outer_exception(self):
        """SA-E05: _generate_comprehensive_policy_results で外部例外（L250）

        scan_analysis.py:L250-253 のouter exceptをカバー。
        _get_recommendation_mappings_for_job（L180）が予期せぬ例外を投げるケース。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _generate_comprehensive_policy_results

        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        # Act
        # _get_recommendation_mappings_for_job をRuntimeErrorで失敗させて
        # outer except（L250）をトリガー
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis._get_recommendation_mappings_for_job",
                   new_callable=AsyncMock, side_effect=RuntimeError("fatal error")), \
             patch("app.jobs.utils.scan_analysis.traceback"), \
             patch("builtins.print"):
            results, mapping = await _generate_comprehensive_policy_results("scan-e05")

        # Assert
        assert results == []
        assert mapping == {}

    @pytest.mark.asyncio
    async def test_summarize_client_none(self):
        """SA-E06: summarize_index_contentでクライアントNone

        scan_analysis.py:L343-344 のクライアントNullチェックをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=None), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"):
            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        assert result == "Error: OpenSearch client is not available."

    @pytest.mark.asyncio
    async def test_summarize_invalid_index_name(self):
        """SA-E07: 無効なindex_name → Errorメッセージ

        scan_analysis.py:L345-346 の無効index判定をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"):
            result = await summarize_index_content("N/A (No index selected)")

        # Assert
        assert result == "Error: index_name is required."

    @pytest.mark.asyncio
    async def test_transport_error_404(self):
        """SA-E08: TransportError 404 → Index not found

        scan_analysis.py:L612-616 のTransportError 404分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.side_effect = TransportError(
            404, "index_not_found_exception",
            {"error": {"type": "index_not_found_exception"}}
        )

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"):
            result = await summarize_index_content("nonexistent-index")

        # Assert
        assert "not found" in result

    @pytest.mark.asyncio
    async def test_transport_error_other(self):
        """SA-E09: TransportError 500 → transport error メッセージ

        scan_analysis.py:L617 のTransportError非404分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.side_effect = TransportError(
            500, "internal_server_error",
            {"error": {"type": "internal_server_error"}}
        )

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"):
            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        assert "transport error" in result

    @pytest.mark.asyncio
    async def test_summarize_unexpected_exception(self):
        """SA-E10: 汎用Exception → unexpected error メッセージ

        scan_analysis.py:L618-622 の汎用exceptをカバー。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.side_effect = RuntimeError("unknown failure")

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis.traceback"):
            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        assert "unexpected error" in result.lower()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SA-SEC-01 | エラーレスポンス・ログにAPIキー非露出 | APIキーを含む例外 | レスポンス文字列とログ出力の両方にAPIキーが含まれないことを確認 |
| SA-SEC-02 | ログインジェクション耐性 | CRLFを含むindex_name | クラッシュせず処理完了 |
| SA-SEC-03 | print文のセキュリティリスク | 機密情報を含む例外 | print出力に機密情報が露出する（既知の問題） |

```python
@pytest.mark.security
class TestScanAnalysisSecurity:
    """scan_analysis セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SA-SEC-01: scan_analysis.py:L619-620 で str(e) をそのまま"
               "ログ出力およびエラーメッセージに含めるため、APIキーが露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_error_response_and_log(self):
        """SA-SEC-01: 例外メッセージのAPIキーがレスポンス・ログに露出しない

        scan_analysis.py:L619-620 の logger.error() と L622 の return 文に
        str(e) が含まれるため、APIキー等が含まれる場合にログ・レスポンスの
        両方に露出する。

        [EXPECTED_TO_FAIL] str(e) をそのままエラーメッセージに含めるため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"
        secret_exception = RuntimeError(f"Auth failed: key={fake_key}")

        mock_client = AsyncMock()
        mock_client.search.side_effect = secret_exception

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger") as MockLogger, \
             patch("app.jobs.utils.scan_analysis.traceback"):
            result = await summarize_index_content("cspm-scan-result-v2")

        # Assert
        # 1. レスポンス文字列にAPIキーが含まれないこと（L622で失敗）
        assert fake_key not in result

        # 2. ログ出力にAPIキーが含まれないこと（L619-620で失敗）
        mock_logger_instance = MockLogger.return_value
        for call in mock_logger_instance.method_calls:
            call_str = str(call)
            assert fake_key not in call_str, (
                f"ログ出力にAPIキーが露出: {call.args[0] if call.args else call}"
            )

    @pytest.mark.asyncio
    async def test_log_injection_resilience(self):
        """SA-SEC-02: CRLFを含むindex_name/job_idでクラッシュしない

        scan_analysis.py:L338 の TaskLogger および L340 の logger.info に
        改行文字を含む入力が渡された場合でも処理を完了することを確認。

        本テストは例外が送出されず正常完了することを暗黙的に検証する。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import summarize_index_content

        mock_client = AsyncMock()
        mock_client.search.side_effect = TransportError(
            404, "not_found", {"error": "not found"}
        )

        # Act - 例外が発生しないこと（暗黙的検証）
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("app.jobs.utils.scan_analysis.TaskLogger"):
            result = await summarize_index_content(
                "test-index\r\nInjected-Header: malicious",
                job_id="job\nfake-log-entry"
            )

        # Assert
        assert isinstance(result, str)

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SA-SEC-03: scan_analysis.py:L95/L174/L251 で print() を使用しており、"
               "例外メッセージがstdoutに直接出力される。logger使用への変更が必要。",
        strict=True,
        raises=AssertionError,
    )
    async def test_print_does_not_expose_secrets(self):
        """SA-SEC-03: print文による機密情報の標準出力への露出

        scan_analysis.py:L95 の print(f"[Recommendation Mapping Error] {str(e)}")
        により、例外メッセージがstdoutに直接出力される。

        [EXPECTED_TO_FAIL] print() を使用しているため、
        現行実装ではこのテストは失敗する。loggerへの変更を推奨。
        """
        # Arrange
        from app.jobs.utils.scan_analysis import _get_recommendation_mappings_for_job

        fake_key = "FAKE-SECRET-KEY-FOR-TESTING-99999"
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception(f"Auth error: key={fake_key}")

        # Act
        with patch("app.jobs.utils.scan_analysis.get_opensearch_client",
                   new_callable=AsyncMock, return_value=mock_client), \
             patch("builtins.print") as mock_print:
            await _get_recommendation_mappings_for_job("job-sec03")

        # Assert
        # 理想: 全print出力にAPIキーが含まれないこと（現行実装では失敗）
        # call_args_list で全呼び出しを検証（call_args は最終呼び出しのみ）
        for call in mock_print.call_args_list:
            print_output = str(call)
            assert fake_key not in print_output, (
                f"print出力にAPIキーが露出: {call.args[0] if call.args else call}"
            )
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

> **注記**: `scan_analysis` はモジュールレベルで `opensearchpy.TransportError`、`get_opensearch_client`、`TaskLogger` をインポート（L14-17）する。これらは標準的なインポートで、`langchain` のような重い初期化副作用はないが、`get_opensearch_client` がインポート時に設定を参照する可能性がある点に注意。conftest.py は `test/unit/jobs/utils/conftest.py`（#17a で定義予定）を共有する。

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

_TARGET_MODULES = (
    "app.jobs.utils.scan_analysis",
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

> **注記**: conftest.py は #17a〜#17f と共有予定。実装時には既存の `_TARGET_MODULES` タプルに `"app.jobs.utils.scan_analysis"` を追加する形で統合する。

---

## 6. テスト実行例

```bash
# スキャン分析テストのみ実行
pytest test/unit/jobs/utils/test_scan_analysis.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_scan_analysis.py::TestSummarizeIndexContent -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_scan_analysis.py \
  --cov=app.jobs.utils.scan_analysis \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_scan_analysis.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 17 | SA-001 〜 SA-017 |
| 異常系 | 10 | SA-E01 〜 SA-E10 |
| セキュリティ | 3 | SA-SEC-01 〜 SA-SEC-03 |
| **合計** | **30** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetRecommendationMappings` | SA-001〜SA-004 | 4 |
| `TestGenerateComprehensivePolicyResults` | SA-005〜SA-007 | 3 |
| `TestMapPolicyNames` | SA-008〜SA-010 | 3 |
| `TestSummarizeIndexContent` | SA-011〜SA-017 | 7 |
| `TestScanAnalysisErrors` | SA-E01〜SA-E10 | 10 |
| `TestScanAnalysisSecurity` | SA-SEC-01〜SA-SEC-03 | 3 |

### 7.1 予想失敗テスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| SA-SEC-01 | scan_analysis.py:L619-620 の `logger.error()` と L622 の `return` 文の両方で `str(e)` をそのまま使用しており、例外メッセージのAPIキーがログとレスポンスの双方に露出する | (1) エラーレスポンス（L622）から `str(e)` を除去し一般的なメッセージのみ返す (2) ログ出力（L619-620）でも `str(e)` をマスクまたは汎用メッセージに置換する |
| SA-SEC-03 | scan_analysis.py:L95/L174/L251 で `print()` を使用しており、`str(e)` がstdoutに直接出力される | `print()` を `logger.error()` に置換。loggerはマスク処理やログレベル制御が可能 |

### xfail 解除手順

1. `scan_analysis.py` の `print()` 文（L95, L174, L247, L251）を `logger.error()` / `logger.warning()` に置換
2. `str(e)` をエラーレスポンス（L622）から除去し、一般的なエラーメッセージのみ返す
3. `str(e)` をログ出力（L619-620）でもマスクまたは汎用メッセージに置換する
4. 上記修正後、SA-SEC-01 および SA-SEC-03 の `@pytest.mark.xfail(...)` デコレータを削除
5. テスト実行で PASS を確認

### 注意事項

- `pytest-asyncio` パッケージが必要（全関数がasync）
- `opensearchpy.TransportError` は実型を使用（モック不要）
- OpenSearchクライアントは `AsyncMock()` で完全モック化
- `_get_recommendation_mappings_for_job` と `_generate_comprehensive_policy_results` はプライベート関数だが、分岐が多いため直接テストする
- `summarize_index_content` テストでは内部関数をモックして単体テストの範囲を限定する
- `print()` 文（L95, L174, L247, L251）はloggerではなくstdoutに直接出力するため、テスト時にはノイズとなる。`patch("builtins.print")` で抑制可能

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | OpenSearch集計クエリの構築ロジック（L350-416）はテスト困難 | クエリの正確性は統合テストでしか検証不可 | 単体テストではレスポンスの解析ロジックのみ検証 |
| 2 | インサイト生成（L540-607）の全分岐組み合わせは膨大 | 全パターンの単体テスト網羅はコスト高 | 主要パスのみカバー（SA-014〜SA-016）。全組み合わせはE2Eテストで補完 |
| 3 | `print()` 文（L95, L174, L247, L251）がloggerの代わりに使用されている | テスト実行時のノイズ、APIキー含む例外メッセージのstdout露出リスク | SA-SEC-03 で現行動作を記録（`xfail`）。`logger` への置換を推奨 |
| 4 | `traceback.print_exc()` (L175, L252, L621) がstderrに直接出力 | テスト実行時のノイズ、スタックトレースの露出リスク | テスト内で `traceback` をモック。実装側では `logger.debug(traceback.format_exc())` への変更を推奨 |
| 5 | `str(e)` がエラーレスポンス文字列に直接含まれる（L622） | 例外メッセージに機密情報が含まれる場合に呼び出し元へ露出 | SA-SEC-01 で記録（`xfail`）。将来的にマスク処理の導入を推奨 |
| 6 | `_generate_comprehensive_policy_results` 内部のOpenSearch検索失敗（L173）が `print()` + `traceback.print_exc()` のみで処理される | エラー情報がloggerに記録されないためモニタリング不可 | loggerへの統一を推奨 |
| 7 | `index_name` / `job_id` 等の外部入力にCRLFが含まれる可能性 | ログインジェクションのリスク | SA-SEC-02 で動作確認済み。実装側でのサニタイズはこのモジュールの責務外 |
| 8 | 未スキャン推奨事項のステータスが常に "適合"（L239） | 実際には "リソースなし" の可能性がある（L239のコメント参照） | 現行実装の制約として SA-006 で "適合" を検証。将来的にステータス判定ロジックの改善を推奨 |
