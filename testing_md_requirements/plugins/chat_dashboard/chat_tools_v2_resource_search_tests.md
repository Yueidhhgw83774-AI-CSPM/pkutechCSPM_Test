# chat_tools_v2 / resource_search_v2 テストケース

## 1. 概要

scan-result v2対応のチャットツールとリソース検索ユーティリティのテストケースを定義します。`chat_tools_v2.py`はv2対応の@tool関数（`get_resource_details_v2`, `quick_resource_search_tool`）と結果フォーマッタを提供し、`resource_search_v2.py`はアプリケーション側での効率的なリソース検索・フィルタリング・キャッシュ機能を提供します。

### 1.1 主要機能

#### chat_tools_v2.py（PREFIX: CTV2）

| 機能 | 説明 |
|------|------|
| `get_resource_details_v2` | @tool: v2対応リソース詳細取得（enabled:false対応の効率的検索） |
| `quick_resource_search_tool` | @tool: クイックリソース検索（検索語の自動判定） |
| `_format_resource_results_v2` | フォーマッタ: v2対応の結果フォーマット（重要度別統計・パフォーマンス情報付き） |
| `_format_quick_search_results` | フォーマッタ: クイック検索結果のフォーマット |

#### resource_search_v2.py（PREFIX: RSRCH）

| 機能 | 説明 |
|------|------|
| `ResourceFilter` | dataclass: リソース検索フィルター条件（9フィールド） |
| `PolicyFilter` | dataclass: ポリシー検索フィルター条件（5フィールド） |
| `EfficientResourceSearch` | クラス: v2対応の効率的リソース検索（2フェーズ：OpenSearch＋アプリ側フィルタ） |
| `EfficientResourceSearch.search_resources` | メソッド: メイン検索（フィルター適用・結果統合） |
| `EfficientResourceSearch._opensearch_base_filter` | メソッド: OpenSearch側での基本絞り込み |
| `EfficientResourceSearch._application_side_filter` | メソッド: アプリ側での詳細フィルタリング（並列処理） |
| `EfficientResourceSearch._process_document` | メソッド: 単一ドキュメントの処理 |
| `EfficientResourceSearch._match_policy_filter` | メソッド: ポリシーレベルのマッチング判定 |
| `EfficientResourceSearch._match_resource_filter` | メソッド: リソースレベルのマッチング判定（7種フィルタ） |
| `EfficientResourceSearch._match_tags` | メソッド: タグマッチング |
| `EfficientResourceSearch._match_ip_range` | メソッド: IP範囲マッチング（セキュリティグループ） |
| `EfficientResourceSearch._consolidate_results` | メソッド: 結果の統合・ランキング・統計情報生成 |
| `create_common_filters` | ヘルパー: よく使われるフィルター組み合わせの定義 |
| `quick_resource_search` | ヘルパー: 検索語からの自動判定フィルター作成・検索実行 |
| `ResourceIndexCache` | クラス: リソース検索の高速化キャッシュ |
| `ResourceIndexCache.build_index` | メソッド: 検索インデックスを構築 |
| `ResourceIndexCache.find_by_id` | メソッド: リソースIDでの高速検索 |
| `ResourceIndexCache.find_by_policy` | メソッド: ポリシー名でのリソース一覧取得 |

### 1.2 カバレッジ目標: 85%

> **注記**: `resource_search_v2.py`は純粋なロジック（フィルタリング・ソート・統計）が多く、高いカバレッジが達成可能。`chat_tools_v2.py`はOpenSearch接続部分をモック化。`EfficientResourceSearch`の各フィルタメソッドは分岐が多いため重点的にカバー。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/chat_dashboard/chat_tools_v2.py`（297行） |
| テスト対象2 | `app/chat_dashboard/resource_search_v2.py`（494行） |
| テストコード | `test/unit/chat_dashboard/test_chat_tools_v2.py` |
| テストコード | `test/unit/chat_dashboard/test_resource_search_v2.py` |
| conftest | `test/unit/chat_dashboard/conftest.py` |

### 1.4 補足情報

**モジュール依存関係:**
- `chat_tools_v2.py` → `resource_search_v2.py`（`EfficientResourceSearch`, `ResourceFilter`, `PolicyFilter`, `quick_resource_search`）
- `chat_tools_v2.py` → `chat_tools.py`（`get_current_scan_info`, `search_historical_scan`, `compare_scan_violations`, `get_policy_recommendations`）— モジュールレベルimport
- `chat_tools_v2.py` → `basic_auth_logic.py`（`decode_basic_auth`）— モジュールレベルimport
- `chat_tools_v2.py` → `app.core.clients`（`get_opensearch_client`, `get_opensearch_client_with_auth`）— モジュールレベルimport

**mockパス（全てモジュールレベルimportのため `app.chat_dashboard.chat_tools_v2.*` でパッチ）:**
- `app.chat_dashboard.chat_tools_v2.get_opensearch_client`
- `app.chat_dashboard.chat_tools_v2.get_opensearch_client_with_auth`
- `app.chat_dashboard.chat_tools_v2.decode_basic_auth`
- `app.chat_dashboard.chat_tools_v2.EfficientResourceSearch`
- `app.chat_dashboard.chat_tools_v2.quick_resource_search`

**エイリアス（`chat_tools_v2.py:296-298`）:**
- `get_scan_info = get_current_scan_info`（互換性維持）
- `compare_violations = compare_scan_violations`（互換性維持）

**主要な分岐ポイント（resource_search_v2.py）:**
- `_match_resource_filter`: resource_id / resource_name / vpc_id / instance_type / state / tag / ip_range の7種フィルタ
- `_match_tags`: tag_key / tag_value の組み合わせマッチ
- `_match_ip_range`: インバウンド / アウトバウンドルールのチェック
- `_consolidate_results`: severity_orderによるソート（Critical > High > Medium > Low）
- `quick_resource_search`: 検索語の自動判定（リソースID / IP範囲 / ポリシー名 / 重要度 / キーワード の5パターン）

**テストID接頭辞:**
- chat_tools_v2 正常系: `CTV2-001` 〜
- chat_tools_v2 異常系: `CTV2-E01` 〜
- chat_tools_v2 セキュリティ: `CTV2-SEC-01` 〜
- resource_search_v2 正常系: `RSRCH-001` 〜
- resource_search_v2 異常系: `RSRCH-E01` 〜
- resource_search_v2 セキュリティ: `RSRCH-SEC-01` 〜

---

## 2. 正常系テストケース

### chat_tools_v2.py 正常系

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTV2-001 | フィルターなしリソース詳細取得 | scan_id="scan_123" | 全リソース情報がマークダウン形式で返却 |
| CTV2-002 | ポリシー名フィルター付き取得 | scan_id, policy_name="sg-rule" | PolicyFilter(policy_name=...)で検索実行 |
| CTV2-003 | リソースIDフィルター付き取得 | scan_id, resource_id="i-123" | ResourceFilter(resource_id=...)で検索実行 |
| CTV2-004 | 重要度フィルター付き取得 | scan_id, severity="Critical" | PolicyFilter(severity=...)で検索実行 |
| CTV2-005 | リソースタイプフィルター付き取得 | scan_id, resource_type="ec2" | ResourceFilter(resource_type=...)で検索実行 |
| CTV2-006 | 複合フィルター付き取得 | scan_id, policy_name, resource_id, severity | ResourceFilter+PolicyFilter両方で検索 |
| CTV2-007 | Basic認証プレフィックス付き認証 | opensearch_auth="Basic dXNlcjpwYXNz" | "Basic "を除去してdecode_basic_auth呼び出し |
| CTV2-008 | 認証なし（デフォルトクライアント） | opensearch_auth=None | get_opensearch_client()で初期化 |
| CTV2-009 | クイック検索（リソースID） | search_term="i-1234567890" | quick_resource_search呼び出し |
| CTV2-010 | クイック検索（IP範囲） | search_term="0.0.0.0/0" | quick_resource_search呼び出し |
| CTV2-011 | クイック検索（重要度） | search_term="Critical" | quick_resource_search呼び出し |
| CTV2-012 | クイック検索（キーワード） | search_term="暗号化" | quick_resource_search呼び出し |
| CTV2-013 | v2結果フォーマット（基本） | 2ポリシー・各3リソースの結果 | 重要度統計・パフォーマンス情報含むマークダウン |
| CTV2-014 | v2結果フォーマット（10ポリシー超） | 12ポリシーの結果 | 10件表示＋「他2件のポリシー」表示 |
| CTV2-015 | v2結果フォーマット（VPC・State・IpPermissions付き） | SG詳細リソース | VPC・状態・インバウンド情報を表示 |
| CTV2-016 | v2結果フォーマット（State文字列型） | State="running" | 文字列Stateを表示 |
| CTV2-017 | v2結果フォーマット（リソース3件超省略） | 5リソース | 3件表示＋「他2件のリソース」 |
| CTV2-018 | クイック検索結果フォーマット（基本） | 3ポリシーの結果 | 番号付きリスト表示 |
| CTV2-019 | クイック検索結果フォーマット（5件超） | 7ポリシーの結果 | 5件表示＋「他2件」表示 |

### 2.1 TestGetResourceDetailsV2 テスト

```python
# test/unit/chat_dashboard/test_chat_tools_v2.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.chat_dashboard.chat_tools_v2 import (
    get_resource_details_v2,
    quick_resource_search_tool,
    _format_resource_results_v2,
    _format_quick_search_results,
)


