# jobs/tasks/new_custodian_scan/error_analyzer テストケース

## 1. 概要

`error_analyzer.py` は Cloud Custodian の実行時エラーを分析し、構造化されたエラー情報を抽出するモジュール。`CustodianErrorAnalyzer` クラスが stderr 出力からエラー種別・影響ポリシー・対処メッセージを判定し、日本語のユーザーフレンドリーなエラーメッセージを生成する。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | job_id と TaskLogger を設定 |
| `analyze_execution_result` | リージョン実行結果から成功/エラーを判定し分析結果辞書を返す |
| `extract_custodian_error` | stderr 行リストから構造化エラー情報を抽出（6種別の elif チェーン） |
| `_analyze_permission_error` | 権限・認証エラーの詳細分析（AuthFailure/PolicyException は認証エラーとして分離） |
| `_analyze_resource_error` | 無効なリソースタイプエラーの詳細分析（正規表現でリソース名抽出） |
| `_analyze_filter_error` | フィルターエラーの詳細分析 |
| `_analyze_action_error` | アクションエラーの詳細分析 |
| `_analyze_network_error` | ネットワーク接続エラーの詳細分析 |
| `_analyze_general_error` | 一般的実行エラーの詳細分析（200文字切り詰め） |
| `extract_policy_names_from_error` | エラーテキストから3種の正規表現パターンでポリシー名を抽出（重複排除） |

### 1.2 カバレッジ目標: 90%

> **注記**: 純粋なロジックモジュール（外部接続なし、非同期なし）。分岐が多いため（6種のエラー分類 + 権限エラー内の4分岐 + 正規表現マッチ有無）、分岐カバレッジに重点を置く。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/error_analyzer.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_error_analyzer.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
error_analyzer.py ──→ TaskLogger（ログ出力のみ）
                  ──→ re（正規表現・標準ライブラリ、モック不要）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| 初期化テスト | TaskLogger をモックして直接インスタンス化 |
| 分析結果テスト | region_result 辞書を直接構築して呼び出し |
| エラー分類テスト | stderr 行リストを直接構築して `extract_custodian_error` を呼び出し |
| 詳細分析テスト | エラーテキスト文字列を直接渡して内部メソッドをテスト |
| ポリシー抽出テスト | パターン含むテキストで正規表現の結果を検証 |

#### 主要分岐（extract_custodian_error L112-144）

1. `UnauthorizedOperation` / `AccessDenied` / `AuthFailure` / `metric:PolicyException` → `_analyze_permission_error`
2. `'Invalid resource:'` → `_analyze_resource_error`
3. `'filter'` + `'error'`（大文字小文字不問） → `_analyze_filter_error`
4. `'action'` + `'error'`（大文字小文字不問） → `_analyze_action_error`
5. `'ConnectionError'` / `'TimeoutError'` → `_analyze_network_error`
6. else → `_analyze_general_error`

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCEA-001 | 初期化で job_id と logger が設定される | `job_id="test-job"` | 属性設定 |
| NCEA-002 | analyze_execution_result 成功パス | return_code=0 | is_success=True, logger.info |
| NCEA-003 | analyze_execution_result 認証エラー→logger.error | AuthFailure stderr | logger.error 呼び出し |
| NCEA-004 | analyze_execution_result 非認証エラー→logger.info | Invalid resource stderr | logger.info 呼び出し |
| NCEA-005 | analyze_execution_result フラグ判定 | return_code=0,1,2,3 | is_fatal/is_warning/has_execution_error |
| NCEA-006 | extract_custodian_error 空 stderr | 空リスト | デフォルト値 |
| NCEA-007 | extract_custodian_error UnauthorizedOperation | UnauthorizedOperation 含む stderr | permission_error |
| NCEA-008 | extract_custodian_error AccessDenied | AccessDenied 含む stderr | permission_error |
| NCEA-009 | extract_custodian_error AuthFailure + 追加ログ | AuthFailure 含む stderr | authentication_error + logger.error |
| NCEA-010 | extract_custodian_error PolicyException + 追加ログ | PolicyException 含む stderr | authentication_error + logger.error |
| NCEA-011 | extract_custodian_error Invalid resource | Invalid resource 含む stderr | invalid_resource |
| NCEA-012 | extract_custodian_error filter error | filter+error 含む stderr | filter_error |
| NCEA-013 | extract_custodian_error action error | action+error 含む stderr | action_error |
| NCEA-014 | extract_custodian_error network error | ConnectionError 含む stderr | network_error |
| NCEA-015 | extract_custodian_error general error | 他パターンに該当しない stderr | execution_error |
| NCEA-016 | _analyze_permission_error AuthFailure→authentication_error | AuthFailure テキスト | 認証エラーメッセージ |
| NCEA-017 | _analyze_permission_error UnauthorizedOperation 正規表現マッチ | 権限名含むテキスト | アクション名含むメッセージ |
| NCEA-018 | _analyze_permission_error UnauthorizedOperation 正規表現不一致 | 権限名なしテキスト | デフォルトメッセージ |
| NCEA-019 | _analyze_permission_error AccessDenied | AccessDenied テキスト | アクセス拒否メッセージ |
| NCEA-025 | _analyze_permission_error PolicyException | PolicyException テキスト | authentication_error + ポリシー抽出 |
| NCEA-020 | _analyze_resource_error 正規表現マッチ | Invalid resource: ec2.instance | リソース名含むメッセージ |
| NCEA-021 | _analyze_resource_error 正規表現不一致 | Invalid resource（名前なし） | "不明" |
| NCEA-022 | _analyze_general_error 短いテキスト | 100文字テキスト | 切り詰めなし |
| NCEA-023 | _analyze_general_error 長いテキスト（200文字超） | 300文字テキスト | "..." 付き切り詰め |
| NCEA-024 | extract_policy_names_from_error 複数パターン+重複排除 | 3パターン含むテキスト | 重複排除済みリスト |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_error_analyzer.py
import pytest
from unittest.mock import MagicMock


