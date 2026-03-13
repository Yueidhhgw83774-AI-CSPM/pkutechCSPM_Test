# chat_tools テストケース

## 1. 概要

CSPMダッシュボード用チャットツールモジュールのテストケースを定義します。OpenSearchを用いたスキャン情報取得、履歴スキャン検索、違反比較、リソース詳細取得、推奨事項取得の各@toolデコレータ関数と、自然言語の時期指定解析・クエリ構築・フォーマットなどのヘルパー関数を対象とします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `parse_time_reference` | 自然言語の時期指定をOpenSearchクエリ用の日時範囲に変換 |
| `build_historical_scan_query` | 履歴スキャン検索用のOpenSearchクエリを生成 |
| `_get_scan_info_v2` | v2インデックスからスキャン情報を取得 |
| `get_current_scan_info` | 現在のスキャンIDの基本情報を取得（v1/v2対応） |
| `search_historical_scan` | 履歴スキャンを検索 |
| `format_severity_comparison` | 重要度別違反数の比較をフォーマット |
| `calculate_trend_assessment` | トレンド評価を計算 |
| `extract_resource_name_with_llm` | LLMを使用してリソースJSONから名前/識別子を抽出 |
| `get_resource_details` | @tool: 違反リソースの詳細情報を取得（v1/v2対応） |
| `get_policy_recommendations` | @tool: 推奨事項IDに基づく詳細情報取得 |
| `get_scan_info` | @tool: スキャンIDの基本情報とインデックス情報を取得 |
| `compare_scan_violations` | @tool: 現在のスキャンと指定時期のスキャン結果を比較 |
| `relativedelta` (fallback) | dateutil未インストール時の月数相対日付計算 |

### 1.2 カバレッジ目標: 80%

> **注記**: @tool関数はOpenSearch接続とLLM呼び出しをモック化。`parse_time_reference`は分岐が多いため重点的にカバー。`extract_resource_name_with_llm`はルールベース分岐のみ単体テスト対象（LLM呼び出し部分はモック化）。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/chat_dashboard/chat_tools.py`（1,442行） |
| テストコード | `test/unit/chat_dashboard/test_chat_tools.py` |
| conftest | `test/unit/chat_dashboard/conftest.py` |

### 1.4 補足情報

**外部依存:**
- `opensearchpy.TransportError`: OpenSearch接続エラーのハンドリング
- `langchain_core.tools.tool`: @toolデコレータ
- `dateutil.relativedelta`: 月単位の日付計算（ImportError時のfallbackあり）
- `app.core.clients`: `get_opensearch_client`（モジュールレベルimport）, `get_opensearch_client_with_auth`（ローカルimport）
- `app.core.config.settings`: 設定値
- `app.core.llm_factory.get_extraction_llm`: リソース名抽出用LLM
- `app.chat_dashboard.basic_auth_logic.decode_basic_auth`: Basic認証デコード

**主要な分岐ポイント:**
- `parse_time_reference`: 「前回」「N日前」「N週間前」「Nヶ月前」「昨日」「先週」「先月」「年月指定」「月のみ」「曖昧表現」「デフォルト」の11パターン
- `get_current_scan_info`: v1/v2インデックス分岐、認証あり/なし分岐
- `get_resource_details`: ポリシー名正規化（a.4/a-4/policy-a-4形式）、v1/v2インデックス分岐
- `extract_resource_name_with_llm`: Name/InstanceId/GroupName/ARN/IDフィールドの優先順位

**テストID接頭辞:**
- 正常系: `CTOOL-001` 〜
- 異常系: `CTOOL-E01` 〜
- セキュリティ: `CTOOL-SEC-01` 〜

---

## 2. 正常系テストケース

### 2.1 parse_time_reference テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-001 | 「前回」キーワード | `"前回"` | start=2020-01-01, end=current-1min, description="前回のスキャン" |
| CTOOL-002 | 「直前」キーワード | `"直前"` | start=2020-01-01, end=current-1min |
| CTOOL-003 | 「latest」キーワード | `"latest"` | start=2020-01-01, end=current-1min |
| CTOOL-004 | 日数指定「3日前」 | `"3日前"` | target=current-3days, ±12h, description="3日前" |
| CTOOL-005 | 週数指定「2週間前」 | `"2週間前"` | target=current-2weeks, ±2days, description="2週間前" |
| CTOOL-006 | 週数指定「1週前」 | `"1週前"` | target=current-1week, ±2days（「間」省略対応） |
| CTOOL-007 | 月数指定「3ヶ月前」 | `"3ヶ月前"` | target=current-3months, ±5days, description="3ヶ月前" |
| CTOOL-008 | 月数指定「1か月前」 | `"1か月前"` | target=current-1month（「か」文字対応） |
| CTOOL-009 | 「昨日」キーワード | `"昨日"` | target=current-1day, ±12h, description="昨日" |
| CTOOL-010 | 「yesterday」キーワード | `"yesterday"` | target=current-1day, ±12h |
| CTOOL-011 | 「先週」キーワード | `"先週"` | target=current-1week, ±3days, description="先週" |
| CTOOL-012 | 「last week」キーワード | `"last week"` | target=current-1week, ±3days |
| CTOOL-013 | 「先月」キーワード | `"先月"` | target=current-1month, ±7days, description="先月" |
| CTOOL-014 | 年月指定「2024年1月」 | `"2024年1月"` | start=2024-01-01, end=2024-01-31 |
| CTOOL-015 | 年月指定12月「2024年12月」 | `"2024年12月"` | start=2024-12-01, end=2024-12-31 |
| CTOOL-016 | 月のみ指定「3月」 | `"3月"` | start=currentYear-03-01, end=currentYear-03-31 |
| CTOOL-017 | 月のみ指定12月「12月」 | `"12月"` | start=currentYear-12-01, end=currentYear-12-31 |
| CTOOL-018 | 曖昧表現「最近」 | `"最近"` | target=current-1week, ±2days, description="約1週間前" |
| CTOOL-019 | デフォルト（認識不能） | `"不明なテキスト"` | target=current-1week, ±2days, description含む"約1週間前" |

```python
# test/unit/chat_dashboard/test_chat_tools.py
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock


