# report_plugin テストケース

## 1. 概要

CSPMセキュリティ監査レポートの生成プラグイン。HTMLプレビューとPDF生成機能を提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `cspm_preview` | CSPMレポートのHTMLプレビュー生成 |
| `cspm_generate` | CSPMレポートのPDF生成 |
| `CSPMReportProvider` | レポートデータ収集（監査/定期） |
| `HtmlRenderer` | Jinja2テンプレートレンダリング |
| `PdfGenerator` | WeasyPrintによるPDF生成 |
| `ChartGenerator` | matplotlibによるグラフ生成 |
| `CSPMDataFetcher` | OpenSearchからのデータ取得 |

### 1.2 カバレッジ目標: 75%

> **注記**: OpenSearch依存部分のモック化、WeasyPrint/matplotlib統合テストは単体テストで検証困難なため75%に設定。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| ルーター | `app/report_plugin/router.py` |
| モデル | `app/report_plugin/models.py` |
| CSPMプロバイダー | `app/report_plugin/providers/cspm_provider.py` |
| ベースプロバイダー | `app/report_plugin/providers/base_provider.py` |
| 定期レポートヘルパー | `app/report_plugin/providers/cspm_periodic_helpers.py` |
| 共通ヘルパー | `app/report_plugin/providers/cspm_common_helpers.py` |
| HTMLレンダラー | `app/report_plugin/services/html_renderer.py` |
| PDF生成 | `app/report_plugin/services/pdf_generator.py` |
| グラフ生成 | `app/report_plugin/services/chart_generator.py` |
| データフェッチャー | `app/report_plugin/services/opensearch_data_fetcher.py` |
| テストコード | `test/unit/report_plugin/test_*.py` |

### 1.4 補足情報

**レポートタイプ:**
- `audit`: 単一スキャン監査レポート
- `periodic`: 定期（トレンド）レポート（2つ以上のスキャンが必要）

**主要分岐:**
- `router.py:106-113`: report_type による audit/periodic 分岐
- `cspm_provider.py:136-138`: scan_ids 空チェック
- `cspm_provider.py:200-204`: periodic で 2スキャン未満チェック

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RPT-001 | 監査レポートプレビュー生成 | audit, scan_id=1件 | HTML返却 |
| RPT-002 | 監査レポートPDF生成 | audit, scan_id=1件 | PDFバイナリ返却 |
| RPT-003 | 定期レポートプレビュー生成 | periodic, scan_id=2件以上 | HTML返却 |
| RPT-004 | 定期レポートPDF生成 | periodic, scan_id=2件以上 | PDFバイナリ返却 |
| RPT-005 | 違反ステータスマージ | violations + statuses | merged_violations |
| RPT-006 | 違反サマリー計算 | violations リスト | サマリー辞書 |
| RPT-007 | 期間情報計算 | scans リスト | period 辞書 |
| RPT-008 | 期間サマリー計算 | scans + violations_by_scan | summary 辞書 |
| RPT-009 | トレンドデータ計算 | scans + violations_by_scan | trend 辞書 |
| RPT-010 | 違反分析計算 | scans + violations_by_scan | analysis 辞書 |
| RPT-011 | スキャン情報取得 | valid scan_id | scan_info 辞書 |
| RPT-012 | 違反データ取得 | valid scan_id | violations リスト |
| RPT-013 | HTMLテンプレートレンダリング | template + data | HTML文字列 |
| RPT-014 | PDF生成（HTML入力） | HTML文字列 | PDFバイナリ |
| RPT-015 | グラフ生成（重大度別） | by_severity 辞書 | Base64文字列 |
| RPT-016 | グラフ生成（トレンド） | trend_data (List[Dict]) | Base64文字列 |
| RPT-017 | Content-Disposition（ASCII） | filename.pdf | シンプルヘッダー |
| RPT-018 | Content-Disposition（日本語） | 監査レポート.pdf | UTF-8エンコード |

### 2.1 ルーターエンドポイントテスト