class TestGetResourceDetailsV2:
    """v2リソース詳細取得のテスト"""

    @pytest.mark.asyncio
    async def test_no_filter(self):
        """CTV2-001: フィルターなしでリソース詳細取得"""
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1,
            "total_resources": 2,
            "severity_stats": {"High": {"policies": 1, "resources": 2}},
            "policies": [{
                "policy_name": "test-policy",
                "violation_summary": {"severity": "High"},
                "matched_resources": [
                    {"resource_id": "i-111", "custodian_resource": {"Name": "web-1"}},
                    {"resource_id": "i-222", "custodian_resource": {"Name": "web-2"}},
                ],
            }],
            "search_performance": {"total_evaluated": 5, "matched": 1},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123"
            })

            # Assert
            assert "リソース詳細情報" in result
            assert "scan_123" in result
            mock_searcher.search_resources.assert_called_once()
            call_kwargs = mock_searcher.search_resources.call_args
            assert call_kwargs.kwargs.get("resource_filter") is None
            assert call_kwargs.kwargs.get("policy_filter") is None

    @pytest.mark.asyncio
    async def test_policy_name_filter(self):
        """CTV2-002: ポリシー名フィルター付き取得"""
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "sg-rule",
                "violation_summary": {"severity": "High"},
                "matched_resources": [{"resource_id": "sg-1", "custodian_resource": {}}],
            }],
            "search_performance": {"total_evaluated": 1, "matched": 1},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123", "policy_name": "sg-rule"
            })

            # Assert
            call_kwargs = mock_searcher.search_resources.call_args
            policy_filter = call_kwargs.kwargs.get("policy_filter")
            assert policy_filter is not None
            assert policy_filter.policy_name == "sg-rule"

    @pytest.mark.asyncio
    async def test_resource_id_filter(self):
        """CTV2-003: リソースIDフィルター付き取得"""
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "p1",
                "violation_summary": {"severity": "Medium"},
                "matched_resources": [{"resource_id": "i-123", "custodian_resource": {}}],
            }],
            "search_performance": {"total_evaluated": 1, "matched": 1},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123", "resource_id": "i-123"
            })

            # Assert
            call_kwargs = mock_searcher.search_resources.call_args
            resource_filter = call_kwargs.kwargs.get("resource_filter")
            assert resource_filter is not None
            assert resource_filter.resource_id == "i-123"

    @pytest.mark.asyncio
    async def test_severity_filter(self):
        """CTV2-004: 重要度フィルター付き取得"""
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "p1",
                "violation_summary": {"severity": "Critical"},
                "matched_resources": [{"resource_id": "r-1", "custodian_resource": {}}],
            }],
            "search_performance": {"total_evaluated": 1, "matched": 1},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123", "severity": "Critical"
            })

            # Assert
            call_kwargs = mock_searcher.search_resources.call_args
            policy_filter = call_kwargs.kwargs.get("policy_filter")
            assert policy_filter is not None
            assert policy_filter.severity == "Critical"

    @pytest.mark.asyncio
    async def test_resource_type_filter(self):
        """CTV2-005: リソースタイプフィルター付き取得

        chat_tools_v2.py:87 の resource_type 分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "p1",
                "violation_summary": {"severity": "Medium"},
                "matched_resources": [{"resource_id": "i-1", "custodian_resource": {}}],
            }],
            "search_performance": {"total_evaluated": 1, "matched": 1},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123", "resource_type": "ec2"
            })

            # Assert
            call_kwargs = mock_searcher.search_resources.call_args
            resource_filter = call_kwargs.kwargs.get("resource_filter")
            assert resource_filter is not None
            assert resource_filter.resource_type == "ec2"

    @pytest.mark.asyncio
    async def test_combined_filters(self):
        """CTV2-006: 複合フィルター（リソースID＋重要度＋ポリシー名）"""
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "sg-rule",
                "violation_summary": {"severity": "Critical"},
                "matched_resources": [{"resource_id": "i-999", "custodian_resource": {}}],
            }],
            "search_performance": {"total_evaluated": 1, "matched": 1},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123",
                "resource_id": "i-999",
                "severity": "Critical",
                "policy_name": "sg-rule",
            })

            # Assert
            call_kwargs = mock_searcher.search_resources.call_args
            rf = call_kwargs.kwargs.get("resource_filter")
            pf = call_kwargs.kwargs.get("policy_filter")
            assert rf is not None and rf.resource_id == "i-999"
            assert pf is not None and pf.severity == "Critical"
            assert pf.policy_name == "sg-rule"

    @pytest.mark.asyncio
    async def test_basic_auth_prefix(self):
        """CTV2-007: "Basic "プレフィックス付き認証トークン処理

        chat_tools_v2.py:64 の条件分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [],
            "search_performance": {"total_evaluated": 0, "matched": 0},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client_with_auth",
                    new_callable=AsyncMock, return_value=mock_client) as mock_auth_client, \
             patch("app.chat_dashboard.chat_tools_v2.decode_basic_auth",
                   return_value=("test", "test")) as mock_decode, \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123",
                "opensearch_auth": "Basic dGVzdDp0ZXN0",  # base64("test:test")
            })

            # Assert — "Basic " が除去されてdecodeに渡される
            mock_decode.assert_called_once_with("dGVzdDp0ZXN0")
            mock_auth_client.assert_called_once_with("test:test")

    @pytest.mark.asyncio
    async def test_default_client_no_auth(self):
        """CTV2-008: 認証なし時はデフォルトクライアント使用"""
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 0, "total_resources": 0,
            "severity_stats": {}, "policies": [],
            "search_performance": {},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client) as mock_default, \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            await get_resource_details_v2.ainvoke({"scan_id": "scan_123"})

            # Assert
            mock_default.assert_called_once()


class TestQuickResourceSearchTool:
    """クイック検索ツールのテスト"""

    @pytest.mark.asyncio
    async def test_search_resource_id(self):
        """CTV2-009: リソースID検索"""
        # Arrange
        mock_client = AsyncMock()
        mock_qs = AsyncMock(return_value={
            "total_policies": 1, "total_resources": 1,
            "policies": [{"policy_name": "p1", "violation_summary": {"severity": "High"},
                          "matched_resources": []}],
        })

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search",
                   mock_qs):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "i-1234567890"
            })

            # Assert
            assert "クイック検索結果" in result
            mock_qs.assert_called_once_with(mock_client, "scan_123", "i-1234567890")

    @pytest.mark.asyncio
    async def test_search_ip_range(self):
        """CTV2-010: IP範囲検索"""
        # Arrange
        mock_client = AsyncMock()
        mock_qs = AsyncMock(return_value={
            "total_policies": 1, "total_resources": 2,
            "policies": [{"policy_name": "sg-open", "violation_summary": {"severity": "Critical"},
                          "matched_resources": [{}, {}]}],
        })

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search", mock_qs):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "0.0.0.0/0"
            })

            # Assert
            assert "クイック検索結果" in result

    @pytest.mark.asyncio
    async def test_search_severity(self):
        """CTV2-011: 重要度キーワード検索"""
        # Arrange
        mock_client = AsyncMock()
        mock_qs = AsyncMock(return_value={
            "total_policies": 2, "total_resources": 5,
            "policies": [
                {"policy_name": "p1", "violation_summary": {"severity": "Critical"},
                 "matched_resources": [{}, {}, {}]},
                {"policy_name": "p2", "violation_summary": {"severity": "Critical"},
                 "matched_resources": [{}, {}]},
            ],
        })

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search", mock_qs):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "Critical"
            })

            # Assert
            assert "2ポリシー" in result

    @pytest.mark.asyncio
    async def test_search_keyword(self):
        """CTV2-012: 一般キーワード検索"""
        # Arrange
        mock_client = AsyncMock()
        mock_qs = AsyncMock(return_value={
            "total_policies": 1, "total_resources": 3,
            "policies": [{"policy_name": "enc-policy",
                          "violation_summary": {"severity": "Medium"},
                          "matched_resources": [{}, {}, {}]}],
        })

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search", mock_qs):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "暗号化"
            })

            # Assert
            assert "暗号化" in result


class TestFormatResourceResultsV2:
    """v2結果フォーマットのテスト"""

    def test_basic_format(self):
        """CTV2-013: 基本的な結果フォーマット（重要度統計・パフォーマンス情報付き）"""
        # Arrange
        results = {
            "total_policies": 2,
            "total_resources": 4,
            "severity_stats": {
                "Critical": {"policies": 1, "resources": 2},
                "High": {"policies": 1, "resources": 2},
            },
            "policies": [
                {
                    "policy_name": "open-sg",
                    "violation_summary": {"severity": "Critical", "recommendation_uuid": "uuid-1"},
                    "region": "ap-northeast-1",
                    "matched_resources": [
                        {"resource_id": "sg-111", "custodian_resource": {"GroupName": "default"}},
                        {"resource_id": "sg-222", "custodian_resource": {"GroupName": "web"}},
                    ],
                },
                {
                    "policy_name": "unencrypted-ebs",
                    "violation_summary": {"severity": "High", "recommendation_uuid": "uuid-2"},
                    "region": "us-east-1",
                    "matched_resources": [
                        {"resource_id": "vol-aaa", "custodian_resource": {"Name": "data-vol"}},
                        {"resource_id": "vol-bbb", "custodian_resource": {}},
                    ],
                },
            ],
            "search_performance": {"total_evaluated": 10, "matched": 2},
        }

        # Act
        result = _format_resource_results_v2("scan_123", results)

        # Assert
        assert "リソース詳細情報" in result
        assert "scan_123" in result
        assert "2ポリシー" in result
        assert "4リソース" in result
        assert "Critical" in result
        assert "High" in result
        assert "10件処理" in result
        assert "open-sg" in result
        assert "unencrypted-ebs" in result

    def test_more_than_10_policies(self):
        """CTV2-014: 10ポリシー超のフォーマット

        chat_tools_v2.py:263 の分岐をカバー。
        """
        # Arrange
        policies = []
        for i in range(12):
            policies.append({
                "policy_name": f"policy-{i}",
                "violation_summary": {"severity": "Medium"},
                "region": "ap-northeast-1",
                "matched_resources": [{"resource_id": f"r-{i}", "custodian_resource": {}}],
            })
        results = {
            "total_policies": 12, "total_resources": 12,
            "severity_stats": {}, "policies": policies,
            "search_performance": {},
        }

        # Act
        result = _format_resource_results_v2("scan_123", results)

        # Assert
        assert "他2件のポリシー" in result
        # policy-0〜policy-9 は表示され、policy-10, policy-11 は省略
        assert "policy-9" in result

    def test_resource_with_vpc_and_state_dict(self):
        """CTV2-015: VPC・State(dict)・IpPermissions付きリソースフォーマット

        chat_tools_v2.py:240-258 の分岐をカバー。
        """
        # Arrange
        results = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "sg-check",
                "violation_summary": {"severity": "Critical"},
                "region": "us-east-1",
                "matched_resources": [{
                    "resource_id": "sg-abc",
                    "custodian_resource": {
                        "GroupName": "my-sg",
                        "VpcId": "vpc-123",
                        "State": {"Name": "active"},
                        "IpPermissions": [
                            {"IpProtocol": "tcp", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                        ],
                    },
                }],
            }],
            "search_performance": {},
        }

        # Act
        result = _format_resource_results_v2("scan_123", results)

        # Assert
        assert "vpc-123" in result
        assert "active" in result
        assert "インバウンド" in result
        assert "0.0.0.0/0" in result

    def test_resource_with_state_string(self):
        """CTV2-016: State が文字列の場合のフォーマット

        chat_tools_v2.py:247 の else 分岐をカバー。
        """
        # Arrange
        results = {
            "total_policies": 1, "total_resources": 1,
            "severity_stats": {}, "policies": [{
                "policy_name": "ec2-check",
                "violation_summary": {"severity": "Low"},
                "region": "us-east-1",
                "matched_resources": [{
                    "resource_id": "i-str",
                    "custodian_resource": {"InstanceId": "i-str", "State": "running"},
                }],
            }],
            "search_performance": {},
        }

        # Act
        result = _format_resource_results_v2("scan_123", results)

        # Assert
        assert "running" in result

    def test_more_than_3_resources_truncation(self):
        """CTV2-017: リソース3件超で省略表示

        chat_tools_v2.py:260-261 の分岐をカバー。
        """
        # Arrange
        resources = [
            {"resource_id": f"r-{i}", "custodian_resource": {"Name": f"res-{i}"}}
            for i in range(5)
        ]
        results = {
            "total_policies": 1, "total_resources": 5,
            "severity_stats": {}, "policies": [{
                "policy_name": "policy-many",
                "violation_summary": {"severity": "High"},
                "region": "us-east-1",
                "matched_resources": resources,
            }],
            "search_performance": {},
        }

        # Act
        result = _format_resource_results_v2("scan_123", results)

        # Assert
        assert "他2件のリソース" in result