class TestParseTimeReference:
    """parse_time_reference: 自然言語の時期指定を日時範囲に変換"""

    @pytest.fixture
    def base_date(self):
        """テスト基準日時"""
        return datetime(2025, 6, 15, 10, 0, 0)

    def test_previous_scan_keyword(self, base_date):
        """CTOOL-001: 「前回」キーワードで前回スキャン検索範囲を返す"""
        # Arrange
        from app.chat_dashboard.chat_tools import parse_time_reference

        # Act
        result = parse_time_reference("前回", base_date)

        # Assert
        assert result["start"] == datetime(2020, 1, 1)
        assert result["end"] == base_date - timedelta(minutes=1)
        assert result["description"] == "前回のスキャン"

    def test_just_before_keyword(self, base_date):
        """CTOOL-002: 「直前」キーワードで前回スキャン検索範囲を返す"""
        # Arrange
        from app.chat_dashboard.chat_tools import parse_time_reference

        # Act
        result = parse_time_reference("直前", base_date)

        # Assert
        assert result["start"] == datetime(2020, 1, 1)
        assert result["end"] == base_date - timedelta(minutes=1)
        assert result["description"] == "前回のスキャン"

    def test_latest_keyword(self, base_date):
        """CTOOL-003: 「latest」キーワードで前回スキャン検索範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("latest", base_date)
        assert result["start"] == datetime(2020, 1, 1)
        assert result["description"] == "前回のスキャン"

    def test_days_ago_pattern(self, base_date):
        """CTOOL-004: 「3日前」パターンで±12時間の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("3日前", base_date)
        target = base_date - timedelta(days=3)
        assert result["start"] == target - timedelta(hours=12)
        assert result["end"] == target + timedelta(hours=12)
        assert result["description"] == "3日前"

    def test_weeks_ago_pattern(self, base_date):
        """CTOOL-005: 「2週間前」パターンで±2日の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("2週間前", base_date)
        target = base_date - timedelta(weeks=2)
        assert result["start"] == target - timedelta(days=2)
        assert result["end"] == target + timedelta(days=2)
        assert result["description"] == "2週間前"

    def test_weeks_ago_without_kan(self, base_date):
        """CTOOL-006: 「1週前」（「間」省略）でも正しく解析される"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("1週前", base_date)
        target = base_date - timedelta(weeks=1)
        assert result["start"] == target - timedelta(days=2)

    def test_months_ago_pattern(self, base_date):
        """CTOOL-007: 「3ヶ月前」パターンで±5日の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("3ヶ月前", base_date)
        assert result["description"] == "3ヶ月前"
        # ±5日の範囲であること
        assert (result["end"] - result["start"]).days == 10

    def test_months_ago_ka_variant(self, base_date):
        """CTOOL-008: 「1か月前」（「か」文字）でも正しく解析される"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("1か月前", base_date)
        assert result["description"] == "1ヶ月前"

    def test_yesterday_keyword(self, base_date):
        """CTOOL-009: 「昨日」キーワードで前日±12時間の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("昨日", base_date)
        target = base_date - timedelta(days=1)
        assert result["start"] == target - timedelta(hours=12)
        assert result["end"] == target + timedelta(hours=12)
        assert result["description"] == "昨日"

    def test_yesterday_english(self, base_date):
        """CTOOL-010: 「yesterday」キーワードで前日±12時間の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("yesterday", base_date)
        assert result["description"] == "昨日"

    def test_last_week_keyword(self, base_date):
        """CTOOL-011: 「先週」キーワードで1週間前±3日の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("先週", base_date)
        target = base_date - timedelta(weeks=1)
        assert result["start"] == target - timedelta(days=3)
        assert result["end"] == target + timedelta(days=3)
        assert result["description"] == "先週"

    def test_last_week_english(self, base_date):
        """CTOOL-012: 「last week」キーワードで先週の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("last week", base_date)
        assert result["description"] == "先週"

    def test_last_month_keyword(self, base_date):
        """CTOOL-013: 「先月」キーワードで1ヶ月前±7日の範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("先月", base_date)
        assert result["description"] == "先月"
        assert (result["end"] - result["start"]).days == 14

    def test_year_month_pattern(self, base_date):
        """CTOOL-014: 「2024年1月」で2024年1月の全日範囲を返す"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("2024年1月", base_date)
        assert result["start"] == datetime(2024, 1, 1)
        assert result["end"] == datetime(2024, 1, 31)
        assert result["description"] == "2024年1月"

    def test_year_month_december(self, base_date):
        """CTOOL-015: 「2024年12月」で年跨ぎの月末計算が正しい"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("2024年12月", base_date)
        assert result["start"] == datetime(2024, 12, 1)
        assert result["end"] == datetime(2024, 12, 31)

    def test_month_only_pattern(self, base_date):
        """CTOOL-016: 「3月」で今年の3月として解釈"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("3月", base_date)
        assert result["start"] == datetime(base_date.year, 3, 1)
        assert result["end"] == datetime(base_date.year, 3, 31)

    def test_month_only_december(self, base_date):
        """CTOOL-017: 「12月」で年跨ぎの月末計算が正しい"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("12月", base_date)
        assert result["start"] == datetime(base_date.year, 12, 1)
        assert result["end"] == datetime(base_date.year, 12, 31)

    def test_ambiguous_expression(self, base_date):
        """CTOOL-018: 曖昧表現「最近」で約1週間前として解釈"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("最近", base_date)
        assert result["description"] == "約1週間前"

    def test_unrecognized_defaults_to_one_week(self, base_date):
        """CTOOL-019: 認識不能な文字列はデフォルト（1週間前）として解釈"""
        from app.chat_dashboard.chat_tools import parse_time_reference
        result = parse_time_reference("不明なテキスト", base_date)
        assert "約1週間前" in result["description"]
```

### 2.2 build_historical_scan_query テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-020 | 基本クエリ生成 | account, provider, date_range, exclude_id | 必須フィールドを含むクエリ辞書 |
| CTOOL-021 | 前回スキャンモード | is_previous_scan=True | size=1 |
| CTOOL-022 | アカウント「不明」時 | target_account="不明" | アカウントフィルタなし |
| CTOOL-023 | プロバイダー「不明」時 | cloud_provider="不明" | プロバイダーフィルタなし |

```python
class TestBuildHistoricalScanQuery:
    """build_historical_scan_query: 履歴スキャン検索用クエリの生成"""

    def test_basic_query_structure(self):
        """CTOOL-020: 基本的なクエリ構造が正しく生成される"""
        from app.chat_dashboard.chat_tools import build_historical_scan_query

        # Arrange
        date_range = {
            "start": datetime(2025, 6, 1),
            "end": datetime(2025, 6, 14)
        }

        # Act
        query = build_historical_scan_query(
            target_account="123456789012",
            cloud_provider="aws",
            date_range=date_range,
            exclude_scan_id="scan_current"
        )

        # Assert
        assert query["size"] == 5
        assert query["sort"][0]["initiated_at"]["order"] == "desc"
        # 日時範囲フィルタ
        range_filter = query["query"]["bool"]["must"][0]["range"]["initiated_at"]
        assert range_filter["gte"] == date_range["start"].isoformat()
        assert range_filter["lte"] == date_range["end"].isoformat()
        # 除外フィルタ
        assert query["query"]["bool"]["must_not"][0]["term"]["scan_id.keyword"] == "scan_current"
        # アカウントフィルタ
        account_filter = query["query"]["bool"]["must"][1]
        assert account_filter["term"]["summary.scan_summary.basic_statistics.target_account_id.keyword"] == "123456789012"
        # プロバイダーフィルタ
        provider_filter = query["query"]["bool"]["must"][2]
        assert provider_filter["term"]["summary.scan_summary.basic_statistics.cloud_provider.keyword"] == "aws"

    def test_previous_scan_mode(self):
        """CTOOL-021: 前回スキャンモードではsize=1"""
        from app.chat_dashboard.chat_tools import build_historical_scan_query
        date_range = {"start": datetime(2025, 1, 1), "end": datetime(2025, 6, 14)}
        query = build_historical_scan_query("acc", "aws", date_range, "scan_x", is_previous_scan=True)
        assert query["size"] == 1

    def test_unknown_account_no_filter(self):
        """CTOOL-022: アカウントが「不明」の場合、アカウントフィルタを追加しない"""
        from app.chat_dashboard.chat_tools import build_historical_scan_query
        date_range = {"start": datetime(2025, 1, 1), "end": datetime(2025, 6, 14)}
        query = build_historical_scan_query("不明", "aws", date_range, "scan_x")
        # must配列にはrange + providerのみ（アカウントフィルタなし）
        must_clauses = query["query"]["bool"]["must"]
        account_terms = [c for c in must_clauses if "term" in c and "target_account_id" in str(c)]
        assert len(account_terms) == 0

    def test_unknown_provider_no_filter(self):
        """CTOOL-023: プロバイダーが「不明」の場合、プロバイダーフィルタを追加しない"""
        from app.chat_dashboard.chat_tools import build_historical_scan_query
        date_range = {"start": datetime(2025, 1, 1), "end": datetime(2025, 6, 14)}
        query = build_historical_scan_query("acc", "不明", date_range, "scan_x")
        must_clauses = query["query"]["bool"]["must"]
        provider_terms = [c for c in must_clauses if "term" in c and "cloud_provider" in str(c)]
        assert len(provider_terms) == 0
```

### 2.3 format_severity_comparison テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-024 | 変化ありの比較 | Critical: 5→3, High: 2→4 | "Critical: 5→3件 (-2), High: 2→4件 (+2)" |
| CTOOL-025 | 変化なしの比較 | 同一データ | "重要度別の変化なし" |
| CTOOL-026 | 空リストの比較 | 両方空リスト | "重要度別の変化なし" |

```python
class TestFormatSeverityComparison:
    """format_severity_comparison: 重要度別違反数の比較フォーマット"""

    def test_with_changes(self):
        """CTOOL-024: 変化がある場合、差分付きフォーマットを返す"""
        from app.chat_dashboard.chat_tools import format_severity_comparison
        current = [
            {"severity": "Critical", "violation_count": 3},
            {"severity": "High", "violation_count": 4}
        ]
        past = [
            {"severity": "Critical", "violation_count": 5},
            {"severity": "High", "violation_count": 2}
        ]
        result = format_severity_comparison(current, past)
        assert "Critical: 5→3件 (-2)" in result
        assert "High: 2→4件 (+2)" in result

    def test_no_changes(self):
        """CTOOL-025: 変化がない場合「重要度別の変化なし」を返す"""
        from app.chat_dashboard.chat_tools import format_severity_comparison
        data = [{"severity": "High", "violation_count": 3}]
        result = format_severity_comparison(data, data)
        assert result == "重要度別の変化なし"

    def test_empty_lists(self):
        """CTOOL-026: 空リスト同士の比較で「重要度別の変化なし」を返す"""
        from app.chat_dashboard.chat_tools import format_severity_comparison
        result = format_severity_comparison([], [])
        assert result == "重要度別の変化なし"
