# jobs/tasks/file_processing テストケース

## 1. 概要

`app/jobs/tasks/file_processing.py` は、ファイル処理タスクの実装クラス `FileProcessingTask` を定義します。`BaseTask` を継承し、入力検証・AI前処理（`ai_pretreatment`）実行・結果整理の一連のファイル処理フローを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `FileProcessingTask.__init__` | job_id設定、TaskLogger・StatusTracker初期化 |
| `_execute_task` | メインタスク実行（入力検証→AI前処理→結果集計） |
| `_validate_inputs` | filename, text_content, target_clouds, output_langの入力検証 |
| `_process_file_content` | AI前処理実行（カテゴリ取得→ai_pretreatment呼出→空結果チェック） |
| `run_file_processing_task` | レガシー互換ラッパー関数 |

### 1.2 カバレッジ目標: 90%

> **注記**: 156行の中規模クラス。AI前処理（`ai_pretreatment`）は外部依存のためモックで検証。入力検証の5分岐を網羅的にテストする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/file_processing.py` |
| テストコード | `test/unit/jobs/tasks/test_file_processing.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
file_processing.py ──→ base_task.BaseTask（親クラス）
                   ──→ common.error_handling.ValidationError, ProcessingError
                   ──→ common.logging.TaskLogger
                   ──→ common.status_tracking.StatusTracker
                   ──→ core.categories.get_available_categories_for_prompt
                   ──→ core.config.settings（settings.DEBUG_MAX_ITEMS）
                   ──→ doc_reader_plugin.ai_pretreatment.ai_pretreatment
```

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `_validate_inputs` | L88 | `not filename` | ValidationError("ファイル名が指定されていません") |
| `_validate_inputs` | L91 | `not text_content` | ValidationError("テキストコンテンツが空です") |
| `_validate_inputs` | L94 | `not target_clouds` | ValidationError("対象クラウドが指定されていません") |
| `_validate_inputs` | L97 | `not isinstance(target_clouds, list)` | ValidationError("対象クラウドはリストである必要があります") |
| `_validate_inputs` | L100 | `not output_lang` | ValidationError("出力言語が設定されていません") |
| `_process_file_content` | L127 | `not structured_results` | ProcessingError("AI前処理が空の結果を返しました") |
| `_process_file_content` | L132 | except Exception | ProcessingError("AI前処理に失敗しました: ...") |
| `_execute_task` | L54 | `"error" not in r`（リスト内包表記で成功件数カウント） | successful_count算出 |

#### モジュールレベルの条件分岐

```python
# L11-15: ai_pretreatment のインポート（ImportError時はプレースホルダー）
try:
    from ...doc_reader_plugin.ai_pretreatment import ai_pretreatment
except ImportError:
    print("ERROR: ai_pretreatment not found! Using placeholder.")
```

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| FPROC-001 | __init__でTaskLoggerとStatusTracker初期化 | job_id="test-fp-001" | logger, status_tracker属性が正しく設定 |
| FPROC-002 | _execute_task全成功パス | 有効な全パラメータ | message, main_payload, summary_dataを含む辞書 |
| FPROC-003 | _execute_taskで部分的にerror含む結果 | AI結果に"error"含むアイテムあり | successful_countが正確にカウント |
| FPROC-004 | _execute_taskでend_page=None | end_page未指定 | page_rangeが{"start": 1, "end": None}辞書 |
| FPROC-005 | _execute_taskで全結果にerrorキー | 全AI結果に"error"含む | successful_count=0、messageに"0 件完了" |
| FPROC-006 | _validate_inputs全項目正常 | 全入力値が正常 | 例外なし（正常終了） |
| FPROC-007 | _process_file_contentで正常結果 | ai_pretreatmentが結果返却 | structured_resultsが返される |
| FPROC-008 | run_file_processing_taskレガシーラッパー | 全パラメータ指定 | FileProcessingTask.executeが呼ばれる |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/test_file_processing.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestFileProcessingTaskInit:
    """FileProcessingTask初期化テスト"""

    def test_init_sets_logger_and_status_tracker(self):
        """FPROC-001: __init__でTaskLoggerとStatusTracker初期化

        file_processing.py:21-24 の初期化処理を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.file_processing.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.tasks.file_processing.StatusTracker") as mock_tracker_cls:
            from app.jobs.tasks.file_processing import FileProcessingTask
            task = FileProcessingTask("test-fp-001")

        # Assert
        assert task.job_id == "test-fp-001"
        mock_logger_cls.assert_called_once_with("test-fp-001", "FileProcessing")
        mock_tracker_cls.assert_called_once_with("test-fp-001")
```