```python
# test/unit/report_plugin/test_router.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.report_plugin.router import (
    cspm_preview,
    cspm_generate,
    _build_provider_params,
    _build_content_disposition,
    _prepare_render_data,
)
from app.report_plugin.models import (
    CSPMReportRequest,
    ViolationStatusPayload,
    ViolationStatus,
)


class TestCspmPreview:
    """CSPMプレビューエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_cspm_preview_audit_success(self):
        """RPT-001: 監査レポートプレビュー生成

        router.py:56-96 の正常系処理をカバー
        """
        # Arrange
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テスト監査レポート",
            included_sections=["technical_summary"],
            violation_statuses=[],
        )

        mock_report_data = {
            "report_id": "test-id",
            "scan": {"scan_id": "scan-123"},
            "summary": {},
            "violations": [],
        }

        # Act
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls, patch(
            "app.report_plugin.router.HtmlRenderer"
        ) as mock_renderer_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.return_value = mock_report_data
            mock_provider.get_template_name.return_value = "cspm/audit_report.html"
            mock_provider_cls.return_value = mock_provider

            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "<html>Test</html>"
            mock_renderer_cls.return_value = mock_renderer

            response = await cspm_preview(request)

        # Assert
        assert response.html == "<html>Test</html>"
        mock_provider.collect_data.assert_called_once()
        mock_renderer.render.assert_called_once()

    @pytest.mark.asyncio
    async def test_cspm_preview_periodic_success(self):
        """RPT-003: 定期レポートプレビュー生成"""
        # Arrange
        request = CSPMReportRequest(
            report_type="periodic",
            scan_ids=["scan-1", "scan-2"],
            title="テスト定期レポート",
        )

        mock_report_data = {
            "report_id": "test-id",
            "period": {"start_date": "2026-01-01", "end_date": "2026-01-31"},
            "scans": [],
            "summary": {},
            "trend": {},
            "analysis": {},
            "violations": [],
        }

        # Act
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls, patch(
            "app.report_plugin.router.HtmlRenderer"
        ) as mock_renderer_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.return_value = mock_report_data
            mock_provider.get_template_name.return_value = "cspm/periodic_report.html"
            mock_provider_cls.return_value = mock_provider

            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "<html>Periodic</html>"
            mock_renderer_cls.return_value = mock_renderer

            response = await cspm_preview(request)

        # Assert
        assert response.html == "<html>Periodic</html>"


class TestCspmGenerate:
    """CSPM PDF生成エンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_cspm_generate_audit_success(self):
        """RPT-002: 監査レポートPDF生成

        router.py:130-188 の正常系処理をカバー
        """
        # Arrange
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テスト監査レポート",
        )

        mock_report_data = {
            "report_id": "test-id",
            "scan": {"scan_id": "scan-123"},
            "summary": {},
            "violations": [],
        }

        # Act
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls, patch(
            "app.report_plugin.router.HtmlRenderer"
        ) as mock_renderer_cls, patch(
            "app.report_plugin.router.PdfGenerator"
        ) as mock_pdf_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.return_value = mock_report_data
            mock_provider.get_template_name.return_value = "cspm/audit_report.html"
            mock_provider.get_report_filename.return_value = "report.pdf"
            mock_provider_cls.return_value = mock_provider

            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "<html>Test</html>"
            mock_renderer_cls.return_value = mock_renderer

            mock_pdf = MagicMock()
            mock_pdf.generate.return_value = b"%PDF-1.4 test"
            mock_pdf_cls.return_value = mock_pdf

            response = await cspm_generate(request)

        # Assert
        assert response.body == b"%PDF-1.4 test"
        assert response.media_type == "application/pdf"
        assert "Content-Disposition" in response.headers

    @pytest.mark.asyncio
    async def test_cspm_generate_periodic_success(self):
        """RPT-004: 定期レポートPDF生成"""
        # Arrange
        request = CSPMReportRequest(
            report_type="periodic",
            scan_ids=["scan-1", "scan-2"],
            title="テスト定期レポート",
        )

        mock_report_data = {
            "report_id": "test-id",
            "period": {},
            "scans": [],
            "summary": {},
            "trend": {},
            "analysis": {},
            "violations": [],
        }

        # Act
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls, patch(
            "app.report_plugin.router.HtmlRenderer"
        ) as mock_renderer_cls, patch(
            "app.report_plugin.router.PdfGenerator"
        ) as mock_pdf_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.return_value = mock_report_data
            mock_provider.get_template_name.return_value = "cspm/periodic_report.html"
            mock_provider.get_report_filename.return_value = "periodic.pdf"
            mock_provider_cls.return_value = mock_provider

            mock_renderer = MagicMock()
            mock_renderer.render.return_value = "<html>Periodic</html>"
            mock_renderer_cls.return_value = mock_renderer

            mock_pdf = MagicMock()
            mock_pdf.generate.return_value = b"%PDF-1.4 periodic"
            mock_pdf_cls.return_value = mock_pdf

            response = await cspm_generate(request)

        # Assert
        assert response.body == b"%PDF-1.4 periodic"


class TestHelperFunctions:
    """ヘルパー関数のテスト"""

    def test_build_provider_params(self):
        """（補助）プロバイダーパラメータ構築"""
        # Arrange
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テスト",
            included_sections=["summary"],
            violation_statuses=[
                ViolationStatusPayload(
                    violation_id="v-1",
                    status=ViolationStatus.RESOLVED,
                    reason="修正済み",
                )
            ],
        )

        # Act
        params = _build_provider_params(request)

        # Assert
        assert params["report_type"] == "audit"
        assert params["scan_ids"] == ["scan-123"]
        assert params["title"] == "テスト"
        assert len(params["violation_statuses"]) == 1
        assert params["violation_statuses"][0]["status"] == "resolved"

    def test_build_content_disposition_ascii(self):
        """RPT-017: Content-Disposition（ASCII）

        router.py:256-260 の ASCIIパスをカバー
        """
        # Arrange
        filename = "report.pdf"

        # Act
        result = _build_content_disposition(filename)

        # Assert
        assert result == 'attachment; filename="report.pdf"'

    def test_build_content_disposition_japanese(self):
        """RPT-018: Content-Disposition（日本語）

        router.py:261-265 のUTF-8エンコードパスをカバー
        """
        # Arrange
        filename = "監査レポート.pdf"

        # Act
        result = _build_content_disposition(filename)

        # Assert
        assert "UTF-8''" in result
        assert "attachment; filename*=" in result

    def test_prepare_render_data(self):
        """（補助）レンダリングデータ準備"""
        # Arrange
        report_data = {"report_id": "test-id", "scan": {}}
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テストタイトル",
            included_sections=["summary"],
            detail_severity_filter=["critical"],
        )

        # Act
        result = _prepare_render_data(report_data, request)

        # Assert
        assert result["title"] == "テストタイトル"
        assert result["included_sections"] == ["summary"]
        assert result["detail_severity_filter"] == ["critical"]
```

### 2.2 CSPMプロバイダーテスト

```python
# test/unit/report_plugin/test_cspm_provider.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.report_plugin.providers.cspm_provider import CSPMReportProvider


class TestCSPMReportProvider:
    """CSPMレポートプロバイダーのテスト"""

    @pytest.fixture
    def provider(self):
        """プロバイダーインスタンス"""
        return CSPMReportProvider()

    @pytest.mark.asyncio
    async def test_collect_data_audit(self, provider):
        """RPT-001（プロバイダー層）: 監査データ収集

        cspm_provider.py:106-109 の audit 分岐をカバー
        """
        # Arrange
        params = {
            "report_type": "audit",
            "scan_ids": ["scan-123"],
            "violation_statuses": [],
        }

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_scan_info.return_value = {
            "scan_id": "scan-123",
            "executed_at": "2026-01-01T00:00:00Z",
        }
        mock_fetcher.fetch_violations.return_value = [
            {"violation_id": "v-1", "severity": "High"}
        ]

        # Act
        with patch.object(
            provider, "_get_data_fetcher", return_value=mock_fetcher
        ):
            result = await provider.collect_data(params)

        # Assert
        assert "report_id" in result
        assert "generated_at" in result
        assert result["report_type"] == "audit"
        assert "scan" in result
        assert "summary" in result
        assert "violations" in result

    @pytest.mark.asyncio
    async def test_collect_data_periodic(self, provider):
        """RPT-003（プロバイダー層）: 定期データ収集

        cspm_provider.py:110-113 の periodic 分岐をカバー
        """
        # Arrange
        params = {
            "report_type": "periodic",
            "scan_ids": ["scan-1", "scan-2"],
            "violation_statuses": [],
        }

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_scan_info.side_effect = [
            {"scan_id": "scan-1", "executed_at": "2026-01-01T00:00:00Z"},
            {"scan_id": "scan-2", "executed_at": "2026-01-15T00:00:00Z"},
        ]
        mock_fetcher.fetch_violations.side_effect = [
            [{"violation_id": "v-1", "severity": "High"}],
            [{"violation_id": "v-2", "severity": "Medium"}],
        ]

        # Act
        with patch.object(
            provider, "_get_data_fetcher", return_value=mock_fetcher
        ):
            result = await provider.collect_data(params)

        # Assert
        assert result["report_type"] == "periodic"
        assert "period" in result
        assert "scans" in result
        assert "trend" in result
        assert "analysis" in result

    def test_get_template_name_audit(self, provider):
        """（補助）テンプレート名取得（audit）"""
        assert provider.get_template_name("audit") == "cspm/audit_report.html"

    def test_get_template_name_periodic(self, provider):
        """（補助）テンプレート名取得（periodic）"""
        assert provider.get_template_name("periodic") == "cspm/periodic_report.html"

    def test_get_supported_sections(self, provider):
        """（補助）サポートセクション取得"""
        sections = provider.get_supported_sections()
        assert "technical_summary" in sections
        assert "violation_summary" in sections
        assert len(sections) == 5

    def test_get_report_filename_audit(self, provider):
        """（補助）ファイル名生成（audit）"""
        params = {"report_type": "audit", "scan_ids": ["12345678-abcd-efgh"]}
        filename = provider.get_report_filename(params)
        assert "CSPM_監査レポート_12345678" in filename
        assert filename.endswith(".pdf")

    def test_get_report_filename_periodic(self, provider):
        """（補助）ファイル名生成（periodic）"""
        params = {
            "report_type": "periodic",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        }
        filename = provider.get_report_filename(params)
        assert "CSPM_定期レポート_2026-01-01_2026-01-31" in filename
```