```

### 2.4 calculate_trend_assessment テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-027 | 両方0（違反なし継続） | current=0, past=0 | "✅ 違反なし" メッセージ |
| CTOOL-028 | 0→正（新規違反検出） | current=5, past=0 | "⚠️ 新たに違反" メッセージ |
| CTOOL-029 | 大幅悪化（≥20%増） | current=120, past=100 | "🔴 大幅に悪化" メッセージ |
| CTOOL-030 | 軽度悪化（5-20%増） | current=110, past=100 | "⚠️ 悪化" メッセージ |
| CTOOL-031 | 大幅改善（≥20%減） | current=70, past=100 | "🟢 大幅に改善" メッセージ |
| CTOOL-032 | 軽度改善（5-20%減） | current=90, past=100 | "✅ 改善" メッセージ |
| CTOOL-033 | 横ばい（±5%未満） | current=102, past=100 | "📊 横ばい" メッセージ |

```python
class TestCalculateTrendAssessment:
    """calculate_trend_assessment: トレンド評価の計算"""

    def test_both_zero(self):
        """CTOOL-027: 違反0→0で「違反なし継続」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(0, 0)
        assert "違反なし" in result

    def test_zero_to_positive(self):
        """CTOOL-028: 0→正で「新たに違反検出」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(5, 0)
        assert "新たに違反" in result

    def test_major_degradation(self):
        """CTOOL-029: 20%以上増加で「大幅に悪化」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(120, 100)
        assert "大幅に悪化" in result

    def test_minor_degradation(self):
        """CTOOL-030: 5-20%増加で「悪化」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(110, 100)
        assert "悪化" in result

    def test_major_improvement(self):
        """CTOOL-031: 20%以上減少で「大幅に改善」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(70, 100)
        assert "大幅に改善" in result

    def test_minor_improvement(self):
        """CTOOL-032: 5-20%減少で「改善」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(90, 100)
        assert "改善" in result

    def test_stable(self):
        """CTOOL-033: ±5%未満で「横ばい」メッセージ"""
        from app.chat_dashboard.chat_tools import calculate_trend_assessment
        result = calculate_trend_assessment(102, 100)
        assert "横ばい" in result
```

### 2.5 extract_resource_name_with_llm テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-034 | S3バケット名（Name） | `{"custodian_resource": {"Name": "my-bucket"}}` | `"my-bucket"` |
| CTOOL-035 | EC2インスタンスID | `{"custodian_resource": {"InstanceId": "i-123"}}` | `"i-123"` |
| CTOOL-036 | セキュリティグループ名 | `{"custodian_resource": {"GroupName": "sg-web"}}` | `"sg-web"` |
| CTOOL-037 | ARNフィールド | `{"custodian_resource": {"Arn": "arn:aws:..."}}` | `"arn:aws:..."` |
| CTOOL-038 | 汎用IDフィールド | `{"custodian_resource": {"BucketName": "b1"}}` | `"b1"` |
| CTOOL-039 | LLMフォールバック | `{"custodian_resource": {"unknown_field": "val"}}` | LLMモック応答 |

```python
class TestExtractResourceNameWithLlm:
    """extract_resource_name_with_llm: リソースJSON→名前/識別子の抽出"""

    @pytest.mark.asyncio
    async def test_name_field(self):
        """CTOOL-034: Nameフィールドがある場合はそれを返す"""
        from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
        result = await extract_resource_name_with_llm(
            {"custodian_resource": {"Name": "my-bucket"}}
        )
        assert result == "my-bucket"

    @pytest.mark.asyncio
    async def test_instance_id_field(self):
        """CTOOL-035: InstanceIdフィールドがある場合はそれを返す"""
        from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
        result = await extract_resource_name_with_llm(
            {"custodian_resource": {"InstanceId": "i-1234567890abcdef0"}}
        )
        assert result == "i-1234567890abcdef0"

    @pytest.mark.asyncio
    async def test_group_name_field(self):
        """CTOOL-036: GroupNameフィールドがある場合はそれを返す"""
        from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
        result = await extract_resource_name_with_llm(
            {"custodian_resource": {"GroupName": "sg-web-server"}}
        )
        assert result == "sg-web-server"

    @pytest.mark.asyncio
    async def test_arn_field(self):
        """CTOOL-037: ARNフィールドがある場合はそれを返す"""
        from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
        result = await extract_resource_name_with_llm(
            {"custodian_resource": {"Arn": "arn:aws:iam::123456789012:role/TestRole"}}
        )
        assert result == "arn:aws:iam::123456789012:role/TestRole"

    @pytest.mark.asyncio
    async def test_generic_id_field(self):
        """CTOOL-038: 汎用IDフィールド（BucketName等）がある場合はそれを返す"""
        from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
        result = await extract_resource_name_with_llm(
            {"custodian_resource": {"BucketName": "data-lake-prod"}}
        )
        assert result == "data-lake-prod"

    @pytest.mark.asyncio
    async def test_llm_fallback(self):
        """CTOOL-039: ルールベースで抽出不能な場合、LLMにフォールバック"""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="extracted-resource-name")

        with patch("app.core.llm_factory.get_extraction_llm", return_value=mock_llm):
            from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
            result = await extract_resource_name_with_llm(
                {"custodian_resource": {"UnknownField": "value"}, "resource_type": "custom"}
            )
            assert result == "extracted-resource-name"
            mock_llm.ainvoke.assert_called_once()
```

### 2.6 _get_scan_info_v2 テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-040 | 正常取得（違反あり） | v2レスポンス | 集計済みスキャン情報辞書 |
| CTOOL-041 | ヒットなし | 空レスポンス | None |

```python
class TestGetScanInfoV2:
    """_get_scan_info_v2: v2インデックスからスキャン情報を取得"""

    @pytest.mark.asyncio
    async def test_successful_retrieval(self):
        """CTOOL-040: v2インデックスから正常にスキャン情報を集計"""
        from app.chat_dashboard.chat_tools import _get_scan_info_v2

        # Arrange
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "scan_id": "scan_v2_001",
                        "account_id": "123456789012",
                        "cloud_provider": "aws",
                        "timestamp": "2025-06-15T10:00:00Z",
                        "scan_metadata": {"job_created_at": "2025-06-15T10:00:00Z"},
                        "scan_summary": {},
                        "policies": [
                            {
                                "policy_name": "policy-a-1",
                                "policy_title": "S3暗号化チェック",
                                "severity": "High",
                                "resource_type": "s3",
                                "recommendation_uuid": "a.1",
                                "execution_details": {"violation_count": 3}
                            },
                            {
                                "policy_name": "policy-b-1",
                                "policy_title": "SG公開チェック",
                                "severity": "Critical",
                                "resource_type": "security-group",
                                "recommendation_uuid": "b.1",
                                "execution_details": {"violation_count": 0}
                            }
                        ]
                    }
                }]
            }
        }

        # Act
        result = await _get_scan_info_v2(mock_client, "scan_v2_001")

        # Assert
        assert result is not None
        assert result["scan_id"] == "scan_v2_001"
        assert result["total_violations"] == 3
        assert result["policies_with_violations"] == 1
        assert result["total_policies_scanned"] == 2
        assert result["cloud_provider"] == "aws"
        assert result["target_account_id"] == "123456789012"
        # 重要度ブレークダウン: Highのみ（violationがあるもの）
        assert len(result["severity_breakdown"]) == 1
        assert result["severity_breakdown"][0]["severity"] == "High"

    @pytest.mark.asyncio
    async def test_no_hits_returns_none(self):
        """CTOOL-041: ヒットなしの場合Noneを返す"""
        from app.chat_dashboard.chat_tools import _get_scan_info_v2
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        result = await _get_scan_info_v2(mock_client, "nonexistent")
        assert result is None
