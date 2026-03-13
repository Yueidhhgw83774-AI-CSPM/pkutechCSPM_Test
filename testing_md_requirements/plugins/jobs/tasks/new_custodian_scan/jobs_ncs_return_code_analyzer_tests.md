# jobs/tasks/new_custodian_scan/return_code_analyzer テストケース

## 1. 概要

`return_code_analyzer.py` は Cloud Custodian の各リージョン実行結果から全体の return_code を判定し、致命的エラー・警告レベルエラー・認証エラーを適切に区別する `ReturnCodeAnalyzer` クラスを提供します。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | job_id設定、TaskLogger初期化 |
| `determine_overall_return_code` | リージョン結果リストから全体のreturn_codeを判定（0=成功, 1=致命的, 2=警告） |
| `_log_return_code_summary` | return_code判定結果のサマリーログ出力 |
| `classify_execution_status` | return_codeからステータス分類辞書を生成 |
| `_get_status_description` | return_codeから状況説明文字列を取得 |
| `_get_recommended_action` | return_codeから推奨アクション文字列を取得 |

### 1.2 カバレッジ目標: 95%

> **注記**: 外部依存が TaskLogger のみで、全メソッドが同期。分岐カバレッジを高くできる。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/return_code_analyzer.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_return_code_analyzer.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
return_code_analyzer.py ──→ TaskLogger（ログ出力のみ）
```

#### return_code の意味（Cloud Custodian仕様）

| return_code | 意味 | 全体判定 |
|-------------|------|---------|
| 0 | 完全成功 | 成功 |
| 1 | 致命的エラー（設定・スキーマエラー） | 即座に全体失敗 |
| 2 | 警告レベルエラー（権限エラー等） | 警告として継続 |
| その他 | 予期しないreturn_code | max_return_codeとして処理 |

#### 特別処理

- `error_analysis.error_type == "authentication_error"` → return_code に関係なく即座に return 1
- `return_code == 1` → 即座に return 1（ループ中断）
- 上記2つの早期リターン時は `_log_return_code_summary` は呼ばれない

#### 全メソッドが同期

pytest-asyncio は不要。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCRCA-001 | 初期化でjob_idとloggerが設定される | `job_id="test-job"` | `self.job_id == "test-job"`, `self.logger` がTaskLoggerインスタンス |
| NCRCA-002 | 全リージョン成功でreturn 0 | 3リージョン全て `return_code=0` | `== 0` |
| NCRCA-003 | 認証エラーで即座にreturn 1 | `error_type="authentication_error"` | `== 1`、ループ中断 |
| NCRCA-004 | return_code=1で即座にreturn 1 | `return_code=1` | `== 1`、ループ中断 |
| NCRCA-005 | return_code=2のみでreturn 2 | 全リージョン `return_code=2` | `== 2` |
| NCRCA-006 | 成功と警告の混在でreturn 2 | 0と2の混在 | `== 2` |
| NCRCA-007 | 予期しないreturn_codeでmaxを返す | `return_code=5` | `== 5` |
| NCRCA-008 | 空のregion_resultsでreturn 1 | `[]` | `== 1` |
| NCRCA-009 | 成功後に認証エラーで即座にreturn 1 | 1番目が成功、2番目が認証エラー | `== 1` |
| NCRCA-010 | 成功と予期しないコードの混在 | 0と3の混在 | `== 3`（max） |
| NCRCA-011 | サマリーログ：認証エラーあり | `authentication_errors=["us-east-1"]` | `logger.error` が "認証エラー" + `error_severity=critical` で呼ばれる |
| NCRCA-012 | サマリーログ：致命的エラーあり | `fatal_errors=["us-east-1"]` | `logger.error` が "致命的エラー" で呼ばれる |
| NCRCA-013 | サマリーログ：警告エラーあり | `warning_errors=["us-east-1"]` | `logger.info` が "警告レベルエラー" で呼ばれる |
| NCRCA-014 | サマリーログ：全成功 | `success_regions=["us-east-1"]` | `logger.info` が "全リージョンで成功" で呼ばれる |
| NCRCA-015 | サマリーログ：authentication_errors=None | `authentication_errors=None` | デフォルト `[]` に変換、total_regions正常計算 |
| NCRCA-016 | classify: return_code=0 → 成功分類 | `return_code=0` | `is_success=True, is_fatal=False, is_warning=False` |
| NCRCA-017 | classify: return_code=1 → 致命的分類 | `return_code=1` | `is_success=False, is_fatal=True, is_warning=False` |
| NCRCA-018 | classify: return_code=2 → 警告分類 | `return_code=2` | `is_success=False, is_fatal=False, is_warning=True` |
| NCRCA-019 | classify: 未知コード → 全てFalse | `return_code=99` | `is_success=False, is_fatal=False, is_warning=False` |
| NCRCA-020 | _get_status_description: 既知コード | 0, 1, 2 | 対応する日本語文字列 |
| NCRCA-021 | _get_status_description: 未知コード | `42` | `"予期しないreturn_code: 42"` |
| NCRCA-022 | _get_recommended_action: 既知コード | 0, 1, 2 | 対応する日本語文字列 |
| NCRCA-023 | _get_recommended_action: 未知コード | `42` | `"予期しない状況のため、ログを詳細に確認してください"` |
| NCRCA-024 | サマリーログ：認証+致命的エラー両方で認証優先 | 両方のリスト非空 | `logger.error` が "認証エラー" で呼ばれ、"致命的エラー" は出ない |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_return_code_analyzer.py
import pytest
from unittest.mock import patch, MagicMock


class TestReturnCodeAnalyzerInit:
    """ReturnCodeAnalyzer.__init__ のテスト"""

    @patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger")
    def test_init_sets_job_id_and_logger(self, mock_logger_cls):
        """NCRCA-001: 初期化でjob_idとloggerが設定される"""
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger_cls.return_value = mock_logger_instance

        # Act
        from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
        analyzer = ReturnCodeAnalyzer("test-job-123")

        # Assert
        assert analyzer.job_id == "test-job-123"
        mock_logger_cls.assert_called_once_with("test-job-123", "ReturnCodeAnalyzer")
        assert analyzer.logger is mock_logger_instance
```