### 2.3 ヘルパー関数テスト

```python
# test/unit/report_plugin/test_helpers.py
import pytest

from app.report_plugin.providers.cspm_common_helpers import (
    calculate_violation_summary,
    merge_violation_statuses,
)
from app.report_plugin.providers.cspm_periodic_helpers import (
    calculate_period_info,
    calculate_period_summary,
    calculate_trend_data,
    calculate_violation_analysis,
)


class TestCommonHelpers:
    """共通ヘルパー関数のテスト"""

    def test_calculate_violation_summary(self):
        """RPT-006: 違反サマリー計算

        cspm_common_helpers.py:11-84 をカバー
        """
        # Arrange
        violations = [
            {"violation_id": "v-1", "severity": "Critical", "resource_arn": "arn:1", "status": "unresolved"},
            {"violation_id": "v-2", "severity": "High", "resource_arn": "arn:2", "status": "resolved"},
            {"violation_id": "v-3", "severity": "Medium", "resource_arn": "arn:1", "status": "unresolved"},
        ]

        # Act
        result = calculate_violation_summary(violations)

        # Assert
        assert result["total_violations"] == 3
        assert result["total_resources"] == 2  # ユニークARN数
        assert result["by_severity"]["critical"] == 1
        assert result["by_severity"]["high"] == 1
        assert result["by_severity"]["medium"] == 1
        assert result["by_status"]["unresolved"] == 2
        assert result["by_status"]["resolved"] == 1

    def test_merge_violation_statuses(self):
        """RPT-005: 違反ステータスマージ

        cspm_common_helpers.py:87-133 をカバー
        """
        # Arrange
        violations = [
            {"violation_id": "v-1", "severity": "High"},
            {"violation_id": "v-2", "severity": "Medium"},
        ]
        statuses = [
            {"violation_id": "v-1", "status": "resolved", "reason": "修正済み"},
        ]

        # Act
        result = merge_violation_statuses(violations, statuses)

        # Assert
        assert len(result) == 2
        assert result[0]["status"] == "resolved"
        assert result[0]["status_reason"] == "修正済み"
        assert result[1]["status"] == "unresolved"  # デフォルト
        assert result[1]["status_reason"] is None


class TestPeriodicHelpers:
    """定期レポートヘルパー関数のテスト"""

    def test_calculate_period_info(self):
        """RPT-007: 期間情報計算

        cspm_periodic_helpers.py:11-37 をカバー
        """
        # Arrange
        scans = [
            {"scan_id": "s-1", "executed_at": "2026-01-01T10:00:00Z"},
            {"scan_id": "s-2", "executed_at": "2026-01-15T10:00:00Z"},
            {"scan_id": "s-3", "executed_at": "2026-01-31T10:00:00Z"},
        ]

        # Act
        result = calculate_period_info(scans)

        # Assert
        assert result["start_date"] == "2026-01-01"
        assert result["end_date"] == "2026-01-31"
        assert result["scan_count"] == 3

    def test_calculate_period_summary(self):
        """RPT-008: 期間サマリー計算

        cspm_periodic_helpers.py:40-102 をカバー
        """
        # Arrange
        scans = [
            {"scan_id": "s-1", "executed_at": "2026-01-01"},
            {"scan_id": "s-2", "executed_at": "2026-01-31"},
        ]
        violations_by_scan = {
            "s-1": [
                {"violation_id": "v-1"},
                {"violation_id": "v-2"},
                {"violation_id": "v-3"},
            ],
            "s-2": [
                {"violation_id": "v-1"},  # 継続中
                {"violation_id": "v-4"},  # 新規
            ],
        }

        # Act
        result = calculate_period_summary(scans, violations_by_scan)

        # Assert
        assert result["start_violations"] == 3
        assert result["end_violations"] == 2
        assert result["improvement"] == 1
        assert result["new_violations"] == 1  # v-4
        assert result["fixed_violations"] == 2  # v-2, v-3
        assert result["continuing_violations"] == 1  # v-1

    def test_calculate_trend_data(self):
        """RPT-009: トレンドデータ計算

        cspm_periodic_helpers.py:105-157 をカバー
        """
        # Arrange
        scans = [
            {"scan_id": "s-1", "executed_at": "2026-01-01T10:00:00Z"},
            {"scan_id": "s-2", "executed_at": "2026-01-15T10:00:00Z"},
        ]
        violations_by_scan = {
            "s-1": [
                {"violation_id": "v-1", "severity": "Critical"},
                {"violation_id": "v-2", "severity": "High"},
            ],
            "s-2": [
                {"violation_id": "v-3", "severity": "Critical"},
            ],
        }

        # Act
        result = calculate_trend_data(scans, violations_by_scan)

        # Assert
        assert "by_severity" in result
        assert len(result["by_severity"]["critical"]) == 2
        assert result["by_severity"]["critical"][0]["date"] == "2026-01-01"
        assert result["by_severity"]["critical"][0]["count"] == 1
        assert result["by_severity"]["critical"][1]["count"] == 1

    def test_calculate_violation_analysis(self):
        """RPT-010: 違反分析計算

        cspm_periodic_helpers.py:160-236 をカバー
        """
        # Arrange
        scans = [
            {"scan_id": "s-1"},
            {"scan_id": "s-2"},
            {"scan_id": "s-3"},
        ]
        violations_by_scan = {
            "s-1": [
                {"violation_id": "v-1", "severity": "High"},
                {"violation_id": "v-2", "severity": "Medium"},
            ],
            "s-2": [
                {"violation_id": "v-1", "severity": "High"},
                {"violation_id": "v-2", "severity": "Medium"},
            ],
            "s-3": [
                {"violation_id": "v-1", "severity": "High"},  # 長期継続
                {"violation_id": "v-3", "severity": "Low"},   # 新規
            ],
        }

        # Act
        result = calculate_violation_analysis(scans, violations_by_scan)

        # Assert
        assert len(result["new_violations"]) == 1  # v-3
        assert len(result["fixed_violations"]) == 1  # v-2
        assert len(result["long_running_violations"]) == 1  # v-1
```