class TestCustodianErrorAnalyzerInit:
    """CustodianErrorAnalyzer.__init__ のテスト"""

    def test_init_sets_job_id_and_logger(self):
        """NCEA-001: 初期化で job_id と logger が設定される

        error_analyzer.py:23-31 の __init__ をカバー。
        TaskLogger はモジュール内部で生成されるため、
        job_id の設定と logger 属性の存在を検証する。
        """
        # Arrange
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer

        # Act
        analyzer = CustodianErrorAnalyzer("test-job-123")

        # Assert
        assert analyzer.job_id == "test-job-123"
        assert analyzer.logger is not None
```

### 2.2 analyze_execution_result テスト

```python
class TestAnalyzeExecutionResult:
    """analyze_execution_result の分岐テスト"""

    @pytest.fixture
    def analyzer(self):
        """TaskLogger をモックした CustodianErrorAnalyzer インスタンス

        注: analyzer.logger は全メソッドで共有される MagicMock。
        analyze_execution_result → extract_custodian_error の呼び出しチェーンでは
        logger の call_count が累積されるため、テストで考慮が必要。
        """
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_success_path_return_code_zero(self, analyzer):
        """NCEA-002: return_code=0 で成功パス

        error_analyzer.py:81-86 の else（成功時）分岐をカバー。
        """
        # Arrange
        region_result = {
            "return_code": 0,
            "stderr_output": [],
            "region": "us-east-1"
        }

        # Act
        result = analyzer.analyze_execution_result(region_result)

        # Assert
        assert result["is_success"] is True
        assert result["error_type"] is None
        assert result["error_message"] is None
        assert result["region"] == "us-east-1"
        analyzer.logger.info.assert_called_once()
        assert "エラーなし" in analyzer.logger.info.call_args[0][0]

    def test_authentication_error_triggers_logger_error(self, analyzer):
        """NCEA-003: 認証エラー検出時に logger.error が呼ばれる

        error_analyzer.py:68-74 の authentication_error 分岐をカバー。
        extract_custodian_error が authentication_error を返す場合、
        analyze_execution_result でも logger.error が呼ばれる。
        """
        # Arrange
        region_result = {
            "return_code": 2,
            "stderr_output": ["AuthFailure: Authentication failed"],
            "region": "ap-northeast-1"
        }

        # Act
        result = analyzer.analyze_execution_result(region_result)

        # Assert
        assert result["error_type"] == "authentication_error"
        # 呼び出しフロー:
        #   1. analyze_execution_result → extract_custodian_error 内 L119 で logger.error
        #   2. analyze_execution_result L69 で logger.error（authentication_error 判定後）
        assert analyzer.logger.error.call_count == 2
        # analyze_execution_result のログにリージョン名が含まれる
        error_calls = [call[0][0] for call in analyzer.logger.error.call_args_list]
        assert any("ap-northeast-1" in msg for msg in error_calls)

    def test_non_auth_error_triggers_logger_info(self, analyzer):
        """NCEA-004: 非認証エラーで logger.info が呼ばれる

        error_analyzer.py:75-80 の else（非認証エラー）分岐をカバー。
        """
        # Arrange
        region_result = {
            "return_code": 1,
            "stderr_output": ["Invalid resource: ec2.badtype"],
            "region": "us-west-2"
        }

        # Act
        result = analyzer.analyze_execution_result(region_result)

        # Assert
        assert result["error_type"] == "invalid_resource"
        analyzer.logger.info.assert_called_once()
        assert "us-west-2" in analyzer.logger.info.call_args[0][0]

    @pytest.mark.parametrize("return_code, expected_success, expected_fatal, expected_warning, expected_has_error", [
        (0, True, False, False, False),
        (1, False, True, False, True),
        (2, False, False, True, True),
        (3, False, False, False, True),
    ])
    def test_flags_by_return_code(self, analyzer, return_code, expected_success,
                                  expected_fatal, expected_warning, expected_has_error):
        """NCEA-005: return_code に応じたフラグ判定

        error_analyzer.py:47-57 の analysis 辞書のフラグ値をカバー。
        return_code=3 は is_fatal=False, is_warning=False だが has_execution_error=True。
        """
        # Arrange
        region_result = {
            "return_code": return_code,
            "stderr_output": ["some error"] if return_code != 0 else [],
            "region": "us-east-1"
        }

        # Act
        result = analyzer.analyze_execution_result(region_result)

        # Assert
        assert result["is_success"] == expected_success
        assert result["is_fatal"] == expected_fatal
        assert result["is_warning"] == expected_warning
        assert result["has_execution_error"] == expected_has_error
