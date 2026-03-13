# jobs/tasks/new_custodian_scan/executor 検査系 テストケース

## 1. 概要

`executor/` サブディレクトリの検査系2ファイル（`error_detector.py`, `security_sanitizer.py`）をまとめたテスト仕様書。Custodian実行エラーの検出・分類とセキュリティサニタイズを担う。

### 1.1 対象クラス

| クラス | ファイル | 行数 | 責務 |
|--------|---------|------|------|
| `ErrorDetector` | `error_detector.py` | 376 | 実行ステータスチェック・バリデーションエラー検出・エラー分類 |
| `SecuritySanitizer` | `security_sanitizer.py` | 272 | エラーメッセージサニタイズ・パストラバーサル対策・環境変数安全性チェック |

### 1.2 カバレッジ目標: 85%

> **注記**: `ErrorDetector.check_execution_status` はファイルシステム操作が多くtmp_pathが必須。`SecuritySanitizer.sanitize_error_message` は10パターンの正規表現+ReDoS対策を含む。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/executor/error_detector.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/executor/security_sanitizer.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py` |

### 1.4 補足情報

#### 依存関係

```
error_detector.py (ErrorDetector)
  ──→ TaskLogger（ログ）
  ──→ CustodianLogAnalyzer（ログ解析）
  ──→ SecuritySanitizer（セキュリティサニタイズ）
  ──→ os, json, re（標準ライブラリ）

security_sanitizer.py (SecuritySanitizer)
  ──→ TaskLogger（ログ）
  ──→ os.path, re, time（標準ライブラリ）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| ErrorDetector | check_execution_statusはtmp_pathで実ファイルシステム構築、CustodianLogAnalyzerはMock化 |
| SecuritySanitizer | 純粋関数が多いため実インスタンスで直接テスト、time.timeのみReDoSテストでモック |

#### 主要分岐マップ

| クラス | メソッド | 行番号 | 条件 | 分岐数 |
|--------|---------|--------|------|--------|
| ErrorDetector | `check_execution_status` | L63, L72, L78, L85, L93, L112, L126, L131-150 | output_dir不在、isdir、detect_error、metadata、PolicyException、log_error、resources.json、エラー種別4分岐 | 10 |
| ErrorDetector | `_detect_execution_error` | L187, L188, L202, L218 | resources.json不在、log存在、サイズ/キーワード、例外 | 5 |
| ErrorDetector | `_classify_custodian_error` | L262-269 | auth/permission/policy/default | 4 |
| ErrorDetector | `_extract_error_details` | L290, L298, L303-316 | Traceback有無、エラー行、修正提案4分岐 | 6 |
| ErrorDetector | `detect_validation_error` | L345, L357, L367 | rc==1、パターンマッチ、error_lines有無 | 4 |
| SecuritySanitizer | `sanitize_error_message` | L43, L48, L84, L91, L96 | 空入力、長さ制限、タイムアウト、regex例外、出力制限 | 6 |
| SecuritySanitizer | `safe_read_log_file` | L117, L120, L125, L137, L142, L147 | パス安全性、存在、サイズ、チャンク終了、max到達、例外 | 6 |
| SecuritySanitizer | `_is_safe_path` | L176, L189 | 危険パターン、正規化例外 | 3 |
| SecuritySanitizer | `sanitize_value` | L202, L206-209, L212 | 空、機密検出(3条件)、長さ制限 | 3 |
| SecuritySanitizer | `is_safe_env_key` | L226, L230, L234 | 危険文字、regex、長さ | 4 |
| SecuritySanitizer | `sanitize_env_value` | L249, L261, L266-269, L273 | 空、危険パターン、機密値、長さ制限 | 4 |

---

## 2. 正常系テストケース

### ErrorDetector (EDET)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| EDET-001 | 初期化時に全コンポーネントが生成される | job_id | logger, log_analyzer, security_sanitizer初期化 |
| EDET-002 | check_execution_status 出力ディレクトリ不在 | 存在しないパス | has_error=True, error_type="output_dir_missing" |
| EDET-003 | check_execution_status 正常（エラーなし） | 空のポリシーディレクトリ+resources.json | has_error=False |
| EDET-004 | check_execution_status 非ディレクトリ項目はスキップ | ファイルのみ | has_error=False |
| EDET-005 | check_execution_status metadata PolicyException | metrics内にPolicyException | has_error=True, policy_errors非空 |
| EDET-006 | check_execution_status log_analyzerエラー検出 | error_occurred=True | has_error=True, log_errors非空 |
| EDET-007 | check_execution_status resources.json不在のみ | resources.jsonなし+エラーなし | missing_resources非空, has_error=False |
| EDET-008 | check_execution_status エラー種別優先度 | 複数detailed_errors | 最高優先度のerror_type採用 |
| EDET-009 | _detect_execution_error resources.json存在 | resources.jsonあり | has_error=False |
| EDET-010 | _detect_execution_error ログサイズ>1000 | 1001バイトのログ | has_error=True |
| EDET-011 | _detect_execution_error エラーキーワード | "ERROR"含むログ | has_error=True |
| EDET-012 | _classify auth_errors | "InvalidAccessKeyId" | "authentication_error" |
| EDET-013 | _classify permission_errors | "AccessDenied" | "permission_error" |
| EDET-014 | _classify policy_errors | "jmespath.exceptions" | "policy_error" |
| EDET-015 | _classify default | 未分類ログ | "execution_error" |
| EDET-016 | _extract Traceback+エラーメッセージ | Traceback+Error行 | full_traceback非空, error_message最長行 |
| EDET-017 | _extract suggested_fix InvalidAccessKeyId | InvalidAccessKeyId含むログ | "AWS認証情報"含む |
| EDET-018 | _extract suggested_fix UnauthorizedOperation+権限 | "not authorized to perform: ec2:DescribeInstances" | 具体的権限名含む |
| EDET-019 | _extract suggested_fix default | 未分類エラーログ | "ログの詳細を確認"含む |
| EDET-020 | detect_validation_error rc!=1 | return_code=0 | has_error=False |
| EDET-021 | detect_validation_error rc=1+パターン一致 | "invalid policy file"含む出力 | has_error=True, error_message非空 |
| EDET-022 | detect_validation_error rc=1+パターン不一致 | パターンなし出力 | has_error=False |