```

### 2.7 get_current_scan_info テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-042 | v1正常取得（認証なし） | scan_id, index_version="v1" | スキャン情報辞書 |
| CTOOL-043 | v2正常取得 | scan_id, index_version="v2" | _get_scan_info_v2へ委譲 |
| CTOOL-044 | 認証付きクライアント | opensearch_auth="Basic xxx" | 認証付きクライアント使用 |

```python
class TestGetCurrentScanInfo:
    """get_current_scan_info: スキャンIDの基本情報取得"""

    @pytest.mark.asyncio
    async def test_v1_successful_retrieval(self):
        """CTOOL-042: v1インデックスから正常にスキャン情報を取得"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "scan_id": "scan_001",
                        "initiated_at": "2025-06-15T10:00:00Z",
                        "summary": {
                            "message": "スキャン完了",
                            "scan_summary": {
                                "ai_scan_summary": {
                                    "basic_statistics": {
                                        "total_violations": 10,
                                        "policies_with_violations": 3,
                                        "total_policies_scanned": 15,
                                        "cloud_provider": "aws",
                                        "target_account_id": "123456789012"
                                    },
                                    "severity_breakdown": [{"severity": "High", "violation_count": 5}],
                                    "all_policy_results": [],
                                    "insights": ["重要な発見事項"],
                                    "top_policy_violations": []
                                }
                            }
                        }
                    }
                }]
            }
        }

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("scan_001")

        assert result is not None
        assert result["scan_id"] == "scan_001"
        assert result["total_violations"] == 10
        assert result["cloud_provider"] == "aws"

    @pytest.mark.asyncio
    async def test_v2_delegates_to_get_scan_info_v2(self):
        """CTOOL-043: v2の場合は_get_scan_info_v2に委譲"""
        mock_client = AsyncMock()
        expected_result = {"scan_id": "scan_v2", "total_violations": 5}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools._get_scan_info_v2", return_value=expected_result) as mock_v2:
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("scan_v2", index_version="v2")

        assert result == expected_result
        mock_v2.assert_called_once_with(mock_client, "scan_v2")

    @pytest.mark.asyncio
    async def test_with_basic_auth(self):
        """CTOOL-044: Basic認証情報が提供された場合、認証付きクライアントを使用"""
        mock_auth_client = AsyncMock()
        mock_auth_client.search.return_value = {
            "hits": {"total": {"value": 1}, "hits": [{"_source": {
                "scan_id": "scan_auth", "initiated_at": "",
                "summary": {"message": "", "scan_summary": {"ai_scan_summary": {"basic_statistics": {}, "severity_breakdown": [], "all_policy_results": [], "insights": [], "top_policy_violations": []}}}
            }}]}
        }

        with patch("app.chat_dashboard.basic_auth_logic.decode_basic_auth", return_value=("user", "pass")), \
             patch("app.core.clients.get_opensearch_client_with_auth", return_value=mock_auth_client):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("scan_auth", opensearch_auth="Basic dXNlcjpwYXNz")

        assert result is not None
```

### 2.8 search_historical_scan テスト

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-045 | 正常取得 | 有効なパラメータ | 最新スキャン情報辞書 |
| CTOOL-046 | ヒットなし | マッチなし | None |

```python
class TestSearchHistoricalScan:
    """search_historical_scan: 履歴スキャンの検索"""

    @pytest.mark.asyncio
    async def test_successful_search(self):
        """CTOOL-045: 正常にスキャン履歴を検索・取得"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "scan_id": "scan_past",
                        "initiated_at": "2025-06-01T10:00:00Z",
                        "summary": {
                            "message": "過去スキャン",
                            "scan_summary": {
                                "ai_scan_summary": {
                                    "basic_statistics": {
                                        "total_violations": 8,
                                        "cloud_provider": "aws",
                                        "target_account_id": "123456789012"
                                    },
                                    "severity_breakdown": []
                                }
                            }
                        }
                    }
                }]
            }
        }

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import search_historical_scan
            result = await search_historical_scan(
                "123456789012", "aws",
                {"start": datetime(2025, 6, 1), "end": datetime(2025, 6, 14)},
                "scan_current"
            )

        assert result is not None
        assert result["scan_id"] == "scan_past"
        assert result["total_violations"] == 8

    @pytest.mark.asyncio
    async def test_no_hits_returns_none(self):
        """CTOOL-046: ヒットなしの場合Noneを返す"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import search_historical_scan
            result = await search_historical_scan(
                "acc", "aws",
                {"start": datetime(2025, 1, 1), "end": datetime(2025, 1, 31)},
                "scan_x"
            )

        assert result is None
```

### 2.9 get_resource_details テスト（@tool）

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-047 | v1正常取得 | scan_id, index_version="v1" | マークダウン形式のリソース詳細 |
| CTOOL-048 | v2インデックス名 | index_version="v2" | インデックス名="cspm-scan-result-v2" |
| CTOOL-049 | ポリシー名正規化（a.4→policy-a-4） | policy_name="a.4" | 正規化パターンで検索 |

```python
class TestGetResourceDetails:
    """get_resource_details: @toolデコレータ付きリソース詳細取得"""

    @pytest.mark.asyncio
    async def test_v1_successful_retrieval(self):
        """CTOOL-047: v1インデックスからリソース詳細を正常取得"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "policy_name": "policy-a-1",
                        "resource_count": 1,
                        "resources": [{
                            "resource_id": "sg-12345",
                            "custodian_resource": {
                                "GroupName": "web-sg",
                                "Description": "Web server SG",
                                "c7n:MatchedFilters": ["IpPermissions"]
                            }
                        }],
                        "custodian_metadata": {"policy": {
                            "description": "SG公開チェック",
                            "resource": "security-group",
                            "metadata": {"severity": "High", "recommendation_id": "a.1"}
                        }},
                        "account_id": "123456789012",
                        "region": "ap-northeast-1",
                        "cloud_provider": "aws"
                    }
                }]
            }
        }

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client), \
             patch("app.chat_dashboard.chat_tools.extract_resource_name_with_llm", return_value="web-sg"):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke(
                {"scan_id": "scan_001", "index_version": "v1"}
            )

        assert "リソース詳細情報" in result
        assert "web-sg" in result
        assert "High" in result

    @pytest.mark.asyncio
    async def test_v2_uses_fixed_index_name(self):
        """CTOOL-048: v2インデックスでは固定インデックス名を使用"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke(
                {"scan_id": "scan_001", "index_version": "v2"}
            )

        # v2では固定インデックス名で検索
        call_args = mock_client.search.call_args
        assert call_args.kwargs.get("index") == "cspm-scan-result-v2" or \
               call_args[1].get("index") == "cspm-scan-result-v2"

    @pytest.mark.asyncio
    async def test_policy_name_normalization(self):
        """CTOOL-049: ポリシー名「a.4」がpolicy-a-4形式に正規化される"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            await get_resource_details.ainvoke(
                {"scan_id": "scan_001", "policy_name": "a.4"}
            )

        # 検索クエリにpolicy-a-4が含まれることを検証
        call_args = mock_client.search.call_args
        query_body = call_args.kwargs.get("body") or call_args[1].get("body")
        query_str = str(query_body)
        assert "policy-a-4" in query_str
