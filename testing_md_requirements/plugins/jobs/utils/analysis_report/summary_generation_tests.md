# jobs/utils サマリー生成 テストケース (#17f)

## 1. 概要

`app/jobs/utils/summary_generation.py` のテスト仕様書。スキャン完了後にOpenSearchインデックスのサマリーを生成する機能を検証する。

### 1.1 主要機能

| 関数 | ファイル | 説明 |
|------|---------|------|
| `generate_scan_summary()` | summary_generation.py | スキャンサマリーを非同期生成（scan_analysisに委譲） |

### 1.2 カバレッジ目標: 90%

> **注記**: 56行の小規模モジュールで関数は1つのみ。分岐カバレッジを重点的にテストする。`summarize_index_content` は動的インポート（L24）されるため、パッチ先は `app.jobs.utils.scan_analysis.summarize_index_content` を使用する。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/utils/summary_generation.py` (56行) |
| テストコード | `test/unit/jobs/utils/test_summary_generation.py` |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存先 | 用途 | モック要否 |
|--------|------|-----------|
| `TaskLogger` | ログ出力 | 要（モック） |
| `summarize_index_content` | インデックスサマリー取得 | 要（モック、動的インポート L24） |
| `json.loads` | JSON解析 | 不要（標準ライブラリ、実値テスト） |

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `generate_scan_summary` | 6 | L35 正常JSON判定, L38 else（サブ分岐: L40 OpenSearch接続エラー / L43 一般エラー）, L47 ImportError, L51 JSONDecodeError, L55 汎用Exception |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SG-001 | 正常なサマリー生成 | 有効なJSON文字列 | 解析された辞書を返す |
| SG-002 | エラー文字列が返された場合 | "Error: ..." | None + エラーログ |
| SG-003 | Noneが返された場合 | None | None + デフォルトエラーメッセージ |
| SG-004 | OpenSearch接続エラー | "OpenSearch client is not available" 含む文字列 | None + 専用エラーログ |
| SG-005 | 正しい引数でsummarize_index_contentを呼び出す | job_id="test-job" | index_name="cspm-scan-result-v2", job_id="test-job" |

### 2.1 generate_scan_summary テスト

```python
# test/unit/jobs/utils/test_summary_generation.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGenerateScanSummary:
    """generate_scan_summary のテスト"""

    @pytest.mark.asyncio
    async def test_successful_summary_generation(self):
        """SG-001: 有効なJSON文字列 → 解析された辞書を返す

        summary_generation.py:L35-37 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        valid_json = '{"total_violations": 5, "severity": {"high": 2, "medium": 3}}'

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=valid_json):

            result = await generate_scan_summary(job_id="job-001")

        # Assert
        assert result is not None
        assert result["total_violations"] == 5
        assert result["severity"]["high"] == 2

    @pytest.mark.asyncio
    async def test_error_string_returned(self):
        """SG-002: "Error:" で始まる文字列 → None + エラーログ

        summary_generation.py:L38-44 の else 分岐（一般エラー）をカバー。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        error_response = "Error: Index not found"

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=error_response):

            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-002")

        # Assert
        assert result is None
        mock_logger_instance.error.assert_called_once()
        error_msg = mock_logger_instance.error.call_args[0][0]
        assert "サマリー生成失敗" in error_msg
        assert "Error: Index not found" in error_msg

    @pytest.mark.asyncio
    async def test_none_returned(self):
        """SG-003: summarize_index_contentがNoneを返す → デフォルトエラーメッセージ

        summary_generation.py:L39 の三項演算子で
        summary_json_str が None の場合のデフォルト値をカバー。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=None):

            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-003")

        # Assert
        assert result is None
        error_msg = mock_logger_instance.error.call_args[0][0]
        assert "サマリー生成で不明なエラー" in error_msg

    @pytest.mark.asyncio
    async def test_opensearch_client_unavailable(self):
        """SG-004: OpenSearchクライアント接続エラー → 専用エラーログ

        summary_generation.py:L40-42 の
        "OpenSearch client is not available" 分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        opensearch_error = "Error: OpenSearch client is not available - connection refused"

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=opensearch_error):

            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-004")

        # Assert
        assert result is None
        # OpenSearch専用エラーログが出力されること
        error_calls = [call[0][0] for call in mock_logger_instance.error.call_args_list]
        assert any("OpenSearchクライアント接続エラー" in msg for msg in error_calls)
        # IAM認証情報の確認メッセージも出力されること
        info_calls = [call[0][0] for call in mock_logger_instance.info.call_args_list]
        assert any("IAM認証情報" in msg for msg in info_calls)

    @pytest.mark.asyncio
    async def test_correct_args_passed(self):
        """SG-005: summarize_index_contentに正しい引数が渡される

        summary_generation.py:L29 の固定インデックス名と
        L33 の job_id 引数をカバー。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        valid_json = '{"result": "ok"}'

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=valid_json) as mock_summarize:

            await generate_scan_summary(job_id="test-job-id")

        # Assert
        mock_summarize.assert_called_once_with(
            "cspm-scan-result-v2", job_id="test-job-id"
        )
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SG-E01 | ImportError → None | scan_analysisインポート失敗 | None + エラーログ |
| SG-E02 | JSONDecodeError → None | 不正なJSON文字列 | None + エラーログ |
| SG-E03 | 汎用Exception → None | 予期しない例外 | None + エラーログ |

### 3.1 サマリー生成 異常系

```python
class TestGenerateScanSummaryErrors:
    """generate_scan_summary エラーテスト"""

    @pytest.mark.asyncio
    async def test_import_error(self):
        """SG-E01: scan_analysisのインポート失敗 → None

        summary_generation.py:L47-48 の except ImportError をカバー。
        動的インポート（L24）が失敗するケース。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch.dict("sys.modules", {"app.jobs.utils.scan_analysis": None}):

            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-e01")

        # Assert
        assert result is None
        error_msg = mock_logger_instance.error.call_args[0][0]
        assert "インポート失敗" in error_msg

    @pytest.mark.asyncio
    async def test_json_decode_error(self):
        """SG-E02: 不正なJSON文字列 → JSONDecodeError → None

        summary_generation.py:L51-52 の except JSONDecodeError をカバー。
        summarize_index_contentが有効な文字列を返すが、JSONとして不正な場合。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        invalid_json = "not a json string {broken"

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=invalid_json):

            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-e02")

        # Assert
        assert result is None
        error_msg = mock_logger_instance.error.call_args[0][0]
        assert "サマリーJSON" in error_msg

    @pytest.mark.asyncio
    async def test_unexpected_exception(self):
        """SG-E03: 予期しない例外 → None

        summary_generation.py:L55-56 の except Exception をカバー。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("unexpected error")):

            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-e03")

        # Assert
        assert result is None
        error_msg = mock_logger_instance.error.call_args[0][0]
        assert "予期しないエラー" in error_msg
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SG-SEC-01 | 例外メッセージにAPIキー非露出 | APIキーを含む例外 | ログにAPIキーが含まれないことを確認 |
| SG-SEC-02 | ログインジェクション耐性 | CRLFを含むjob_id | クラッシュせず処理完了 |
| SG-SEC-03 | 大量JSONレスポンスの安定性 | 巨大JSON文字列 | 正常に解析して返す |