### SecuritySanitizer (SSAN)

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SSAN-001 | 初期化 | job_id | logger初期化 |
| SSAN-002 | sanitize_error_message 空入力 | "" | "" |
| SSAN-003 | sanitize_error_message 入力長制限 | 10001文字 | 10000文字+"...[truncated for security]" |
| SSAN-004 | sanitize_error_message ARNパターン | "arn:aws:iam::123456789012:role/test" | "arn:aws:***:***:***ACCOUNT***:***RESOURCE***" |
| SSAN-005 | sanitize_error_message AKIDパターン | "AKIAIOSFODNN7EXAMPLE" | "AKIA***ACCESS_KEY***" |
| SSAN-006 | sanitize_error_message AccountID+IPパターン | "123456789012 10.0.1.5" | "***ACCOUNT_ID*** ***PRIVATE_IP***" |
| SSAN-007 | sanitize_error_message 出力長500制限 | サニタイズ後501文字以上 | 500文字+"...[truncated for security]" |
| SSAN-008 | safe_read_log_file 正常読み込み | 正常なファイル | ファイル内容 |
| SSAN-009 | safe_read_log_file ファイル不在 | 存在しないパス | "" |
| SSAN-010 | safe_read_log_file サイズ超過 | max_sizeを超えるファイル | ValueError |
| SSAN-011 | safe_read_log_file max_size到達でtruncate | ちょうどmax_size | 内容+"...[truncated for security - file too large]" |
| SSAN-012 | _is_safe_path 安全なパス | "/tmp/output/policy-1" | True |
| SSAN-013 | _is_safe_path dot-dot トラバーサル | "/tmp/../etc/passwd" | False |
| SSAN-014 | _is_safe_path システムディレクトリ | "/etc/shadow" | False |
| SSAN-015 | _is_safe_path コマンドインジェクション | "file;rm -rf /" | False |
| SSAN-016 | sanitize_value 空入力 | "" | "" |
| SSAN-017 | sanitize_value Base64マスク | 21文字以上のBase64文字列 | "***MASKED***" |
| SSAN-018 | sanitize_value 通常値50文字制限 | "normal_value" | "normal_value" |
| SSAN-019 | is_safe_env_key 安全なキー | "AWS_REGION" | True |
| SSAN-020 | is_safe_env_key 危険文字 | "KEY;rm" | False |
| SSAN-021 | is_safe_env_key 非英数字 | "KEY-NAME" | False |
| SSAN-022 | is_safe_env_key 長さ超過 | 101文字のキー | False |
| SSAN-023 | sanitize_env_value 空入力 | "" | "" |
| SSAN-024 | sanitize_env_value 危険パターン検出 | "value;rm -rf /" | "***DANGEROUS_VALUE_DETECTED***" |
| SSAN-025 | sanitize_env_value 機密値マスク | 21文字以上Base64 | "***MASKED***" |
| SSAN-026 | sanitize_env_value 通常値200文字制限 | 201文字の値 | 200文字+"...[truncated]" |

### 2.1 ErrorDetector テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py
import pytest
import json
import os
from unittest.mock import patch, MagicMock

MODULE_EDET = "app.jobs.tasks.new_custodian_scan.executor.error_detector"
MODULE_SSAN = "app.jobs.tasks.new_custodian_scan.executor.security_sanitizer"