class TestFormatQuickSearchResults:
    """クイック検索結果フォーマットのテスト"""

    def test_basic_format(self):
        """CTV2-018: 基本的なクイック検索結果フォーマット"""
        # Arrange
        results = {
            "total_policies": 3, "total_resources": 8,
            "policies": [
                {"policy_name": "p1", "violation_summary": {"severity": "Critical"},
                 "matched_resources": [{}, {}, {}]},
                {"policy_name": "p2", "violation_summary": {"severity": "High"},
                 "matched_resources": [{}, {}]},
                {"policy_name": "p3", "violation_summary": {"severity": "Medium"},
                 "matched_resources": [{}, {}, {}]},
            ],
        }

        # Act
        result = _format_quick_search_results("scan_123", "暗号化", results)

        # Assert
        assert "クイック検索結果" in result
        assert "暗号化" in result
        assert "3ポリシー" in result
        assert "8リソース" in result
        assert "1. **p1**" in result
        assert "get_resource_details_v2" in result

    def test_more_than_5_policies(self):
        """CTV2-019: 5ポリシー超のクイック検索結果

        chat_tools_v2.py:288 の分岐をカバー。
        """
        # Arrange
        policies = [
            {"policy_name": f"p{i}", "violation_summary": {"severity": "Low"},
             "matched_resources": [{}]}
            for i in range(7)
        ]
        results = {"total_policies": 7, "total_resources": 7, "policies": policies}

        # Act
        result = _format_quick_search_results("scan_123", "test", results)

        # Assert
        assert "他2件" in result
```

---

### resource_search_v2.py 正常系

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RSRCH-001 | ResourceFilter デフォルト値 | ResourceFilter() | 全フィールドNone |
| RSRCH-002 | PolicyFilter デフォルト値 | PolicyFilter() | 全フィールドNone |
| RSRCH-003 | EfficientResourceSearch 初期化 | opensearch_client | client・キャッシュ初期化 |
| RSRCH-004 | search_resources フィルターなし | scan_id のみ | 全結果返却 |
| RSRCH-005 | search_resources ポリシーフィルター | PolicyFilter指定 | フィルタ適用結果 |
| RSRCH-006 | search_resources リソースフィルター | ResourceFilter指定 | フィルタ適用結果 |
| RSRCH-007 | _opensearch_base_filter 基本クエリ | scan_id のみ | scan_id + resource_count>0 |
| RSRCH-008 | _opensearch_base_filter severity条件 | PolicyFilter(severity="Critical") | severity term追加 |
| RSRCH-009 | _opensearch_base_filter policy_name条件 | PolicyFilter(policy_name="sg") | wildcard追加 |
| RSRCH-010 | _opensearch_base_filter recommendation_uuid条件 | PolicyFilter(recommendation_uuid="uuid-1") | term追加 |
| RSRCH-011 | _match_policy_filter description_keywords一致 | keywords=["暗号化"] | True |
| RSRCH-012 | _match_policy_filter description_keywords不一致 | keywords=["不存在"] | False |
| RSRCH-013 | _match_policy_filter resource_type一致 | resource_type="ec2" | True |
| RSRCH-014 | _match_policy_filter resource_type不一致 | resource_type="s3" | False |
| RSRCH-015 | _match_resource_filter resource_id一致 | resource_id="i-123" | True |
| RSRCH-016 | _match_resource_filter resource_name一致（Name） | resource_name="web" | True |
| RSRCH-017 | _match_resource_filter resource_name一致（GroupName） | resource_name="default" | True |
| RSRCH-018 | _match_resource_filter vpc_id一致 | vpc_id="vpc-123" | True |
| RSRCH-019 | _match_resource_filter vpc_id不一致 | vpc_id="vpc-123" vs "vpc-999" | False |
| RSRCH-020 | _match_resource_filter instance_type一致 | instance_type="t3.micro" | True |
| RSRCH-021 | _match_resource_filter state一致（dict型） | state="running" | True |
| RSRCH-022 | _match_resource_filter state一致（str型） | state="active" | True |
| RSRCH-023 | _match_resource_filter タグフィルター | tag_key="Environment" | True（_match_tags経由でマッチ） |
| RSRCH-024 | _match_resource_filter IP範囲フィルター | ip_range="0.0.0.0/0" | True（_match_ip_range経由でマッチ） |
| RSRCH-025 | _match_tags key一致 | tag_key="Name" | True |
| RSRCH-026 | _match_tags value一致 | tag_value="production" | True |
| RSRCH-027 | _match_tags key+value両方一致 | tag_key="Env", tag_value="prod" | True |
| RSRCH-028 | _match_ip_range インバウンド一致 | IpPermissions内CidrIp一致 | True |
| RSRCH-029 | _match_ip_range アウトバウンド一致 | IpPermissionsEgress内CidrIp一致 | True |
| RSRCH-030 | _consolidate_results 重要度ソート | Critical+High+Medium混在 | Critical→High→Medium順 |
| RSRCH-031 | _consolidate_results max_results制限 | 10件結果, max_results=3 | 3件に制限 |
| RSRCH-032 | _consolidate_results 統計情報 | 複数重要度混在 | severity_stats正確 |
| RSRCH-033 | quick_resource_search リソースID判定 | "i-1234" | ResourceFilter(resource_id=...) |
| RSRCH-034 | quick_resource_search IP範囲判定 | "10.0.0.0/8" | ResourceFilter(ip_range=...) |
| RSRCH-035 | quick_resource_search ポリシー名判定 | "policy-sg-check" | PolicyFilter(policy_name=...) |
| RSRCH-036 | quick_resource_search 重要度判定 | "critical" | PolicyFilter(severity="Critical") |
| RSRCH-037 | quick_resource_search キーワード判定 | "暗号化" | PolicyFilter(description_keywords=["暗号化"]) |
| RSRCH-038 | create_common_filters 定義確認 | なし | 5つのフィルター定義 |
| RSRCH-039 | ResourceIndexCache build_index | スキャン結果リスト | インデックス構築 |
| RSRCH-040 | ResourceIndexCache find_by_id | 存在するID | リソース返却 |
| RSRCH-041 | ResourceIndexCache find_by_policy | 存在するポリシー | リソースリスト返却 |
| RSRCH-042 | _match_policy_filter フィルター条件なし | PolicyFilter() (全None) | True（無条件マッチ） |
| RSRCH-043 | _match_resource_filter resource_name値不一致 | Name="database", resource_name="web" | False |

> **注記**: RSRCH-042/043 はレビュー指摘による後付け追加のため、テーブル末尾に採番しています。テストコードは各々 `TestMatchPolicyFilter`、`TestMatchResourceFilter` クラスに配置されています。

### 2.2 TestResourceFilter / TestPolicyFilter テスト

```python
# test/unit/chat_dashboard/test_resource_search_v2.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.chat_dashboard.resource_search_v2 import (
    ResourceFilter,
    PolicyFilter,
    EfficientResourceSearch,
    create_common_filters,
    quick_resource_search,
    ResourceIndexCache,
)


class TestResourceFilter:
    """ResourceFilter dataclass のテスト"""

    def test_default_values(self):
        """RSRCH-001: 全フィールドのデフォルト値がNone"""
        # Arrange & Act
        rf = ResourceFilter()

        # Assert
        assert rf.resource_id is None
        assert rf.resource_name is None
        assert rf.resource_type is None
        assert rf.vpc_id is None
        assert rf.instance_type is None
        assert rf.state is None
        assert rf.tag_key is None
        assert rf.tag_value is None
        assert rf.ip_range is None


class TestPolicyFilter:
    """PolicyFilter dataclass のテスト"""

    def test_default_values(self):
        """RSRCH-002: 全フィールドのデフォルト値がNone"""
        # Arrange & Act
        pf = PolicyFilter()

        # Assert
        assert pf.policy_name is None
        assert pf.description_keywords is None
        assert pf.severity is None
        assert pf.resource_type is None
        assert pf.recommendation_uuid is None
```

### 2.3 TestEfficientResourceSearch テスト

```python
class TestEfficientResourceSearch:
    """EfficientResourceSearch メイン検索のテスト"""

    @pytest.fixture
    def mock_os_client(self):
        """OpenSearchクライアントモック"""
        return AsyncMock()

    @pytest.fixture
    def searcher(self, mock_os_client):
        """EfficientResourceSearchインスタンス"""
        return EfficientResourceSearch(mock_os_client)

    def test_init(self, searcher, mock_os_client):
        """RSRCH-003: 初期化時にclientとキャッシュが設定される"""
        # Assert
        assert searcher.client is mock_os_client
        assert searcher._policy_cache == {}
        assert searcher._resource_index_cache == {}

    @pytest.mark.asyncio
    async def test_search_resources_no_filter(self, searcher, mock_os_client):
        """RSRCH-004: フィルターなしで全結果を返却"""
        # Arrange
        mock_os_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {
                    "policy_name": "test-policy",
                    "violation_summary": {"severity": "High", "resource_count": 2},
                    "region": "ap-northeast-1",
                    "resources": [
                        {"resource_id": "i-111", "custodian_resource": {}},
                        {"resource_id": "i-222", "custodian_resource": {}},
                    ],
                    "custodian_metadata": {},
                }},
            ]},
        }

        # Act
        result = await searcher.search_resources("scan_123")

        # Assert
        assert result["total_policies"] == 1
        assert result["total_resources"] == 2

    @pytest.mark.asyncio
    async def test_search_resources_with_policy_filter(self, searcher, mock_os_client):
        """RSRCH-005: ポリシーフィルター付き検索"""
        # Arrange
        mock_os_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {
                    "policy_name": "sg-rule",
                    "violation_summary": {"severity": "Critical"},
                    "region": "us-east-1",
                    "resources": [{"resource_id": "sg-1", "custodian_resource": {}}],
                    "custodian_metadata": {"policy": {"description": "security group check", "resource": "ec2"}},
                }},
            ]},
        }
        pf = PolicyFilter(severity="Critical")

        # Act
        result = await searcher.search_resources("scan_123", policy_filter=pf)

        # Assert — severity="Critical" のドキュメント1件がマッチ
        assert result["total_policies"] == 1
        assert result["total_resources"] == 1

    @pytest.mark.asyncio
    async def test_search_resources_with_resource_filter(self, searcher, mock_os_client):
        """RSRCH-006: リソースフィルター付き検索"""
        # Arrange
        mock_os_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {
                    "policy_name": "test",
                    "violation_summary": {"severity": "Medium"},
                    "resources": [
                        {"resource_id": "i-match", "custodian_resource": {}},
                        {"resource_id": "i-nomatch", "custodian_resource": {}},
                    ],
                    "custodian_metadata": {},
                }},
            ]},
        }
        rf = ResourceFilter(resource_id="i-match")

        # Act
        result = await searcher.search_resources("scan_123", resource_filter=rf)

        # Assert
        assert result["total_resources"] == 1