```

### 2.10 get_policy_recommendations テスト（@tool）

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-050 | 正常取得 | recommendation_id="a.1" | マークダウン形式の推奨事項詳細 |
| CTOOL-051 | ID正規化（policy-a-1→a.1） | recommendation_id="policy-a-1" | 正規化されたIDで検索 |

```python
class TestGetPolicyRecommendations:
    """get_policy_recommendations: @toolデコレータ付き推奨事項取得"""

    @pytest.mark.asyncio
    async def test_successful_retrieval(self):
        """CTOOL-050: 推奨事項IDから詳細情報を正常取得"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {
            "hits": {
                "total": {"value": 1},
                "hits": [{
                    "_source": {
                        "recommendationId": "a.1",
                        "title": "S3バケットの暗号化",
                        "description": "S3バケットはサーバーサイド暗号化を有効にすべきです",
                        "severity": "High",
                        "rationale": "データ保護のため",
                        "impact": "暗号化されていないデータは漏洩リスクが高い",
                        "audit": ["手順1", "手順2"],
                        "remediation": ["修正手順1"],
                        "references": ["https://example.com"],
                        "additionalInformation": [],
                        "category": ["Storage"],
                        "targetClouds": ["aws"],
                        "severity_reason": ""
                    }
                }]
            }
        }

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_policy_recommendations
            result = await get_policy_recommendations.ainvoke(
                {"recommendation_id": "a.1"}
            )

        assert "S3バケットの暗号化" in result
        assert "High" in result
        assert "監査手順" in result

    @pytest.mark.asyncio
    async def test_id_normalization(self):
        """CTOOL-051: policy-a-1形式がa.1形式に正規化される"""
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_policy_recommendations
            result = await get_policy_recommendations.ainvoke(
                {"recommendation_id": "policy-a-1"}
            )

        # 検索パターンにa.1が含まれること
        call_args = mock_client.search.call_args
        query_str = str(call_args)
        assert "a.1" in query_str
```

### 2.11 get_scan_info テスト（@tool）

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-052 | 正常取得 | scan_id | マークダウン形式のスキャン情報 |

```python
class TestGetScanInfo:
    """get_scan_info: @toolデコレータ付きスキャン情報取得"""

    @pytest.mark.asyncio
    async def test_successful_retrieval(self):
        """CTOOL-052: スキャン情報を正常取得しマークダウン形式で返す"""
        mock_scan_info = {
            "scan_id": "scan_001",
            "created_at": "2025-06-15T10:00:00Z",
            "total_violations": 10,
            "policies_with_violations": 3,
            "total_policies_scanned": 15,
            "cloud_provider": "aws",
            "target_account_id": "123456789012",
            "severity_breakdown": [],
            "all_policy_results": [
                {"severity": "High", "violation_count": 5, "status": "違反あり",
                 "policy_name": "policy-a-1", "policy_title": "S3暗号化"}
            ],
            "insights": ["重要な発見"],
            "top_policy_violations": [],
            "message": "スキャン完了"
        }

        with patch("app.chat_dashboard.chat_tools.get_current_scan_info", return_value=mock_scan_info):
            from app.chat_dashboard.chat_tools import get_scan_info
            result = await get_scan_info.ainvoke({"scan_id": "scan_001"})

        assert "スキャン情報詳細" in result
        assert "scan_001" in result
        assert "aws" in result
        assert "10" in result
```

### 2.12 compare_scan_violations テスト（@tool）

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-053 | 正常比較 | current_scan_id, time_reference="前回" | マークダウン形式の比較結果 |

```python
class TestCompareScanViolations:
    """compare_scan_violations: @toolデコレータ付きスキャン比較"""

    @pytest.mark.asyncio
    async def test_successful_comparison(self):
        """CTOOL-053: 現在と過去のスキャンを正常比較"""
        current_scan = {
            "scan_id": "scan_current",
            "created_at": "2025-06-15T10:00:00Z",
            "total_violations": 15,
            "target_account_id": "123456789012",
            "cloud_provider": "aws",
            "severity_breakdown": [{"severity": "High", "violation_count": 10}]
        }
        past_scan = {
            "scan_id": "scan_past",
            "created_at": "2025-06-08T10:00:00Z",
            "total_violations": 10,
            "cloud_provider": "aws",
            "target_account_id": "123456789012",
            "severity_breakdown": [{"severity": "High", "violation_count": 8}]
        }

        with patch("app.chat_dashboard.chat_tools.get_current_scan_info", return_value=current_scan), \
             patch("app.chat_dashboard.chat_tools.search_historical_scan", return_value=past_scan):
            from app.chat_dashboard.chat_tools import compare_scan_violations
            result = await compare_scan_violations.ainvoke(
                {"current_scan_id": "scan_current", "time_reference": "前回"}
            )

        assert "スキャン結果比較" in result
        assert "15" in result  # 現在の違反数
        assert "10" in result  # 過去の違反数
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-E01 | OpenSearchクライアント初期化失敗（get_current_scan_info） | クライアント=None | None |
| CTOOL-E02 | OpenSearch検索例外（get_current_scan_info） | 検索時Exception | None |
| CTOOL-E03 | v1ヒットなし（get_current_scan_info） | 空結果 | None |
| CTOOL-E04 | 認証デコード失敗（get_current_scan_info） | 不正なBasic認証 | クライアント=None→None |
| CTOOL-E05 | v2検索例外（_get_scan_info_v2） | Exception発生 | None |
| CTOOL-E06 | OpenSearchクライアント初期化失敗（search_historical_scan） | クライアント=None | None |
| CTOOL-E07 | 検索例外（search_historical_scan） | Exception発生 | None |
| CTOOL-E08 | LLM抽出失敗（extract_resource_name_with_llm） | Exception | resource_id fallback |
| CTOOL-E09 | LLM空レスポンス（extract_resource_name_with_llm） | 空文字列 | resource_id fallback |
| CTOOL-E10 | LLM「申し訳」レスポンス | 「申し訳ございません」 | resource_id fallback |
| CTOOL-E11 | OpenSearchクライアント初期化失敗（get_resource_details） | クライアント=None | エラーメッセージ文字列 |
| CTOOL-E12 | TransportError（get_resource_details） | TransportError | DBエラーメッセージ |
| CTOOL-E13 | 予期しない例外（get_resource_details） | Exception | 汎用エラーメッセージ |
| CTOOL-E14 | ヒットなし（get_resource_details） | 空結果 | 「リソースが見つかりません」メッセージ |
| CTOOL-E15 | OpenSearchクライアント初期化失敗（get_policy_recommendations） | クライアント=None | エラーメッセージ |
| CTOOL-E16 | TransportError（get_policy_recommendations） | TransportError | DBエラーメッセージ |
| CTOOL-E17 | ヒットなし（get_policy_recommendations） | 空結果 | 「推奨事項が見つかりません」メッセージ |
| CTOOL-E18 | スキャンID不存在（get_scan_info） | 不存在ID | エラーメッセージ |
| CTOOL-E19 | TransportError（get_scan_info） | TransportError | DBエラーメッセージ |
| CTOOL-E20 | スキャンID不存在（compare_scan_violations） | 不存在ID | エラーメッセージ |
| CTOOL-E21 | 比較対象なし（compare_scan_violations） | 該当期間スキャンなし | 「比較対象が見つかりません」メッセージ |
| CTOOL-E22 | 無効な日時フォーマット（get_scan_info） | created_at="invalid" | formatted_date="不明" |

### 3.1 get_current_scan_info 異常系

```python
class TestGetCurrentScanInfoErrors:
    """get_current_scan_info: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_client_initialization_failure(self):
        """CTOOL-E01: OpenSearchクライアント初期化失敗でNoneを返す

        chat_tools.py:433-435 のクライアントNullチェック分岐をカバー
        """
        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=None):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("scan_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """CTOOL-E02: OpenSearch検索中の例外でNoneを返す

        chat_tools.py:500-504 のexceptブロックをカバー
        """
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("Connection refused")

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("scan_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_v1_no_hits(self):
        """CTOOL-E03: v1検索でヒットなしの場合Noneを返す

        chat_tools.py:471-473 の空ヒットチェック分岐をカバー
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_auth_decode_failure(self):
        """CTOOL-E04: 認証デコード失敗でクライアント=None→Noneを返す

        chat_tools.py:426-428 のauth_errorブロックをカバー
        """
        with patch("app.chat_dashboard.basic_auth_logic.decode_basic_auth", side_effect=Exception("Invalid auth")):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            result = await get_current_scan_info("scan_001", opensearch_auth="Basic invalid")
        assert result is None
```

### 3.2 _get_scan_info_v2 異常系

```python
class TestGetScanInfoV2Errors:
    """_get_scan_info_v2: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        """CTOOL-E05: 検索例外でNoneを返す

        chat_tools.py:385-389 のexceptブロックをカバー
        """
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("Timeout")

        from app.chat_dashboard.chat_tools import _get_scan_info_v2
        result = await _get_scan_info_v2(mock_client, "scan_v2")
        assert result is None
```

### 3.3 search_historical_scan 異常系

```python
class TestSearchHistoricalScanErrors:
    """search_historical_scan: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_client_none(self):
        """CTOOL-E06: OpenSearchクライアントNoneでNoneを返す

        chat_tools.py:549-550 のクライアントNullチェック分岐をカバー
        """
        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=None):
            from app.chat_dashboard.chat_tools import search_historical_scan
            result = await search_historical_scan(
                "acc", "aws",
                {"start": datetime(2025, 1, 1), "end": datetime(2025, 6, 1)},
                "scan_x"
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_search_exception(self):
        """CTOOL-E07: 検索例外でNoneを返す

        chat_tools.py:583-585 のexceptブロックをカバー
        """
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("Search error")

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import search_historical_scan
            result = await search_historical_scan(
                "acc", "aws",
                {"start": datetime(2025, 1, 1), "end": datetime(2025, 6, 1)},
                "scan_x"
            )
        assert result is None
```

### 3.4 extract_resource_name_with_llm 異常系

```python
class TestExtractResourceNameWithLlmErrors:
    """extract_resource_name_with_llm: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_llm_exception_fallback(self):
        """CTOOL-E08: LLM呼び出し例外時にresource_idへフォールバック

        chat_tools.py:724-727 のexceptブロックをカバー
        """
        with patch("app.core.llm_factory.get_extraction_llm", side_effect=Exception("LLM error")):
            from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
            result = await extract_resource_name_with_llm(
                {"custodian_resource": {"UnknownField": "val"}, "resource_id": "res-fallback"}
            )
        assert result == "res-fallback"

    @pytest.mark.asyncio
    async def test_llm_empty_response_fallback(self):
        """CTOOL-E09: LLMが空文字列を返した場合にresource_idへフォールバック

        chat_tools.py:718-722 の妥当性チェック分岐をカバー
        """
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="")

        with patch("app.core.llm_factory.get_extraction_llm", return_value=mock_llm):
            from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
            result = await extract_resource_name_with_llm(
                {"custodian_resource": {"UnknownField": "val"}, "resource_id": "res-empty"}
            )
        assert result == "res-empty"

    @pytest.mark.asyncio
    async def test_llm_apology_response_fallback(self):
        """CTOOL-E10: LLMが「申し訳」で始まるレスポンスの場合にresource_idへフォールバック

        chat_tools.py:718 の「申し訳」チェック分岐をカバー
        """
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = MagicMock(content="申し訳ございません、識別できません")

        with patch("app.core.llm_factory.get_extraction_llm", return_value=mock_llm):
            from app.chat_dashboard.chat_tools import extract_resource_name_with_llm
            result = await extract_resource_name_with_llm(
                {"custodian_resource": {"UnknownField": "val"}, "resource_id": "res-sorry"}
            )
        assert result == "res-sorry"
```

### 3.5 @tool関数 異常系

```python
class TestGetResourceDetailsErrors:
    """get_resource_details: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_client_none(self):
        """CTOOL-E11: OpenSearchクライアントNoneでエラーメッセージを返す

        chat_tools.py:783-784 のクライアントNullチェック分岐をカバー
        """
        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=None):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke({"scan_id": "scan_001"})
        assert "エラー" in result
        assert "OpenSearchクライアント" in result

    @pytest.mark.asyncio
    async def test_transport_error(self):
        """CTOOL-E12: TransportErrorでDBエラーメッセージを返す

        chat_tools.py:981-982 のTransportErrorハンドリングをカバー
        """
        from opensearchpy import TransportError
        mock_client = AsyncMock()
        mock_client.search.side_effect = TransportError(500, "internal_server_error", {})

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke({"scan_id": "scan_001"})
        assert "データベース接続エラー" in result

    @pytest.mark.asyncio
    async def test_unexpected_exception(self):
        """CTOOL-E13: 予期しない例外で汎用エラーメッセージを返す

        chat_tools.py:983-984 の汎用Exceptionハンドリングをカバー
        """
        mock_client = AsyncMock()
        mock_client.search.side_effect = RuntimeError("Unexpected error")

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke({"scan_id": "scan_001"})
        assert "予期しないエラー" in result

    @pytest.mark.asyncio
    async def test_no_hits(self):
        """CTOOL-E14: ヒットなしで「リソースが見つかりません」メッセージを返す

        chat_tools.py:869-877 の空ヒットハンドリングをカバー
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke({"scan_id": "scan_001"})
        assert "リソースが見つかりません" in result


class TestGetPolicyRecommendationsErrors:
    """get_policy_recommendations: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_client_none(self):
        """CTOOL-E15: OpenSearchクライアントNoneでエラーメッセージを返す

        chat_tools.py:1032-1033 のクライアントNullチェック分岐をカバー
        """
        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=None):
            from app.chat_dashboard.chat_tools import get_policy_recommendations
            result = await get_policy_recommendations.ainvoke(
                {"recommendation_id": "a.1"}
            )
        assert "エラー" in result

    @pytest.mark.asyncio
    async def test_transport_error(self):
        """CTOOL-E16: TransportErrorでDBエラーメッセージを返す

        chat_tools.py:1174-1175 のTransportErrorハンドリングをカバー
        """
        from opensearchpy import TransportError
        mock_client = AsyncMock()
        mock_client.search.side_effect = TransportError(500, "error", {})

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_policy_recommendations
            result = await get_policy_recommendations.ainvoke(
                {"recommendation_id": "a.1"}
            )
        assert "データベース接続エラー" in result

    @pytest.mark.asyncio
    async def test_no_hits(self):
        """CTOOL-E17: ヒットなしで「推奨事項が見つかりません」メッセージを返す

        chat_tools.py:1097-1098 の空ヒットハンドリングをカバー
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_policy_recommendations
            result = await get_policy_recommendations.ainvoke(
                {"recommendation_id": "nonexistent"}
            )
        assert "推奨事項が見つかりません" in result


class TestGetScanInfoErrors:
    """get_scan_info: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_scan_not_found(self):
        """CTOOL-E18: スキャンID不存在でエラーメッセージを返す

        chat_tools.py:1206-1207 のscan_info Noneチェック分岐をカバー
        """
        with patch("app.chat_dashboard.chat_tools.get_current_scan_info", return_value=None):
            from app.chat_dashboard.chat_tools import get_scan_info
            result = await get_scan_info.ainvoke({"scan_id": "nonexistent"})
        assert "エラー" in result
        assert "nonexistent" in result

    @pytest.mark.asyncio
    async def test_transport_error(self):
        """CTOOL-E19: TransportErrorでDBエラーメッセージを返す

        chat_tools.py:1323-1324 のTransportErrorハンドリングをカバー
        """
        from opensearchpy import TransportError
        with patch("app.chat_dashboard.chat_tools.get_current_scan_info",
                    side_effect=TransportError(500, "error", {})):
            from app.chat_dashboard.chat_tools import get_scan_info
            result = await get_scan_info.ainvoke({"scan_id": "scan_001"})
        assert "データベース接続エラー" in result

    @pytest.mark.asyncio
    async def test_invalid_datetime_format(self):
        """CTOOL-E22: 無効な日時フォーマットで「不明」にフォールバック

        chat_tools.py:1216 のValueErrorハンドリング分岐をカバー
        """
        mock_info = {
            "scan_id": "scan_001", "created_at": "invalid-date",
            "total_violations": 0, "policies_with_violations": 0,
            "total_policies_scanned": 0, "cloud_provider": "aws",
            "target_account_id": "acc", "severity_breakdown": [],
            "all_policy_results": [], "insights": [],
            "top_policy_violations": [], "message": "test"
        }
        with patch("app.chat_dashboard.chat_tools.get_current_scan_info", return_value=mock_info):
            from app.chat_dashboard.chat_tools import get_scan_info
            result = await get_scan_info.ainvoke({"scan_id": "scan_001"})
        assert "不明" in result