class TestErrorDetectorInit:
    """ErrorDetector初期化テスト"""

    def test_init_creates_all_components(self, mock_edet_components):
        """EDET-001: 初期化時に全コンポーネントが生成される

        error_detector.py:L25-35 の4コンポーネント初期化をカバー。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.executor.error_detector import ErrorDetector

        # Act
        detector = ErrorDetector("test-job-id")

        # Assert
        assert detector.job_id == "test-job-id"
        mock_edet_components["TaskLogger"].assert_called_once_with("test-job-id", "ErrorDetector")
        mock_edet_components["CustodianLogAnalyzer"].assert_called_once_with("test-job-id")
        mock_edet_components["SecuritySanitizer"].assert_called_once_with("test-job-id")


class TestCheckExecutionStatus:
    """実行ステータスチェックテスト"""

    def test_output_dir_missing(self, error_detector):
        """EDET-002: check_execution_status 出力ディレクトリ不在

        error_detector.py:L63-67 のoutput_dir不在分岐をカバー。
        """
        # Act
        result = error_detector.check_execution_status("/nonexistent/path")

        # Assert
        assert result["has_error"] is True
        assert result["error_type"] == "output_dir_missing"

    def test_no_errors(self, error_detector, tmp_path):
        """EDET-003: check_execution_status 正常（エラーなし）

        error_detector.py:L70-155 のエラーなし正常フローをカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(json.dumps([]))
        # _detect_execution_errorはエラーなし
        error_detector.security_sanitizer.safe_read_log_file.return_value = ""
        error_detector.log_analyzer.analyze_policy_execution.return_value = {
            "error_details": {"error_occurred": False}
        }

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        assert result["has_error"] is False
        assert result["error_type"] is None

    def test_non_dir_items_skipped(self, error_detector, tmp_path):
        """EDET-004: check_execution_status 非ディレクトリ項目はスキップ

        error_detector.py:L72-73 のisdir=False分岐をカバー。
        """
        # Arrange - ファイルのみ配置（ディレクトリなし）
        (tmp_path / "some_file.txt").write_text("data")

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        assert result["has_error"] is False
        # log_analyzerは呼ばれない
        error_detector.log_analyzer.analyze_policy_execution.assert_not_called()

    def test_metadata_policy_exception(self, error_detector, tmp_path):
        """EDET-005: check_execution_status metadata PolicyException

        error_detector.py:L84-102 のmetadata.json + PolicyException分岐をカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(json.dumps([]))
        metadata = {"metrics": [{"MetricName": "PolicyException", "Value": 1}]}
        (policy_dir / "metadata.json").write_text(json.dumps(metadata))
        error_detector.security_sanitizer.safe_read_log_file.return_value = ""
        error_detector.log_analyzer.analyze_policy_execution.return_value = {
            "error_details": {"error_occurred": False}
        }

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        assert result["has_error"] is True
        assert len(result["policy_errors"]) == 1
        assert result["policy_errors"][0]["type"] == "PolicyException"
        assert result["error_type"] == "policy_exception"

    def test_log_analyzer_error_detection(self, error_detector, tmp_path):
        """EDET-006: check_execution_status log_analyzerエラー検出

        error_detector.py:L105-122 のlog_analyzer.analyze_policy_execution分岐をカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(json.dumps([]))
        error_detector.security_sanitizer.safe_read_log_file.return_value = ""
        error_detector.log_analyzer.analyze_policy_execution.return_value = {
            "error_details": {"error_occurred": True, "message": "実行エラー"}
        }

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        assert result["has_error"] is True
        assert len(result["log_errors"]) == 1
        assert result["error_type"] == "execution_error"

    def test_missing_resources_only(self, error_detector, tmp_path):
        """EDET-007: check_execution_status resources.json不在のみ

        error_detector.py:L124-153 のresources.json不在でもhas_error=False分岐をカバー。
        resources.json不在・custodian-run.logも不在の場合、_detect_execution_errorは
        L187-188の条件でスキップされ、missing_resourcesに記録されるのみ。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        # resources.jsonなし、custodian-run.logもなし
        # → _detect_execution_error内L187-188で両方不在のため処理スキップ
        error_detector.log_analyzer.analyze_policy_execution.return_value = {
            "error_details": {"error_occurred": False}
        }

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        assert "policy-1" in result["missing_resources"]
        assert result["has_error"] is False

    def test_error_type_priority(self, error_detector, tmp_path):
        """EDET-008: check_execution_status エラー種別優先度

        error_detector.py:L131-145 のdetailed_errorsの優先度ランキングをカバー。
        validation_error(1) > authentication_error(2) の順で最高優先度を採用。
        """
        # Arrange
        policy_dir1 = tmp_path / "policy-1"
        policy_dir1.mkdir()
        policy_dir2 = tmp_path / "policy-2"
        policy_dir2.mkdir()

        # _detect_execution_errorの戻り値をモック
        detect_results = [
            {"has_error": True, "error_type": "permission_error", "policy_name": "policy-1"},
            {"has_error": True, "error_type": "authentication_error", "policy_name": "policy-2"}
        ]
        error_detector._detect_execution_error = MagicMock(side_effect=detect_results)
        error_detector.log_analyzer.analyze_policy_execution.return_value = {
            "error_details": {"error_occurred": False}
        }

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        # authentication_error(2) < permission_error(3) → authentication_errorが採用
        assert result["error_type"] == "authentication_error"


class TestDetectExecutionError:
    """実行エラー検出テスト"""

    def test_resources_json_exists_no_error(self, error_detector, tmp_path):
        """EDET-009: _detect_execution_error resources.json存在

        error_detector.py:L187 のresources.json存在でスキップをカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(json.dumps([]))

        # Act
        result = error_detector._detect_execution_error(str(policy_dir), "policy-1")

        # Assert
        assert result["has_error"] is False

    def test_log_size_exceeds_threshold(self, error_detector, tmp_path):
        """EDET-010: _detect_execution_error ログサイズ>1000

        error_detector.py:L202 のlog_size > 1000条件をカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        # resources.jsonなし + 1001バイト以上のログ
        log_content = "INFO normal log\n" * 100  # 1000バイト超
        (policy_dir / "custodian-run.log").write_text(log_content)
        error_detector.security_sanitizer.safe_read_log_file.return_value = log_content
        error_detector._classify_custodian_error = MagicMock(return_value="execution_error")
        error_detector._extract_error_details = MagicMock(return_value={
            "full_traceback": "", "error_message": "", "error_location": "", "suggested_fix": ""
        })

        # Act
        result = error_detector._detect_execution_error(str(policy_dir), "policy-1")

        # Assert
        assert result["has_error"] is True
        assert result["log_size"] > 1000

    def test_error_keywords_trigger(self, error_detector, tmp_path):
        """EDET-011: _detect_execution_error エラーキーワード

        error_detector.py:L199-202 のerror_keywords検出をカバー。
        ログサイズ<1000でもERRORキーワードがあればエラー判定。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        log_content = "ERROR: Something failed"  # 短いがERROR含む
        (policy_dir / "custodian-run.log").write_text(log_content)
        error_detector.security_sanitizer.safe_read_log_file.return_value = log_content
        error_detector._classify_custodian_error = MagicMock(return_value="execution_error")
        error_detector._extract_error_details = MagicMock(return_value={
            "full_traceback": "", "error_message": "", "error_location": "", "suggested_fix": ""
        })

        # Act
        result = error_detector._detect_execution_error(str(policy_dir), "policy-1")

        # Assert
        assert result["has_error"] is True


class TestClassifyCustodianError:
    """Custodianエラー分類テスト"""

    def test_auth_errors(self, error_detector):
        """EDET-012: _classify auth_errors

        error_detector.py:L262-263 の認証エラー分岐をカバー。
        """
        # Act
        result = error_detector._classify_custodian_error("InvalidAccessKeyId: key not found")

        # Assert
        assert result == "authentication_error"

    def test_permission_errors(self, error_detector):
        """EDET-013: _classify permission_errors

        error_detector.py:L264-265 の権限エラー分岐をカバー。
        """
        # Act
        result = error_detector._classify_custodian_error("AccessDenied for operation")

        # Assert
        assert result == "permission_error"

    def test_policy_errors(self, error_detector):
        """EDET-014: _classify policy_errors

        error_detector.py:L266-267 のポリシーエラー分岐をカバー。
        """
        # Act
        result = error_detector._classify_custodian_error("jmespath.exceptions.LexerError: bad expression")

        # Assert
        assert result == "policy_error"

    def test_default_execution_error(self, error_detector):
        """EDET-015: _classify default

        error_detector.py:L268-269 のデフォルト分岐をカバー。
        """
        # Act
        result = error_detector._classify_custodian_error("Some unknown error occurred")

        # Assert
        assert result == "execution_error"


