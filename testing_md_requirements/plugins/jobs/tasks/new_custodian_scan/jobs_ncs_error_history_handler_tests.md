# jobs/tasks/new_custodian_scan/error_history_handler テストケース

## 1. 概要

`error_history_handler.py` は Custodian スキャンのエラー情報を `cspm-scan-history-v2` インデックスに保存するモジュールです。モジュールレベル関数 `_get_custodian_version` と `ErrorHistoryHandler` クラスで構成され、エラー発生時の履歴データ構築・OpenSearch 保存を担当します。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `_get_custodian_version` | Cloud Custodian (c7n) のバージョン取得（pkg_resources → importlib.metadata → "unknown"） |
| `__init__` | job_id と logger を設定 |
| `_create_error_execution_summary` | エラー時の実行サマリー辞書を生成 |
| `_create_error_insights_summary` | エラー時のインサイトサマリー辞書を生成 |
| `_build_error_history_data` | cspm-scan-history-v2 マッピング適合のエラーデータを構築 |
| `save_error_to_history` | エラー情報を OpenSearch に非同期保存（唯一の async メソッド） |

### 1.2 カバレッジ目標: 90%

> **注記**: `save_error_to_history` は非同期で OpenSearch に接続するため pytest-asyncio が必要。外部接続は全てモックする。`datetime.now` のモックが必要な箇所がある。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/error_history_handler.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_error_history_handler.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
error_history_handler.py ──→ TaskLogger（ログ出力）
                         ──→ get_opensearch_client（非同期 OpenSearch クライアント取得）
                         ──→ pkg_resources / importlib.metadata（バージョン取得）
                         ──→ ProcessingError / ValidationError（エラー種別判定）
                         ──→ datetime.now（タイムスタンプ生成）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| バージョン取得テスト | `patch` で pkg_resources / importlib.metadata をモック |
| データ構築テスト | インスタンス直接呼び出し（純粋ロジック） |
| 非同期保存テスト | `patch` で get_opensearch_client をモック、`@pytest.mark.asyncio` |
| エラー種別判定テスト | ProcessingError / ValidationError の実インスタンスを使用 |

#### 非同期メソッド

`save_error_to_history` のみ非同期。pytest-asyncio が必要。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCEHH-001 | pkg_resources でバージョン取得成功 | c7n インストール済み環境 | バージョン文字列 |
| NCEHH-002 | pkg_resources 失敗→importlib で取得成功 | pkg_resources 例外 | バージョン文字列 |
| NCEHH-003 | 両方失敗で "unknown" を返す | 両方例外 | `"unknown"` |
| NCEHH-004 | 初期化で job_id と logger が設定される | `job_id="test-job"` | 属性設定 |
| NCEHH-005 | _create_error_execution_summary の構造 | error, stage, provider | 正しいキー・値 |
| NCEHH-006 | _create_error_insights_summary の構造 | error, stage | compliance_summary 等 |
| NCEHH-007 | _create_error_insights_summary の recommendations | error, stage | error_stage を含むメッセージ |
| NCEHH-008 | _build_error_history_data: scan_metadata あり | metadata 辞書 | initiated_by_user 等抽出 |
| NCEHH-009 | _build_error_history_data: scan_metadata なし | None | "undefined" にフォールバック |
| NCEHH-010 | _build_error_history_data: 必須トップレベルキー | error, stage, provider | 全キー存在、status=="failed" |
| NCEHH-011 | save_error_to_history: ProcessingError 判定 | ProcessingError | error_stage==processing_stage |
| NCEHH-012 | save_error_to_history: ValidationError 判定 | ValidationError | error_stage=="validation" |
| NCEHH-013 | save_error_to_history: 未知のエラー型 | RuntimeError | error_stage=="unknown" |
| NCEHH-014 | save_error_to_history: クライアント存在→index 呼出 | モックclient | client.index 呼び出し確認 |
| NCEHH-015 | save_error_to_history: クライアント None→warning | None | logger.warning 呼び出し |
| NCEHH-016 | save_error_to_history: 成功時 info ログ | モックclient | error_type を含む info ログ |
| NCEHH-017 | save_error_to_history: ProcessingError hasattr False | processing_stage 属性削除 | error_stage=="processing_error" |