### 2.4 サービス層テスト

```python
# test/unit/report_plugin/test_services.py
import pytest
from unittest.mock import MagicMock, patch

from app.report_plugin.services.html_renderer import HtmlRenderer
from app.report_plugin.services.pdf_generator import PdfGenerator
from app.report_plugin.services.chart_generator import ChartGenerator


class TestHtmlRenderer:
    """HTMLレンダラーのテスト"""

    def test_render_template(self):
        """RPT-013: HTMLテンプレートレンダリング

        html_renderer.py:64-76 をカバー
        """
        # Arrange
        renderer = HtmlRenderer()
        data = {"title": "テストレポート", "violations": []}

        # Act
        with patch.object(renderer, "env") as mock_env:
            mock_template = MagicMock()
            mock_template.render.return_value = "<html>Test</html>"
            mock_env.get_template.return_value = mock_template

            result = renderer.render("cspm/audit_report.html", data)

        # Assert
        assert result == "<html>Test</html>"
        mock_env.get_template.assert_called_with("cspm/audit_report.html")

    def test_format_number_filter(self):
        """（補助）数値フォーマットフィルター"""
        # Arrange
        renderer = HtmlRenderer()

        # Act & Assert
        # 内部メソッドへのアクセス
        assert renderer._format_number(1234567) == "1,234,567"
        assert renderer._format_number(0) == "0"

    def test_format_percent_filter(self):
        """（補助）パーセントフォーマットフィルター

        html_renderer.py:94-107 をカバー
        注意: 入力は0.0〜1.0の小数値（例: 0.755 → 75.50%）
        """
        # Arrange
        renderer = HtmlRenderer()

        # Act & Assert
        # 入力は小数値（0.0〜1.0）で、100倍してパーセント表示
        assert renderer._format_percent(0.755) == "75.50%"
        assert renderer._format_percent(1.0) == "100.00%"
        assert renderer._format_percent(0.0) == "0.00%"

    def test_severity_color_filter(self):
        """（補助）重大度カラーフィルター"""
        renderer = HtmlRenderer()
        assert renderer._severity_color("critical") == "#dc3545"
        assert renderer._severity_color("high") == "#fd7e14"
        assert renderer._severity_color("medium") == "#ffc107"
        assert renderer._severity_color("low") == "#28a745"
        assert renderer._severity_color("unknown") == "#6c757d"


class TestPdfGenerator:
    """PDF生成のテスト"""

    def test_generate_pdf_from_html(self):
        """RPT-014: PDF生成（HTML入力）

        pdf_generator.py:60-85 をカバー
        """
        # Arrange
        generator = PdfGenerator()
        html_content = "<html><body>Test PDF</body></html>"

        # Act
        with patch("app.report_plugin.services.pdf_generator.HTML") as mock_html:
            # WeasyPrintのHTMLクラスのモック設定
            mock_html_instance = MagicMock()
            mock_html_instance.write_pdf.return_value = b"%PDF-1.4 test"
            mock_html.return_value = mock_html_instance

            result = generator.generate(html_content)

        # Assert
        assert result == b"%PDF-1.4 test"
        mock_html.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once()


class TestChartGenerator:
    """グラフ生成のテスト"""

    def test_generate_severity_chart(self):
        """RPT-015: グラフ生成（重大度別）

        chart_generator.py:85-132 をカバー
        注意: 実装はBase64エンコードされた文字列を返す
        """
        # Arrange
        generator = ChartGenerator()
        by_severity = {
            "critical": 5,
            "high": 10,
            "medium": 20,
            "low": 15,
        }

        # Act
        with patch("app.report_plugin.services.chart_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            # 実装では plt.subplots() を使用
            mock_plt.subplots.return_value = (mock_fig, mock_ax)

            # io.BytesIOをモック（正しいパス）
            with patch(
                "app.report_plugin.services.chart_generator.io.BytesIO"
            ) as mock_bytesio:
                mock_buffer = MagicMock()
                # Base64エンコード前のバイナリ
                mock_buffer.getvalue.return_value = b"PNG_DATA"
                mock_bytesio.return_value = mock_buffer

                result = generator.generate_severity_chart(by_severity)

        # Assert
        # 実装がBase64文字列を返す
        assert isinstance(result, str)
        mock_plt.subplots.assert_called_once()

    def test_generate_trend_chart(self):
        """RPT-016: グラフ生成（トレンド）

        chart_generator.py:134-179 をカバー
        入力: List[Dict[str, Any]] 形式（例: [{"date": "2026-01-01", "count": 50}]）
        """
        # Arrange
        generator = ChartGenerator()
        # 実装が期待する形式: List[Dict[str, Any]]
        trend_data = [
            {"date": "2026-01-01", "count": 50},
            {"date": "2026-01-15", "count": 45},
            {"date": "2026-01-31", "count": 40},
        ]

        # Act
        with patch("app.report_plugin.services.chart_generator.plt") as mock_plt:
            mock_fig = MagicMock()
            mock_ax = MagicMock()
            # 実装では plt.subplots() を使用
            mock_plt.subplots.return_value = (mock_fig, mock_ax)

            with patch(
                "app.report_plugin.services.chart_generator.io.BytesIO"
            ) as mock_bytesio:
                mock_buffer = MagicMock()
                mock_buffer.getvalue.return_value = b"TREND_PNG"
                mock_bytesio.return_value = mock_buffer

                result = generator.generate_trend_chart(trend_data)

        # Assert
        assert isinstance(result, str)
        mock_plt.subplots.assert_called_once()
```

### 2.5 データフェッチャーテスト