```python
@pytest.mark.security
class TestSummaryGenerationSecurity:
    """summary_generation セキュリティテスト"""

    @pytest.mark.asyncio
    @pytest.mark.xfail(
        reason="SG-SEC-01: summary_generation.py:L56 で str(e) をそのまま"
               "ログ出力するため、例外メッセージにAPIキーが含まれる場合に露出する。",
        strict=True,
        raises=AssertionError,
    )
    async def test_api_key_not_in_error_log(self):
        """SG-SEC-01: 例外メッセージのAPIキーがログに露出しない

        summary_generation.py:L56 の logger.error(f"...{str(e)}")
        に機密情報が含まれないことを確認する。

        [EXPECTED_TO_FAIL] str(e) をそのままログ出力するため、
        現行実装ではこのテストは失敗する。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        fake_key = "FAKE-API-KEY-FOR-TESTING-12345"
        secret_exception = RuntimeError(
            f"Connection failed: auth_key={fake_key}"
        )

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, side_effect=secret_exception):

            # TaskLogger() の呼び出し（L20）で返されるインスタンスを取得
            mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = mock_logger_instance

            result = await generate_scan_summary(job_id="job-sec01")

        # Assert
        assert result is None
        error_log_call = mock_logger_instance.error.call_args[0][0]
        # 理想: APIキーがログに含まれないこと（現行実装では失敗する）
        assert fake_key not in error_log_call

    @pytest.mark.asyncio
    async def test_log_injection_resilience(self):
        """SG-SEC-02: CRLFを含むjob_idでクラッシュしない

        summary_generation.py:L20 の TaskLogger(job_id, ...) および
        L30 の logger.info(f"...{index_name}") に改行文字を含む
        入力が渡された場合でも処理を完了することを確認する。

        本テストは例外が送出されず正常完了することを暗黙的に検証する。
        ログサニタイズ自体はこのモジュールの責務外。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary

        valid_json = '{"result": "ok"}'

        # Act - 例外が発生しないこと（暗黙的検証）+ 正常結果が返ること
        with patch("app.jobs.utils.summary_generation.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=valid_json):

            result = await generate_scan_summary(
                job_id="job-001\r\nERROR: injected_log_entry"
            )

        # Assert
        assert result is not None

    @pytest.mark.asyncio
    async def test_large_json_response_stability(self):
        """SG-SEC-03: 巨大JSONレスポンス（1MB超）の処理安定性

        json.loads() が大量データでもメモリ枯渇なく処理できることを確認。
        """
        # Arrange
        from app.jobs.utils.summary_generation import generate_scan_summary
        import json

        # 約1.2MBのJSON文字列を生成（要素数×detail長で1MB超を保証）
        large_data = {"violations": [{"id": f"v-{i}", "detail": "x" * 200} for i in range(5000)]}
        large_json = json.dumps(large_data)

        # Act
        with patch("app.jobs.utils.summary_generation.TaskLogger"), \
             patch("app.jobs.utils.scan_analysis.summarize_index_content",
                   new_callable=AsyncMock, return_value=large_json):

            result = await generate_scan_summary(job_id="job-sec03")

        # Assert
        assert result is not None
        assert len(result["violations"]) == 5000
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

> **注記**: conftest.py は `test/unit/jobs/utils/conftest.py`（#17a で定義予定）を共有する。実装時には既存の `_TARGET_MODULES` タプルに `"app.jobs.utils.summary_generation"` を追加する形で統合する。

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

# 本テストファイルで使用するモジュールのみを対象とする
_TARGET_MODULES = (
    "app.jobs.utils.summary_generation",
)


@pytest.fixture(autouse=True)
def reset_utils_module():
    """テストごとにモジュールのグローバル状態をリセット

    summary_generation のモジュールキャッシュをクリアし、
    テスト間の独立性を保証する。
    """
    yield
    # テスト後にクリーンアップ（対象モジュールのみ）
    modules_to_remove = [
        key for key in sys.modules
        if key in _TARGET_MODULES
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# サマリー生成テストのみ実行
pytest test/unit/jobs/utils/test_summary_generation.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_summary_generation.py::TestGenerateScanSummary -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_summary_generation.py \
  --cov=app.jobs.utils.summary_generation \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_summary_generation.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 5 | SG-001 〜 SG-005 |
| 異常系 | 3 | SG-E01 〜 SG-E03 |
| セキュリティ | 3 | SG-SEC-01 〜 SG-SEC-03 |
| **合計** | **11** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGenerateScanSummary` | SG-001〜SG-005 | 5 |
| `TestGenerateScanSummaryErrors` | SG-E01〜SG-E03 | 3 |
| `TestSummaryGenerationSecurity` | SG-SEC-01〜SG-SEC-03 | 3 |