class TestExtractErrorDetails:
    """エラー詳細抽出テスト"""

    def test_traceback_and_error_message(self, error_detector):
        """EDET-016: _extract Traceback+エラーメッセージ

        error_detector.py:L290-300 のTraceback抽出+最長エラー行をカバー。
        L298-300: 複数のエラー行のうちlen(line.strip())が最大の行を選択。
        """
        # Arrange - 短いERROR行と長いError行を混在
        log_content = (
            "INFO: Starting\n"
            "Traceback (most recent call last):\n"
            "  File test.py\n"
            "ERROR: short\n"
            "Error: Something broke with additional details here"
        )

        # Act
        result = error_detector._extract_error_details(log_content)

        # Assert
        assert "Traceback" in result["full_traceback"]
        # 最長のエラー行が採用される（L299の len(line.strip()) > len(...) 条件）
        assert result["error_message"] == "Error: Something broke with additional details here"

    def test_suggested_fix_invalid_access_key(self, error_detector):
        """EDET-017: _extract suggested_fix InvalidAccessKeyId

        error_detector.py:L303-304 のInvalidAccessKeyId修正提案をカバー。
        """
        # Act
        result = error_detector._extract_error_details("InvalidAccessKeyId: AKIA...")

        # Assert
        assert "AWS認証情報" in result["suggested_fix"]

    def test_suggested_fix_unauthorized_with_permission(self, error_detector):
        """EDET-018: _extract suggested_fix UnauthorizedOperation+権限抽出

        error_detector.py:L305-310 の権限名抽出分岐をカバー。
        """
        # Arrange
        log_content = "UnauthorizedOperation: not authorized to perform: ec2:DescribeInstances"

        # Act
        result = error_detector._extract_error_details(log_content)

        # Assert
        assert "ec2:DescribeInstances" in result["suggested_fix"]

    def test_suggested_fix_default(self, error_detector):
        """EDET-019: _extract suggested_fix default

        error_detector.py:L315-316 のデフォルト修正提案をカバー。
        """
        # Act
        result = error_detector._extract_error_details("Some unknown error")

        # Assert
        assert "ログの詳細を確認" in result["suggested_fix"]


class TestDetectValidationError:
    """バリデーションエラー検出テスト"""

    def test_return_code_not_one(self, error_detector):
        """EDET-020: detect_validation_error rc!=1

        error_detector.py:L345 のreturn_code != 1分岐をカバー。
        """
        # Act
        result = error_detector.detect_validation_error(0, ["success"], [])

        # Assert
        assert result["has_error"] is False
        assert result["return_code"] == 0

    def test_return_code_one_with_patterns(self, error_detector):
        """EDET-021: detect_validation_error rc=1+パターン一致

        error_detector.py:L345-375 のrc=1+バリデーションパターン検出をカバー。
        """
        # Act
        result = error_detector.detect_validation_error(
            1,
            ["Error: invalid policy file /tmp/policy.yml"],
            ["Configuration invalid"]
        )

        # Assert
        assert result["has_error"] is True
        assert result["error_type"] == "validation_error"
        assert "invalid policy file" in result["error_message"]

    def test_return_code_one_without_patterns(self, error_detector):
        """EDET-022: detect_validation_error rc=1+パターン不一致

        error_detector.py:L357 のパターン不一致分岐をカバー。
        rc=1だがバリデーションパターンがない場合はエラーにしない。
        """
        # Act
        result = error_detector.detect_validation_error(
            1, ["Some other error"], ["generic error"]
        )

        # Assert
        assert result["has_error"] is False
```

### 2.2 SecuritySanitizer テスト

```python
class TestSecuritySanitizerInit:
    """SecuritySanitizer初期化テスト"""

    def test_init(self, security_sanitizer):
        """SSAN-001: 初期化

        security_sanitizer.py:L23-31 をカバー。
        """
        assert security_sanitizer.job_id == "test-job-id"


class TestSanitizeErrorMessage:
    """エラーメッセージサニタイズテスト"""

    def test_empty_input(self, security_sanitizer):
        """SSAN-002: sanitize_error_message 空入力

        security_sanitizer.py:L43-44 の空文字列分岐をカバー。
        """
        # Act
        result = security_sanitizer.sanitize_error_message("")

        # Assert
        assert result == ""

    def test_max_input_length_truncation(self, security_sanitizer):
        """SSAN-003: sanitize_error_message 入力長制限

        security_sanitizer.py:L47-49 のMAX_INPUT_LENGTH=10000をカバー。
        """
        # Arrange
        long_input = "A" * 10001

        # Act
        result = security_sanitizer.sanitize_error_message(long_input)

        # Assert
        assert "[truncated for security]" in result

    def test_arn_pattern(self, security_sanitizer):
        """SSAN-004: sanitize_error_message ARNパターン

        security_sanitizer.py:L54 のARN正規表現をカバー。
        """
        # Arrange
        msg = "Error accessing arn:aws:iam::123456789012:role/admin"

        # Act
        result = security_sanitizer.sanitize_error_message(msg)

        # Assert
        assert "123456789012" not in result
        assert "admin" not in result
        assert "***ACCOUNT***" in result or "***RESOURCE***" in result

    def test_access_key_id_pattern(self, security_sanitizer):
        """SSAN-005: sanitize_error_message AKIDパターン

        security_sanitizer.py:L56 のAccess Key IDパターンをカバー。
        """
        # Arrange
        msg = "Key: AKIAIOSFODNN7EXAMPLE"

        # Act
        result = security_sanitizer.sanitize_error_message(msg)

        # Assert
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "ACCESS_KEY" in result

    def test_account_id_and_private_ip(self, security_sanitizer):
        """SSAN-006: sanitize_error_message AccountID+IPパターン

        security_sanitizer.py:L60, L70 のAccount IDとプライベートIPをカバー。
        """
        # Arrange
        msg = "Account 123456789012 at 10.0.1.50"

        # Act
        result = security_sanitizer.sanitize_error_message(msg)

        # Assert
        assert "123456789012" not in result
        assert "10.0.1.50" not in result

    def test_output_length_limit(self, security_sanitizer):
        """SSAN-007: sanitize_error_message 出力長500制限

        security_sanitizer.py:L96-97 の出力長制限をカバー。
        """
        # Arrange - サニタイズ後も500文字を超える入力
        msg = "Error: " + "x" * 600

        # Act
        result = security_sanitizer.sanitize_error_message(msg)

        # Assert
        assert len(result) <= 500 + len("...[truncated for security]")
        assert result.endswith("...[truncated for security]")