```

### 2.4 TestOpenSearchBaseFilter テスト

```python
class TestOpenSearchBaseFilter:
    """OpenSearch側クエリ構築のテスト"""

    @pytest.fixture
    def searcher(self):
        mock_client = AsyncMock()
        return EfficientResourceSearch(mock_client)

    @pytest.mark.asyncio
    async def test_basic_query(self, searcher):
        """RSRCH-007: 基本クエリ（scan_id + resource_count > 0）"""
        # Arrange
        searcher.client.search.return_value = {"hits": {"hits": []}}

        # Act
        result = await searcher._opensearch_base_filter("scan_123", None)

        # Assert
        call_args = searcher.client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must_clauses = body["query"]["bool"]["must"]
        assert {"term": {"scan_id": "scan_123"}} in must_clauses
        assert {"range": {"violation_summary.resource_count": {"gt": 0}}} in must_clauses
        assert call_args.kwargs.get("index") == "cspm-scan-result-scan_123"

    @pytest.mark.asyncio
    async def test_severity_filter(self, searcher):
        """RSRCH-008: severity条件付きクエリ"""
        # Arrange
        searcher.client.search.return_value = {"hits": {"hits": []}}
        pf = PolicyFilter(severity="Critical")

        # Act
        await searcher._opensearch_base_filter("scan_123", pf)

        # Assert
        call_args = searcher.client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must_clauses = body["query"]["bool"]["must"]
        assert {"term": {"violation_summary.severity": "Critical"}} in must_clauses

    @pytest.mark.asyncio
    async def test_policy_name_wildcard(self, searcher):
        """RSRCH-009: policy_name wildcard条件"""
        # Arrange
        searcher.client.search.return_value = {"hits": {"hits": []}}
        pf = PolicyFilter(policy_name="sg-rule")

        # Act
        await searcher._opensearch_base_filter("scan_123", pf)

        # Assert
        call_args = searcher.client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must_clauses = body["query"]["bool"]["must"]
        assert {"wildcard": {"policy_name": "*sg-rule*"}} in must_clauses

    @pytest.mark.asyncio
    async def test_recommendation_uuid_filter(self, searcher):
        """RSRCH-010: recommendation_uuid条件"""
        # Arrange
        searcher.client.search.return_value = {"hits": {"hits": []}}
        pf = PolicyFilter(recommendation_uuid="uuid-abc")

        # Act
        await searcher._opensearch_base_filter("scan_123", pf)

        # Assert
        call_args = searcher.client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must_clauses = body["query"]["bool"]["must"]
        assert {"term": {"violation_summary.recommendation_uuid": "uuid-abc"}} in must_clauses
```

### 2.5 TestMatchPolicyFilter テスト

```python
class TestMatchPolicyFilter:
    """ポリシーフィルターマッチングのテスト"""

    @pytest.fixture
    def searcher(self):
        return EfficientResourceSearch(AsyncMock())

    def test_description_keywords_match(self, searcher):
        """RSRCH-011: descriptionキーワード一致"""
        # Arrange
        metadata = {"policy": {"description": "暗号化チェックポリシー", "resource": "ec2"}}
        pf = PolicyFilter(description_keywords=["暗号化"])

        # Act
        result = searcher._match_policy_filter("test-policy", metadata, pf)

        # Assert
        assert result is True

    def test_description_keywords_no_match(self, searcher):
        """RSRCH-012: descriptionキーワード不一致"""
        # Arrange
        metadata = {"policy": {"description": "security group rule", "resource": "ec2"}}
        pf = PolicyFilter(description_keywords=["暗号化", "encryption"])

        # Act
        result = searcher._match_policy_filter("test-policy", metadata, pf)

        # Assert
        assert result is False

    def test_resource_type_match(self, searcher):
        """RSRCH-013: resource_type一致"""
        # Arrange
        metadata = {"policy": {"description": "test", "resource": "ec2.instance"}}
        pf = PolicyFilter(resource_type="ec2")

        # Act
        result = searcher._match_policy_filter("test-policy", metadata, pf)

        # Assert
        assert result is True

    def test_resource_type_no_match(self, searcher):
        """RSRCH-014: resource_type不一致"""
        # Arrange
        metadata = {"policy": {"description": "test", "resource": "ec2.instance"}}
        pf = PolicyFilter(resource_type="s3")

        # Act
        result = searcher._match_policy_filter("test-policy", metadata, pf)

        # Assert
        assert result is False

    def test_no_filter_conditions_returns_true(self, searcher):
        """RSRCH-042: フィルター条件なし（全フィールドNone）で無条件マッチ

        resource_search_v2.py:219-233 の全分岐をスキップして return True に到達。
        """
        # Arrange
        metadata = {"policy": {"description": "any description", "resource": "ec2"}}
        pf = PolicyFilter()  # 全フィールド None

        # Act
        result = searcher._match_policy_filter("test-policy", metadata, pf)

        # Assert
        assert result is True
```

### 2.6 TestMatchResourceFilter テスト

```python
class TestMatchResourceFilter:
    """リソースフィルターマッチングのテスト（7種フィルタ）"""

    @pytest.fixture
    def searcher(self):
        return EfficientResourceSearch(AsyncMock())

    def test_resource_id_match(self, searcher):
        """RSRCH-015: resource_id部分一致"""
        # Arrange
        resource = {"resource_id": "i-1234567890abcdef", "custodian_resource": {}}
        rf = ResourceFilter(resource_id="i-123")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_resource_name_match_name_field(self, searcher):
        """RSRCH-016: resource_name 一致（Nameフィールド）"""
        # Arrange
        resource = {"resource_id": "i-1", "custodian_resource": {"Name": "web-server-01"}}
        rf = ResourceFilter(resource_name="web-server")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_resource_name_match_group_name(self, searcher):
        """RSRCH-017: resource_name 一致（GroupNameフィールド）"""
        # Arrange
        resource = {"resource_id": "sg-1", "custodian_resource": {"GroupName": "default-sg"}}
        rf = ResourceFilter(resource_name="default")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_vpc_id_match(self, searcher):
        """RSRCH-018: vpc_id完全一致"""
        # Arrange
        resource = {"resource_id": "i-1", "custodian_resource": {"VpcId": "vpc-123"}}
        rf = ResourceFilter(vpc_id="vpc-123")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_vpc_id_no_match(self, searcher):
        """RSRCH-019: vpc_id不一致"""
        # Arrange
        resource = {"resource_id": "i-1", "custodian_resource": {"VpcId": "vpc-999"}}
        rf = ResourceFilter(vpc_id="vpc-123")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is False

    def test_instance_type_match(self, searcher):
        """RSRCH-020: instance_type完全一致"""
        # Arrange
        resource = {"resource_id": "i-1", "custodian_resource": {"InstanceType": "t3.micro"}}
        rf = ResourceFilter(instance_type="t3.micro")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_state_dict_match(self, searcher):
        """RSRCH-021: state一致（dict型 State.Name）

        resource_search_v2.py:272-273 の分岐をカバー。
        """
        # Arrange
        resource = {"resource_id": "i-1", "custodian_resource": {"State": {"Name": "running"}}}
        rf = ResourceFilter(state="running")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_state_string_match(self, searcher):
        """RSRCH-022: state一致（str型）

        resource_search_v2.py:274-275 の else 分岐をカバー。
        """
        # Arrange
        resource = {"resource_id": "i-1", "custodian_resource": {"State": "active"}}
        rf = ResourceFilter(state="active")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_tag_filter_delegates(self, searcher):
        """RSRCH-023: タグフィルター指定時に _match_tags が呼ばれる"""
        # Arrange
        resource = {
            "resource_id": "i-1",
            "custodian_resource": {
                "Tags": [{"Key": "Environment", "Value": "production"}],
            },
        }
        rf = ResourceFilter(tag_key="Environment")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_ip_range_filter_delegates(self, searcher):
        """RSRCH-024: IP範囲フィルター指定時に _match_ip_range が呼ばれる"""
        # Arrange
        resource = {
            "resource_id": "sg-1",
            "custodian_resource": {
                "IpPermissions": [{"IpRanges": [{"CidrIp": "0.0.0.0/0"}]}],
            },
        }
        rf = ResourceFilter(ip_range="0.0.0.0/0")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is True

    def test_resource_name_value_no_match(self, searcher):
        """RSRCH-043: resource_name フィールド存在だが値不一致

        resource_search_v2.py:250-259 の found_name=False 分岐をカバー。
        Nameフィールドは存在するが、フィルター値と不一致のケース。
        """
        # Arrange
        resource = {"resource_id": "i-db", "custodian_resource": {"Name": "database-server"}}
        rf = ResourceFilter(resource_name="web")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is False
```

### 2.7 TestMatchTags テスト

```python
class TestMatchTags:
    """タグマッチングのテスト"""

    @pytest.fixture
    def searcher(self):
        return EfficientResourceSearch(AsyncMock())

    def test_key_match(self, searcher):
        """RSRCH-025: タグキー一致"""
        # Arrange
        resource = {"Tags": [{"Key": "Name", "Value": "web-01"}]}
        rf = ResourceFilter(tag_key="Name")

        # Act & Assert
        assert searcher._match_tags(resource, rf) is True

    def test_value_match(self, searcher):
        """RSRCH-026: タグ値一致"""
        # Arrange
        resource = {"Tags": [{"Key": "Environment", "Value": "production"}]}
        rf = ResourceFilter(tag_value="production")

        # Act & Assert
        assert searcher._match_tags(resource, rf) is True

    def test_key_and_value_match(self, searcher):
        """RSRCH-027: タグキー＋値の両方一致"""
        # Arrange
        resource = {"Tags": [
            {"Key": "Name", "Value": "web"},
            {"Key": "Env", "Value": "prod"},
        ]}
        rf = ResourceFilter(tag_key="Env", tag_value="prod")

        # Act & Assert
        assert searcher._match_tags(resource, rf) is True