### 2.2 _execute_task テスト

```python
class TestExecuteTask:
    """_execute_taskメインフローテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.file_processing.TaskLogger"), \
             patch("app.jobs.tasks.file_processing.StatusTracker"):
            from app.jobs.tasks.file_processing import FileProcessingTask
            return FileProcessingTask("test-fp-exec")

    @pytest.mark.asyncio
    async def test_execute_task_full_success(self, task):
        """FPROC-002: _execute_task全成功パス

        file_processing.py:26-78 のメインフロー全体を検証。
        全AI結果が成功の場合、successful_count=total_chunksとなる。
        """
        # Arrange
        mock_results = [
            {"title": "推奨事項1", "content": "内容1"},
            {"title": "推奨事項2", "content": "内容2"},
        ]
        task._process_file_content = AsyncMock(return_value=mock_results)

        # Act
        result = await task._execute_task(
            filename="test.pdf",
            text_content="テスト文書の内容",
            target_clouds=["aws"],
            start_page_from_arg=1,
            end_page_from_arg=10,
            output_lang="jp",
        )

        # Assert
        assert result["message"] == "'test.pdf'の推奨事項の構造化が 2 件完了しました。"
        assert result["main_payload"] == mock_results
        assert result["summary_data"]["successfully_structured_chunks"] == 2
        assert result["summary_data"]["total_chunks"] == 2
        assert result["summary_data"]["page_range"] == {"start": 1, "end": 10}

    @pytest.mark.asyncio
    async def test_execute_task_with_partial_errors(self, task):
        """FPROC-003: _execute_taskで部分的にerror含む結果

        file_processing.py:54 のリスト内包表記を検証。
        "error"キーを含むアイテムはsuccessful_countに含まれない。
        """
        # Arrange
        mock_results = [
            {"title": "推奨事項1", "content": "内容1"},
            {"error": "解析失敗", "title": "推奨事項2"},
            {"title": "推奨事項3", "content": "内容3"},
        ]
        task._process_file_content = AsyncMock(return_value=mock_results)

        # Act
        result = await task._execute_task(
            filename="test.pdf",
            text_content="テスト文書の内容",
            target_clouds=["aws"],
            start_page_from_arg=1,
            end_page_from_arg=5,
            output_lang="jp",
        )

        # Assert
        assert result["summary_data"]["successfully_structured_chunks"] == 2
        assert result["summary_data"]["total_chunks"] == 3

    @pytest.mark.asyncio
    async def test_execute_task_end_page_none(self, task):
        """FPROC-004: _execute_taskでend_page=None時のpage_range

        file_processing.py:43 のf-string書式を検証。
        end_page=Noneの場合、page_rangeが{"start": 1, "end": None}辞書になる。
        """
        # Arrange
        mock_results = [{"title": "推奨事項1", "content": "内容1"}]
        task._process_file_content = AsyncMock(return_value=mock_results)

        # Act
        result = await task._execute_task(
            filename="test.pdf",
            text_content="テスト文書の内容",
            target_clouds=["aws"],
            start_page_from_arg=1,
            end_page_from_arg=None,
            output_lang="jp",
        )

        # Assert（summary_dataのpage_rangeを検証）
        assert result["summary_data"]["page_range"] == {"start": 1, "end": None}

    @pytest.mark.asyncio
    async def test_execute_task_all_results_have_errors(self, task):
        """FPROC-005: _execute_taskで全結果にerrorキー

        file_processing.py:54 のリスト内包表記を検証。
        全アイテムに"error"キーが含まれる場合、successful_count=0となる。
        """
        # Arrange
        mock_results = [
            {"error": "解析失敗1", "title": "推奨事項1"},
            {"error": "解析失敗2", "title": "推奨事項2"},
        ]
        task._process_file_content = AsyncMock(return_value=mock_results)

        # Act
        result = await task._execute_task(
            filename="test.pdf",
            text_content="テスト文書の内容",
            target_clouds=["aws"],
            start_page_from_arg=1,
            end_page_from_arg=5,
            output_lang="jp",
        )

        # Assert
        assert result["summary_data"]["successfully_structured_chunks"] == 0
        assert result["summary_data"]["total_chunks"] == 2
        assert "0 件完了" in result["message"]
```