class TestSafeReadLogFile:
    """安全なログファイル読み込みテスト"""

    def test_normal_read(self, security_sanitizer, tmp_path):
        """SSAN-008: safe_read_log_file 正常読み込み

        security_sanitizer.py:L128-145 の正常チャンク読み込みをカバー。
        """
        # Arrange
        log_file = tmp_path / "test.log"
        log_file.write_text("log line 1\nlog line 2")

        # Act
        result = security_sanitizer.safe_read_log_file(str(log_file))

        # Assert
        assert "log line 1" in result
        assert "log line 2" in result

    def test_file_not_exists(self, security_sanitizer, tmp_path):
        """SSAN-009: safe_read_log_file ファイル不在

        security_sanitizer.py:L120-121 のファイル不在分岐をカバー。
        """
        # Act
        result = security_sanitizer.safe_read_log_file(str(tmp_path / "nonexistent.log"))

        # Assert
        assert result == ""

    def test_size_exceeded(self, security_sanitizer, tmp_path):
        """SSAN-010: safe_read_log_file サイズ超過

        security_sanitizer.py:L125-126 のファイルサイズ超過をカバー。
        """
        # Arrange
        log_file = tmp_path / "large.log"
        log_file.write_text("x" * 1000)

        # Act & Assert
        with pytest.raises(ValueError, match="ファイルサイズが制限を超えています"):
            security_sanitizer.safe_read_log_file(str(log_file), max_size=100)

    def test_chunk_read_at_max_size(self, security_sanitizer, tmp_path):
        """SSAN-011: safe_read_log_file max_size到達でtruncate

        security_sanitizer.py:L135-143 のmax_size到達時のtruncateをカバー。
        getsize < max_size（L125通過）だが、チャンク読み込み中にread_size >= max_size
        （L142）に到達してtruncateメッセージが付与される。
        """
        # Arrange
        log_file = tmp_path / "medium.log"
        # 500バイトのファイルを作成
        content = "x" * 500
        log_file.write_text(content)

        # Act - max_size=200でチャンク読み込み中にmax到達
        # getsize(500) > max_size(200)なのでL125のValueErrorが先に発生するため
        # getsizeをモックしてL125を通過させ、チャンクでL142に到達させる
        with patch(f"{MODULE_SSAN}.os.path.getsize", return_value=100):
            result = security_sanitizer.safe_read_log_file(str(log_file), max_size=200)

        # Assert
        assert result.endswith("...[truncated for security - file too large]")
        # max_size分だけ読み込まれる
        assert len(result) > 200


class TestIsSafePath:
    """パス安全性チェックテスト"""

    def test_safe_path(self, security_sanitizer):
        """SSAN-012: _is_safe_path 安全なパス

        security_sanitizer.py:L188 の正常パスをカバー。
        """
        # Act
        result = security_sanitizer._is_safe_path("/tmp/output/policy-1/custodian-run.log")

        # Assert
        assert result is True

    def test_dotdot_traversal(self, security_sanitizer):
        """SSAN-013: _is_safe_path dot-dot トラバーサル

        security_sanitizer.py:L162 の".."パターンをカバー。
        """
        # Act
        result = security_sanitizer._is_safe_path("/tmp/../etc/passwd")

        # Assert
        assert result is False

    def test_system_directories(self, security_sanitizer):
        """SSAN-014: _is_safe_path システムディレクトリ

        security_sanitizer.py:L164-167 のシステムパスパターンをカバー。
        """
        # Act & Assert
        assert security_sanitizer._is_safe_path("/etc/shadow") is False
        assert security_sanitizer._is_safe_path("/proc/1/environ") is False
        assert security_sanitizer._is_safe_path("/sys/class/net") is False

    def test_command_injection_chars(self, security_sanitizer):
        """SSAN-015: _is_safe_path コマンドインジェクション

        security_sanitizer.py:L170-172 のインジェクション文字パターンをカバー。
        """
        # Act & Assert
        assert security_sanitizer._is_safe_path("file|cat /etc/passwd") is False
        assert security_sanitizer._is_safe_path("file;rm -rf /") is False
        assert security_sanitizer._is_safe_path("file&echo hack") is False


class TestSanitizeValue:
    """値サニタイズテスト"""

    def test_empty_input(self, security_sanitizer):
        """SSAN-016: sanitize_value 空入力

        security_sanitizer.py:L202-203 の空文字列分岐をカバー。
        """
        # Act & Assert
        assert security_sanitizer.sanitize_value("") == ""

    def test_base64_masked(self, security_sanitizer):
        """SSAN-017: sanitize_value Base64マスク

        security_sanitizer.py:L206-210 の機密値検出をカバー。
        21文字以上のBase64文字列はマスクされる。
        """
        # Arrange - 40文字のBase64風文字列
        base64_value = "A" * 40

        # Act
        result = security_sanitizer.sanitize_value(base64_value)

        # Assert
        assert result == "***MASKED***"

    def test_normal_value_truncated(self, security_sanitizer):
        """SSAN-018: sanitize_value 通常値50文字制限

        security_sanitizer.py:L212 の長さ制限をカバー。
        """
        # Act
        result = security_sanitizer.sanitize_value("normal_value")

        # Assert
        assert result == "normal_value"


class TestIsSafeEnvKey:
    """環境変数キー安全性チェックテスト"""

    def test_safe_key(self, security_sanitizer):
        """SSAN-019: is_safe_env_key 安全なキー

        security_sanitizer.py:L237 の正常キーをカバー。
        """
        # Act & Assert
        assert security_sanitizer.is_safe_env_key("AWS_REGION") is True
        assert security_sanitizer.is_safe_env_key("PATH") is True

    def test_dangerous_chars(self, security_sanitizer):
        """SSAN-020: is_safe_env_key 危険文字

        security_sanitizer.py:L225-227 の危険文字検出をカバー。
        """
        # Act & Assert
        assert security_sanitizer.is_safe_env_key("KEY;rm") is False
        assert security_sanitizer.is_safe_env_key("KEY`whoami`") is False
        assert security_sanitizer.is_safe_env_key("KEY\nINJECT") is False

    def test_non_alphanumeric(self, security_sanitizer):
        """SSAN-021: is_safe_env_key 非英数字

        security_sanitizer.py:L230-231 の正規表現チェックをカバー。
        """
        # Act & Assert
        assert security_sanitizer.is_safe_env_key("KEY-NAME") is False
        assert security_sanitizer.is_safe_env_key("KEY.NAME") is False

    def test_length_exceeds_100(self, security_sanitizer):
        """SSAN-022: is_safe_env_key 長さ超過

        security_sanitizer.py:L234-235 の長さ制限をカバー。
        """
        # Act & Assert
        assert security_sanitizer.is_safe_env_key("A" * 101) is False