```

### 2.8 TestMatchIpRange テスト

```python
class TestMatchIpRange:
    """IP範囲マッチングのテスト"""

    @pytest.fixture
    def searcher(self):
        return EfficientResourceSearch(AsyncMock())

    def test_inbound_match(self, searcher):
        """RSRCH-028: インバウンドルールでCidrIp一致"""
        # Arrange
        resource = {
            "IpPermissions": [
                {"IpProtocol": "tcp", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            ],
        }

        # Act & Assert
        assert searcher._match_ip_range(resource, "0.0.0.0/0") is True

    def test_egress_match(self, searcher):
        """RSRCH-029: アウトバウンドルールでCidrIp一致"""
        # Arrange
        resource = {
            "IpPermissions": [],
            "IpPermissionsEgress": [
                {"IpProtocol": "-1", "IpRanges": [{"CidrIp": "10.0.0.0/8"}]},
            ],
        }

        # Act & Assert
        assert searcher._match_ip_range(resource, "10.0.0.0/8") is True
```

### 2.9 TestConsolidateResults テスト

```python
class TestConsolidateResults:
    """結果統合・ランキングのテスト"""

    @pytest.fixture
    def searcher(self):
        return EfficientResourceSearch(AsyncMock())

    def test_severity_sort_order(self, searcher):
        """RSRCH-030: 重要度ソート（Critical > High > Medium > Low）"""
        # Arrange
        docs = [
            {"match": True, "policy_name": "low-p",
             "violation_summary": {"severity": "Low"}, "total_resources": 1},
            {"match": True, "policy_name": "critical-p",
             "violation_summary": {"severity": "Critical"}, "total_resources": 1},
            {"match": True, "policy_name": "high-p",
             "violation_summary": {"severity": "High"}, "total_resources": 1},
        ]

        # Act
        result = searcher._consolidate_results(docs, max_results=100)

        # Assert
        policies = result["policies"]
        assert policies[0]["policy_name"] == "critical-p"
        assert policies[1]["policy_name"] == "high-p"
        assert policies[2]["policy_name"] == "low-p"

    def test_max_results_limit(self, searcher):
        """RSRCH-031: max_results で結果数を制限"""
        # Arrange
        docs = [
            {"match": True, "policy_name": f"p-{i}",
             "violation_summary": {"severity": "Medium"}, "total_resources": 1}
            for i in range(10)
        ]

        # Act
        result = searcher._consolidate_results(docs, max_results=3)

        # Assert
        assert len(result["policies"]) == 3
        assert result["total_policies"] == 3
        assert result["search_performance"]["matched"] == 10
        assert result["search_performance"]["returned"] == 3

    def test_severity_stats(self, searcher):
        """RSRCH-032: 重要度別統計の正確性"""
        # Arrange
        docs = [
            {"match": True, "policy_name": "p1",
             "violation_summary": {"severity": "Critical"}, "total_resources": 3},
            {"match": True, "policy_name": "p2",
             "violation_summary": {"severity": "Critical"}, "total_resources": 2},
            {"match": True, "policy_name": "p3",
             "violation_summary": {"severity": "High"}, "total_resources": 5},
        ]

        # Act
        result = searcher._consolidate_results(docs, max_results=100)

        # Assert
        stats = result["severity_stats"]
        assert stats["Critical"]["policies"] == 2
        assert stats["Critical"]["resources"] == 5
        assert stats["High"]["policies"] == 1
        assert stats["High"]["resources"] == 5
```

### 2.10 TestQuickResourceSearch テスト

```python
class TestQuickResourceSearch:
    """quick_resource_search 自動判定のテスト"""

    @pytest.mark.asyncio
    async def test_resource_id_detection(self):
        """RSRCH-033: リソースID（i-プレフィックス）を検出"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        # Act
        result = await quick_resource_search(mock_client, "scan_123", "i-1234")

        # Assert — 結果は空だが、呼び出しが成功すること
        assert result["total_policies"] == 0

    @pytest.mark.asyncio
    async def test_ip_range_detection(self):
        """RSRCH-034: IP範囲（CIDR形式）を検出"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        # Act
        result = await quick_resource_search(mock_client, "scan_123", "10.0.0.0/8")

        # Assert
        assert result["total_policies"] == 0

    @pytest.mark.asyncio
    async def test_policy_name_detection(self):
        """RSRCH-035: ポリシー名（policy-プレフィックス）を検出"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        # Act
        result = await quick_resource_search(mock_client, "scan_123", "policy-sg-check")

        # Assert — wildcard クエリが使われること
        call_args = mock_client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must = body["query"]["bool"]["must"]
        wildcard_found = any("wildcard" in str(clause) for clause in must)
        assert wildcard_found

    @pytest.mark.asyncio
    async def test_severity_detection(self):
        """RSRCH-036: 重要度キーワードを検出（capitalize変換）"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        # Act
        result = await quick_resource_search(mock_client, "scan_123", "critical")

        # Assert — severity条件が追加されること
        call_args = mock_client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must = body["query"]["bool"]["must"]
        severity_found = any(
            clause.get("term", {}).get("violation_summary.severity") == "Critical"
            for clause in must
        )
        assert severity_found

    @pytest.mark.asyncio
    async def test_keyword_detection(self):
        """RSRCH-037: 一般キーワード → description_keywords"""
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {"hits": [
                {"_source": {
                    "policy_name": "enc-policy",
                    "violation_summary": {"severity": "Medium"},
                    "resources": [{"resource_id": "r-1", "custodian_resource": {}}],
                    "custodian_metadata": {"policy": {"description": "暗号化チェック", "resource": "s3"}},
                }},
            ]},
        }

        # Act
        result = await quick_resource_search(mock_client, "scan_123", "暗号化")

        # Assert
        assert result["total_policies"] == 1
```

### 2.11 TestCreateCommonFilters / TestResourceIndexCache テスト

```python
class TestCreateCommonFilters:
    """共通フィルター定義のテスト"""

    def test_returns_5_filters(self):
        """RSRCH-038: 5つのフィルター定義を返却"""
        # Act
        filters = create_common_filters()

        # Assert
        assert len(filters) == 5
        assert "instance_search" in filters
        assert "security_group" in filters
        assert "public_access" in filters
        assert "encryption_policies" in filters
        assert "critical_only" in filters
        assert isinstance(filters["instance_search"], ResourceFilter)
        assert isinstance(filters["critical_only"], PolicyFilter)


class TestResourceIndexCache:
    """ResourceIndexCache のテスト"""

    def test_build_index(self):
        """RSRCH-039: 検索インデックスの構築"""
        # Arrange
        cache = ResourceIndexCache()
        scan_results = [
            {
                "policy_name": "policy-a",
                "resources": [
                    {"resource_id": "i-111", "custodian_resource": {}},
                    {"resource_id": "i-222", "custodian_resource": {}},
                ],
            },
            {
                "policy_name": "policy-b",
                "resources": [
                    {"resource_id": "sg-333", "custodian_resource": {}},
                ],
            },
        ]

        # Act
        cache.build_index(scan_results)

        # Assert
        assert len(cache._resource_by_id) == 3
        assert len(cache._resources_by_policy) == 2

    def test_find_by_id(self):
        """RSRCH-040: リソースIDで検索"""
        # Arrange
        cache = ResourceIndexCache()
        resource = {"resource_id": "i-111", "custodian_resource": {"Name": "web"}}
        cache._resource_by_id["i-111"] = resource

        # Act
        result = cache.find_by_id("i-111")

        # Assert
        assert result is resource

    def test_find_by_policy(self):
        """RSRCH-041: ポリシー名でリソース一覧取得"""
        # Arrange
        cache = ResourceIndexCache()
        resources = [
            {"resource_id": "i-1", "custodian_resource": {}},
            {"resource_id": "i-2", "custodian_resource": {}},
        ]
        cache._resources_by_policy["policy-a"] = resources

        # Act
        result = cache.find_by_policy("policy-a")

        # Assert
        assert len(result) == 2
```

---

## 3. 異常系テストケース

### chat_tools_v2.py 異常系

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTV2-E01 | OpenSearchクライアントNone | get_opensearch_client → None | エラーメッセージ返却 |
| CTV2-E02 | 認証エラー（decode_basic_auth失敗） | opensearch_auth="invalid" | os_client=Noneでエラー |
| CTV2-E03 | 検索結果0件（フィルターあり） | 該当なし条件 | フィルター情報付きメッセージ |
| CTV2-E04 | 予期しない例外 | EfficientResourceSearch例外 | エラー詳細メッセージ |
| CTV2-E05 | クイック検索 クライアントNone | get_opensearch_client → None | エラーメッセージ |
| CTV2-E06 | クイック検索 結果0件 | 該当なし | ヒント付きメッセージ |
| CTV2-E07 | クイック検索 認証エラー | decode_basic_auth失敗 | os_client=Noneでエラー |
| CTV2-E08 | クイック検索 予期しない例外 | quick_resource_search例外 | エラー詳細メッセージ |

### resource_search_v2.py 異常系

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RSRCH-E01 | OpenSearch検索エラー | client.search例外 | 空リスト返却 |
| RSRCH-E02 | base_hits空で早期リターン | 検索結果0件 | total_policies:0（通常フローと同一キー構造） |
| RSRCH-E03 | _process_document ポリシーフィルター不一致 | マッチしない条件 | {"match": False} |
| RSRCH-E04 | リソースフィルター全不一致 | 全リソース条件外 | {"match": False} |
| RSRCH-E05 | タグなしリソースへのタグフィルタ | Tags=[] | False |
| RSRCH-E06 | IP範囲なしリソースへのIP範囲フィルタ | IpPermissions無し | False |
| RSRCH-E07 | _consolidate_results 全match:False | 全不一致 | total_policies:0 |
| RSRCH-E08 | resource_name フィールドなし | Name/GroupName/BucketName全てなし | False |
| RSRCH-E09 | ResourceIndexCache 空データ | 空リスト | 空インデックス |
| RSRCH-E10 | find_by_id 存在しないID | 未登録ID | None |
| RSRCH-E11 | find_by_policy 存在しないポリシー | 未登録ポリシー | 空リスト |

### 3.1 TestGetResourceDetailsV2Errors テスト

```python
class TestGetResourceDetailsV2Errors:
    """get_resource_details_v2 エラーテスト"""

    @pytest.mark.asyncio
    async def test_client_none(self):
        """CTV2-E01: OpenSearchクライアントがNoneの場合

        chat_tools_v2.py:77-78 の分岐をカバー。
        """
        # Arrange
        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=None):
            # Act
            result = await get_resource_details_v2.ainvoke({"scan_id": "scan_123"})

            # Assert
            assert "エラー" in result
            assert "初期化に失敗" in result

    @pytest.mark.asyncio
    async def test_auth_decode_error(self):
        """CTV2-E02: 認証トークンのデコード失敗

        chat_tools_v2.py:71-73 の except 分岐をカバー。
        """
        # Arrange
        with patch("app.chat_dashboard.chat_tools_v2.decode_basic_auth",
                    side_effect=Exception("Invalid base64")):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123",
                "opensearch_auth": "invalid_token",
            })

            # Assert — os_client=Noneになり、エラーメッセージ返却
            assert "エラー" in result

    @pytest.mark.asyncio
    async def test_zero_results_with_filters(self):
        """CTV2-E03: 検索結果0件（フィルター情報付きメッセージ）

        chat_tools_v2.py:107-117 の分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.return_value = {
            "total_policies": 0, "total_resources": 0,
            "severity_stats": {}, "policies": [],
            "search_performance": {},
        }

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123",
                "policy_name": "not-exist",
                "resource_id": "i-0000",
                "severity": "Critical",
            })

            # Assert
            assert "リソースが見つかりません" in result
            assert "ポリシー名: not-exist" in result
            assert "リソースID: i-0000" in result
            assert "重要度: Critical" in result

    @pytest.mark.asyncio
    async def test_unexpected_exception(self):
        """CTV2-E04: 予期しない例外ハンドリング

        chat_tools_v2.py:122-123 の except 分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.side_effect = RuntimeError("unexpected")

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({"scan_id": "scan_123"})

            # Assert
            assert "予期しないエラー" in result
            assert "unexpected" in result