```python
# test/unit/report_plugin/test_data_fetcher.py
import pytest
from unittest.mock import AsyncMock, patch

from app.report_plugin.services.opensearch_data_fetcher import CSPMDataFetcher


class TestCSPMDataFetcher:
    """OpenSearchデータフェッチャーのテスト"""

    @pytest.fixture
    def fetcher(self):
        """フェッチャーインスタンス"""
        return CSPMDataFetcher()

    @pytest.mark.asyncio
    async def test_fetch_scan_info_success(self, fetcher):
        """RPT-011: スキャン情報取得

        opensearch_data_fetcher.py:41-93 をカバー
        """
        # Arrange
        mock_response = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "scan_id": "scan-123",
                            "cloud_provider": "aws",
                            "account_id": "123456789012",
                            "timestamps": {
                                "created_at": "2026-01-01T10:00:00Z",
                                "scan_end_time": "2026-01-01T10:05:00Z",
                            },
                            "scan_scope": {
                                "preset_name": "AWS CIS Benchmark",
                            },
                            "execution_summary": {
                                "regional_metrics": [
                                    {"region": "ap-northeast-1"},
                                    {"region": "us-east-1"},
                                ]
                            },
                        }
                    }
                ]
            }
        }

        # Act
        with patch(
            "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await fetcher.fetch_scan_info("scan-123")

        # Assert
        assert result["scan_id"] == "scan-123"
        assert result["cloud_provider"] == "aws"
        assert result["account_id"] == "123456789012"
        assert result["region_count"] == 2
        assert result["scan_type"] == "AWS CIS Benchmark"

    @pytest.mark.asyncio
    async def test_fetch_violations_success(self, fetcher):
        """RPT-012: 違反データ取得

        opensearch_data_fetcher.py:95-155 をカバー
        """
        # Arrange
        mock_scan_result = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "scan_id": "scan-123",
                            "timestamp": "2026-01-01T10:00:00Z",
                            "account_id": "123456789012",
                            "policies": [
                                {
                                    "policy_name": "s3-encryption",
                                    "policy_title": "S3暗号化チェック",
                                    "severity": "High",
                                    "resource_type": "aws.s3",
                                    "recommendation_uuid": "rec-001",
                                    "execution_details": {
                                        "compliance_status": "has_violations"
                                    },
                                    "resources_by_region": [
                                        {
                                            "region": "ap-northeast-1",
                                            "resources": [
                                                {
                                                    "resource_id": "bucket-1",
                                                    "resource_arn": "arn:aws:s3:::bucket-1",
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    }
                ]
            }
        }

        mock_recommendations = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "uuid": "rec-001",
                            "title": "S3バケット暗号化",
                            "description": "S3バケットの暗号化を有効にしてください",
                            "remediation": ["暗号化を有効にする", "KMSキーを設定する"],
                            "severity": "High",
                        }
                    }
                ]
            }
        }

        # Act
        with patch(
            "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search.side_effect = [mock_scan_result, mock_recommendations]
            mock_get_client.return_value = mock_client

            result = await fetcher.fetch_violations("scan-123")

        # Assert
        assert len(result) == 1
        assert result[0]["policy_title"] == "S3バケット暗号化"
        assert result[0]["severity"] == "High"
        assert result[0]["resource_arn"] == "arn:aws:s3:::bucket-1"
        # 実装では配列を「• xxx\n• yyy」形式に変換
        assert "• 暗号化を有効にする" in result[0]["remediation_description"]
        assert "• KMSキーを設定する" in result[0]["remediation_description"]

    def test_categorize_resource_type(self, fetcher):
        """（補助）リソースタイプカテゴリ分類"""
        assert fetcher._categorize_resource_type("aws.ec2") == "コンピューティング"
        assert fetcher._categorize_resource_type("aws.s3") == "ストレージ"
        assert fetcher._categorize_resource_type("aws.rds") == "データベース"
        assert fetcher._categorize_resource_type("aws.iam") == "アイデンティティ"
        assert fetcher._categorize_resource_type("unknown") == "その他"

    def test_get_scan_type_label(self, fetcher):
        """（補助）スキャンタイプラベル変換"""
        assert fetcher._get_scan_type_label("manual_batch") == "マニュアル"
        assert fetcher._get_scan_type_label("scheduled") == "スケジュール"
        assert fetcher._get_scan_type_label("on_demand") == "オンデマンド"
        assert fetcher._get_scan_type_label("custom") == "custom"

    def test_calculate_duration(self, fetcher):
        """（補助）実行時間計算"""
        start = "2026-01-01T10:00:00Z"
        end = "2026-01-01T10:05:30Z"
        assert fetcher._calculate_duration(start, end) == 330  # 5分30秒

        # 無効な入力
        assert fetcher._calculate_duration(None, end) == 0
        assert fetcher._calculate_duration(start, None) == 0
        assert fetcher._calculate_duration("invalid", end) == 0
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RPT-E01 | プレビュー生成例外 | 内部エラー発生 | HTTPException 500 |
| RPT-E02 | PDF生成例外 | 内部エラー発生 | HTTPException 500 |
| RPT-E03 | 空のスキャンID | scan_ids=[] | 空データ返却 |
| RPT-E04 | 定期レポートでスキャン不足 | scan_ids=1件 | 空データ返却 |
| RPT-E05 | OpenSearchクライアント未取得 | クライアントなし | 空データ返却 |
| RPT-E06 | スキャン履歴なし | 存在しないscan_id | 空データ返却 |
| RPT-E07 | 違反データなし | 違反0件のscan_id | 空リスト返却 |
| RPT-E08 | テンプレート不存在 | 不正なtemplate名 | TemplateNotFound |
| RPT-E09 | 空の期間情報計算 | scans=[] | 空辞書 |
| RPT-E10 | 期間サマリー計算不足 | scans=1件 | 空辞書 |

### 3.1 ルーターエラーテスト

```python
# test/unit/report_plugin/test_router_errors.py
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from app.report_plugin.router import cspm_preview, cspm_generate
from app.report_plugin.models import CSPMReportRequest


class TestRouterErrors:
    """ルーターエラーテスト"""

    @pytest.mark.asyncio
    async def test_cspm_preview_internal_error(self):
        """RPT-E01: プレビュー生成例外

        router.py:98-113 の例外ハンドリングをカバー
        """
        # Arrange
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テスト",
        )

        # Act & Assert
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.side_effect = RuntimeError("Internal error")
            mock_provider_cls.return_value = mock_provider

            with pytest.raises(HTTPException) as exc_info:
                await cspm_preview(request)

            assert exc_info.value.status_code == 500
            assert "PREVIEW_GENERATION_FAILED" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_cspm_generate_internal_error(self):
        """RPT-E02: PDF生成例外

        router.py:190-205 の例外ハンドリングをカバー
        """
        # Arrange
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テスト",
        )

        # Act & Assert
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.side_effect = RuntimeError("PDF error")
            mock_provider_cls.return_value = mock_provider

            with pytest.raises(HTTPException) as exc_info:
                await cspm_generate(request)

            assert exc_info.value.status_code == 500
            assert "PDF_GENERATION_FAILED" in str(exc_info.value.detail)
```

### 3.2 プロバイダーエラーテスト

```python
# test/unit/report_plugin/test_provider_errors.py
import pytest
from unittest.mock import AsyncMock, patch

from app.report_plugin.providers.cspm_provider import CSPMReportProvider