class TestSanitizeEnvValue:
    """環境変数値サニタイズテスト"""

    def test_empty_input(self, security_sanitizer):
        """SSAN-023: sanitize_env_value 空入力

        security_sanitizer.py:L249-250 の空文字列分岐をカバー。
        """
        # Act & Assert
        assert security_sanitizer.sanitize_env_value("") == ""

    def test_dangerous_pattern_detected(self, security_sanitizer):
        """SSAN-024: sanitize_env_value 危険パターン検出

        security_sanitizer.py:L253-263 のコマンドインジェクション検出をカバー。
        """
        # Act
        result = security_sanitizer.sanitize_env_value("value;rm -rf /")

        # Assert
        assert result == "***DANGEROUS_VALUE_DETECTED***"

    def test_sensitive_value_masked(self, security_sanitizer):
        """SSAN-025: sanitize_env_value 機密値マスク

        security_sanitizer.py:L266-270 の機密値検出をカバー。
        """
        # Arrange - 40文字のBase64風値（危険パターンなし）
        base64_value = "A" * 40

        # Act
        result = security_sanitizer.sanitize_env_value(base64_value)

        # Assert
        assert result == "***MASKED***"

    def test_normal_value_truncated(self, security_sanitizer):
        """SSAN-026: sanitize_env_value 通常値200文字制限

        security_sanitizer.py:L273 の長さ制限をカバー。
        """
        # Arrange
        long_value = "x" * 250

        # Act
        result = security_sanitizer.sanitize_env_value(long_value)

        # Assert
        assert len(result) <= 200 + len("...[truncated]")
        assert result.endswith("...[truncated]")
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| EDET-E01 | metadata.json読み込みエラー | 不正なJSON | has_error=False維持、warningログ出力 |
| EDET-E02 | log_analyzer例外 | analyze_policy_execution例外 | debugログ出力、正常な結果dict返却（処理継続） |
| EDET-E03 | _detect ログファイル読み込み例外 | safe_read_log_file例外 | has_error=True, error_type="log_analysis_error" |
| SSAN-E01 | sanitize_error_message regex タイムアウト | 処理時間>1秒 | 途中で中断、warningログ |
| SSAN-E02 | sanitize_error_message regex例外 | 正規表現エラー | スキップして継続 |
| SSAN-E03 | safe_read_log_file 読み込み例外 | ファイル読み込みエラー | エラーメッセージ返却 |
| SSAN-E04 | _is_safe_path 正規化例外 | 不正なパス | False |

### 3.1 異常系テスト