```

### 2.3 extract_custodian_error テスト

```python
class TestExtractCustodianError:
    """extract_custodian_error の6種エラー分類テスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_empty_stderr_returns_defaults(self, analyzer):
        """NCEA-006: 空の stderr でデフォルト値を返す

        error_analyzer.py:108 の `if not error_text:` 分岐をカバー。
        """
        # Arrange
        stderr_lines = []

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "unknown"
        assert result["message"] == "予期しないエラーが発生しました"
        assert result["policies"] == []

    def test_unauthorized_operation_returns_permission_error(self, analyzer):
        """NCEA-007: UnauthorizedOperation → permission_error

        error_analyzer.py:112 の最初の if 条件をカバー。
        入力に "UnauthorizedOperation" 文字列が必須（条件判定はキーワード検索）。
        """
        # Arrange
        stderr_lines = [
            "UnauthorizedOperation: You are not authorized to perform: ec2:DescribeInstances policy:test-policy"
        ]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "permission_error"

    def test_access_denied_returns_permission_error(self, analyzer):
        """NCEA-008: AccessDenied → permission_error

        error_analyzer.py:112 の AccessDenied 条件をカバー。
        """
        # Arrange
        stderr_lines = ["AccessDenied: User is not authorized"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "permission_error"

    def test_auth_failure_returns_authentication_error_with_logging(self, analyzer):
        """NCEA-009: AuthFailure → authentication_error + logger.error

        error_analyzer.py:112 の AuthFailure 条件と
        L117-124 の追加ログ出力（auth_type="AuthFailure"）をカバー。
        """
        # Arrange
        stderr_lines = ["AuthFailure: Invalid credentials"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "authentication_error"
        analyzer.logger.error.assert_called_once()
        log_context = analyzer.logger.error.call_args[1]["context"]
        assert log_context["auth_error_type"] == "AuthFailure"
        assert log_context["has_auth_failure"] is True

    def test_policy_exception_returns_authentication_error_with_logging(self, analyzer):
        """NCEA-010: metric:PolicyException → authentication_error + logger.error

        error_analyzer.py:113 の PolicyException 条件と
        L118 の auth_type="PolicyException" 分岐をカバー。
        """
        # Arrange
        stderr_lines = ["metric:PolicyException policy:my-policy"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "authentication_error"
        analyzer.logger.error.assert_called_once()
        log_context = analyzer.logger.error.call_args[1]["context"]
        assert log_context["auth_error_type"] == "PolicyException"

    def test_invalid_resource_returns_invalid_resource(self, analyzer):
        """NCEA-011: 'Invalid resource:' → invalid_resource

        error_analyzer.py:127 の elif 分岐をカバー。
        """
        # Arrange
        stderr_lines = ["Invalid resource: ec2.badtype"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "invalid_resource"

    def test_filter_error_returns_filter_error(self, analyzer):
        """NCEA-012: filter + error → filter_error

        error_analyzer.py:131 の elif 分岐をカバー（大文字小文字不問）。
        """
        # Arrange
        stderr_lines = ["Filter Error: invalid configuration"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "filter_error"

    def test_action_error_returns_action_error(self, analyzer):
        """NCEA-013: action + error → action_error

        error_analyzer.py:135 の elif 分岐をカバー（大文字小文字不問）。
        """
        # Arrange
        stderr_lines = ["Action Error: failed to execute"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "action_error"

    @pytest.mark.parametrize("error_keyword", ["ConnectionError", "TimeoutError"])
    def test_network_error_returns_network_error(self, analyzer, error_keyword):
        """NCEA-014: ConnectionError/TimeoutError → network_error

        error_analyzer.py:139 の elif 分岐をカバー。
        ConnectionError と TimeoutError の両方を検証する。
        """
        # Arrange
        stderr_lines = [f"{error_keyword}: Failed to connect to AWS endpoint"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "network_error"

    def test_general_error_returns_execution_error(self, analyzer):
        """NCEA-015: 他パターンに該当しない stderr → execution_error

        error_analyzer.py:143-144 の else 分岐をカバー。
        """
        # Arrange
        stderr_lines = ["Some unexpected internal error occurred"]

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "execution_error"
```

### 2.4 _analyze_permission_error テスト

```python
class TestAnalyzePermissionError:
    """_analyze_permission_error の詳細分岐テスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_auth_failure_returns_authentication_error_message(self, analyzer):
        """NCEA-016: AuthFailure → authentication_error タイプとメッセージ

        error_analyzer.py:152-155 の AuthFailure/PolicyException 分岐をカバー。
        """
        # Arrange
        error_text = "AuthFailure: Invalid credentials"

        # Act
        result = analyzer._analyze_permission_error(error_text)

        # Assert
        assert result["error_type"] == "authentication_error"
        assert "認証失敗" in result["message"]
        assert "アクセスキーとシークレットキー" in result["message"]

    def test_unauthorized_operation_with_regex_extracts_action(self, analyzer):
        """NCEA-017: UnauthorizedOperation で正規表現マッチ → アクション名抽出

        error_analyzer.py:164-169 の regex マッチ成功分岐をカバー。
        """
        # Arrange
        error_text = "UnauthorizedOperation: You are not authorized to perform: ec2:DescribeInstances"

        # Act
        result = analyzer._analyze_permission_error(error_text)

        # Assert
        assert result["error_type"] == "permission_error"
        assert "ec2:DescribeInstances" in result["message"]
        assert "アクションが許可されていません" in result["message"]

    def test_unauthorized_operation_without_regex_returns_default(self, analyzer):
        """NCEA-018: UnauthorizedOperation で正規表現不一致 → デフォルトメッセージ

        error_analyzer.py:170-171 の regex マッチ失敗分岐をカバー。
        """
        # Arrange
        error_text = "UnauthorizedOperation: generic error"

        # Act
        result = analyzer._analyze_permission_error(error_text)

        # Assert
        assert result["error_type"] == "permission_error"
        assert result["message"] == "権限不足: 必要なアクセス権限がありません"

    def test_access_denied_returns_specific_message(self, analyzer):
        """NCEA-019: AccessDenied → アクセス拒否メッセージ

        error_analyzer.py:172-173 の AccessDenied 分岐をカバー。
        """
        # Arrange
        error_text = "AccessDenied: Cannot access resource"

        # Act
        result = analyzer._analyze_permission_error(error_text)

        # Assert
        assert result["error_type"] == "permission_error"
        assert "アクセス拒否" in result["message"]

    def test_policy_exception_returns_authentication_error_message(self, analyzer):
        """NCEA-025: metric:PolicyException → authentication_error タイプとメッセージ

        error_analyzer.py:152-155 の PolicyException 分岐をカバー。
        NCEA-016 は AuthFailure のみ検証するため、PolicyException を単独で検証する。
        """
        # Arrange
        error_text = "metric:PolicyException policy:my-policy"

        # Act
        result = analyzer._analyze_permission_error(error_text)

        # Assert
        assert result["error_type"] == "authentication_error"
        assert "認証失敗" in result["message"]
        assert result["policies"] == ["my-policy"]