### 2.2 determine_overall_return_code テスト

```python
class TestDetermineOverallReturnCode:
    """determine_overall_return_code の分岐テスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用アナライザー（TaskLoggerモック済み）"""
        with patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
            return ReturnCodeAnalyzer("test-job")

    def test_all_success_returns_zero(self, analyzer):
        """NCRCA-002: 全リージョン成功でreturn 0

        return_code_analyzer.py:82-85 の return_code == 0 分岐を全リージョンでカバー。
        ループ完了後 L92-96 で _log_return_code_summary が呼ばれ max_return_code=0 を返す。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 0},
            {"region": "us-west-2", "return_code": 0},
            {"region": "ap-northeast-1", "return_code": 0},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 0

    def test_authentication_error_returns_one_immediately(self, analyzer):
        """NCRCA-003: 認証エラーで即座にreturn 1

        return_code_analyzer.py:65-68 の authentication_error 分岐をカバー。
        return 1 で即座にループ中断。_log_return_code_summary は呼ばれない。
        """
        # Arrange
        region_results = [
            {
                "region": "us-east-1",
                "return_code": 2,
                "error_analysis": {"error_type": "authentication_error"},
            },
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 1
        # 認証エラーは return_code の値に関係なく即座に 1 を返す
        analyzer.logger.error.assert_called()

    def test_fatal_error_returns_one_immediately(self, analyzer):
        """NCRCA-004: return_code=1で即座にreturn 1

        return_code_analyzer.py:70-74 の return_code == 1 分岐をカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 1},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 1
        analyzer.logger.error.assert_called()

    def test_warning_only_returns_two(self, analyzer):
        """NCRCA-005: return_code=2のみでreturn 2

        return_code_analyzer.py:76-80 の return_code == 2 分岐をカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 2},
            {"region": "us-west-2", "return_code": 2},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 2

    def test_mixed_success_and_warning_returns_two(self, analyzer):
        """NCRCA-006: 成功と警告の混在でreturn 2

        return_code_analyzer.py:76-85 の return_code == 2 と return_code == 0 の混在をカバー。
        ループ完了後 max_return_code=2 が返る。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 0},
            {"region": "us-west-2", "return_code": 2},
            {"region": "ap-northeast-1", "return_code": 0},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 2

    def test_unexpected_return_code_returns_max(self, analyzer):
        """NCRCA-007: 予期しないreturn_codeでmaxを返す

        return_code_analyzer.py:86-89 の else 分岐をカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 5},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 5
        analyzer.logger.warning.assert_called()

    def test_empty_results_returns_one(self, analyzer):
        """NCRCA-008: 空のregion_resultsでreturn 1

        return_code_analyzer.py:49-51 の空チェック分岐をカバー。
        """
        # Arrange / Act
        result = analyzer.determine_overall_return_code([])

        # Assert
        assert result == 1
        analyzer.logger.warning.assert_called_once()

    def test_success_then_auth_error_returns_one(self, analyzer):
        """NCRCA-009: 成功後に認証エラーで即座にreturn 1

        1番目のリージョンは成功処理されるが、2番目の認証エラーで即座に return 1。
        3番目のリージョンは処理されない。
        return_code_analyzer.py:65-68 の早期リターンにより _log_return_code_summary は呼ばれない。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 0},
            {
                "region": "us-west-2",
                "return_code": 0,
                "error_analysis": {"error_type": "authentication_error"},
            },
            {"region": "ap-northeast-1", "return_code": 0},
        ]

        # _log_return_code_summary の呼び出し監視
        with patch.object(analyzer, '_log_return_code_summary') as mock_summary:
            # Act
            result = analyzer.determine_overall_return_code(region_results)

            # Assert
            assert result == 1
            # 早期リターンのため _log_return_code_summary は呼ばれない
            mock_summary.assert_not_called()

    def test_mixed_success_and_unexpected_returns_max(self, analyzer):
        """NCRCA-010: 成功と予期しないコードの混在

        return_code_analyzer.py:82-89 の return_code == 0 と else 分岐の混在をカバー。
        max(0, 3) = 3 が返る。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 0},
            {"region": "us-west-2", "return_code": 3},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 3
```