```python
class TestInspectionErrors:
    """検査系異常系テスト"""

    def test_metadata_json_parse_error(self, error_detector, tmp_path):
        """EDET-E01: metadata.json読み込みエラー

        error_detector.py:L101-102 のmetadata.json例外ハンドリングをカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(json.dumps([]))
        (policy_dir / "metadata.json").write_text("{invalid json")
        error_detector.security_sanitizer.safe_read_log_file.return_value = ""
        error_detector.log_analyzer.analyze_policy_execution.return_value = {
            "error_details": {"error_occurred": False}
        }

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        # metadata.json読み込みエラーのwarningが出力される
        warning_msgs = [str(call) for call in error_detector.logger.warning.call_args_list]
        assert any("metadata.json" in msg for msg in warning_msgs), \
            f"metadata.json関連のwarningが未出力: {warning_msgs}"
        # has_errorは変化しない（metadata.jsonパースエラーはpolicy_errorsに影響しない）
        # resources.json存在 + log_analyzerエラーなし → 他のエラー源がないためFalse
        assert result["has_error"] is False

    def test_log_analyzer_exception(self, error_detector, tmp_path):
        """EDET-E02: log_analyzer例外

        error_detector.py:L121-122 のログ解析例外ハンドリングをカバー。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(json.dumps([]))
        error_detector.security_sanitizer.safe_read_log_file.return_value = ""
        error_detector.log_analyzer.analyze_policy_execution.side_effect = RuntimeError("解析失敗")

        # Act
        result = error_detector.check_execution_status(str(tmp_path))

        # Assert
        # debugログが出力され、処理は継続される
        error_detector.logger.debug.assert_called()
        # 例外にもかかわらず正常な結果dictが返却される（処理継続の証拠）
        assert "has_error" in result
        assert "missing_resources" in result
        assert "policy_errors" in result

    def test_detect_log_read_exception(self, error_detector, tmp_path):
        """EDET-E03: _detect ログファイル読み込み例外

        error_detector.py:L218-224 のログファイル読み込み例外をカバー。
        エラーメッセージはsanitize_error_messageでサニタイズされる。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "custodian-run.log").write_text("log data")
        # resources.jsonなし
        error_detector.security_sanitizer.safe_read_log_file.side_effect = PermissionError("読み取り拒否")
        error_detector.security_sanitizer.sanitize_error_message.return_value = "サニタイズ済みエラー"

        # Act
        result = error_detector._detect_execution_error(str(policy_dir), "policy-1")

        # Assert
        assert result["has_error"] is True
        assert result["error_type"] == "log_analysis_error"
        # sanitize_error_messageが呼ばれたことを確認
        error_detector.security_sanitizer.sanitize_error_message.assert_called_once()

    def test_sanitize_regex_timeout(self, security_sanitizer):
        """SSAN-E01: sanitize_error_message regex タイムアウト

        security_sanitizer.py:L84-86 のReDoSタイムアウト分岐をカバー。
        fake_timeは最初の呼び出し（L78のstart_time取得）で0.0を返し、
        2回目以降（L84のループ内チェック）で2.0を返す。
        これにより最初のパターン（ARN, L54）の処理前にタイムアウトとなり
        breakが実行される。結果として全パターンがスキップされ入力がほぼそのまま返る。
        """
        # Arrange - time.timeをモックしてタイムアウトをシミュレート
        call_count = 0
        def fake_time():
            nonlocal call_count
            call_count += 1
            # 最初の呼び出し(L78 start_time)は0.0
            # 2回目以降(L84 ループ内チェック)は2.0（REGEX_TIMEOUT=1.0超過）
            return 0.0 if call_count <= 1 else 2.0

        with patch(f"{MODULE_SSAN}.time.time", side_effect=fake_time):
            # Act
            result = security_sanitizer.sanitize_error_message("test message with AKIAIOSFODNN7EXAMPLE")

        # Assert
        # タイムアウトwarningが出力される
        security_sanitizer.logger.warning.assert_called()
        # 最初のパターン処理前にbreakするため、AKIAパターンは未適用
        assert "AKIAIOSFODNN7EXAMPLE" in result

    def test_sanitize_regex_exception(self, security_sanitizer):
        """SSAN-E02: sanitize_error_message regex例外

        security_sanitizer.py:L91-93 の正規表現例外ハンドリングをカバー。
        """
        # Arrange - re.subが例外を投げるようモック
        with patch(f"{MODULE_SSAN}.re.sub", side_effect=Exception("regex error")):
            # Act
            result = security_sanitizer.sanitize_error_message("test message")

        # Assert
        # 例外はスキップされ処理継続
        assert result is not None
        security_sanitizer.logger.warning.assert_called()

    def test_safe_read_exception(self, security_sanitizer, tmp_path):
        """SSAN-E03: safe_read_log_file 読み込み例外

        security_sanitizer.py:L147-149 のファイル読み込み例外をカバー。
        """
        # Arrange
        log_file = tmp_path / "test.log"
        log_file.write_text("content")

        with patch("builtins.open", side_effect=IOError("読み込みエラー")):
            # Act
            result = security_sanitizer.safe_read_log_file(str(log_file))

        # Assert
        assert "Error reading log file" in result

    def test_is_safe_path_normalization_exception(self, security_sanitizer):
        """SSAN-E04: _is_safe_path 正規化例外

        security_sanitizer.py:L189 のos.path.abspath例外をカバー。
        """
        # Arrange
        with patch(f"{MODULE_SSAN}.os.path.abspath", side_effect=Exception("正規化失敗")):
            # Act
            result = security_sanitizer._is_safe_path("/valid/looking/path")

        # Assert
        assert result is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| EDET-SEC-01 | _detect例外時のエラーメッセージサニタイズ確認 | 機密情報含む例外 | sanitize_error_message呼び出し |
| EDET-SEC-02 | detect_validation_error error_lines最大3行制限 | 5行のエラー出力 | error_message内に最大3行 |
| SSAN-SEC-01 | sanitize_error_message 代表的5パターン検証 | 各パターンの代表入力 | 全て機密情報除去 |
| SSAN-SEC-02 | safe_read_log_file パストラバーサル攻撃ベクター | "../"等の攻撃パス | ValueError |
| SSAN-SEC-03 | sanitize_env_value 全危険パターン網羅 | 4種の危険パターン | 全て"***DANGEROUS_VALUE_DETECTED***" |

```python
@pytest.mark.security
class TestInspectionSecurity:
    """検査系セキュリティテスト"""

    def test_detect_error_sanitizes_exception(self, error_detector, tmp_path):
        """EDET-SEC-01: _detect例外時のエラーメッセージサニタイズ確認

        error_detector.py:L220 のsanitize_error_message呼び出しをカバー。
        例外メッセージにAWS認証情報が含まれていてもサニタイズされる。
        """
        # Arrange
        policy_dir = tmp_path / "policy-1"
        policy_dir.mkdir()
        (policy_dir / "custodian-run.log").write_text("log")
        error_detector.security_sanitizer.safe_read_log_file.side_effect = \
            Exception("Error with AKIAIOSFODNN7EXAMPLE key")
        error_detector.security_sanitizer.sanitize_error_message.return_value = "sanitized"

        # Act
        result = error_detector._detect_execution_error(str(policy_dir), "policy-1")

        # Assert
        # sanitize_error_messageに元の例外メッセージが渡される
        error_detector.security_sanitizer.sanitize_error_message.assert_called_once_with(
            "Error with AKIAIOSFODNN7EXAMPLE key"
        )
        # 結果のerror_messageには固定文言のみ（サニタイズ済み例外は使用しない）
        assert "AKIAIOSFODNN7EXAMPLE" not in result["error_message"]

    def test_validation_error_lines_max_3(self, error_detector):
        """EDET-SEC-02: detect_validation_error error_lines最大3行制限

        error_detector.py:L368 のerror_lines[:3]制限をカバー。
        大量のエラー出力でもerror_messageは最大3行に制限される。
        """
        # Arrange
        stdout = [
            "invalid policy file: policy1.yml",
            "has unknown keys: [bad_key]",
            "is not valid under any of the given schemas",
            "Configuration invalid: missing required field",
            "Failed to validate policy: syntax error"
        ]

        # Act
        result = error_detector.detect_validation_error(1, stdout, [])

        # Assert
        assert result["has_error"] is True
        # " | "区切りで最大3行
        parts = result["error_message"].split(" | ")
        assert len(parts) <= 3

    def test_sanitize_representative_5_patterns(self, security_sanitizer):
        """SSAN-SEC-01: sanitize_error_message 代表的5パターン検証

        security_sanitizer.py:L52-73 の10パターンのうち代表的5パターンを検証。
        対象: ARN(L54), AKID(L56), AccountID(L60), PrivateIP(L70), Password(L66)。
        残り5パターン（SecretKey, Base64Token, SessionToken, Secret, PublicIP）は
        制限事項#3として記載。
        """
        # Arrange
        msg = (
            "arn:aws:iam::123456789012:role/admin "
            "AKIAIOSFODNN7EXAMPLE "
            "Account: 123456789012 "
            "IP: 10.0.1.50 "
            "password=SuperSecret123"
        )

        # Act
        result = security_sanitizer.sanitize_error_message(msg)

        # Assert
        assert "123456789012" not in result
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "10.0.1.50" not in result
        assert "SuperSecret123" not in result

    def test_path_traversal_attack_vectors(self, security_sanitizer):
        """SSAN-SEC-02: safe_read_log_file パストラバーサル攻撃ベクター

        security_sanitizer.py:L117-118 のパストラバーサル対策をカバー。
        """
        # Act & Assert
        with pytest.raises(ValueError, match="危険なファイルパス"):
            security_sanitizer.safe_read_log_file("/tmp/../../../etc/passwd")

        with pytest.raises(ValueError, match="危険なファイルパス"):
            security_sanitizer.safe_read_log_file("/tmp/file;cat /etc/shadow")

    def test_all_dangerous_env_patterns(self, security_sanitizer):
        """SSAN-SEC-03: sanitize_env_value 全危険パターン網羅

        security_sanitizer.py:L253-258 の4種の危険パターンすべてを検証。
        """
        # Arrange
        dangerous_values = [
            "value;rm -rf /",      # コマンドセパレータ
            "$(cat /etc/passwd)",   # コマンド置換
            "`whoami`",            # バッククォート
            "value\ninjected",     # 改行インジェクション
        ]

        # Act & Assert
        for value in dangerous_values:
            result = security_sanitizer.sanitize_env_value(value)
            assert result == "***DANGEROUS_VALUE_DETECTED***", \
                f"危険パターン未検出: {repr(value)}"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse | 定義元 |