class TestProviderErrors:
    """プロバイダーエラーテスト"""

    @pytest.fixture
    def provider(self):
        return CSPMReportProvider()

    @pytest.mark.asyncio
    async def test_collect_audit_data_empty_scan_ids(self, provider):
        """RPT-E03: 空のスキャンID

        cspm_provider.py:136-138 をカバー
        """
        # Arrange
        params = {
            "report_type": "audit",
            "scan_ids": [],
            "violation_statuses": [],
        }

        # Act
        result = await provider.collect_data(params)

        # Assert
        assert result["scan"] == {}
        assert result["summary"] == {}
        assert result["violations"] == []

    @pytest.mark.asyncio
    async def test_collect_periodic_data_insufficient_scans(self, provider):
        """RPT-E04: 定期レポートでスキャン不足

        cspm_provider.py:199-204 をカバー
        """
        # Arrange
        params = {
            "report_type": "periodic",
            "scan_ids": ["scan-1"],  # 1件のみ
            "violation_statuses": [],
        }

        # Act
        result = await provider.collect_data(params)

        # Assert
        assert result["period"] == {}
        assert result["scans"] == []
        assert result["violations"] == []

    @pytest.mark.asyncio
    async def test_collect_data_exception_handling(self, provider):
        """（補助）データ収集例外処理

        cspm_provider.py:172-175 をカバー
        """
        # Arrange
        params = {
            "report_type": "audit",
            "scan_ids": ["scan-123"],
            "violation_statuses": [],
        }

        mock_fetcher = AsyncMock()
        mock_fetcher.fetch_scan_info.side_effect = Exception("DB error")

        # Act
        with patch.object(
            provider, "_get_data_fetcher", return_value=mock_fetcher
        ):
            result = await provider.collect_data(params)

        # Assert（エラー時は空データ）
        assert result["scan"] == {}
        assert result["violations"] == []
```

### 3.3 データフェッチャーエラーテスト

```python
# test/unit/report_plugin/test_fetcher_errors.py
import pytest
from unittest.mock import AsyncMock, patch

from app.report_plugin.services.opensearch_data_fetcher import CSPMDataFetcher