### 2.3 _validate_inputs テスト

```python
class TestValidateInputs:
    """_validate_inputs入力検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.file_processing.TaskLogger"), \
             patch("app.jobs.tasks.file_processing.StatusTracker"):
            from app.jobs.tasks.file_processing import FileProcessingTask
            return FileProcessingTask("test-fp-valid")

    def test_validate_inputs_all_valid(self, task):
        """FPROC-006: _validate_inputs全項目正常

        file_processing.py:80-101 の全検証を通過するケース。
        """
        # Arrange & Act（例外が発生しなければ成功）
        task._validate_inputs("test.pdf", "テスト内容", ["aws", "azure"], "jp")

        # Assert（例外が発生しないこと自体が検証）
```

### 2.4 _process_file_content テスト

```python
class TestProcessFileContent:
    """_process_file_contentテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.file_processing.TaskLogger"), \
             patch("app.jobs.tasks.file_processing.StatusTracker"):
            from app.jobs.tasks.file_processing import FileProcessingTask
            return FileProcessingTask("test-fp-process")

    @pytest.mark.asyncio
    async def test_process_file_content_success(self, task):
        """FPROC-007: _process_file_contentで正常結果

        file_processing.py:103-130 の正常パスを検証。
        ai_pretreatmentが結果を返す場合、そのまま返却される。
        """
        # Arrange
        expected_results = [{"title": "推奨事項1"}]

        with patch("app.jobs.tasks.file_processing.get_available_categories_for_prompt",
                   return_value="カテゴリ情報") as mock_categories, \
             patch("app.jobs.tasks.file_processing.ai_pretreatment",
                   new_callable=AsyncMock, return_value=expected_results) as mock_ai, \
             patch("app.jobs.tasks.file_processing.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 0

            # Act
            result = await task._process_file_content("テスト内容", ["aws"], "jp")

        # Assert
        assert result == expected_results
        mock_categories.assert_called_once()
        mock_ai.assert_called_once_with(
            "テスト内容", ["aws"], "カテゴリ情報",
            "test-fp-process", "jp", 0, True
        )
```

### 2.5 レガシーラッパー関数テスト