```

### 2.5 _analyze_resource_error テスト

```python
class TestAnalyzeResourceError:
    """_analyze_resource_error の正規表現マッチテスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_regex_match_extracts_resource_type(self, analyzer):
        """NCEA-020: 正規表現マッチでリソースタイプを抽出

        error_analyzer.py:183-184 の `match.group(1)` 分岐をカバー。
        """
        # Arrange
        error_text = "Invalid resource: ec2.instance policy:test-policy"

        # Act
        result = analyzer._analyze_resource_error(error_text)

        # Assert
        assert result["error_type"] == "invalid_resource"
        assert "ec2.instance" in result["message"]

    def test_no_regex_match_returns_unknown(self, analyzer):
        """NCEA-021: 正規表現不一致で "不明" を返す

        error_analyzer.py:184 の `else "不明"` 分岐をカバー。
        """
        # Arrange
        error_text = "Invalid resource:"

        # Act
        result = analyzer._analyze_resource_error(error_text)

        # Assert
        assert "不明" in result["message"]
```

### 2.6 _analyze_general_error テスト

```python
class TestAnalyzeGeneralError:
    """_analyze_general_error の切り詰めテスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_short_text_no_truncation(self, analyzer):
        """NCEA-022: 200文字以下のテキストは切り詰めなし

        error_analyzer.py:219-221 の `if len(error_text) > 200` が False の場合。
        """
        # Arrange
        error_text = "短いエラーメッセージ"

        # Act
        result = analyzer._analyze_general_error(error_text)

        # Assert
        assert result["error_type"] == "execution_error"
        assert "..." not in result["message"]
        assert "短いエラーメッセージ" in result["message"]

    def test_long_text_truncated_with_ellipsis(self, analyzer):
        """NCEA-023: 200文字超のテキストは "..." 付きで切り詰め

        error_analyzer.py:220-221 の `if len(error_text) > 200` が True の場合。
        """
        # Arrange
        error_text = "A" * 300

        # Act
        result = analyzer._analyze_general_error(error_text)

        # Assert
        assert result["error_type"] == "execution_error"
        assert result["message"].endswith("...")
        # 切り詰め後のプレビュー部分は200文字以内
        # "実行エラー: " + 200文字 + "..." の形式
        assert "A" * 200 in result["message"]