### 2.1 _get_custodian_version テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_error_history_handler.py
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestGetCustodianVersion:
    """_get_custodian_version のフォールバック分岐テスト

    _get_custodian_version は関数内 import で pkg_resources / importlib.metadata を使用。
    テスト環境に setuptools (pkg_resources) が存在しない場合にも対応するため、
    patch.dict(sys.modules, ...) でモジュールを仮置きする。
    """

    def test_pkg_resources_success(self):
        """NCEHH-001: pkg_resources でバージョン取得成功

        error_history_handler.py:17-19 の try ブロック正常パスをカバー。
        setuptools 非依存: pkg_resources モジュールを sys.modules に仮置きする。
        """
        # Arrange
        mock_pkg = MagicMock()
        mock_dist = MagicMock()
        mock_dist.version = "0.9.35"
        mock_pkg.get_distribution.return_value = mock_dist

        with patch.dict(sys.modules, {"pkg_resources": mock_pkg}):
            # Act
            from app.jobs.tasks.new_custodian_scan.error_history_handler import _get_custodian_version
            result = _get_custodian_version()

        # Assert
        assert result == "0.9.35"

    def test_pkg_resources_fails_importlib_success(self):
        """NCEHH-002: pkg_resources 失敗→importlib.metadata で取得成功

        error_history_handler.py:20-23 の 内側 try ブロックをカバー。
        """
        # Arrange
        mock_pkg = MagicMock()
        mock_pkg.get_distribution.side_effect = Exception("not found")

        with patch.dict(sys.modules, {"pkg_resources": mock_pkg}):
            with patch("importlib.metadata.version", return_value="0.9.36"):
                # Act
                from app.jobs.tasks.new_custodian_scan.error_history_handler import _get_custodian_version
                result = _get_custodian_version()

        # Assert
        assert result == "0.9.36"

    def test_both_fail_returns_unknown(self):
        """NCEHH-003: 両方失敗で "unknown" を返す

        error_history_handler.py:24-25 の 内側 except ブロックをカバー。
        """
        # Arrange
        mock_pkg = MagicMock()
        mock_pkg.get_distribution.side_effect = Exception("not found")

        with patch.dict(sys.modules, {"pkg_resources": mock_pkg}):
            with patch("importlib.metadata.version", side_effect=Exception("not found")):
                # Act
                from app.jobs.tasks.new_custodian_scan.error_history_handler import _get_custodian_version
                result = _get_custodian_version()

        # Assert
        assert result == "unknown"
```

### 2.2 ErrorHistoryHandler 初期化テスト

```python
class TestErrorHistoryHandlerInit:
    """ErrorHistoryHandler.__init__ のテスト"""

    def test_init_sets_job_id_and_logger(self):
        """NCEHH-004: 初期化で job_id と logger が設定される

        error_history_handler.py:31-33 の __init__ をカバー。
        """
        # Arrange
        mock_logger = MagicMock()

        # Act
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        handler = ErrorHistoryHandler("test-job-123", mock_logger)

        # Assert
        assert handler.job_id == "test-job-123"
        assert handler.logger is mock_logger
```

### 2.3 _create_error_execution_summary テスト

```python
class TestCreateErrorExecutionSummary:
    """_create_error_execution_summary のテスト"""

    @pytest.fixture
    def handler(self):
        mock_logger = MagicMock()
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        return ErrorHistoryHandler("test-job", mock_logger)

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    def test_returns_correct_structure(self, mock_version, handler):
        """NCEHH-005: _create_error_execution_summary の構造が正しい

        error_history_handler.py:35-58 の全キーをカバー。
        """
        # Arrange
        error = RuntimeError("テストエラー")

        # Act
        result = handler._create_error_execution_summary(error, "validation", "aws")

        # Assert
        assert result["total_duration_seconds"] == 0.0
        assert result["custodian_version"] == "0.9.35"
        assert result["has_errors"] is True
        assert result["error_occurred"] is True
        assert result["error_stage"] == "validation"
        assert result["error_message"] == "テストエラー"
        assert result["performance_metrics"]["total_api_calls"] == 0
        assert result["cloud_provider_info"]["provider"] == "aws"
        assert result["cloud_provider_info"]["regions_scanned"] == []