class TestQuickResourceSearchToolErrors:
    """quick_resource_search_tool エラーテスト"""

    @pytest.mark.asyncio
    async def test_client_none(self):
        """CTV2-E05: OpenSearchクライアントNone

        chat_tools_v2.py:173-174 の分岐をカバー。
        """
        # Arrange
        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=None):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "test"
            })

            # Assert
            assert "エラー" in result

    @pytest.mark.asyncio
    async def test_zero_results(self):
        """CTV2-E06: 検索結果0件（ヒント付きメッセージ）

        chat_tools_v2.py:179-180 の分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_qs = AsyncMock(return_value={
            "total_policies": 0, "total_resources": 0, "policies": [],
        })

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search", mock_qs):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "nonexistent"
            })

            # Assert
            assert "検索結果なし" in result
            assert "nonexistent" in result
            assert "検索のヒント" in result

    @pytest.mark.asyncio
    async def test_auth_error(self):
        """CTV2-E07: クイック検索の認証エラー

        chat_tools_v2.py:167-169 の except 分岐をカバー。
        """
        # Arrange
        with patch("app.chat_dashboard.chat_tools_v2.decode_basic_auth",
                    side_effect=Exception("decode failed")):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123",
                "search_term": "test",
                "opensearch_auth": "bad_token",
            })

            # Assert
            assert "エラー" in result

    @pytest.mark.asyncio
    async def test_unexpected_exception(self):
        """CTV2-E08: クイック検索の予期しない例外

        chat_tools_v2.py:185-186 の except 分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search",
                   side_effect=ConnectionError("connection lost")):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "test"
            })

            # Assert
            assert "予期しないエラー" in result
            assert "connection lost" in result
```

### 3.2 TestResourceSearchV2Errors テスト

```python
class TestOpenSearchBaseFilterErrors:
    """_opensearch_base_filter エラーテスト"""

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """RSRCH-E01: OpenSearch検索時の例外

        resource_search_v2.py:137-139 の except 分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.side_effect = ConnectionError("connection refused")
        searcher = EfficientResourceSearch(mock_client)

        # Act
        result = await searcher._opensearch_base_filter("scan_123", None)

        # Assert
        assert result == []


class TestSearchResourcesErrors:
    """search_resources エラーテスト"""

    @pytest.mark.asyncio
    async def test_empty_base_hits(self):
        """RSRCH-E02: base_hits空で早期リターン

        resource_search_v2.py:74-75 の分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}
        searcher = EfficientResourceSearch(mock_client)

        # Act
        result = await searcher.search_resources("scan_empty")

        # Assert — 通常フロー（_consolidate_results）と同じキー構造
        assert result["total_policies"] == 0
        assert result["total_resources"] == 0
        assert result["policies"] == []
        assert result["severity_stats"] == {}
        assert result["search_performance"]["total_evaluated"] == 0
        assert result["search_performance"]["matched"] == 0
        assert result["search_performance"]["returned"] == 0


class TestProcessDocumentErrors:
    """_process_document エラーテスト"""

    @pytest.mark.asyncio
    async def test_policy_filter_no_match(self):
        """RSRCH-E03: ポリシーフィルター不一致で match:False

        resource_search_v2.py:177-180 の分岐をカバー。
        """
        # Arrange
        searcher = EfficientResourceSearch(AsyncMock())
        hit = {"_source": {
            "policy_name": "test",
            "violation_summary": {},
            "resources": [{"resource_id": "r-1"}],
            "custodian_metadata": {"policy": {"description": "other", "resource": "ec2"}},
        }}
        pf = PolicyFilter(description_keywords=["暗号化"])

        # Act
        result = await searcher._process_document(hit, None, pf)

        # Assert
        assert result["match"] is False

    @pytest.mark.asyncio
    async def test_resource_filter_all_mismatch(self):
        """RSRCH-E04: リソースフィルタで全リソースが不一致

        resource_search_v2.py:191-192 の分岐をカバー。
        """
        # Arrange
        searcher = EfficientResourceSearch(AsyncMock())
        hit = {"_source": {
            "policy_name": "test",
            "violation_summary": {},
            "resources": [
                {"resource_id": "i-111", "custodian_resource": {}},
                {"resource_id": "i-222", "custodian_resource": {}},
            ],
            "custodian_metadata": {},
        }}
        rf = ResourceFilter(resource_id="sg-999")  # どのリソースにも一致しない

        # Act
        result = await searcher._process_document(hit, rf, None)

        # Assert
        assert result["match"] is False


class TestMatchFiltersErrors:
    """フィルターマッチングのエラーテスト"""

    @pytest.fixture
    def searcher(self):
        return EfficientResourceSearch(AsyncMock())

    def test_tags_empty(self, searcher):
        """RSRCH-E05: Tags空配列でのタグフィルタ適用

        resource_search_v2.py:295-296 の分岐をカバー。
        """
        # Arrange
        resource = {"Tags": []}
        rf = ResourceFilter(tag_key="Name")

        # Act & Assert
        assert searcher._match_tags(resource, rf) is False

    def test_ip_range_no_permissions(self, searcher):
        """RSRCH-E06: IpPermissions/IpPermissionsEgress無しでのIP範囲フィルタ"""
        # Arrange
        resource = {}  # IpPermissions なし

        # Act & Assert
        assert searcher._match_ip_range(resource, "0.0.0.0/0") is False

    def test_consolidate_all_false(self, searcher):
        """RSRCH-E07: 全ドキュメントが match:False"""
        # Arrange
        docs = [
            {"match": False},
            {"match": False},
            {"match": False},
        ]

        # Act
        result = searcher._consolidate_results(docs, max_results=100)

        # Assert
        assert result["total_policies"] == 0
        assert result["total_resources"] == 0

    def test_resource_name_no_name_fields(self, searcher):
        """RSRCH-E08: Name/GroupName/BucketName いずれのフィールドもない

        resource_search_v2.py:250-259 の分岐をカバー。
        """
        # Arrange
        resource = {"resource_id": "r-1", "custodian_resource": {"State": "active"}}
        rf = ResourceFilter(resource_name="web")

        # Act & Assert
        assert searcher._match_resource_filter(resource, rf) is False


class TestResourceIndexCacheErrors:
    """ResourceIndexCache エラーテスト"""

    def test_build_index_empty(self):
        """RSRCH-E09: 空データでインデックス構築"""
        # Arrange
        cache = ResourceIndexCache()

        # Act
        cache.build_index([])

        # Assert
        assert cache._resource_by_id == {}
        assert cache._resources_by_policy == {}

    def test_find_by_id_not_found(self):
        """RSRCH-E10: 存在しないIDで検索"""
        # Arrange
        cache = ResourceIndexCache()

        # Act & Assert
        assert cache.find_by_id("i-nonexistent") is None

    def test_find_by_policy_not_found(self):
        """RSRCH-E11: 存在しないポリシーで検索"""
        # Arrange
        cache = ResourceIndexCache()

        # Act & Assert
        assert cache.find_by_policy("nonexistent-policy") == []
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTV2-SEC-01 | 認証エラーログでの資格情報漏洩検証 | 不正なopensearch_auth | パスワード・Base64トークンがログに含まれない |
| CTV2-SEC-02 | scan_idによるインデックス名操作 | scan_id="../../admin" | パストラバーサルが防止される |
| CTV2-SEC-03 | quick_resource_search_tool認証エラーログでの資格情報漏洩検証 | 不正なopensearch_auth | パスワード・Base64トークンがログに含まれない |
| CTV2-SEC-04 | get_resource_details_v2 例外メッセージ内資格情報のレスポンス漏洩 | 資格情報含む例外 | レスポンスに資格情報が含まれない |
| CTV2-SEC-05 | quick_resource_search_tool 例外メッセージ内資格情報のレスポンス漏洩 | 資格情報含む例外 | レスポンスに資格情報が含まれない |
| RSRCH-SEC-01 | wildcardクエリのインジェクション | policy_name="*;DROP INDEX*" | エスケープまたはサニタイズ |
| RSRCH-SEC-02 | 大量リソース処理のメモリ安全性 | 10,000件リソース | max_results制限が有効 |
| RSRCH-SEC-03 | リソースフィルタへの悪意ある入力 | 長大文字列フィルタ | タイムアウトなし・安定動作 |