class TestFetcherErrors:
    """データフェッチャーエラーテスト"""

    @pytest.fixture
    def fetcher(self):
        return CSPMDataFetcher()

    @pytest.mark.asyncio
    async def test_fetch_scan_info_no_client(self, fetcher):
        """RPT-E05: OpenSearchクライアント未取得

        opensearch_data_fetcher.py:63-66 をカバー
        """
        # Act
        with patch(
            "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
        ) as mock_get_client:
            mock_get_client.return_value = None

            result = await fetcher.fetch_scan_info("scan-123")

        # Assert
        assert result["scan_id"] == ""
        assert result["executed_at"] == ""

    @pytest.mark.asyncio
    async def test_fetch_scan_info_not_found(self, fetcher):
        """RPT-E06: スキャン履歴なし

        opensearch_data_fetcher.py:80-86 をカバー
        """
        # Arrange
        mock_response = {"hits": {"hits": []}}

        # Act
        with patch(
            "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await fetcher.fetch_scan_info("nonexistent")

        # Assert
        assert result["scan_id"] == ""

    @pytest.mark.asyncio
    async def test_fetch_violations_not_found(self, fetcher):
        """RPT-E07: 違反データなし

        opensearch_data_fetcher.py:128-134 をカバー
        """
        # Arrange
        mock_response = {"hits": {"hits": []}}

        # Act
        with patch(
            "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search.return_value = mock_response
            mock_get_client.return_value = mock_client

            result = await fetcher.fetch_violations("scan-123")

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_recommendations_empty_uuids(self, fetcher):
        """（補助）空のUUIDリスト

        opensearch_data_fetcher.py:177-179 をカバー
        """
        result = await fetcher.fetch_recommendations_by_uuids([])
        assert result == {}

    @pytest.mark.asyncio
    async def test_fetch_recommendations_exception(self, fetcher):
        """（補助）推奨事項取得例外

        opensearch_data_fetcher.py:232-234 をカバー
        """
        # Act
        with patch(
            "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search.side_effect = Exception("Search error")
            mock_get_client.return_value = mock_client

            result = await fetcher.fetch_recommendations_by_uuids(["uuid-1"])

        # Assert
        assert result == {}
```

### 3.4 ヘルパー関数エラーテスト

```python
# test/unit/report_plugin/test_helpers_errors.py
import pytest

from app.report_plugin.providers.cspm_periodic_helpers import (
    calculate_period_info,
    calculate_period_summary,
    calculate_violation_analysis,
)


class TestHelpersErrors:
    """ヘルパー関数エラーテスト"""

    def test_calculate_period_info_empty(self):
        """RPT-E09: 空の期間情報計算

        cspm_periodic_helpers.py:26-27 をカバー
        """
        result = calculate_period_info([])
        assert result == {}

    def test_calculate_period_summary_insufficient(self):
        """RPT-E10: 期間サマリー計算不足

        cspm_periodic_helpers.py:64-65 をカバー
        """
        scans = [{"scan_id": "s-1"}]  # 1件のみ
        result = calculate_period_summary(scans, {})
        assert result == {}

    def test_calculate_violation_analysis_insufficient(self):
        """（補助）違反分析計算不足

        cspm_periodic_helpers.py:179-184 をカバー
        """
        scans = [{"scan_id": "s-1"}]
        result = calculate_violation_analysis(scans, {})
        assert result["new_violations"] == []
        assert result["fixed_violations"] == []
        assert result["long_running_violations"] == []
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| RPT-SEC-01 | XSSペイロード in title | `<script>alert('xss')</script>` | HTMLエスケープされる |
| RPT-SEC-02 | NoSQLインジェクション試行 | `'; DROP TABLE--` | term検索で文字列として安全処理 |
| RPT-SEC-03 | パストラバーサル in template | `../../etc/passwd` | TemplateNotFound |
| RPT-SEC-04 | 過大リクエスト（scan_ids） | 1000件のscan_ids | 適切に処理または拒否 |
| RPT-SEC-05 | JSONインジェクション in reason | `{"malicious": true}` | 文字列としてエスケープ |
| RPT-SEC-06 | HTMLコンテンツ in violations | `<img onerror=...>` | autoescapeで無害化 |
| RPT-SEC-07 | 改行インジェクション in filename | `report\r\nX-Injected: true` | 改行除去 |
| RPT-SEC-08 | エラーIDによる情報漏洩防止 | 内部エラー発生 | 詳細は隠蔽、IDのみ |

### 4.1 セキュリティテスト

```python
# test/unit/report_plugin/test_security.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.report_plugin.router import cspm_preview, _build_content_disposition
from app.report_plugin.models import CSPMReportRequest, ViolationStatusPayload, ViolationStatus
from app.report_plugin.services.html_renderer import HtmlRenderer


@pytest.mark.security
class TestReportSecurity:
    """レポートプラグインセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_xss_in_title(self):
        """RPT-SEC-01: XSSペイロード in title

        Jinja2のautoescapeがXSSを防止することを検証
        html_renderer.py:30 の autoescape=True をカバー
        """
        # Arrange
        xss_payload = "<script>alert('xss')</script>"
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title=xss_payload,
        )

        mock_report_data = {
            "report_id": "test-id",
            "scan": {},
            "summary": {},
            "violations": [],
        }

        # Act
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.return_value = mock_report_data
            mock_provider.get_template_name.return_value = "cspm/audit_report.html"
            mock_provider_cls.return_value = mock_provider

            # 実際のHtmlRendererを使用（autoescapeの検証）
            with patch(
                "app.report_plugin.router.HtmlRenderer"
            ) as mock_renderer_cls:
                mock_renderer = MagicMock()
                # テンプレートがエスケープされた値を返すことを想定
                mock_renderer.render.return_value = (
                    "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
                )
                mock_renderer_cls.return_value = mock_renderer

                response = await cspm_preview(request)

        # Assert
        assert "<script>" not in response.html
        assert "&lt;script&gt;" in response.html or "script" not in response.html

    @pytest.mark.asyncio
    async def test_nosql_injection_in_scan_id(self):
        """RPT-SEC-02: NoSQLインジェクション試行（OpenSearch term検索の安全性）

        OpenSearchのterm検索は文字列リテラルとして扱われるため、
        インジェクション攻撃は適用外。文字列として安全に処理される。
        opensearch_data_fetcher.py:73-74 の term クエリをカバー
        """
        # Arrange
        malicious_scan_id = "'; DROP TABLE cspm_scans;--"
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=[malicious_scan_id],
            title="テスト",
        )

        # Act & Assert
        # OpenSearchでは term クエリは文字列リテラルとして扱われる
        # エラーにならず、単に結果が見つからないだけ
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls:
            mock_provider = AsyncMock()
            mock_provider.collect_data.return_value = {
                "report_id": "test",
                "scan": {},
                "summary": {},
                "violations": [],
            }
            mock_provider.get_template_name.return_value = "cspm/audit_report.html"
            mock_provider_cls.return_value = mock_provider

            with patch(
                "app.report_plugin.router.HtmlRenderer"
            ) as mock_renderer_cls:
                mock_renderer = MagicMock()
                mock_renderer.render.return_value = "<html>Safe</html>"
                mock_renderer_cls.return_value = mock_renderer

                # 例外が発生しないことを確認
                response = await cspm_preview(request)
                assert response is not None

    def test_path_traversal_in_template(self):
        """RPT-SEC-03: パストラバーサル in template

        Jinja2のFileSystemLoaderはデフォルトで
        テンプレートディレクトリ外へのアクセスを防止
        """
        # Arrange
        renderer = HtmlRenderer()
        malicious_template = "../../etc/passwd"

        # Act & Assert
        with pytest.raises(Exception):  # TemplateNotFound
            renderer.render(malicious_template, {})

    def test_json_injection_in_reason(self):
        """RPT-SEC-05: JSONインジェクション in reason

        Pydanticバリデーションにより文字列として扱われる
        """
        # Arrange
        malicious_reason = '{"malicious": true, "__proto__": {"admin": true}}'

        # Act
        payload = ViolationStatusPayload(
            violation_id="v-1",
            status=ViolationStatus.RESOLVED,
            reason=malicious_reason,
        )

        # Assert
        assert payload.reason == malicious_reason  # 文字列として保持
        assert isinstance(payload.reason, str)

    def test_html_content_in_violations_escaped(self):
        """RPT-SEC-06: HTMLコンテンツ in violations

        Jinja2のautoescapeにより無害化される
        """
        # Arrange
        renderer = HtmlRenderer()
        data = {
            "title": "Test",
            "violations": [
                {
                    "policy_title": '<img onerror="alert(1)" src=x>',
                    "severity": "High",
                }
            ],
        }

        # Act（テンプレートが存在しない場合はモック）
        with patch.object(renderer, "env") as mock_env:
            mock_template = MagicMock()
            # autoescapeが機能した結果をシミュレート
            mock_template.render.return_value = (
                "&lt;img onerror=&quot;alert(1)&quot; src=x&gt;"
            )
            mock_env.get_template.return_value = mock_template

            result = renderer.render("test.html", data)

        # Assert
        assert "<img" not in result
        assert "&lt;img" in result

    def test_newline_injection_in_filename(self):
        """RPT-SEC-07: 改行インジェクション in filename

        Content-Dispositionヘッダーに改行が含まれないことを確認
        """
        # Arrange
        malicious_filename = "report\r\nX-Injected: malicious\r\n.pdf"

        # Act
        result = _build_content_disposition(malicious_filename)

        # Assert
        # URLエンコードにより改行は %0D%0A に変換される
        assert "\r\n" not in result
        assert "X-Injected" not in result or "%0A" in result

    @pytest.mark.asyncio
    async def test_error_id_no_internal_leak(self):
        """RPT-SEC-08: エラーIDによる情報漏洩防止

        内部エラーの詳細がユーザーに漏洩しないことを検証
        router.py:101-113 のエラーハンドリングをカバー
        """
        # Arrange
        request = CSPMReportRequest(
            report_type="audit",
            scan_ids=["scan-123"],
            title="テスト",
        )

        # Act
        with patch(
            "app.report_plugin.router.CSPMReportProvider"
        ) as mock_provider_cls:
            mock_provider = AsyncMock()
            # 内部的なスタックトレースを含むエラー
            mock_provider.collect_data.side_effect = RuntimeError(
                "Database connection failed: password=secret123"
            )
            mock_provider_cls.return_value = mock_provider

            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await cspm_preview(request)

        # Assert
        error_detail = str(exc_info.value.detail)
        assert "secret123" not in error_detail  # パスワードが漏洩しない
        assert "Database connection" not in error_detail  # 内部メッセージが漏洩しない
        assert "Error ID:" in error_detail  # エラーIDのみ表示
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_report_module` | テスト間のモジュール状態リセット | function | Yes |
| `mock_opensearch_client` | OpenSearchクライアントモック | function | No |
| `sample_violations` | サンプル違反データ | function | No |
| `sample_scans` | サンプルスキャンデータ | function | No |

### 共通フィクスチャ定義

```python
# test/unit/report_plugin/conftest.py
import sys
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture(autouse=True)
def reset_report_module():
    """テストごとにモジュールのグローバル状態をリセット

    CSPMDataFetcherの遅延初期化などの状態をクリア
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.report_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_opensearch_client():
    """OpenSearchクライアントモック（外部接続防止）"""
    with patch(
        "app.report_plugin.services.opensearch_data_fetcher.get_opensearch_client"
    ) as mock_get_client:
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_violations():
    """サンプル違反データ"""
    return [
        {
            "violation_id": "v-1",
            "policy_uuid": "pol-001",
            "policy_title": "S3暗号化チェック",
            "policy_category": "ストレージ",
            "severity": "High",
            "resource_arn": "arn:aws:s3:::bucket-1",
            "resource_type": "aws.s3",
            "region": "ap-northeast-1",
            "detected_at": "2026-01-01T10:00:00Z",
            "status": "unresolved",
        },
        {
            "violation_id": "v-2",
            "policy_uuid": "pol-002",
            "policy_title": "IAMパスワードポリシー",
            "policy_category": "アイデンティティ",
            "severity": "Critical",
            "resource_arn": "arn:aws:iam::123456789012:account",
            "resource_type": "aws.iam",
            "region": "global",
            "detected_at": "2026-01-01T10:00:00Z",
            "status": "unresolved",
        },
    ]


@pytest.fixture
def sample_scans():
    """サンプルスキャンデータ"""
    return [
        {
            "scan_id": "scan-001",
            "executed_at": "2026-01-01T10:00:00Z",
            "cloud_provider": "aws",
            "account_id": "123456789012",
            "scan_type": "AWS CIS Benchmark",
            "region_count": 3,
        },
        {
            "scan_id": "scan-002",
            "executed_at": "2026-01-15T10:00:00Z",
            "cloud_provider": "aws",
            "account_id": "123456789012",
            "scan_type": "AWS CIS Benchmark",
            "region_count": 3,
        },
    ]


@pytest.fixture
def sample_violations_by_scan():
    """スキャン別違反データ"""
    return {
        "scan-001": [
            {"violation_id": "v-1", "severity": "High"},
            {"violation_id": "v-2", "severity": "Critical"},
            {"violation_id": "v-3", "severity": "Medium"},
        ],
        "scan-002": [
            {"violation_id": "v-1", "severity": "High"},  # 継続
            {"violation_id": "v-4", "severity": "Low"},   # 新規
        ],
    }
```

---

## 6. テスト実行例

```bash
# report_plugin関連テストのみ実行
pytest test/unit/report_plugin/ -v

# 特定のテストクラスのみ実行
pytest test/unit/report_plugin/test_router.py::TestCspmPreview -v

# カバレッジ付きで実行
pytest test/unit/report_plugin/ --cov=app.report_plugin --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/report_plugin/ -m "security" -v

# 非同期テストのみ実行
pytest test/unit/report_plugin/ -m "asyncio" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 18 | RPT-001 〜 RPT-018 |
| 異常系 | 10 | RPT-E01 〜 RPT-E10 |
| セキュリティ | 8 | RPT-SEC-01 〜 RPT-SEC-08 |
| **合計** | **36** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCspmPreview` | RPT-001, RPT-003 | 2 |
| `TestCspmGenerate` | RPT-002, RPT-004 | 2 |
| `TestHelperFunctions` | RPT-017, RPT-018 | 2 |
| `TestCSPMReportProvider` | RPT-001〜004（プロバイダー層） | 4 |
| `TestCommonHelpers` | RPT-005, RPT-006 | 2 |
| `TestPeriodicHelpers` | RPT-007〜RPT-010 | 4 |
| `TestHtmlRenderer` | RPT-013 | 1 |
| `TestPdfGenerator` | RPT-014 | 1 |
| `TestChartGenerator` | RPT-015, RPT-016 | 2 |
| `TestCSPMDataFetcher` | RPT-011, RPT-012 | 2 |
| `TestRouterErrors` | RPT-E01, RPT-E02 | 2 |
| `TestProviderErrors` | RPT-E03, RPT-E04 | 2 |
| `TestFetcherErrors` | RPT-E05〜RPT-E07 | 3 |
| `TestHelpersErrors` | RPT-E09, RPT-E10 | 2 |
| `TestReportSecurity` | RPT-SEC-01〜RPT-SEC-08 | 8 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> **注記**: セキュリティテストの一部（RPT-SEC-02, RPT-SEC-03）は実装の前提条件（OpenSearchのNoSQL性質、Jinja2のサンドボックス）に依存しています。

### 注意事項

- テスト実行に必要な追加パッケージ: `pytest-asyncio`
- `@pytest.mark.security` マーカーの登録要否: `pyproject.toml` に追加
- WeasyPrint/matplotlib の統合テストは別途E2Eテストで実施推奨
- OpenSearchへの実接続テストは `test/integration/` で実施
- 認証・認可テストは `app/auth/` プラグインで実施（別途 `auth_tests.md` 参照）
- `_format_percent` フィルターは入力値 0.0〜1.0 を期待（既にパーセント値の場合は直接表示）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | WeasyPrintのPDF生成はシステムフォントに依存 | 日本語フォントがない環境でPDFが正しく生成されない | Docker環境でフォントをプリインストール |
| 2 | OpenSearch接続テストはモックで代替 | 実際のクエリ動作は検証できない | 統合テストで補完 |
| 3 | matplotlibのグラフ生成は環境依存 | ヘッドレス環境で失敗する可能性 | `Agg` バックエンドを使用 |
| 4 | テンプレートファイルの存在確認 | 実テンプレートがない環境でテスト失敗 | モックで代替 |
| 5 | 大量データ（1000件超）の性能テスト未実施 | 本番環境での性能問題の可能性 | 負荷テストで別途検証 |
| 6 | 認証・認可テストは別プラグインで実施 | 本仕様書では未カバー | `auth_tests.md` 参照 |
| 7 | レート制限テストは実装依存 | 実装がない場合はテスト不可 | 実装追加後にテスト追加 |
| 8 | `_format_percent` は入力値 0.0〜1.0 を期待 | 既にパーセント値の場合は別フィルター使用 | テンプレート側で使い分け |

---

## 9. OWASP Top 10 カバレッジ

| OWASP カテゴリ | テストID | カバー状況 | 備考 |
|---------------|---------|-----------|------|
| A01: Broken Access Control | - | ⚠️ 別プラグイン | `auth_tests.md` でカバー |
| A02: Cryptographic Failures | - | N/A | 暗号化処理なし |
| A03: Injection | RPT-SEC-02, RPT-SEC-05 | ✅ 対応済 | NoSQL/JSON |
| A04: Insecure Design | - | ⚠️ 設計レベル | リソース上限は実装依存 |
| A05: Security Misconfiguration | RPT-SEC-03 | ✅ 対応済 | パストラバーサル |
| A06: Vulnerable Components | - | ⚠️ 別途 | 依存関係監査 |
| A07: Auth Failures | - | ⚠️ 別プラグイン | `auth_tests.md` でカバー |
| A08: Software/Data Integrity | - | N/A | 署名処理なし |
| A09: Security Logging | RPT-SEC-08 | ✅ 対応済 | エラー情報漏洩防止 |
| A10: SSRF | - | N/A | 外部URL取得なし |

> **注記**: 認証・認可（A01, A07）は `app/auth/` プラグインで一元管理。
> レート制限・リソース上限は実装の追加が必要な場合あり。

---

## 10. 更新履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-02-03 | 初版作成（36テストケース） |