### 7.1 予想失敗テスト

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| SG-SEC-01 | summary_generation.py:L48/L52/L56 で `str(e)` / `str(ie)` / `str(je)` をそのままログ出力するため、例外メッセージにAPIキーが含まれる場合に露出する | `str(e)` から機密情報をマスクするユーティリティを導入。`@pytest.mark.xfail(strict=True)` で管理 |

### 注意事項

- `pytest-asyncio` パッケージが必要（`generate_scan_summary` はasync関数）
- `@pytest.mark.asyncio` マーカーの使用が必要
- `summarize_index_content` は動的インポート（L24）されるが、`from .scan_analysis import summarize_index_content` の形式のため、パッチ先は `app.jobs.utils.scan_analysis.summarize_index_content` を使用する
- SG-E01 の `ImportError` テストでは `patch.dict("sys.modules", ...)` を使用して動的インポート失敗をシミュレートする

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `summarize_index_content` の内部動作はテスト対象外 | サマリー生成のロジック自体は `scan_analysis.py` の責務 | `scan_analysis_tests.md` でカバー |
| 2 | インデックス名 `cspm-scan-result-v2` がハードコード（L29） | インデックス名変更時にテスト修正が必要 | SG-005 で固定値を検証。将来的には設定値化を推奨 |
| 3 | L48/L52/L56 で例外文字列をそのままログ出力（`str(ie)`/`str(je)`/`str(e)`） | 例外メッセージにAPIキー等が含まれる場合に露出リスク | SG-SEC-01 で現行動作を記録（`xfail`）。将来的にマスク処理の導入を推奨 |
| 4 | `job_id` 等の外部入力にCRLFが含まれる可能性 | ログインジェクションのリスク | SG-SEC-02 で動作確認済み。実装側でのサニタイズはこのモジュールの責務外 |