```python
@pytest.mark.security
class TestChatToolsV2Security:
    """chat_tools_v2 セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        strict=True,
        reason="chat_tools_v2.py:72 で auth_error をそのままログ出力（資格情報漏洩リスク）"
    )
    async def test_auth_error_no_credential_leak(self, capsys, caplog):
        """CTV2-SEC-01: 認証エラーログに資格情報が含まれないこと

        chat_tools_v2.py:72 で print(f"... {auth_error}") により
        例外メッセージに資格情報が含まれる場合にログ漏洩する。
        capsys（print出力）と caplog（logging出力）の両方を検証し、
        将来の logging 移行にも耐性を持たせる。
        """
        import logging

        # Arrange
        auth_header = "Basic YWRtaW46U3VwZXJTZWNyZXQxMjMh"  # admin:SuperSecret123!
        token = "YWRtaW46U3VwZXJTZWNyZXQxMjMh"
        password = "SuperSecret123!"

        with caplog.at_level(logging.DEBUG), \
             patch("app.chat_dashboard.chat_tools_v2.decode_basic_auth",
                    side_effect=Exception(f"Failed to decode: {token}")):
            # Act
            await get_resource_details_v2.ainvoke({
                "scan_id": "scan_123",
                "opensearch_auth": auth_header,
            })

            # Assert — print出力にBase64トークン・パスワードが含まれないこと
            captured = capsys.readouterr()
            assert token not in captured.out, "Base64トークンがログに漏洩(stdout)"
            assert password not in captured.out, "パスワードがログに漏洩(stdout)"
            assert auth_header not in captured.out, "Authorizationヘッダーがログに漏洩(stdout)"

            # Assert — logging出力にも含まれないこと（将来のlogging移行対応）
            log_text = caplog.text
            assert token not in log_text, "Base64トークンがログに漏洩(logging)"
            assert password not in log_text, "パスワードがログに漏洩(logging)"

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        strict=True,
        reason="chat_tools_v2.py / resource_search_v2.py ではscan_idのサニタイズ未実装"
    )
    async def test_scan_id_path_traversal(self):
        """CTV2-SEC-02: scan_idを利用したインデックス名操作の防止

        resource_search_v2.py:141 で
        f"cspm-scan-result-{scan_id}" としてインデックス名を構築。
        EfficientResourceSearchをモックせず、実際のインデックス名構築処理を通して
        client.search の index 引数にパストラバーサル文字列が含まれないことを検証。
        """
        # Arrange
        malicious_scan_id = "../../admin-index"
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client):
            # Act
            await get_resource_details_v2.ainvoke({
                "scan_id": malicious_scan_id
            })

            # Assert — client.search に渡された index 引数を検証
            assert mock_client.search.call_args is not None, "client.search が呼ばれていない"
            used_index = mock_client.search.call_args.kwargs.get("index", "")
            assert "../../" not in used_index, (
                f"インデックス名にパストラバーサルが含まれている: {used_index}"
            )

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        strict=True,
        reason="chat_tools_v2.py:168 で auth_error をそのままログ出力（資格情報漏洩リスク）"
    )
    async def test_quick_search_auth_error_no_credential_leak(self, capsys, caplog):
        """CTV2-SEC-03: quick_resource_search_tool 認証エラーログに資格情報が含まれないこと

        chat_tools_v2.py:168 で print(f"... {auth_error}") により
        例外メッセージに資格情報が含まれる場合にログ漏洩する。
        get_resource_details_v2 (CTV2-SEC-01) と同一パターン。
        """
        import logging

        # Arrange
        auth_header = "Basic YWRtaW46U3VwZXJTZWNyZXQxMjMh"  # admin:SuperSecret123!
        token = "YWRtaW46U3VwZXJTZWNyZXQxMjMh"
        password = "SuperSecret123!"

        with caplog.at_level(logging.DEBUG), \
             patch("app.chat_dashboard.chat_tools_v2.decode_basic_auth",
                    side_effect=Exception(f"Failed to decode: {token}")):
            # Act
            await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123",
                "search_term": "test",
                "opensearch_auth": auth_header,
            })

            # Assert — print出力にBase64トークン・パスワードが含まれないこと
            captured = capsys.readouterr()
            assert token not in captured.out, "Base64トークンがログに漏洩(stdout)"
            assert password not in captured.out, "パスワードがログに漏洩(stdout)"
            assert auth_header not in captured.out, "Authorizationヘッダーがログに漏洩(stdout)"

            # Assert — logging出力にも含まれないこと（将来のlogging移行対応）
            log_text = caplog.text
            assert token not in log_text, "Base64トークンがログに漏洩(logging)"
            assert password not in log_text, "パスワードがログに漏洩(logging)"

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        strict=True,
        reason="chat_tools_v2.py:123 で str(e) をそのままレスポンスに返却（内部情報漏洩リスク）"
    )
    async def test_exception_message_no_credential_in_response(self):
        """CTV2-SEC-04: get_resource_details_v2 の例外メッセージに資格情報が含まれる場合のレスポンス漏洩

        chat_tools_v2.py:123 で f"エラー詳細: {str(e)}" がレスポンスに返却されるため、
        例外メッセージに資格情報が含まれる場合にクライアントへ漏洩する。
        """
        # Arrange
        secret_password = "SuperSecret123!"
        mock_client = AsyncMock()
        mock_searcher = AsyncMock()
        mock_searcher.search_resources.side_effect = RuntimeError(
            f"Connection failed: password={secret_password} host=db.internal"
        )

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.EfficientResourceSearch",
                   return_value=mock_searcher):
            # Act
            result = await get_resource_details_v2.ainvoke({"scan_id": "scan_123"})

            # Assert — レスポンスに資格情報が含まれないこと
            assert secret_password not in result, "パスワードがレスポンスに漏洩"
            assert "db.internal" not in result, "内部ホスト名がレスポンスに漏洩"

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        strict=True,
        reason="chat_tools_v2.py:186 で str(e) をそのままレスポンスに返却（内部情報漏洩リスク）"
    )
    async def test_quick_search_exception_no_credential_in_response(self):
        """CTV2-SEC-05: quick_resource_search_tool の例外メッセージに資格情報が含まれる場合のレスポンス漏洩

        chat_tools_v2.py:186 で f"エラー詳細: {str(e)}" がレスポンスに返却されるため、
        例外メッセージに資格情報が含まれる場合にクライアントへ漏洩する。
        """
        # Arrange
        secret_password = "SuperSecret123!"
        mock_client = AsyncMock()

        with patch("app.chat_dashboard.chat_tools_v2.get_opensearch_client",
                    new_callable=AsyncMock, return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools_v2.quick_resource_search",
                   side_effect=RuntimeError(
                       f"Connection failed: password={secret_password} host=db.internal"
                   )):
            # Act
            result = await quick_resource_search_tool.ainvoke({
                "scan_id": "scan_123", "search_term": "test"
            })

            # Assert — レスポンスに資格情報が含まれないこと
            assert secret_password not in result, "パスワードがレスポンスに漏洩"
            assert "db.internal" not in result, "内部ホスト名がレスポンスに漏洩"


@pytest.mark.security
class TestResourceSearchV2Security:
    """resource_search_v2 セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        strict=True,
        reason="resource_search_v2.py:115 で policy_name をサニタイズせずにwildcardクエリに使用"
    )
    async def test_wildcard_injection(self):
        """RSRCH-SEC-01: wildcardクエリへのインジェクション

        resource_search_v2.py:126 で
        f"*{policy_filter.policy_name}*" としてwildcardクエリを構築。
        悪意のある文字列がサニタイズされること。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"hits": []}}
        searcher = EfficientResourceSearch(mock_client)
        # 引用符・DROP文・バックスラッシュ・?ワイルドカードを含む悪性文字列
        malicious_name = '*";DROP INDEX cspm*\\path?single'
        pf = PolicyFilter(policy_name=malicious_name)

        # Act
        await searcher._opensearch_base_filter("scan_123", pf)

        # Assert — クエリ内のwildcard値に悪性文字列が含まれないこと
        call_args = mock_client.search.call_args
        body = call_args.kwargs.get("body") or call_args[1].get("body")
        must = body["query"]["bool"]["must"]
        for clause in must:
            if "wildcard" in clause:
                wc_value = clause["wildcard"]["policy_name"]
                assert '"' not in wc_value, "引用符がサニタイズされていない"
                assert "DROP" not in wc_value.upper(), "SQLインジェクション文字列が通過"
                assert '\\' not in wc_value, "バックスラッシュがエスケープされていない"
                assert '?' not in wc_value, "?ワイルドカードがサニタイズされていない"

    def test_max_results_limits_memory(self):
        """RSRCH-SEC-02: max_results制限による大量データメモリ安全性"""
        # Arrange
        searcher = EfficientResourceSearch(AsyncMock())
        # 10,000件の大量ドキュメント
        docs = [
            {"match": True, "policy_name": f"p-{i}",
             "violation_summary": {"severity": "Low"}, "total_resources": 1}
            for i in range(10000)
        ]

        # Act
        result = searcher._consolidate_results(docs, max_results=100)

        # Assert
        assert len(result["policies"]) == 100
        assert result["total_policies"] == 100
        assert result["search_performance"]["matched"] == 10000
        assert result["search_performance"]["returned"] == 100

    @pytest.mark.timeout(5)
    def test_long_filter_string(self):
        """RSRCH-SEC-03: 悪意のある長大文字列フィルタへの耐性"""
        # Arrange
        searcher = EfficientResourceSearch(AsyncMock())
        long_string = "A" * 100000  # 100KB文字列
        resource = {"resource_id": "i-123", "custodian_resource": {"Name": "normal"}}
        rf = ResourceFilter(resource_name=long_string)

        # Act — タイムアウトせずに完了すること
        result = searcher._match_resource_filter(resource, rf)

        # Assert
        assert result is False  # 一致しないがクラッシュしない
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `set_required_env_vars` | config.pyバリデーション通過用の環境変数設定 | function | Yes |
| `reset_chat_tools_v2_module` | app.coreモジュールキャッシュのリセット（クライアント再初期化強制） | function | Yes |
| `mock_opensearch_client` | OpenSearchクライアントモック | function | No |
| `sample_scan_result_v2_hits` | v2スキャン結果ヒットサンプル | function | No |
| `sample_resource_with_tags` | タグ付きリソースサンプル | function | No |
| `sample_security_group_resource` | セキュリティグループリソースサンプル（IpPermissions付き） | function | No |
| `efficient_resource_search` | EfficientResourceSearchインスタンス | function | No |
| `resource_index_cache` | ResourceIndexCacheインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/chat_dashboard/conftest.py に追加
import sys
import pytest
from unittest.mock import AsyncMock

# テスト用定数（config.pyバリデーション通過に必要な最小環境変数セット）
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-key",
    "GPT5_1_CODEX_API_KEY": "test-key",
    "GPT5_2_API_KEY": "test-key",
    "GPT5_MINI_API_KEY": "test-key",
    "GPT5_NANO_API_KEY": "test-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-key",
    "CLAUDE_SONNET_4_5_KEY": "test-key",
    "GEMINI_API": "test-key",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",
    "OPENSEARCH_URL": "https://localhost:9200",
}


@pytest.fixture(autouse=True)
def set_required_env_vars(monkeypatch):
    """config.pyバリデーション通過に必要な環境変数を設定

    REQUIRED_ENV_VARS に定義されたテスト用ダミー値を環境変数に注入し、
    モジュールインポート時の Settings バリデーションエラーを防止する。
    """
    for key, value in REQUIRED_ENV_VARS.items():
        monkeypatch.setenv(key, value)


@pytest.fixture(autouse=True)
def reset_chat_tools_v2_module():
    """テストごとに app.core モジュールキャッシュをリセット

    app.core.clients 等がキャッシュする OpenSearch クライアントインスタンスを
    テスト間で引き継がないよう、sys.modules から除去して再初期化を強制する。
    """
    yield
    # テスト後にクリーンアップ — app.core* モジュールをアンロード
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_opensearch_client():
    """OpenSearchクライアントモック（外部接続防止）"""
    return AsyncMock()


@pytest.fixture
def sample_scan_result_v2_hits():
    """v2スキャン結果ヒットサンプル"""
    return [
        {
            "_source": {
                "policy_name": "sg-open-access",
                "violation_summary": {
                    "severity": "Critical",
                    "resource_count": 2,
                    "recommendation_uuid": "rec-001",
                },
                "region": "ap-northeast-1",
                "account_id": "123456789012",
                "resources": [
                    {
                        "resource_id": "sg-aaa111",
                        "custodian_resource": {
                            "GroupName": "default",
                            "VpcId": "vpc-123",
                            "IpPermissions": [
                                {"IpProtocol": "tcp", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                            ],
                        },
                    },
                    {
                        "resource_id": "sg-bbb222",
                        "custodian_resource": {
                            "GroupName": "web-sg",
                            "VpcId": "vpc-123",
                            "Tags": [{"Key": "Environment", "Value": "production"}],
                        },
                    },
                ],
                "custodian_metadata": {
                    "policy": {
                        "description": "Security group with open access",
                        "resource": "ec2.security-group",
                    },
                },
            },
        },
    ]


@pytest.fixture
def sample_resource_with_tags():
    """タグ付きリソースサンプル"""
    return {
        "resource_id": "i-tagged-001",
        "custodian_resource": {
            "Name": "web-server-01",
            "InstanceId": "i-tagged-001",
            "InstanceType": "t3.micro",
            "State": {"Name": "running"},
            "VpcId": "vpc-abc",
            "Tags": [
                {"Key": "Name", "Value": "web-server-01"},
                {"Key": "Environment", "Value": "production"},
                {"Key": "Team", "Value": "platform"},
            ],
        },
    }


@pytest.fixture
def sample_security_group_resource():
    """セキュリティグループリソースサンプル（IpPermissions付き）"""
    return {
        "resource_id": "sg-sec-001",
        "custodian_resource": {
            "GroupName": "open-sg",
            "VpcId": "vpc-xyz",
            "IpPermissions": [
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 443,
                    "ToPort": 443,
                    "IpRanges": [{"CidrIp": "10.0.0.0/8"}],
                },
            ],
            "IpPermissionsEgress": [
                {
                    "IpProtocol": "-1",
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                },
            ],
        },
    }


@pytest.fixture
def efficient_resource_search(mock_opensearch_client):
    """EfficientResourceSearchインスタンス"""
    from app.chat_dashboard.resource_search_v2 import EfficientResourceSearch
    return EfficientResourceSearch(mock_opensearch_client)


@pytest.fixture
def resource_index_cache():
    """ResourceIndexCacheインスタンス"""
    from app.chat_dashboard.resource_search_v2 import ResourceIndexCache
    return ResourceIndexCache()
```