### 2.3 _log_return_code_summary テスト

```python
class TestLogReturnCodeSummary:
    """_log_return_code_summary の分岐テスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用アナライザー"""
        with patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
            return ReturnCodeAnalyzer("test-job")

    def test_authentication_errors_log(self, analyzer):
        """NCRCA-011: サマリーログ：認証エラーあり

        return_code_analyzer.py:111-117 の authentication_errors 分岐をカバー。
        error_severity="critical" がコンテキストに含まれること。
        """
        # Arrange / Act
        analyzer._log_return_code_summary(
            fatal_errors=[],
            warning_errors=[],
            success_regions=[],
            final_return_code=1,
            authentication_errors=["us-east-1"],
        )

        # Assert
        analyzer.logger.error.assert_called_once()
        call_args = analyzer.logger.error.call_args
        assert "認証エラー" in call_args[0][0]
        context = call_args[1]["context"]
        assert context["error_severity"] == "critical"
        assert context["authentication_error_regions"] == ["us-east-1"]
        assert context["total_regions"] == 1

    def test_fatal_errors_log_direct_call(self, analyzer):
        """NCRCA-012: サマリーログ：致命的エラーあり（直接呼び出し専用）

        return_code_analyzer.py:118-123 の fatal_errors 分岐をカバー。
        authentication_errors が空で fatal_errors が存在するケース。
        注意: determine_overall_return_code 経由では発生しない（既知の制限 #2）。
        分岐カバレッジ確保のため直接呼び出しでテスト。
        """
        # Arrange / Act
        analyzer._log_return_code_summary(
            fatal_errors=["us-east-1"],
            warning_errors=[],
            success_regions=["us-west-2"],
            final_return_code=1,
            authentication_errors=[],
        )

        # Assert
        analyzer.logger.error.assert_called_once()
        call_args = analyzer.logger.error.call_args
        assert "致命的エラー" in call_args[0][0]
        context = call_args[1]["context"]
        assert context["fatal_error_regions"] == ["us-east-1"]
        assert context["total_regions"] == 2

    def test_warning_errors_log(self, analyzer):
        """NCRCA-013: サマリーログ：警告エラーあり

        return_code_analyzer.py:124-130 の warning_errors 分岐をカバー。
        """
        # Arrange / Act
        analyzer._log_return_code_summary(
            fatal_errors=[],
            warning_errors=["us-east-1"],
            success_regions=["us-west-2"],
            final_return_code=2,
            authentication_errors=[],
        )

        # Assert
        analyzer.logger.info.assert_called_once()
        call_args = analyzer.logger.info.call_args
        assert "警告レベルエラー" in call_args[0][0]
        context = call_args[1]["context"]
        assert context["warning_regions"] == ["us-east-1"]
        assert context["success_regions"] == ["us-west-2"]
        assert context["total_regions"] == 2

    def test_all_success_log(self, analyzer):
        """NCRCA-014: サマリーログ：全成功

        return_code_analyzer.py:131-136 の else 分岐をカバー。
        """
        # Arrange / Act
        analyzer._log_return_code_summary(
            fatal_errors=[],
            warning_errors=[],
            success_regions=["us-east-1", "us-west-2"],
            final_return_code=0,
            authentication_errors=[],
        )

        # Assert
        analyzer.logger.info.assert_called_once()
        call_args = analyzer.logger.info.call_args
        assert "全リージョンで成功" in call_args[0][0]
        context = call_args[1]["context"]
        assert context["successful_regions"] == ["us-east-1", "us-west-2"]
        assert context["total_regions"] == 2

    def test_none_authentication_errors_defaults_to_empty_list(self, analyzer):
        """NCRCA-015: サマリーログ：authentication_errors=None

        return_code_analyzer.py:108 の `authentication_errors = authentication_errors or []`
        による None → [] 変換をカバー。total_regions が正常に計算されること。
        """
        # Arrange / Act
        analyzer._log_return_code_summary(
            fatal_errors=[],
            warning_errors=[],
            success_regions=["us-east-1"],
            final_return_code=0,
            authentication_errors=None,
        )

        # Assert
        analyzer.logger.info.assert_called_once()
        call_args = analyzer.logger.info.call_args
        context = call_args[1]["context"]
        # None が [] に変換されるため、total_regions = 0 + 0 + 1 + 0 = 1
        assert context["total_regions"] == 1

    def test_auth_and_fatal_errors_prioritizes_auth(self, analyzer):
        """NCRCA-024: サマリーログ：認証+致命的エラー両方で認証エラー優先

        return_code_analyzer.py:111 の if authentication_errors 分岐が
        elif fatal_errors (L118) より優先されることを検証。
        直接呼び出し専用テスト。
        """
        # Arrange / Act
        analyzer._log_return_code_summary(
            fatal_errors=["us-west-2"],
            warning_errors=[],
            success_regions=[],
            final_return_code=1,
            authentication_errors=["us-east-1"],
        )

        # Assert
        analyzer.logger.error.assert_called_once()
        call_args = analyzer.logger.error.call_args
        assert "認証エラー" in call_args[0][0]
        # 致命的エラーのメッセージではないことを確認
        assert "致命的エラーが発生したリージョン" not in call_args[0][0]
        context = call_args[1]["context"]
        assert context["error_severity"] == "critical"
        assert context["total_regions"] == 2
```