```

### 2.4 _create_error_insights_summary テスト

```python
class TestCreateErrorInsightsSummary:
    """_create_error_insights_summary のテスト"""

    @pytest.fixture
    def handler(self):
        mock_logger = MagicMock()
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        return ErrorHistoryHandler("test-job", mock_logger)

    def test_returns_correct_structure(self, handler):
        """NCEHH-006: _create_error_insights_summary の構造が正しい

        error_history_handler.py:60-84 の全キーをカバー。
        """
        # Arrange
        error = RuntimeError("テストエラー")

        # Act
        result = handler._create_error_insights_summary(error, "execution")

        # Assert
        assert result["top_violations"] == []
        assert result["compliance_summary"]["total_resources"] == 0
        assert result["compliance_summary"]["compliance_rate"] == 0.0
        assert result["severity_distribution"] == {}
        assert result["resource_type_summary"] == []
        assert len(result["top_failed_policies"]) == 1
        assert result["top_failed_policies"][0]["error_message"] == "テストエラー"
        assert result["top_failed_policies"][0]["error_stage"] == "execution"

    def test_recommendations_contain_error_stage(self, handler):
        """NCEHH-007: recommendations に error_stage を含むメッセージが格納される

        error_history_handler.py:81-83 の recommendations 生成をカバー。
        """
        # Arrange
        error = RuntimeError("テスト")

        # Act
        result = handler._create_error_insights_summary(error, "credential_validation")

        # Assert
        assert len(result["recommendations"]) == 1
        expected_msg = "credential_validation段階でエラーが発生しました。ログを確認してください。"
        assert result["recommendations"][0] == expected_msg