class TestCompareScanViolationsErrors:
    """compare_scan_violations: 異常系テスト"""

    @pytest.mark.asyncio
    async def test_scan_not_found(self):
        """CTOOL-E20: スキャンID不存在でエラーメッセージを返す

        chat_tools.py:1359-1360 のスキャン不存在チェック分岐をカバー
        """
        with patch("app.chat_dashboard.chat_tools.get_current_scan_info", return_value=None):
            from app.chat_dashboard.chat_tools import compare_scan_violations
            result = await compare_scan_violations.ainvoke(
                {"current_scan_id": "nonexistent", "time_reference": "前回"}
            )
        assert "エラー" in result
        assert "nonexistent" in result

    @pytest.mark.asyncio
    async def test_no_historical_match(self):
        """CTOOL-E21: 比較対象スキャンなしで「比較対象が見つかりません」メッセージ

        chat_tools.py:1386-1387 の比較対象不存在チェック分岐をカバー
        """
        current_scan = {
            "scan_id": "scan_current",
            "created_at": "2025-06-15T10:00:00Z",
            "total_violations": 10,
            "target_account_id": "acc",
            "cloud_provider": "aws",
            "severity_breakdown": []
        }

        with patch("app.chat_dashboard.chat_tools.get_current_scan_info", return_value=current_scan), \
             patch("app.chat_dashboard.chat_tools.search_historical_scan", return_value=None):
            from app.chat_dashboard.chat_tools import compare_scan_violations
            result = await compare_scan_violations.ainvoke(
                {"current_scan_id": "scan_current", "time_reference": "前回"}
            )
        assert "比較対象が見つかりません" in result
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CTOOL-SEC-01 | 認証情報ログ漏洩 | opensearch_auth="Basic YWRtaW46..." | パスワード平文・Base64トークン・Authorization生値がログに含まれない |
| CTOOL-SEC-02 | scan_idインデックス名インジェクション | scan_id="../../admin" | 不正インデックスアクセスの検証 |
| CTOOL-SEC-03 | ポリシー名wildcardインジェクション | policy_name="*" | 全データ返却しないことの検証 |
| CTOOL-SEC-04 | time_reference極端入力 | 10,000文字の文字列 | デフォルトにフォールバック、クラッシュなし |
| CTOOL-SEC-05 | 推奨事項IDインジェクション | recommendation_id="a.1\" OR 1=1" | 入力がterm/wildcard値内に閉じ込められ、クエリ構造を破壊しないこと |
| CTOOL-SEC-06 | time_reference制御文字 | "\x00\x0a\x0d" | デフォルトにフォールバック、例外なし |