```

### 2.7 extract_policy_names_from_error テスト

```python
class TestExtractPolicyNames:
    """extract_policy_names_from_error のパターンマッチテスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_multiple_patterns_with_dedup(self, analyzer):
        """NCEA-024: 3種のパターンから抽出し重複排除

        error_analyzer.py:239-251 の全パターンと list(set(...)) をカバー。
        パターン1: policy:name, パターン2: Error on policy:name,
        パターン3: policy name had errors
        """
        # Arrange
        error_text = (
            "Error on policy:alpha-policy\n"
            "policy:alpha-policy metric:error\n"
            "policy:beta-policy had issues\n"
            "policy gamma-policy had errors"
        )

        # Act
        result = analyzer.extract_policy_names_from_error(error_text)

        # Assert
        # パターン1: "alpha-policy"(2回), "beta-policy" → alpha-policy, beta-policy
        # パターン2: "alpha-policy" → alpha-policy（重複）
        # パターン3: "gamma-policy" → gamma-policy
        assert set(result) == {"alpha-policy", "beta-policy", "gamma-policy"}
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCEA-E01 | analyze_execution_result キー欠損→デフォルト値 | 空の辞書 | get() のデフォルト値使用 |
| NCEA-E02 | extract_custodian_error None 入力 | None | 空テキスト扱い |
| NCEA-E03 | extract_policy_names_from_error パターン不一致 | パターンなしテキスト | 空リスト |

### 3.1 異常系テスト

```python
class TestCustodianErrorAnalyzerErrors:
    """異常入力のテスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_missing_keys_use_defaults(self, analyzer):
        """NCEA-E01: region_result のキーが欠損している場合 get() のデフォルト値を使用

        error_analyzer.py:43-45 の get() デフォルト値をカバー。
        return_code=0, stderr_output=[], region="unknown" にフォールバック。
        """
        # Arrange
        region_result = {}

        # Act
        result = analyzer.analyze_execution_result(region_result)

        # Assert
        assert result["return_code"] == 0
        assert result["region"] == "unknown"
        assert result["is_success"] is True

    def test_none_stderr_input(self, analyzer):
        """NCEA-E02: stderr_lines が None の場合でも空テキスト扱い

        error_analyzer.py:100 の `if stderr_lines else ""` をカバー。
        None は falsy なので空文字列になる。
        """
        # Arrange
        stderr_lines = None

        # Act
        result = analyzer.extract_custodian_error(stderr_lines)

        # Assert
        assert result["error_type"] == "unknown"
        assert result["policies"] == []

    def test_no_pattern_match_returns_empty_list(self, analyzer):
        """NCEA-E03: パターンに一致しないテキストで空リストを返す

        error_analyzer.py:245-248 のループで matches が空の場合。
        """
        # Arrange
        error_text = "No policy information in this error message"

        # Act
        result = analyzer.extract_policy_names_from_error(error_text)

        # Assert
        assert result == []
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCEA-SEC-01 | _analyze_general_error が200文字で切り詰め | 大量テキスト | エラーメッセージ肥大化防止 |
| NCEA-SEC-02 | 正規表現パターンが大量入力を正常に処理できる | 長大な繰り返しテキスト | 例外なく有効な結果を返す |
| NCEA-SEC-03 | 構造化エラー経路のメッセージが日本語テンプレートで生成される | 権限・リソースエラー | テンプレート文字列のみ（一般エラーは対象外） |