```python
class TestRunFileProcessingTask:
    """run_file_processing_taskレガシーラッパーテスト"""

    @pytest.mark.asyncio
    async def test_legacy_wrapper_creates_task_and_executes(self):
        """FPROC-008: run_file_processing_taskレガシーラッパー

        file_processing.py:138-156 のラッパー関数を検証。
        FileProcessingTaskを生成しexecuteを呼び出すことを確認。
        """
        # Arrange
        with patch("app.jobs.tasks.file_processing.FileProcessingTask") as mock_task_cls:
            mock_task_instance = MagicMock()
            mock_task_instance.execute = AsyncMock()
            mock_task_cls.return_value = mock_task_instance

            # Act
            from app.jobs.tasks.file_processing import run_file_processing_task
            await run_file_processing_task(
                job_id="test-legacy",
                filename="test.pdf",
                text_content="テスト内容",
                target_clouds=["aws"],
                start_page_from_arg=1,
                end_page_from_arg=10,
                output_lang="jp",
            )

        # Assert
        mock_task_cls.assert_called_once_with("test-legacy")
        mock_task_instance.execute.assert_called_once_with(
            filename="test.pdf",
            text_content="テスト内容",
            target_clouds=["aws"],
            start_page_from_arg=1,
            end_page_from_arg=10,
            output_lang="jp",
        )
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| FPROC-E01 | filename空でValidationError | filename=None | ValidationError("ファイル名が指定されていません") |
| FPROC-E02 | text_content空でValidationError | text_content="" | ValidationError("テキストコンテンツが空です") |
| FPROC-E03 | target_clouds空でValidationError | target_clouds=None | ValidationError("対象クラウドが指定されていません") |
| FPROC-E04 | target_cloudsがリストでない場合 | target_clouds="aws" | ValidationError("対象クラウドはリストである必要があります") |
| FPROC-E05 | output_lang空でValidationError | output_lang="" | ValidationError("出力言語が設定されていません") |
| FPROC-E06 | ai_pretreatmentが空結果返却 | ai_pretreatment → [] | ProcessingError("AI前処理に失敗しました: AI前処理が空の結果を返しました") |
| FPROC-E07 | ai_pretreatmentが例外発生 | ai_pretreatment → Exception | ProcessingError("AI前処理に失敗しました: ...") |

### 3.1 _validate_inputs 異常系

```python
class TestValidateInputsErrors:
    """_validate_inputs入力検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.file_processing.TaskLogger"), \
             patch("app.jobs.tasks.file_processing.StatusTracker"):
            from app.jobs.tasks.file_processing import FileProcessingTask
            return FileProcessingTask("test-fp-err")

    def test_filename_empty_raises_validation_error(self, task):
        """FPROC-E01: filename空でValidationError

        file_processing.py:88 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="ファイル名が指定されていません"):
            task._validate_inputs(None, "テスト内容", ["aws"], "jp")

    def test_text_content_empty_raises_validation_error(self, task):
        """FPROC-E02: text_content空でValidationError

        file_processing.py:91 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="テキストコンテンツが空です"):
            task._validate_inputs("test.pdf", "", ["aws"], "jp")

    def test_target_clouds_none_raises_validation_error(self, task):
        """FPROC-E03: target_clouds空でValidationError

        file_processing.py:94 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="対象クラウドが指定されていません"):
            task._validate_inputs("test.pdf", "テスト内容", None, "jp")

    def test_target_clouds_not_list_raises_validation_error(self, task):
        """FPROC-E04: target_cloudsがリストでない場合ValidationError

        file_processing.py:97 の分岐をカバー。
        target_cloudsが文字列の場合、L94のnot判定は通過するがL97のisinstance判定で失敗。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="対象クラウドはリストである必要があります"):
            task._validate_inputs("test.pdf", "テスト内容", "aws", "jp")

    def test_output_lang_empty_raises_validation_error(self, task):
        """FPROC-E05: output_lang空でValidationError

        file_processing.py:100 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="出力言語が設定されていません"):
            task._validate_inputs("test.pdf", "テスト内容", ["aws"], "")