|--------------|------|---------|---------|--------|
| `reset_executor_module` | テスト間のモジュール状態リセット | function | Yes | #14aで定義済み（流用） |
| `mock_edet_components` | ErrorDetector全依存クラスのパッチ | function | No | #14b新規 |
| `error_detector` | テスト用ErrorDetectorインスタンス | function | No | #14b新規 |
| `security_sanitizer` | テスト用SecuritySanitizerインスタンス | function | No | #14b新規 |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/executor/conftest.py に追記
#
# 統合方針:
#   - reset_executor_module は #14a で定義済み（flow_tests L1134）。
#     同一conftest.pyに存在するため新規定義は不要（#14aの定義をそのまま流用）。
#   - 以下は #14b 固有のフィクスチャと MODULE 定数のみを追記する。
#   - import文は #14a の既存 import と重複するため、未定義のもののみ追加。

# --- ここから #14b 追記分 ---
# （#14a で import sys, pytest, patch, MagicMock, AsyncMock は定義済み）

MODULE_EDET = "app.jobs.tasks.new_custodian_scan.executor.error_detector"
MODULE_SSAN = "app.jobs.tasks.new_custodian_scan.executor.security_sanitizer"

# reset_executor_module は #14a の定義を流用（再定義しない）
# #14a定義: key.startswith("app.jobs.tasks.new_custodian_scan.executor") で
# error_detector/security_sanitizer モジュールも含めてクリアされる。


@pytest.fixture
def mock_edet_components():
    """ErrorDetector全依存クラスのモックパッチ

    error_detector.py の __init__ が参照する全クラスをMagicMockに置き換える。
    """
    patches = {}
    mocks = {}
    for name in ["TaskLogger", "CustodianLogAnalyzer", "SecuritySanitizer"]:
        p = patch(f"{MODULE_EDET}.{name}")
        mocks[name] = p.start()
        patches[name] = p

    yield mocks

    for p in patches.values():
        p.stop()


@pytest.fixture
def error_detector(mock_edet_components):
    """テスト用ErrorDetectorインスタンス

    log_analyzerとsecurity_sanitizerがモック化された状態で生成。
    check_execution_statusのファイルシステムテストはtmp_pathと組み合わせる。
    """
    from app.jobs.tasks.new_custodian_scan.executor.error_detector import ErrorDetector
    return ErrorDetector("test-job-id")


@pytest.fixture
def security_sanitizer():
    """テスト用SecuritySanitizerインスタンス

    SecuritySanitizerは純粋関数が多いため、TaskLoggerのみパッチして
    実インスタンスで直接テストする。
    """
    with patch(f"{MODULE_SSAN}.TaskLogger"):
        from app.jobs.tasks.new_custodian_scan.executor.security_sanitizer import SecuritySanitizer
        return SecuritySanitizer("test-job-id")
```

---

## 6. テスト実行例

```bash
# 検査系テスト全体を実行
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py -v

# クラス単位で実行
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py::TestCheckExecutionStatus -v
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py::TestSanitizeErrorMessage -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py \
  --cov=app.jobs.tasks.new_custodian_scan.executor.error_detector \
  --cov=app.jobs.tasks.new_custodian_scan.executor.security_sanitizer \
  --cov-report=term-missing -v

# セキュリティマーカーで実行（実行前提テーブルのマーカー登録が必要）
pytest test/unit/jobs/tasks/new_custodian_scan/executor/test_executor_inspection.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 48 | EDET-001〜022, SSAN-001〜026 |
| 異常系 | 7 | EDET-E01〜E03, SSAN-E01〜E04 |
| セキュリティ | 5 | EDET-SEC-01〜02, SSAN-SEC-01〜03 |
| **合計** | **60** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestErrorDetectorInit` | EDET-001 | 1 |
| `TestCheckExecutionStatus` | EDET-002〜008 | 7 |
| `TestDetectExecutionError` | EDET-009〜011 | 3 |
| `TestClassifyCustodianError` | EDET-012〜015 | 4 |
| `TestExtractErrorDetails` | EDET-016〜019 | 4 |
| `TestDetectValidationError` | EDET-020〜022 | 3 |
| `TestSecuritySanitizerInit` | SSAN-001 | 1 |
| `TestSanitizeErrorMessage` | SSAN-002〜007 | 6 |
| `TestSafeReadLogFile` | SSAN-008〜011 | 4 |
| `TestIsSafePath` | SSAN-012〜015 | 4 |
| `TestSanitizeValue` | SSAN-016〜018 | 3 |
| `TestIsSafeEnvKey` | SSAN-019〜022 | 4 |
| `TestSanitizeEnvValue` | SSAN-023〜026 | 4 |
| `TestInspectionErrors` | EDET-E01〜E03, SSAN-E01〜E04 | 7 |
| `TestInspectionSecurity` | EDET-SEC-01〜02, SSAN-SEC-01〜03 | 5 |

### 実装失敗が予想されるテスト

以下の実行前提が整備されていれば、失敗が予想されるテストはありません。

#### 実行前提（実装タスクとしてpyproject.tomlへの追加が必要）

| 前提 | 対応内容 |
|------|---------|
| `security`マーカー | `[tool.pytest.ini_options].markers` に `"security: セキュリティテスト"` を追加 |

### 注意事項

- ErrorDetectorのcheck_execution_statusテストは`tmp_path`で実ファイルシステムを構築する
- ErrorDetectorのlog_analyzerとsecurity_sanitizerはMock化（内部ロジックは個別テスト対象）
- SecuritySanitizerは純粋関数が多いため、実インスタンスで直接テスト
- SSAN-E01のReDoSテストではtime.timeをモックしてタイムアウトをシミュレート

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | ErrorDetectorのCustodianLogAnalyzerはモック対象 | ログ解析の詳細動作は検証しない | log_analyzer/の個別テスト仕様書で対応 |
| 2 | check_execution_statusの複数ポリシー同時テストは限定的 | 実際の環境では数十ポリシーの場合がある | 結合テストで大規模データを検証 |
| 3 | sanitize_error_messageの全正規表現パターンは代表検証 | 全10パターン×全入力パターンは網羅しない | SSAN-SEC-01で代表的5パターンを検証 |
| 4 | ReDoSテストはtime.timeモックによるシミュレーション | 実際のReDoS攻撃による1秒超過は検証しない | 正規表現パターンの安全性は別途静的解析で確認 |
| 5 | safe_read_log_fileの大容量ファイルテストは限定的 | 実際の50MBファイルは生成しない | max_sizeパラメータを小さく設定してチャンク動作を検証 |