### 4.1 セキュリティテスト

```python
@pytest.mark.security
class TestCustodianErrorAnalyzerSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def analyzer(self):
        from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
        instance = CustodianErrorAnalyzer("test-job")
        instance.logger = MagicMock()
        return instance

    def test_general_error_truncation_prevents_message_bloat(self, analyzer):
        """NCEA-SEC-01: _analyze_general_error が大量テキストを200文字で切り詰める

        error_analyzer.py:219-221 の切り詰め処理がエラーメッセージの
        肥大化（ログ・DB保存時のリソース消費）を防止することを検証。
        """
        # Arrange
        # 10,000文字の大量テキスト
        large_error_text = "X" * 10000

        # Act
        result = analyzer._analyze_general_error(large_error_text)

        # Assert
        # メッセージ全体（"実行エラー: " + preview + "..."）の長さを検証
        # プレビュー部分は200文字以下
        assert len(result["message"]) < 300
        assert result["message"].endswith("...")

    def test_regex_patterns_handle_large_input(self, analyzer):
        """NCEA-SEC-02: 正規表現パターンが大量入力を正常に処理できる

        error_analyzer.py:166,176,183,239-243 の正規表現が
        長大な文字列に対して例外なく完了し、有効な結果を返すことを検証。
        時間ベースの閾値判定は CI 負荷でフレークしやすいため、
        機能的な正常完了のみを検証する。
        """
        # Arrange
        # 長大な繰り返しパターン
        crafted_text = "policy:" + "a" * 10000 + " " + "policy " + "b" * 10000 + " had errors"

        # Act
        result = analyzer.extract_policy_names_from_error(crafted_text)

        # Assert
        # 例外なく完了し、リストが返ること
        assert isinstance(result, list)
        # 正規表現が意図通り抽出していること
        assert len(result) >= 1

    def test_structured_error_messages_are_user_friendly(self, analyzer):
        """NCEA-SEC-03: 構造化エラー経路のメッセージが日本語テンプレートで生成される

        error_analyzer.py:155,160,169,171,173,188 の
        _analyze_permission_error / _analyze_resource_error が返すメッセージは
        テンプレート文字列から生成されるため、内部実装詳細を含まないことを検証。

        注: _analyze_general_error (L219-225) は生の error_text を200文字まで
        そのまま含める設計のため、本テストの対象外。
        一般エラー経路のメッセージサイズ制限は NCEA-SEC-01 でカバーする。
        """
        # Arrange
        import re as re_mod
        test_cases = [
            ("AuthFailure: error", "authentication_error"),
            ("UnauthorizedOperation: error", "permission_error"),
            ("AccessDenied: error", "permission_error"),
            ("Invalid resource: ec2.bad", "invalid_resource"),
        ]
        # ひらがな・カタカナ・漢字の存在を検証する正規表現
        japanese_pattern = re_mod.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')

        for error_text, expected_type in test_cases:
            # Act
            result = analyzer._analyze_permission_error(error_text) if expected_type in (
                "authentication_error", "permission_error"
            ) else analyzer._analyze_resource_error(error_text)

            # Assert
            message = result["message"]
            assert "Traceback" not in message
            assert "File \"" not in message
            assert "/app/" not in message
            # メッセージは日本語（ユーザー向け）であること
            assert japanese_pattern.search(message), \
                f"メッセージに日本語が含まれていません: {message}"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `analyzer` | TaskLogger モック済み CustodianErrorAnalyzer インスタンス（各テストクラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加（必要に応じて）
#
# error_analyzer はモジュールレベルの状態を持たないため、
# autouse のモジュールリセットフィクスチャは不要。
# 各テストクラス内で analyzer フィクスチャを定義する。
#
# 注: analyzer フィクスチャは以下のパターンで統一:
#   from app.jobs.tasks.new_custodian_scan.error_analyzer import CustodianErrorAnalyzer
#   instance = CustodianErrorAnalyzer("test-job")
#   instance.logger = MagicMock()
#   return instance
```