### 2.4 classify_execution_status テスト

```python
class TestClassifyExecutionStatus:
    """classify_execution_status のテスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用アナライザー"""
        with patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
            return ReturnCodeAnalyzer("test-job")

    def test_classify_success(self, analyzer):
        """NCRCA-016: classify: return_code=0 → 成功分類

        return_code_analyzer.py:148-155 のis_success=True, is_fatal=False, is_warning=Falseをカバー。
        """
        # Arrange / Act
        result = analyzer.classify_execution_status(0)

        # Assert
        assert result["return_code"] == 0
        assert result["is_success"] is True
        assert result["is_fatal"] is False
        assert result["is_warning"] is False
        assert result["status_description"] == "完全成功"
        assert result["recommended_action"] == "特に対処は必要ありません"

    def test_classify_fatal(self, analyzer):
        """NCRCA-017: classify: return_code=1 → 致命的分類

        return_code_analyzer.py:148-155 の return_code == 1 ケースをカバー。
        """
        # Arrange / Act
        result = analyzer.classify_execution_status(1)

        # Assert
        assert result["return_code"] == 1
        assert result["is_success"] is False
        assert result["is_fatal"] is True
        assert result["is_warning"] is False
        assert result["status_description"] == "致命的エラー（設定・スキーマエラー）"
        assert result["recommended_action"] == "ポリシー設定またはスキーマを確認してください"

    def test_classify_warning(self, analyzer):
        """NCRCA-018: classify: return_code=2 → 警告分類

        return_code_analyzer.py:148-155 の return_code == 2 ケースをカバー。
        """
        # Arrange / Act
        result = analyzer.classify_execution_status(2)

        # Assert
        assert result["return_code"] == 2
        assert result["is_success"] is False
        assert result["is_fatal"] is False
        assert result["is_warning"] is True
        assert result["status_description"] == "警告レベルエラー（権限エラー・部分的失敗）"
        assert result["recommended_action"] == "権限設定を確認するか、警告として許容してください"

    def test_classify_unknown_code(self, analyzer):
        """NCRCA-019: classify: 未知コード → 全てFalse

        return_code_analyzer.py:150-152 で 0/1/2 以外は全て False。
        _get_status_description, _get_recommended_action のデフォルト値が使われる。
        """
        # Arrange / Act
        result = analyzer.classify_execution_status(99)

        # Assert
        assert result["return_code"] == 99
        assert result["is_success"] is False
        assert result["is_fatal"] is False
        assert result["is_warning"] is False
        assert "予期しないreturn_code: 99" in result["status_description"]
        assert "ログを詳細に確認" in result["recommended_action"]
```