```

### 3.2 _process_file_content 異常系

```python
class TestProcessFileContentErrors:
    """_process_file_contentエラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.file_processing.TaskLogger"), \
             patch("app.jobs.tasks.file_processing.StatusTracker"):
            from app.jobs.tasks.file_processing import FileProcessingTask
            return FileProcessingTask("test-fp-proc-err")

    @pytest.mark.asyncio
    async def test_empty_result_raises_processing_error(self, task):
        """FPROC-E06: ai_pretreatmentが空結果返却でProcessingError

        file_processing.py:127-128 の空結果チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError

        with patch("app.jobs.tasks.file_processing.get_available_categories_for_prompt",
                   return_value="カテゴリ"), \
             patch("app.jobs.tasks.file_processing.ai_pretreatment",
                   new_callable=AsyncMock, return_value=[]), \
             patch("app.jobs.tasks.file_processing.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 0

            # Act & Assert
            # L128のProcessingErrorはL132のexceptでキャッチされ再ラップされる
            with pytest.raises(ProcessingError, match="AI前処理に失敗しました: AI前処理が空の結果を返しました"):
                await task._process_file_content("テスト内容", ["aws"], "jp")

    @pytest.mark.asyncio
    async def test_ai_pretreatment_exception_raises_processing_error(self, task):
        """FPROC-E07: ai_pretreatmentが例外発生でProcessingError

        file_processing.py:132-134 のexceptブロックをカバー。
        元の例外メッセージがProcessingErrorにラップされる。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError

        with patch("app.jobs.tasks.file_processing.get_available_categories_for_prompt",
                   return_value="カテゴリ"), \
             patch("app.jobs.tasks.file_processing.ai_pretreatment",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("API接続タイムアウト")), \
             patch("app.jobs.tasks.file_processing.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 0

            # Act & Assert
            with pytest.raises(ProcessingError, match="AI前処理に失敗しました"):
                await task._process_file_content("テスト内容", ["aws"], "jp")
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| FPROC-SEC-01 | ValidationErrorメッセージにフィールド値が漏洩しない | 不正入力各種 | エラーメッセージにフィールド名のみ含まれ値は含まれない |
| FPROC-SEC-02 | AI前処理例外のProcessingErrorラップ確認 | ai_pretreatmentが内部URL含む例外 | ProcessingErrorにラップされログにも詳細記録 |
| FPROC-SEC-03 | _validate_inputsがNone/不正型を確実に拒否 | 各パラメータにNone/不正型 | 対応するValidationErrorが必ず発生 |

```python
@pytest.mark.security
class TestFileProcessingSecurity:
    """FileProcessingTaskセキュリティテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.file_processing.TaskLogger"), \
             patch("app.jobs.tasks.file_processing.StatusTracker"):
            from app.jobs.tasks.file_processing import FileProcessingTask
            return FileProcessingTask("test-fp-sec")

    def test_validation_error_messages_do_not_leak_field_values(self, task):
        """FPROC-SEC-01: ValidationErrorメッセージにフィールド値が漏洩しない

        file_processing.py:88-101 の各ValidationErrorを検証。
        エラーメッセージに入力値そのもの（特に大きなテキストや機密情報）が
        含まれないことを確認する回帰テスト。

        注: ValidationErrorの第3引数（value）はエラーオブジェクトに格納されるが、
        str(error) のメッセージ部分には含まれないことを検証。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        sensitive_content = "機密情報を含む大量のテキストコンテンツ" * 100

        # Act & Assert（text_contentが空でない不正な組み合わせではなく、空の場合をテスト）
        # filenameが空の場合のエラーメッセージを検証
        with pytest.raises(ValidationError) as exc_info:
            task._validate_inputs(None, sensitive_content, ["aws"], "jp")

        error_msg = str(exc_info.value)
        assert sensitive_content not in error_msg, \
            "機密テキストコンテンツがエラーメッセージに漏洩しています"

    @pytest.mark.asyncio
    async def test_ai_exception_wrapped_without_raw_stacktrace(self, task):
        """FPROC-SEC-02: AI前処理例外のProcessingErrorラップ確認

        file_processing.py:132-134 の例外ラッピングを検証。
        内部の例外メッセージはProcessingErrorのメッセージに含まれる（str(e)が付加）。
        またログにもエラー詳細が記録される。元の例外型（Exception）から
        ProcessingErrorへの変換が正しく行われることを確認。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        internal_error_msg = "ConnectionError: https://api.internal.example.com:8443/v1/chat"

        with patch("app.jobs.tasks.file_processing.get_available_categories_for_prompt",
                   return_value="カテゴリ"), \
             patch("app.jobs.tasks.file_processing.ai_pretreatment",
                   new_callable=AsyncMock,
                   side_effect=Exception(internal_error_msg)), \
             patch("app.jobs.tasks.file_processing.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 0

            # Act & Assert
            with pytest.raises(ProcessingError) as exc_info:
                await task._process_file_content("テスト内容", ["aws"], "jp")

        # ProcessingErrorにラップされていることを確認
        error_msg = str(exc_info.value)
        assert "AI前処理に失敗しました" in error_msg
        # ログにエラー詳細が記録されていることを確認
        task.logger.error.assert_called_once()
        log_call = str(task.logger.error.call_args)
        assert internal_error_msg in log_call

    def test_validate_inputs_rejects_none_and_invalid_types(self, task):
        """FPROC-SEC-03: _validate_inputsがNone/不正型を確実に拒否

        file_processing.py:80-101 の全検証分岐を網羅的に確認。
        各パラメータにNoneや不正な型を与えた場合、必ずValidationErrorが発生し
        後続処理（AI前処理）に到達しないことを保証。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（各パラメータのNullチェック）
        invalid_cases = [
            (None, "テスト", ["aws"], "jp", "ファイル名"),
            ("test.pdf", None, ["aws"], "jp", "テキストコンテンツ"),
            ("test.pdf", "テスト", None, "jp", "対象クラウド"),
            ("test.pdf", "テスト", "aws", "jp", "リスト"),  # 文字列（not list）
            ("test.pdf", "テスト", ["aws"], None, "出力言語"),
        ]

        for filename, text, clouds, lang, expected_msg_part in invalid_cases:
            with pytest.raises(ValidationError) as exc_info:
                task._validate_inputs(filename, text, clouds, lang)
            assert expected_msg_part in str(exc_info.value), \
                f"入力({filename}, {type(clouds).__name__}, {lang})で期待メッセージ'{expected_msg_part}'が見つかりません"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_file_processing_module` | テスト間のstatus_managerグローバル状態リセット | function | Yes |
| `task` | 各テストクラス内のFileProcessingTaskインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/conftest.py に追加
# （既存のreset_base_task_moduleフィクスチャと共存）
import pytest


@pytest.fixture(autouse=True)
def reset_file_processing_module():
    """テストごとにstatus_managerのグローバル状態をリセット

    status_manager.job_statusesはモジュールレベルの辞書であり、
    テスト間で状態が共有されるのを防止する。
    """
    from app.jobs.status_manager import job_statuses
    job_statuses.clear()
    yield
    job_statuses.clear()
```

---

## 6. テスト実行例

```bash
# file_processing関連テストのみ実行
pytest test/unit/jobs/tasks/test_file_processing.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/test_file_processing.py::TestExecuteTask -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/test_file_processing.py --cov=app.jobs.tasks.file_processing --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/jobs/tasks/test_file_processing.py -m "security" -v

# 非同期テスト実行（pytest-asyncioが必要）
# pyproject.toml: asyncio_mode = "auto"
pytest test/unit/jobs/tasks/test_file_processing.py -v --asyncio-mode=auto
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 8 | FPROC-001 〜 FPROC-008 |
| 異常系 | 7 | FPROC-E01 〜 FPROC-E07 |
| セキュリティ | 3 | FPROC-SEC-01 〜 FPROC-SEC-03 |
| **合計** | **18** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestFileProcessingTaskInit` | FPROC-001 | 1 |
| `TestExecuteTask` | FPROC-002〜FPROC-005 | 4 |
| `TestValidateInputs` | FPROC-006 | 1 |
| `TestProcessFileContent` | FPROC-007 | 1 |
| `TestRunFileProcessingTask` | FPROC-008 | 1 |
| `TestValidateInputsErrors` | FPROC-E01〜FPROC-E05 | 5 |
| `TestProcessFileContentErrors` | FPROC-E06〜FPROC-E07 | 2 |
| `TestFileProcessingSecurity` | FPROC-SEC-01〜FPROC-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- `pytest-asyncio` が必要（async テストメソッドあり）
- `pyproject.toml` に `asyncio_mode = "auto"` 設定推奨
- `@pytest.mark.security` マーカーの登録が必要
- `ai_pretreatment` のモックは `new_callable=AsyncMock` を使用（async関数のため）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `ai_pretreatment` は外部LLM依存 | 実際のAI応答は単体テストで検証不可 | AsyncMockで返却値を制御し、呼び出し引数と結果ハンドリングを検証 |
| 2 | モジュールレベルのtry/except ImportError（L11-15）はテスト困難 | `ai_pretreatment` が存在しない環境のフォールバックは検証しない | インポートエラーのテストはモジュール再読込が必要で副作用が大きいため対象外 |
| 3 | `settings.DEBUG_MAX_ITEMS` はグローバル設定 | テスト間で設定値が影響し合う可能性 | `patch("app.jobs.tasks.file_processing.settings")` でモック化 |