```python
@pytest.mark.security
class TestChatToolsSecurity:
    """chat_tools セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(strict=True, reason="chat_tools.py:411 で opensearch_auth[:50] を直接ログ出力")
    async def test_auth_credentials_not_logged(self, capsys):
        """CTOOL-SEC-01: 認証情報（パスワード・トークン生値）がログに出力されないこと

        chat_tools.py:411 で opensearch_auth[:50] がそのまま出力されるため、
        短いBasicトークンは実質全文がログに漏洩する。
        デコード後のパスワード平文だけでなく、Authorization ヘッダの生値
        （Base64エンコード済みトークン）も非出力であることを検証する。

        【実装失敗予定】chat_tools.py:411 で opensearch_auth[:50] を直接出力している。
        修正方針: 認証情報のログ出力を「認証あり」程度に留め、トークン値を除去する。
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        auth_header = "Basic YWRtaW46U3VwZXJTZWNyZXQxMjMh"
        with patch("app.chat_dashboard.basic_auth_logic.decode_basic_auth", return_value=("admin", "SuperSecret123!")), \
             patch("app.core.clients.get_opensearch_client_with_auth", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_current_scan_info
            await get_current_scan_info("scan_001", opensearch_auth=auth_header)

        captured = capsys.readouterr()
        # パスワード平文がstdoutに含まれないことを確認
        assert "SuperSecret123!" not in captured.out
        # Base64エンコード済みトークンがstdoutに含まれないことを確認
        assert "YWRtaW46U3VwZXJTZWNyZXQxMjMh" not in captured.out
        # Authorization生値（Basic ...）がstdoutに含まれないことを確認
        assert auth_header not in captured.out

    @pytest.mark.asyncio
    @pytest.mark.xfail(strict=True, reason="chat_tools.py:791 でscan_idバリデーション未実装")
    async def test_scan_id_index_injection(self):
        """CTOOL-SEC-02: scan_idを利用したインデックス名インジェクション

        chat_tools.py:791 で `cspm-scan-result-{scan_id}` としてインデックス名を構築。
        パストラバーサル文字を含むscan_idが拒否されることを検証。

        【実装失敗予定】chat_tools.py:791 でscan_idのバリデーションが行われていない。
        修正方針: scan_idの入力検証（英数字・ハイフン・アンダースコアのみ許可）を追加。
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            result = await get_resource_details.ainvoke(
                {"scan_id": "../../admin", "index_version": "v1"}
            )

        # 防御的アサーション: パストラバーサルがインデックス名に含まれないこと
        call_args = mock_client.search.call_args
        assert call_args is not None, "searchが呼ばれなかった"
        used_index = call_args.kwargs.get("index") or call_args[1].get("index")
        assert "../../" not in used_index, "scan_idにパストラバーサル文字が含まれている"

    @pytest.mark.asyncio
    @pytest.mark.xfail(strict=True, reason="chat_tools.py:840 でpolicy_nameサニタイズ未実装")
    async def test_policy_name_wildcard_injection(self):
        """CTOOL-SEC-03: ポリシー名にワイルドカード「*」を指定した場合の挙動

        chat_tools.py:840 で wildcard クエリが使用されており、
        「*」指定で意図しない全件マッチが発生する可能性がある。

        【実装失敗予定】chat_tools.py:840 で入力サニタイズが行われていない。
        修正方針: wildcardメタ文字（`*`, `?`）のエスケープ処理を追加。
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_resource_details
            await get_resource_details.ainvoke(
                {"scan_id": "scan_001", "policy_name": "*"}
            )

        # 防御的アサーション: wildcardクエリにエスケープされていない「*」が含まれないこと
        call_args = mock_client.search.call_args
        query_str = str(call_args)
        assert "***" not in query_str and "**" not in query_str, \
            "policy_nameのwildcardメタ文字がエスケープされていない"

    def test_time_reference_extreme_input(self):
        """CTOOL-SEC-04: 極端に長いtime_reference入力でクラッシュしないこと

        parse_time_reference内の正規表現マッチで、ReDoS攻撃等を引き起こさないことを確認。
        """
        from app.chat_dashboard.chat_tools import parse_time_reference
        long_input = "A" * 10000
        base_date = datetime(2025, 6, 15, 10, 0, 0)

        # Act - 例外なく完了すること
        result = parse_time_reference(long_input, base_date)

        # Assert - デフォルトにフォールバック
        assert "約1週間前" in result["description"]

    @pytest.mark.asyncio
    async def test_recommendation_id_injection(self):
        """CTOOL-SEC-05: 推奨事項IDへのクエリインジェクション試行

        chat_tools.py:1060-1071 でterm/wildcardクエリに値が直接埋め込まれる。
        OpenSearch DSLではSQLインジェクション相当の攻撃は限定的だが、
        入力がクエリ構造を破壊せずterm/wildcard値としてのみ使用されることを検証。
        """
        mock_client = AsyncMock()
        mock_client.search.return_value = {"hits": {"total": {"value": 0}, "hits": []}}
        malicious_id = 'a.1" OR 1=1'

        with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
            from app.chat_dashboard.chat_tools import get_policy_recommendations
            result = await get_policy_recommendations.ainvoke(
                {"recommendation_id": malicious_id}
            )

        # Assert 1: レスポンスがエラーまたは「見つかりません」であること
        assert "推奨事項が見つかりません" in result or "エラー" in result

        # Assert 2: クエリ構造の検証 — 入力値がterm/wildcard値に厳密一致で閉じ込められていること
        call_args = mock_client.search.call_args
        assert call_args is not None, "searchが呼ばれなかった"
        query_body = call_args.kwargs.get("body") or call_args[1].get("body")
        should_clauses = query_body["query"]["bool"]["should"]

        # 実装の正規化ロジック（chat_tools.py:1036-1057）から導出される期待値:
        #   normalized_id = 'a.1" OR 1=1'（変換なし）
        #   search_patterns = [normalized_id, malicious_id, 'a-1" OR 1=1']
        expected_term_values = {malicious_id, malicious_id.replace(".", "-")}
        expected_wc_values = {f"*{p}*" for p in expected_term_values | {malicious_id}}

        # term/wildcard値が期待値と厳密一致し、クエリ構造を破壊していないことを検証
        term_values = set()
        wc_values = set()
        for clause in should_clauses:
            if "term" in clause:
                term_values.add(list(clause["term"].values())[0])
            if "wildcard" in clause:
                wc_values.add(list(clause["wildcard"].values())[0])

        # 悪性入力がそのまま値としてのみ使用されていること
        assert term_values <= expected_term_values, \
            f"予期しないterm値: {term_values - expected_term_values}"
        assert wc_values <= expected_wc_values, \
            f"予期しないwildcard値: {wc_values - expected_wc_values}"

    def test_time_reference_control_characters(self):
        """CTOOL-SEC-06: time_referenceに制御文字を含む場合でも例外なく処理される

        NUL、改行、キャリッジリターン等の制御文字がparse_time_referenceに渡された場合の安全性。
        """
        from app.chat_dashboard.chat_tools import parse_time_reference
        base_date = datetime(2025, 6, 15, 10, 0, 0)

        # Act - 制御文字を含む入力
        result = parse_time_reference("\x00\x0a\x0d", base_date)

        # Assert - 例外なくデフォルトにフォールバック
        assert "約1週間前" in result["description"]
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_chat_tools_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_opensearch_client` | OpenSearchクライアントモック | function | No |
| `mock_opensearch_client_with_auth` | 認証付きOpenSearchクライアントモック | function | No |
| `mock_extraction_llm` | リソース名抽出用LLMモック | function | No |
| `sample_scan_response_v1` | v1スキャン検索レスポンスサンプル | function | No |
| `sample_scan_response_v2` | v2スキャン検索レスポンスサンプル | function | No |
| `sample_resource_json` | リソースJSONサンプル | function | No |

### 共通フィクスチャ定義