```

### 2.5 _build_error_history_data テスト

```python
class TestBuildErrorHistoryData:
    """_build_error_history_data のテスト"""

    @pytest.fixture
    def handler(self):
        mock_logger = MagicMock()
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        return ErrorHistoryHandler("test-job-456", mock_logger)

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler.datetime")
    def test_with_scan_metadata(self, mock_dt, mock_version, handler):
        """NCEHH-008: scan_metadata ありで initiated_by_user 等を抽出

        error_history_handler.py:123-124 の scan_metadata.get() をカバー。
        datetime パッチ: 実装は `from datetime import datetime, timezone` で import し
        `datetime.now(timezone.utc)` を呼ぶ。モジュールレベルの datetime クラスを
        置き換えるため、MagicMock が任意の引数を受け取り return_value を返す。
        """
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
        error = RuntimeError("スキャンエラー")
        metadata = {
            "initiated_by_user": "admin",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        result = handler._build_error_history_data(error, "execution", "aws", metadata)

        # Assert
        assert result["scan_scope"]["initiated_by_user"] == "admin"
        assert result["scan_scope"]["scan_type"] == "manual_batch"

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler.datetime")
    def test_without_scan_metadata_defaults_to_undefined(self, mock_dt, mock_version, handler):
        """NCEHH-009: scan_metadata なしで "undefined" にフォールバック

        error_history_handler.py:123-124 の `if scan_metadata else "undefined"` をカバー。
        """
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
        error = RuntimeError("エラー")

        # Act
        result = handler._build_error_history_data(error, "unknown", "aws", None)

        # Assert
        assert result["scan_scope"]["initiated_by_user"] == "undefined"
        assert result["scan_scope"]["scan_type"] == "undefined"

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler.datetime")
    def test_required_top_level_keys_and_status(self, mock_dt, mock_version, handler):
        """NCEHH-010: 必須トップレベルキーと status=="failed"

        error_history_handler.py:96-174 の返却辞書全体構造をカバー。
        """
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
        error = ValueError("テスト")

        # Act
        result = handler._build_error_history_data(error, "validation", "azure")

        # Assert
        required_keys = [
            "job_id", "scan_id", "status", "cloud_provider",
            "timestamps", "scan_scope", "execution_summary",
            "policy_executions", "insights_summary", "error_summary",
            "resource_overview", "system_metadata"
        ]
        for key in required_keys:
            assert key in result, f"必須キー '{key}' が存在しない"
        assert result["status"] == "failed"
        assert result["job_id"] == "test-job-456"
        assert result["cloud_provider"] == "azure"
        assert result["error_summary"]["error_code"] == "SCAN_FAILED"
        assert result["error_summary"]["total_errors"] == 1
        assert result["system_metadata"]["engine_version"] == "0.9.35"
```

### 2.6 save_error_to_history テスト

```python
class TestSaveErrorToHistory:
    """save_error_to_history の分岐テスト（非同期）"""

    @pytest.fixture
    def handler(self):
        mock_logger = MagicMock()
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        return ErrorHistoryHandler("test-job", mock_logger)

    @pytest.mark.asyncio
    async def test_processing_error_sets_stage(self, handler):
        """NCEHH-011: ProcessingError で error_stage が processing_stage に設定

        error_history_handler.py:189-191 の isinstance(ProcessingError) 分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        error = ProcessingError("処理エラー", processing_stage="policy_execution")
        mock_client = AsyncMock()

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"test": "data"}) as mock_build:
                # Act
                await handler.save_error_to_history(error, "aws")

        # Assert
        call_args = mock_build.call_args
        # L190: error_type = error.processing_stage → L191: error_stage = error_type
        assert call_args[0][1] == "policy_execution"  # error_stage が processing_stage と一致

    @pytest.mark.asyncio
    async def test_validation_error_sets_stage(self, handler):
        """NCEHH-012: ValidationError で error_stage が "validation" に設定

        error_history_handler.py:192-194 の isinstance(ValidationError) 分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        error = ValidationError("検証エラー", field_name="region")
        mock_client = AsyncMock()

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"test": "data"}) as mock_build:
                # Act
                await handler.save_error_to_history(error, "aws")

        # Assert
        call_args = mock_build.call_args
        assert call_args[0][1] == "validation"  # error_stage

    @pytest.mark.asyncio
    async def test_unknown_error_type_sets_unknown_stage(self, handler):
        """NCEHH-013: 未知のエラー型で error_stage が "unknown" に設定

        error_history_handler.py:187-188 のデフォルト値をカバー。
        isinstance チェックのいずれにも該当しない場合。
        """
        # Arrange
        error = RuntimeError("不明なエラー")
        mock_client = AsyncMock()

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"test": "data"}) as mock_build:
                # Act
                await handler.save_error_to_history(error, "aws")

        # Assert
        call_args = mock_build.call_args
        assert call_args[0][1] == "unknown"  # error_stage

    @pytest.mark.asyncio
    async def test_client_exists_calls_index(self, handler):
        """NCEHH-014: クライアント存在時に client.index が呼ばれる

        error_history_handler.py:203-210 の `if client:` 分岐をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        error = RuntimeError("テスト")

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"mock": "data"}):
                # Act
                await handler.save_error_to_history(error, "aws")

        # Assert
        mock_client.index.assert_awaited_once_with(
            index="cspm-scan-history-v2",
            id="test-job",
            body={"mock": "data"}
        )

    @pytest.mark.asyncio
    async def test_client_none_logs_warning(self, handler):
        """NCEHH-015: クライアントが None の場合 warning ログ出力

        error_history_handler.py:213-214 の `else` 分岐をカバー。
        """
        # Arrange
        error = RuntimeError("テスト")

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=None
        ):
            # Act
            await handler.save_error_to_history(error, "aws")

        # Assert
        handler.logger.warning.assert_called_once()
        assert "OpenSearchクライアント" in handler.logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_success_logs_info_with_error_type(self, handler):
        """NCEHH-016: 成功時の info ログに error_type が含まれる

        error_history_handler.py:212 の logger.info をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        error = ValidationError("テスト", field_name="x")
        mock_client = AsyncMock()

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"test": "data"}):
                # Act
                await handler.save_error_to_history(error, "aws")

        # Assert
        handler.logger.info.assert_called_once()
        assert "validation_error" in handler.logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_processing_error_without_stage_attribute(self, handler):
        """NCEHH-017: ProcessingError の processing_stage 属性が存在しない場合のフォールバック

        error_history_handler.py:190 の `hasattr(error, 'processing_stage')` が
        False となる場合、error_type が "processing_error" にフォールバックすることをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        error = ProcessingError("処理エラー", processing_stage="temp")
        delattr(error, 'processing_stage')  # hasattr を False にする
        mock_client = AsyncMock()

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"test": "data"}) as mock_build:
                # Act
                await handler.save_error_to_history(error, "aws")

        # Assert
        call_args = mock_build.call_args
        assert call_args[0][1] == "processing_error"  # フォールバック値
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCEHH-E01 | save_error_to_history 外側 except で例外キャッチ | client.index 例外 | warning ログ、例外伝播なし |
| NCEHH-E02 | get_opensearch_client 自体が例外 | 接続例外 | warning ログ、例外伝播なし |
| NCEHH-E03 | _build_error_history_data 内の error_code 取得 | カスタム例外 | type(error).__name__ が格納 |

### 3.1 異常系テスト

```python
class TestErrorHistoryHandlerErrors:
    """異常入力・エラー状態のテスト"""

    @pytest.fixture
    def handler(self):
        mock_logger = MagicMock()
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        return ErrorHistoryHandler("test-job", mock_logger)

    @pytest.mark.asyncio
    async def test_client_index_exception_caught(self, handler):
        """NCEHH-E01: client.index が例外を送出しても外側 except でキャッチ

        error_history_handler.py:216-217 の外側 except Exception をカバー。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.index.side_effect = RuntimeError("OpenSearch接続エラー")
        error = RuntimeError("テスト")

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            return_value=mock_client
        ):
            with patch.object(handler, '_build_error_history_data',
                              return_value={"test": "data"}):
                # Act（例外が伝播しないことを検証）
                await handler.save_error_to_history(error, "aws")

        # Assert
        handler.logger.warning.assert_called()
        assert "例外発生" in handler.logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_opensearch_client_exception_caught(self, handler):
        """NCEHH-E02: get_opensearch_client 自体が例外を送出

        error_history_handler.py:216-217 の外側 except で
        get_opensearch_client の例外もキャッチされることを検証。
        """
        # Arrange
        error = RuntimeError("テスト")

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            side_effect=ConnectionError("接続不可")
        ):
            # Act（例外が伝播しないことを検証）
            await handler.save_error_to_history(error, "aws")

        # Assert
        handler.logger.warning.assert_called()

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler.datetime")
    def test_error_code_uses_exception_class_name(self, mock_dt, mock_version, handler):
        """NCEHH-E03: error_code に type(error).__name__ が格納される

        error_history_handler.py:120 の `type(error).__name__` をカバー。
        カスタム例外クラス名が正しく取得されることを検証。
        """
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"

        class CustomScanError(Exception):
            pass

        error = CustomScanError("カスタムエラー")

        # Act
        result = handler._build_error_history_data(error, "execution", "aws")

        # Assert
        failed_detail = result["scan_scope"]["failed_region_details"][0]
        assert failed_detail["error_code"] == "CustomScanError"
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCEHH-SEC-01 | エラーメッセージに str(e) のみ格納 | スタックトレース含む例外 | str(e) のみ、Traceback なし |
| NCEHH-SEC-02 | 認証情報がエラー履歴に漏洩しない | 認証情報含む metadata | 履歴データに認証情報なし |
| NCEHH-SEC-03 | save_error_to_history の例外が呼び出し元に伝播しない | 内部例外 | グレースフル失敗 |