---

## 6. テスト実行例

```bash
# error_analyzer テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_analyzer.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_analyzer.py::TestExtractCustodianError -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_analyzer.py \
  --cov=app.jobs.tasks.new_custodian_scan.error_analyzer \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_error_analyzer.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 25 | NCEA-001 〜 NCEA-025 |
| 異常系 | 3 | NCEA-E01 〜 NCEA-E03 |
| セキュリティ | 3 | NCEA-SEC-01 〜 NCEA-SEC-03 |
| **合計** | **31** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCustodianErrorAnalyzerInit` | NCEA-001 | 1 |
| `TestAnalyzeExecutionResult` | NCEA-002〜NCEA-005 | 4 |
| `TestExtractCustodianError` | NCEA-006〜NCEA-015 | 10 |
| `TestAnalyzePermissionError` | NCEA-016〜NCEA-019, NCEA-025 | 5 |
| `TestAnalyzeResourceError` | NCEA-020〜NCEA-021 | 2 |
| `TestAnalyzeGeneralError` | NCEA-022〜NCEA-023 | 2 |
| `TestExtractPolicyNames` | NCEA-024 | 1 |
| `TestCustodianErrorAnalyzerErrors` | NCEA-E01〜NCEA-E03 | 3 |
| `TestCustodianErrorAnalyzerSecurity` | NCEA-SEC-01〜NCEA-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> 純粋なロジックモジュールのため、外部接続のモックや非同期処理の制御が不要で安定動作が期待される。

### 注意事項

- `--strict-markers` 運用時は `@pytest.mark.security` を `pyproject.toml` に登録する必要あり
- NCEA-005 は `@pytest.mark.parametrize` を使用（4パターン分を1テストメソッドで実行）
- NCEA-014 は `@pytest.mark.parametrize` を使用（ConnectionError / TimeoutError の2パターン）
- `_analyze_permission_error` 等のプライベートメソッドを直接テストしている（分岐カバレッジのため）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `extract_custodian_error` の elif チェーンは評価順序に依存する | 複数パターンに該当する stderr の場合、最初にマッチした分類のみ適用 | テストでは各分岐を単独で検証。複合パターンのテストは統合テストで対応 |
| 2 | `_analyze_permission_error` L164-173 の `if 'UnauthorizedOperation'` / `elif 'AccessDenied'` チェーン後の暗黙 else は、`extract_custodian_error` 経由では到達しない | 呼び出し元が4キーワードのいずれかを保証するため、AuthFailure/PolicyException 以外では必ず UnauthorizedOperation か AccessDenied にマッチする。NCEA-018 が通る「正規表現不一致」分岐（L170-171）はこれとは別の分岐 | プライベートメソッド直接呼び出し時のみ到達可能。テストでは各分岐を個別に検証しており影響なし |
| 3 | `extract_policy_names_from_error` の返却順序は不定（set 変換） | ポリシー名リストの順序が実行ごとに異なる可能性がある | テストでは `set()` で比較し、順序に依存しない検証を行う |