```python
# test/unit/chat_dashboard/conftest.py に追加
import sys
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

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
def reset_chat_tools_module():
    """テストごとにモジュールのグローバル状態をリセット

    chat_tools.pyはモジュールレベルの状態を持たないが、
    importキャッシュの影響を排除するためcore系モジュールを除去
    """
    yield
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_opensearch_client():
    """OpenSearchクライアントモック（外部接続防止）"""
    mock_client = AsyncMock()
    with patch("app.chat_dashboard.chat_tools.get_opensearch_client", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_opensearch_client_with_auth():
    """認証付きOpenSearchクライアントモック"""
    mock_client = AsyncMock()
    with patch("app.chat_dashboard.basic_auth_logic.decode_basic_auth", return_value=("user", "pass")), \
         patch("app.core.clients.get_opensearch_client_with_auth", return_value=mock_client):
        yield mock_client


@pytest.fixture
def mock_extraction_llm():
    """リソース名抽出用LLMモック"""
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = MagicMock(content="mocked-resource-name")
    with patch("app.core.llm_factory.get_extraction_llm", return_value=mock_llm):
        yield mock_llm


@pytest.fixture
def sample_scan_response_v1():
    """v1スキャン検索レスポンスサンプル"""
    return {
        "hits": {
            "total": {"value": 1},
            "hits": [{
                "_source": {
                    "scan_id": "scan_v1_sample",
                    "initiated_at": "2025-06-15T10:00:00Z",
                    "summary": {
                        "message": "スキャン完了",
                        "scan_summary": {
                            "ai_scan_summary": {
                                "basic_statistics": {
                                    "total_violations": 5,
                                    "policies_with_violations": 2,
                                    "total_policies_scanned": 10,
                                    "cloud_provider": "aws",
                                    "target_account_id": "123456789012"
                                },
                                "severity_breakdown": [
                                    {"severity": "High", "violation_count": 3},
                                    {"severity": "Medium", "violation_count": 2}
                                ],
                                "all_policy_results": [],
                                "insights": [],
                                "top_policy_violations": []
                            }
                        }
                    }
                }
            }]
        }
    }


@pytest.fixture
def sample_scan_response_v2():
    """v2スキャン検索レスポンスサンプル"""
    return {
        "hits": {
            "total": {"value": 1},
            "hits": [{
                "_source": {
                    "scan_id": "scan_v2_sample",
                    "account_id": "123456789012",
                    "cloud_provider": "aws",
                    "timestamp": "2025-06-15T10:00:00Z",
                    "scan_metadata": {"job_created_at": "2025-06-15T10:00:00Z"},
                    "scan_summary": {},
                    "policies": [
                        {
                            "policy_name": "policy-a-1",
                            "policy_title": "S3暗号化チェック",
                            "severity": "High",
                            "resource_type": "s3",
                            "recommendation_uuid": "a.1",
                            "execution_details": {"violation_count": 3}
                        }
                    ]
                }
            }]
        }
    }


@pytest.fixture
def sample_resource_json():
    """リソースJSONサンプル"""
    return {
        "resource_id": "sg-12345678",
        "custodian_resource": {
            "GroupName": "web-server-sg",
            "GroupId": "sg-12345678",
            "Description": "Web server security group",
            "VpcId": "vpc-abcdef01",
            "IpPermissions": [{
                "IpProtocol": "tcp",
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            }],
            "c7n:MatchedFilters": ["IpPermissions"]
        }
    }
```

---

## 6. テスト実行例

```bash
# chat_tools関連テストのみ実行
pytest test/unit/chat_dashboard/test_chat_tools.py -v

# 特定のテストクラスのみ実行
pytest test/unit/chat_dashboard/test_chat_tools.py::TestParseTimeReference -v
pytest test/unit/chat_dashboard/test_chat_tools.py::TestGetResourceDetails -v

# カバレッジ付きで実行
pytest test/unit/chat_dashboard/test_chat_tools.py --cov=app.chat_dashboard.chat_tools --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/chat_dashboard/test_chat_tools.py -m "security" -v

# asyncioテストの実行（pytest-asyncioが必要）
pytest test/unit/chat_dashboard/test_chat_tools.py -v --asyncio-mode=auto
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 53 | CTOOL-001 〜 CTOOL-053 |
| 異常系 | 22 | CTOOL-E01 〜 CTOOL-E22 |
| セキュリティ | 6 | CTOOL-SEC-01 〜 CTOOL-SEC-06 |
| **合計** | **81** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestParseTimeReference` | CTOOL-001〜CTOOL-019 | 19 |
| `TestBuildHistoricalScanQuery` | CTOOL-020〜CTOOL-023 | 4 |
| `TestFormatSeverityComparison` | CTOOL-024〜CTOOL-026 | 3 |
| `TestCalculateTrendAssessment` | CTOOL-027〜CTOOL-033 | 7 |
| `TestExtractResourceNameWithLlm` | CTOOL-034〜CTOOL-039 | 6 |
| `TestGetScanInfoV2` | CTOOL-040〜CTOOL-041 | 2 |
| `TestGetCurrentScanInfo` | CTOOL-042〜CTOOL-044 | 3 |
| `TestSearchHistoricalScan` | CTOOL-045〜CTOOL-046 | 2 |
| `TestGetResourceDetails` | CTOOL-047〜CTOOL-049 | 3 |
| `TestGetPolicyRecommendations` | CTOOL-050〜CTOOL-051 | 2 |
| `TestGetScanInfo` | CTOOL-052 | 1 |
| `TestCompareScanViolations` | CTOOL-053 | 1 |
| `TestGetCurrentScanInfoErrors` | CTOOL-E01〜CTOOL-E04 | 4 |
| `TestGetScanInfoV2Errors` | CTOOL-E05 | 1 |
| `TestSearchHistoricalScanErrors` | CTOOL-E06〜CTOOL-E07 | 2 |
| `TestExtractResourceNameWithLlmErrors` | CTOOL-E08〜CTOOL-E10 | 3 |
| `TestGetResourceDetailsErrors` | CTOOL-E11〜CTOOL-E14 | 4 |
| `TestGetPolicyRecommendationsErrors` | CTOOL-E15〜CTOOL-E17 | 3 |
| `TestGetScanInfoErrors` | CTOOL-E18〜CTOOL-E19, CTOOL-E22 | 3 |
| `TestCompareScanViolationsErrors` | CTOOL-E20〜CTOOL-E21 | 2 |
| `TestChatToolsSecurity` | CTOOL-SEC-01〜CTOOL-SEC-06 | 6 |

> **注記**: CTOOL-E22（日時フォーマット検証）は`TestGetScanInfoErrors`クラスに配置。E20-E21は`TestCompareScanViolationsErrors`クラスに所属。

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| CTOOL-SEC-01 | `chat_tools.py:411` で `opensearch_auth[:50]` をそのままログ出力しており、短いBasicトークンは全文漏洩する | 認証情報のログ出力を「認証あり」程度に留め、トークン値を除去する |
| CTOOL-SEC-02 | `chat_tools.py:791` でscan_idのバリデーションが行われていない（v1インデックス名構築時） | scan_idの入力検証（英数字・ハイフン・アンダースコアのみ許可）を追加 |
| CTOOL-SEC-03 | `chat_tools.py:840` でpolicy_nameの入力サニタイズが行われていない（wildcardクエリに「*」がそのまま渡される） | wildcardメタ文字（`*`, `?`）のエスケープ処理を追加 |

### 注意事項

- `pytest-asyncio` が必要（@tool関数は全てasync）
- `@pytest.mark.security` マーカーの登録要（pyproject.toml）
- OpenSearch接続・LLM呼び出しは必ずモック化すること
- `dateutil` のImportError分岐テストにはsys.modulesの操作が必要（本仕様では対象外）
- @tool関数のテストは `.ainvoke()` メソッド経由で呼び出すこと

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | LLMリソース名抽出の品質検証不可 | 抽出精度の確認困難 | ルールベース分岐のみ検証、LLMはモック化 |
| 2 | OpenSearch実際の検索動作確認不可 | クエリ構文の正確性未検証 | モック使用、統合テストで別途検証 |
| 3 | dateutil fallbackの月末処理 | calendar.monthrangeの精度 | 境界値テストで補完（本仕様では対象外） |
| 4 | v2インデックスの実データ構造 | v2固有のフィールド差異 | サンプルデータで検証 |
| 5 | @toolデコレータの副作用 | LangChainの内部状態 | `.ainvoke()` メソッドで間接呼び出し |
| 6 | dateutil ImportError分岐 | fallback relativedelta関数の完全テスト | sys.modules操作が必要、将来的に追加検討 |
| 7 | SEC-01のcapsys制限 | `capsys`はstdoutのみキャプチャし、`logging`モジュール出力は取得不可 | 実装がprint()でなくlogger使用の場合は`caplog`フィクスチャに変更が必要 |