### 2.5 _get_status_description / _get_recommended_action テスト

```python
class TestStatusDescriptionAndAction:
    """_get_status_description / _get_recommended_action のテスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用アナライザー"""
        with patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
            return ReturnCodeAnalyzer("test-job")

    @pytest.mark.parametrize("code, expected", [
        (0, "完全成功"),
        (1, "致命的エラー（設定・スキーマエラー）"),
        (2, "警告レベルエラー（権限エラー・部分的失敗）"),
    ])
    def test_get_status_description_known_codes(self, analyzer, code, expected):
        """NCRCA-020: _get_status_description: 既知コード

        return_code_analyzer.py:161-165 の status_map 各エントリをカバー。
        """
        # Arrange / Act
        result = analyzer._get_status_description(code)

        # Assert
        assert result == expected

    def test_get_status_description_unknown_code(self, analyzer):
        """NCRCA-021: _get_status_description: 未知コード

        return_code_analyzer.py:166 の .get() デフォルト分岐をカバー。
        """
        # Arrange / Act
        result = analyzer._get_status_description(42)

        # Assert
        assert result == "予期しないreturn_code: 42"

    @pytest.mark.parametrize("code, expected", [
        (0, "特に対処は必要ありません"),
        (1, "ポリシー設定またはスキーマを確認してください"),
        (2, "権限設定を確認するか、警告として許容してください"),
    ])
    def test_get_recommended_action_known_codes(self, analyzer, code, expected):
        """NCRCA-022: _get_recommended_action: 既知コード

        return_code_analyzer.py:170-174 の action_map 各エントリをカバー。
        """
        # Arrange / Act
        result = analyzer._get_recommended_action(code)

        # Assert
        assert result == expected

    def test_get_recommended_action_unknown_code(self, analyzer):
        """NCRCA-023: _get_recommended_action: 未知コード

        return_code_analyzer.py:175 の .get() デフォルト分岐をカバー。
        """
        # Arrange / Act
        result = analyzer._get_recommended_action(42)

        # Assert
        assert result == "予期しない状況のため、ログを詳細に確認してください"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCRCA-E01 | regionキー欠落で"unknown"にフォールバック | `{"return_code": 0}` | region="unknown"として処理、return 0 |
| NCRCA-E02 | return_codeキー欠落でデフォルト0 | `{"region": "us-east-1"}` | return_code=0として処理、return 0 |
| NCRCA-E03 | error_analysisキー欠落で空辞書 | `{"region": "us-east-1", "return_code": 2}` | 認証エラー判定されず警告として処理、return 2 |

### 3.1 入力キー欠落テスト

```python
class TestReturnCodeAnalyzerErrors:
    """異常入力に対するフォールバック動作のテスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用アナライザー"""
        with patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
            return ReturnCodeAnalyzer("test-job")

    def test_missing_region_key_defaults_to_unknown(self, analyzer):
        """NCRCA-E01: regionキー欠落で"unknown"にフォールバック

        return_code_analyzer.py:60 の `result.get("region", "unknown")` をカバー。
        """
        # Arrange
        region_results = [{"return_code": 0}]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 0
        # L85: f"リージョン {region} は成功 (return_code=0)" の region が "unknown"
        analyzer.logger.info.assert_called()
        log_message = analyzer.logger.info.call_args_list[0][0][0]
        assert "リージョン unknown は成功" in log_message

    def test_missing_return_code_defaults_to_zero(self, analyzer):
        """NCRCA-E02: return_codeキー欠落でデフォルト0

        return_code_analyzer.py:61 の `result.get("return_code", 0)` をカバー。
        """
        # Arrange
        region_results = [{"region": "us-east-1"}]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        assert result == 0

    def test_missing_error_analysis_defaults_to_empty_dict(self, analyzer):
        """NCRCA-E03: error_analysisキー欠落で空辞書

        return_code_analyzer.py:62 の `result.get("error_analysis", {})` をカバー。
        error_analysis が {} の場合、.get("error_type") は None となり
        L65 の authentication_error 判定に入らない。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 2},
        ]

        # Act
        result = analyzer.determine_overall_return_code(region_results)

        # Assert
        # 認証エラーではなく通常の warning として処理される
        assert result == 2
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCRCA-SEC-01 | 認証エラーで残りリージョンの処理が停止 | 3リージョン、2番目に認証エラー | 3番目は処理されない |
| NCRCA-SEC-02 | 致命的エラーで残りリージョンの処理が停止 | 3リージョン、2番目にreturn_code=1 | 3番目は処理されない |
| NCRCA-SEC-03 | ログコンテキストに機密情報が含まれない | 各分岐のログ出力 | region名・return_code・カウントのみ |

### 4.1 セキュリティテスト

```python
@pytest.mark.security
class TestReturnCodeAnalyzerSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def analyzer(self):
        """テスト用アナライザー"""
        with patch("app.jobs.tasks.new_custodian_scan.return_code_analyzer.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.return_code_analyzer import ReturnCodeAnalyzer
            return ReturnCodeAnalyzer("test-job")

    def test_auth_error_stops_processing_remaining_regions(self, analyzer):
        """NCRCA-SEC-01: 認証エラーで残りリージョンの処理が停止

        認証エラー発生時に即座に return 1 し、後続リージョンの処理を行わない。
        これにより、無効な認証情報での追加リクエストを防止する。
        return_code_analyzer.py:65-68 の早期リターンをカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 0},
            {
                "region": "us-west-2",
                "return_code": 0,
                "error_analysis": {"error_type": "authentication_error"},
            },
            {"region": "ap-northeast-1", "return_code": 0},
        ]

        with patch.object(analyzer, '_log_return_code_summary') as mock_summary:
            # Act
            result = analyzer.determine_overall_return_code(region_results)

            # Assert
            assert result == 1
            # us-east-1 の info + us-west-2 の error のみ。ap-northeast-1 の info は無い。
            assert analyzer.logger.info.call_count == 1  # us-east-1 の成功ログのみ
            assert analyzer.logger.error.call_count == 1  # us-west-2 の認証エラーのみ
            # 早期リターンのため _log_return_code_summary は呼ばれない
            mock_summary.assert_not_called()

    def test_fatal_error_stops_processing_remaining_regions(self, analyzer):
        """NCRCA-SEC-02: 致命的エラーで残りリージョンの処理が停止

        return_code=1 発生時に即座に return 1 し、後続リージョンの処理を行わない。
        return_code_analyzer.py:70-74 の早期リターンをカバー。
        """
        # Arrange
        region_results = [
            {"region": "us-east-1", "return_code": 0},
            {"region": "us-west-2", "return_code": 1},
            {"region": "ap-northeast-1", "return_code": 0},
        ]

        with patch.object(analyzer, '_log_return_code_summary') as mock_summary:
            # Act
            result = analyzer.determine_overall_return_code(region_results)

            # Assert
            assert result == 1
            # us-east-1 の info + us-west-2 の error のみ
            assert analyzer.logger.info.call_count == 1
            assert analyzer.logger.error.call_count == 1
            # 早期リターンのため _log_return_code_summary は呼ばれない
            mock_summary.assert_not_called()

    def test_log_context_contains_no_credentials(self, analyzer):
        """NCRCA-SEC-03: ログコンテキストに機密情報が含まれない

        _log_return_code_summary のログコンテキストが
        リージョン名・return_code・カウント等の安全な情報のみを含むことを検証。
        """
        # Arrange
        sensitive_keywords = ["password", "secret", "token", "key", "credential", "accessKey"]

        # Act
        analyzer._log_return_code_summary(
            fatal_errors=[],
            warning_errors=["us-east-1"],
            success_regions=["us-west-2"],
            final_return_code=2,
            authentication_errors=[],
        )

        # Assert
        call_args = analyzer.logger.info.call_args
        context = call_args[1]["context"]
        # コンテキストのキーと値に機密情報キーワードが含まれないこと
        for key in context:
            for keyword in sensitive_keywords:
                assert keyword not in key.lower(), f"コンテキストキー '{key}' に機密キーワード '{keyword}' が含まれる"
        for value in context.values():
            # 文字列値の検証
            if isinstance(value, str):
                for keyword in sensitive_keywords:
                    assert keyword not in value.lower(), f"コンテキスト値 '{value}' に機密キーワード '{keyword}' が含まれる"
            # リスト型値の検証（リージョン名リスト等）
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        for keyword in sensitive_keywords:
                            assert keyword not in item.lower(), f"リスト内の値 '{item}' に機密キーワード '{keyword}' が含まれる"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------:|--------:|