---

## 6. テスト実行例

```bash
# chat_tools_v2関連テストのみ実行
pytest test/unit/chat_dashboard/test_chat_tools_v2.py -v

# resource_search_v2関連テストのみ実行
pytest test/unit/chat_dashboard/test_resource_search_v2.py -v

# 特定のテストクラスのみ実行
pytest test/unit/chat_dashboard/test_resource_search_v2.py::TestMatchResourceFilter -v

# 両方を実行（カバレッジ付き）
pytest test/unit/chat_dashboard/test_chat_tools_v2.py test/unit/chat_dashboard/test_resource_search_v2.py \
  --cov=app.chat_dashboard.chat_tools_v2 \
  --cov=app.chat_dashboard.resource_search_v2 \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/chat_dashboard/test_chat_tools_v2.py test/unit/chat_dashboard/test_resource_search_v2.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

### chat_tools_v2.py

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 19 | CTV2-001 〜 CTV2-019 |
| 異常系 | 8 | CTV2-E01 〜 CTV2-E08 |
| セキュリティ | 5 | CTV2-SEC-01 〜 CTV2-SEC-05 |
| **小計** | **32** | - |

### resource_search_v2.py

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 43 | RSRCH-001 〜 RSRCH-043 |
| 異常系 | 11 | RSRCH-E01 〜 RSRCH-E11 |
| セキュリティ | 3 | RSRCH-SEC-01 〜 RSRCH-SEC-03 |
| **小計** | **57** | - |

### 合計

| カテゴリ | 件数 |
|---------|------|
| 正常系 | 62 |
| 異常系 | 19 |
| セキュリティ | 8 |
| **合計** | **89** |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetResourceDetailsV2` | CTV2-001〜CTV2-008 | 8 |
| `TestQuickResourceSearchTool` | CTV2-009〜CTV2-012 | 4 |
| `TestFormatResourceResultsV2` | CTV2-013〜CTV2-017 | 5 |
| `TestFormatQuickSearchResults` | CTV2-018〜CTV2-019 | 2 |
| `TestGetResourceDetailsV2Errors` | CTV2-E01〜CTV2-E04 | 4 |
| `TestQuickResourceSearchToolErrors` | CTV2-E05〜CTV2-E08 | 4 |
| `TestChatToolsV2Security` | CTV2-SEC-01〜CTV2-SEC-05 | 5 |
| `TestResourceFilter` | RSRCH-001 | 1 |
| `TestPolicyFilter` | RSRCH-002 | 1 |
| `TestEfficientResourceSearch` | RSRCH-003〜RSRCH-006 | 4 |
| `TestOpenSearchBaseFilter` | RSRCH-007〜RSRCH-010 | 4 |
| `TestMatchPolicyFilter` | RSRCH-011〜RSRCH-014, RSRCH-042 | 5 |
| `TestMatchResourceFilter` | RSRCH-015〜RSRCH-024, RSRCH-043 | 11 |
| `TestMatchTags` | RSRCH-025〜RSRCH-027 | 3 |
| `TestMatchIpRange` | RSRCH-028〜RSRCH-029 | 2 |
| `TestConsolidateResults` | RSRCH-030〜RSRCH-032 | 3 |
| `TestQuickResourceSearch` | RSRCH-033〜RSRCH-037 | 5 |
| `TestCreateCommonFilters` | RSRCH-038 | 1 |
| `TestResourceIndexCache` | RSRCH-039〜RSRCH-041 | 3 |
| `TestOpenSearchBaseFilterErrors` | RSRCH-E01 | 1 |
| `TestSearchResourcesErrors` | RSRCH-E02 | 1 |
| `TestProcessDocumentErrors` | RSRCH-E03〜RSRCH-E04 | 2 |
| `TestMatchFiltersErrors` | RSRCH-E05〜RSRCH-E08 | 4 |
| `TestResourceIndexCacheErrors` | RSRCH-E09〜RSRCH-E11 | 3 |
| `TestResourceSearchV2Security` | RSRCH-SEC-01〜RSRCH-SEC-03 | 3 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CTV2-SEC-01 | `chat_tools_v2.py:72` で `auth_error` をそのままログ出力（資格情報漏洩リスク） | 例外メッセージをサニタイズしてからログ出力 |
| CTV2-SEC-02 | `chat_tools_v2.py` / `resource_search_v2.py:141` で `scan_id` のサニタイズ未実装 | `scan_id` を英数字・ハイフン・アンダースコアに制限 |
| CTV2-SEC-03 | `chat_tools_v2.py:168` で `auth_error` をそのままログ出力（CTV2-SEC-01と同一パターン） | 例外メッセージをサニタイズしてからログ出力 |
| CTV2-SEC-04 | `chat_tools_v2.py:123` で `str(e)` をそのままレスポンスに返却 | 例外メッセージをサニタイズし、一般的なエラーメッセージのみ返却 |
| CTV2-SEC-05 | `chat_tools_v2.py:186` で `str(e)` をそのままレスポンスに返却（SEC-04と同一パターン） | 例外メッセージをサニタイズし、一般的なエラーメッセージのみ返却 |
| RSRCH-SEC-01 | `resource_search_v2.py:126` で `policy_name` をサニタイズせずにwildcardクエリに使用 | 特殊文字をエスケープしてからwildcardクエリに渡す |

### 注意事項

- `pytest-asyncio` が必要（@tool関数・EfficientResourceSearchメソッドは全てasync）
- `pytest-timeout` が必要（RSRCH-SEC-03 の `@pytest.mark.timeout(5)` で使用）
- `@pytest.mark.security` マーカーの登録要（`pyproject.toml` に `markers = ["security: セキュリティ関連テスト"]`）
- OpenSearch接続は必ずモック化すること
- `resource_search_v2.py` のフィルタメソッド（`_match_*`）は同期メソッドのため直接テスト可能
- `chat_tools_v2.py` は `chat_tools.py` からインポートしているため、conftest.py で適切にモック化が必要
- @tool関数のテストには `.ainvoke()` を使用（`.invoke()` は `NotImplementedError`）
- CTV2-SEC-01/SEC-03 では `capsys`（print出力）と `caplog`（logging出力）の両方で検証し、将来の `print` → `logging` 移行にも耐性を持たせている

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | OpenSearch実際の検索動作確認不可 | クエリ構文・enabled:false挙動の検証困難 | モック使用、統合テストで別途検証 |
| 2 | 並列処理（asyncio.gather）の動作検証 | 並列実行時の競合条件確認困難 | 順次実行でのロジック正確性を優先検証 |
| 3 | 大量データでのパフォーマンス検証 | 1000件規模のデータ処理速度未測定 | パフォーマンステストは統合テストで対応 |
| 4 | v2インデックスの実データ構造 | enabled:false フィールドの実挙動 | サンプルデータで検証 |
| 5 | `capsys` は `print()` のみキャプチャ | `logging` 出力の検証不可 | SEC-01/SEC-03 は `caplog` も併記済み |

### xfail テスト運用ガイドライン

本仕様書には `@pytest.mark.xfail(strict=True)` を付与したテストが6件存在します（CTV2-SEC-01〜SEC-05、RSRCH-SEC-01）。
`strict=True` はテストが**失敗する**ことを期待するため、実装修正後にテストが通ると **XPASS（予期しない成功）** として失敗扱いになります。

**修正後の手順:**
1. 対象の実装を修正する
2. 該当テストの `@pytest.mark.xfail(...)` デコレータを**削除**する
3. テストを実行して PASS することを確認する
4. 必要に応じてアサーション条件を修正後の実装に合わせる
5. 「実装失敗が予想されるテスト」テーブルから該当行を削除する