### 4.1 セキュリティテスト

```python
@pytest.mark.security
class TestErrorHistoryHandlerSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def handler(self):
        mock_logger = MagicMock()
        from app.jobs.tasks.new_custodian_scan.error_history_handler import ErrorHistoryHandler
        return ErrorHistoryHandler("test-job", mock_logger)

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler.datetime")
    def test_error_message_contains_only_str_e(self, mock_dt, mock_version, handler):
        """NCEHH-SEC-01: エラーメッセージに str(e) のみが格納される

        error_history_handler.py:48,78,119,145 の `str(error)` 使用箇所で
        スタックトレースが漏洩しないことを検証。
        """
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
        error = RuntimeError("テスト用エラー")

        # Act
        result = handler._build_error_history_data(error, "execution", "aws")

        # Assert
        # error_message フィールドを全箇所チェック
        assert result["error_summary"]["error_message"] == "テスト用エラー"
        assert "Traceback" not in result["error_summary"]["error_message"]
        assert "File \"" not in result["error_summary"]["error_message"]

        # scan_scope 内のエラーメッセージ
        detail = result["scan_scope"]["failed_region_details"][0]
        assert detail["error_message"] == "テスト用エラー"

        # execution_summary 内のエラーメッセージ
        assert result["execution_summary"]["error_message"] == "テスト用エラー"

    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler._get_custodian_version",
           return_value="0.9.35")
    @patch("app.jobs.tasks.new_custodian_scan.error_history_handler.datetime")
    def test_credentials_not_leaked_in_history_data(self, mock_dt, mock_version, handler):
        """NCEHH-SEC-02: 認証情報がエラー履歴データに漏洩しない

        error_history_handler.py:123-124 で scan_metadata から
        initiated_by_user と scan_trigger_type のみを抽出する設計により、
        認証情報（accessKey 等）が cspm-scan-history-v2 に格納されないことを検証。
        """
        # Arrange
        mock_dt.now.return_value.isoformat.return_value = "2025-01-01T00:00:00+00:00"
        error = RuntimeError("エラー")
        metadata = {
            "initiated_by_user": "admin",
            "scan_trigger_type": "manual_batch",
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        }

        # Act
        result = handler._build_error_history_data(error, "execution", "aws", metadata)

        # Assert
        # 結果全体を文字列化して認証情報がどこにも含まれないことを確認
        import json
        result_str = json.dumps(result)
        assert "AKIAIOSFODNN7EXAMPLE" not in result_str
        assert "wJalrXUtnFEMI" not in result_str
        # scan_metadata から取得するのは initiated_by_user と scan_trigger_type のみ
        assert result["scan_scope"]["initiated_by_user"] == "admin"

    @pytest.mark.asyncio
    async def test_save_exception_does_not_propagate(self, handler):
        """NCEHH-SEC-03: save_error_to_history の例外が呼び出し元に伝播しない

        error_history_handler.py:216-217 の外側 except により、
        保存処理の失敗がスキャン処理全体を停止させないことを検証。
        """
        # Arrange
        error = RuntimeError("テスト")

        with patch(
            "app.jobs.tasks.new_custodian_scan.error_history_handler.get_opensearch_client",
            side_effect=Exception("致命的エラー")
        ):
            # Act（例外が発生しないことを検証）
            await handler.save_error_to_history(error, "aws")

        # Assert
        # ここに到達すること自体が、例外が伝播しなかった証拠
        handler.logger.warning.assert_called()
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------:|--------:|
| `reset_error_history_handler_module` | error_history_handler モジュールの import キャッシュリセット（任意） | function | No |
| `handler` | TaskLogger モック済み ErrorHistoryHandler インスタンス（各テストクラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加
import sys
import pytest


@pytest.fixture
def reset_error_history_handler_module():
    """error_history_handler モジュールの import キャッシュをリセット（任意）

    _get_custodian_version にはキャッシュがないため通常は不要。
    テスト間でモジュールレベルの副作用が疑われる場合にのみ使用する。
    """
    yield
    mod_key = "app.jobs.tasks.new_custodian_scan.error_history_handler"
    if mod_key in sys.modules:
        del sys.modules[mod_key]
```