| `reset_return_code_analyzer_module` | テスト間のモジュール状態リセット | function | Yes |
| `analyzer` | TaskLoggerモック済みアナライザーインスタンス（各テストクラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加
import sys
import pytest


@pytest.fixture(autouse=True)
def reset_return_code_analyzer_module():
    """テストごとにモジュールのグローバル状態をリセット

    ReturnCodeAnalyzer 自体にグローバル状態はないが、
    import キャッシュの一貫性を保証するためリセットする。
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.jobs")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# return_code_analyzer テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_return_code_analyzer.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_return_code_analyzer.py::TestDetermineOverallReturnCode -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_return_code_analyzer.py \
  --cov=app.jobs.tasks.new_custodian_scan.return_code_analyzer \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_return_code_analyzer.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|-----:|--------|
| 正常系 | 24 | NCRCA-001 〜 NCRCA-024 |
| 異常系 | 3 | NCRCA-E01 〜 NCRCA-E03 |
| セキュリティ | 3 | NCRCA-SEC-01 〜 NCRCA-SEC-03 |
| **合計** | **30** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|-----:|
| `TestReturnCodeAnalyzerInit` | NCRCA-001 | 1 |
| `TestDetermineOverallReturnCode` | NCRCA-002〜NCRCA-010 | 9 |
| `TestLogReturnCodeSummary` | NCRCA-011〜NCRCA-015, NCRCA-024 | 6 |
| `TestClassifyExecutionStatus` | NCRCA-016〜NCRCA-019 | 4 |
| `TestStatusDescriptionAndAction` | NCRCA-020〜NCRCA-023 | 4 |
| `TestReturnCodeAnalyzerErrors` | NCRCA-E01〜NCRCA-E03 | 3 |
| `TestReturnCodeAnalyzerSecurity` | NCRCA-SEC-01〜NCRCA-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> `ReturnCodeAnalyzer` は外部依存が `TaskLogger` のみで、全メソッドが同期のため、
> モック設計がシンプルで全テストが通る見込みです。

### 注意事項

- `@pytest.mark.security` マーカーを `pyproject.toml` に登録する必要あり
- `@pytest.mark.parametrize` を NCRCA-020, NCRCA-022 で使用（既知コード3パターン）
- 全メソッドが同期のため `pytest-asyncio` は不要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `determine_overall_return_code` の早期リターンにより `_log_return_code_summary` が呼ばれないケースがある | 認証エラー・致命的エラー時のサマリーログが出力されない | `_log_return_code_summary` は直接呼び出しでテスト。統合テストで補完可能 |
| 2 | `_log_return_code_summary` に fatal_errors が渡されるケースは `determine_overall_return_code` 経由では発生しない | 直接呼び出しテスト（NCRCA-012）でカバーするが、実運用での呼び出し経路ではない | 将来リファクタリングで _log_return_code_summary の呼び出しタイミングが変更される可能性を考慮し、テストは維持 |
| 3 | `_get_status_description` / `_get_recommended_action` はプライベートメソッドだが分岐カバレッジのため直接テストする | テストがプライベートAPIに依存 | `classify_execution_status` 経由のテスト（NCRCA-016〜019）でも間接的にカバー済み |