---

## 6. テスト実行例

```bash
# error_history_handler テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_history_handler.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_history_handler.py::TestSaveErrorToHistory -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_history_handler.py \
  --cov=app.jobs.tasks.new_custodian_scan.error_history_handler \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_history_handler.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|-----:|--------|
| 正常系 | 17 | NCEHH-001 〜 NCEHH-017 |
| 異常系 | 3 | NCEHH-E01 〜 NCEHH-E03 |
| セキュリティ | 3 | NCEHH-SEC-01 〜 NCEHH-SEC-03 |
| **合計** | **23** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|-----:|
| `TestGetCustodianVersion` | NCEHH-001〜NCEHH-003 | 3 |
| `TestErrorHistoryHandlerInit` | NCEHH-004 | 1 |
| `TestCreateErrorExecutionSummary` | NCEHH-005 | 1 |
| `TestCreateErrorInsightsSummary` | NCEHH-006〜NCEHH-007 | 2 |
| `TestBuildErrorHistoryData` | NCEHH-008〜NCEHH-010 | 3 |
| `TestSaveErrorToHistory` | NCEHH-011〜NCEHH-017 | 7 |
| `TestErrorHistoryHandlerErrors` | NCEHH-E01〜NCEHH-E03 | 3 |
| `TestErrorHistoryHandlerSecurity` | NCEHH-SEC-01〜NCEHH-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> `_get_custodian_version` と同期メソッドはモック不要で安定、
> `save_error_to_history` は AsyncMock + patch で制御可能です。

### 注意事項

- `save_error_to_history` は非同期のため `pytest-asyncio` パッケージが必要
- `--strict-markers` 運用時は `@pytest.mark.security` を `pyproject.toml` に登録する必要あり
- `_get_custodian_version` は関数内 import で `pkg_resources` / `importlib.metadata` を使用。テスト環境に setuptools がない場合に備え、`patch.dict(sys.modules, ...)` で仮置きする

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_get_custodian_version` は関数内 import を使用（キャッシュなし） | 通常のテストでは再 import は不要 | モジュールリセットフィクスチャは任意。副作用が疑われる場合にのみ局所的に使用 |
| 2 | `datetime.now(timezone.utc)` のモックは `datetime` モジュール全体をパッチする必要がある | タイムスタンプの厳密な値検証が煩雑 | NCEHH-008〜010 では datetime をモックし、他テストではタイムスタンプ値の検証を省略 |
| 3 | `save_error_to_history` 内の `from ....jobs.common.error_handling import ...` は遅延 import | テスト時の import パスが深くなる | 実際の ProcessingError / ValidationError インスタンスを使用し、import の問題を回避 |
