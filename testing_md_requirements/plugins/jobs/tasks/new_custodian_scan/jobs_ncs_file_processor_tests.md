# jobs/tasks/new_custodian_scan/file_processor テストケース

## 1. 概要

`file_processor.py` は Custodian スキャン結果のファイル読み込み・解析・分類を行う `FileProcessor` クラスを提供します。JSON/YAML/ログ/メタデータファイルを拡張子で判別し、違反件数カウントやバイナリファイル検出を含む結果辞書を構築します。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | job_id設定、TaskLogger初期化 |
| `read_detailed_scan_results` | メインエントリ：出力ディレクトリ存在確認→ファイル処理→サマリーログ |
| `_initialize_detailed_results` | 結果辞書の初期構造を生成 |
| `_process_directory_files` | os.walkで再帰的にファイルを処理（per-fileエラーハンドリング付き） |
| `_process_single_file` | 拡張子別ディスパッチ（.json/.yaml/.yml/.log/.txt/その他） |
| `_process_json_file` | JSON読み込み＋違反件数カウント→resource_files |
| `_process_yaml_file` | YAMLテキスト読み込み→policy_files |
| `_process_log_file` | ログテキスト読み込み→logs |
| `_process_metadata_file` | テキスト/バイナリファイル処理→metadata_files |
| `_count_violations` | list→len / dict+resources→len / その他→0 |
| `_log_scan_results_summary` | 処理結果サマリーのログ出力 |

### 1.2 カバレッジ目標: 90%

> **注記**: ファイルI/Oが多く、`tmp_path` フィクスチャでテスト用ファイルを作成する。os.walk の全パターン網羅は困難なため 90% を目標とする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/file_processor.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_file_processor.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
file_processor.py ──→ TaskLogger（ログ出力）
                  ──→ os.path.exists, os.walk, os.path.join, os.path.relpath, os.path.getsize
                  ──→ json.load（JSON解析）
                  ──→ open()（ファイル読み込み）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| ファイル処理テスト | `tmp_path` で実ファイル作成 |
| ディスパッチテスト | `patch.object` で処理メソッドをモック |
| 制御フローテスト | `patch` で os 関数・メソッドをモック |
| 純粋ロジックテスト | 直接呼び出し |

#### 全メソッドが同期

pytest-asyncio は不要。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCFP-001 | 初期化でjob_idとloggerが設定される | `job_id="test-job"` | `self.job_id == "test-job"`, TaskLoggerインスタンス |
| NCFP-002 | ディレクトリ内ファイルを正常に処理 | JSON+YAML+ログファイルを含むtmp_path | 各リストにファイル情報追加、violations合計 |
| NCFP-003 | 存在しないディレクトリで早期リターン | 存在しないパス | 初期構造のまま返却、warning出力 |
| NCFP-004 | ファイル処理中の例外でerrorを格納 | _process_directory_files例外 | `results["error"]`にメッセージ格納 |
| NCFP-005 | _initialize_detailed_resultsが正しい初期構造を返す | region, output_dir | 7キーの辞書 |
| NCFP-006 | ネストしたディレクトリのファイルを再帰処理 | 2階層のtmp_path | 全ファイルが処理される |
| NCFP-007 | 個別ファイルエラーで処理を継続 | 1番目がエラー、2番目が正常 | 2番目は正常処理、warning出力 |
| NCFP-008 | .jsonファイルで_process_json_fileにディスパッチ | `"data.json"` | _process_json_file呼び出し |
| NCFP-009 | .yamlファイルで_process_yaml_fileにディスパッチ | `"policy.yaml"` | _process_yaml_file呼び出し |
| NCFP-010 | .ymlファイルで_process_yaml_fileにディスパッチ | `"policy.yml"` | _process_yaml_file呼び出し |
| NCFP-011 | .logファイルで_process_log_fileにディスパッチ | `"output.log"` | _process_log_file呼び出し |
| NCFP-012 | .txtファイルで_process_log_fileにディスパッチ | `"notes.txt"` | _process_log_file呼び出し |
| NCFP-013 | その他拡張子で_process_metadata_fileにディスパッチ | `"data.bin"` | _process_metadata_file呼び出し |
| NCFP-014 | JSONファイル読み込みと違反件数カウント | リスト形式JSON | resource_filesに追加、violation_count正確 |
| NCFP-015 | YAMLファイルテキスト読み込み | YAMLファイル | policy_filesに追加 |
| NCFP-016 | ログファイルテキスト読み込み | ログファイル | logsに追加 |
| NCFP-017 | メタデータファイルテキスト読み込み | テキストファイル | metadata_filesに追加 |
| NCFP-018 | バイナリファイルでUnicodeDecodeError処理 | バイナリファイル | `"[バイナリファイル: ...]"` |
| NCFP-019 | _count_violations: list → len | 3要素リスト | `== 3` |
| NCFP-020 | _count_violations: dict+resources → len | resources 2件 | `== 2` |
| NCFP-021 | _count_violations: dict without resources → 0 | resourcesキーなし | `== 0` |
| NCFP-022 | _count_violations: その他の型 → 0 | 文字列, None | `== 0` |
| NCFP-023 | _log_scan_results_summary | 結果辞書 | logger.infoにcontext付きで呼ばれる |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_file_processor.py
import pytest
import json
import os
from unittest.mock import patch, MagicMock


class TestFileProcessorInit:
    """FileProcessor.__init__ のテスト"""

    @patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger")
    def test_init_sets_job_id_and_logger(self, mock_logger_cls):
        """NCFP-001: 初期化でjob_idとloggerが設定される

        file_processor.py:23-31 の __init__ をカバー。
        """
        # Arrange
        mock_logger_instance = MagicMock()
        mock_logger_cls.return_value = mock_logger_instance

        # Act
        from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
        processor = FileProcessor("test-job-123")

        # Assert
        assert processor.job_id == "test-job-123"
        mock_logger_cls.assert_called_once_with("test-job-123", "FileProcessor")
        assert processor.logger is mock_logger_instance
```

### 2.2 read_detailed_scan_results テスト

```python
class TestReadDetailedScanResults:
    """read_detailed_scan_results の分岐テスト"""

    @pytest.fixture
    def processor(self):
        """テスト用プロセッサー（TaskLoggerモック済み）"""
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_happy_path_with_real_files(self, processor, tmp_path):
        """NCFP-002: ディレクトリ内ファイルを正常に処理

        file_processor.py:46-54 の正常パスをカバー。
        tmp_path にJSON・YAML・ログファイルを作成し、統合的にテスト。
        """
        # Arrange
        # JSON ファイル（違反2件）
        json_file = tmp_path / "resources.json"
        json_file.write_text(json.dumps([{"id": "r1"}, {"id": "r2"}]))
        # YAML ファイル
        yaml_file = tmp_path / "policy.yaml"
        yaml_file.write_text("policies:\n  - name: test-policy")
        # ログファイル
        log_file = tmp_path / "custodian.log"
        log_file.write_text("2024-01-01 INFO: scan started")

        # Act
        result = processor.read_detailed_scan_results(str(tmp_path), "us-east-1")

        # Assert
        assert result["region"] == "us-east-1"
        assert len(result["resource_files"]) == 1
        assert result["resource_files"][0]["violation_count"] == 2
        assert len(result["policy_files"]) == 1
        assert len(result["logs"]) == 1
        assert result["total_violations"] == 2
        assert "error" not in result

    def test_nonexistent_directory_returns_initial_results(self, processor):
        """NCFP-003: 存在しないディレクトリで早期リターン

        file_processor.py:47-49 の `not os.path.exists` 分岐をカバー。
        os.path.exists をモックして環境非依存にする。
        """
        # Arrange
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.os.path.exists",
                   return_value=False):
            # Act
            result = processor.read_detailed_scan_results("/any/path", "us-east-1")

        # Assert
        assert result["region"] == "us-east-1"
        assert result["policy_files"] == []
        assert result["resource_files"] == []
        assert result["total_violations"] == 0
        processor.logger.warning.assert_called_once()
        assert "存在しません" in processor.logger.warning.call_args[0][0]

    def test_exception_stores_error_in_results(self, processor):
        """NCFP-004: ファイル処理中の例外でerrorを格納

        file_processor.py:56-58 の except Exception 分岐をカバー。
        """
        # Arrange
        with patch.object(processor, '_process_directory_files',
                          side_effect=RuntimeError("テスト例外")):
            with patch("app.jobs.tasks.new_custodian_scan.file_processor.os.path.exists",
                       return_value=True):
                # Act
                result = processor.read_detailed_scan_results("/some/dir", "us-east-1")

        # Assert
        assert result["error"] == "テスト例外"
        processor.logger.error.assert_called_once()
```

### 2.3 _initialize_detailed_results / _process_directory_files テスト

```python
class TestInitializeDetailedResults:
    """_initialize_detailed_results のテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_returns_correct_initial_structure(self, processor):
        """NCFP-005: _initialize_detailed_resultsが正しい初期構造を返す

        file_processor.py:62-72 の全キーをカバー。
        """
        # Arrange / Act
        result = processor._initialize_detailed_results("us-east-1", "/output/dir")

        # Assert
        assert result["region"] == "us-east-1"
        assert result["output_directory"] == "/output/dir"
        assert result["policy_files"] == []
        assert result["resource_files"] == []
        assert result["metadata_files"] == []
        assert result["logs"] == []
        assert result["total_violations"] == 0


class TestProcessDirectoryFiles:
    """_process_directory_files のテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_walks_nested_directories(self, processor, tmp_path):
        """NCFP-006: ネストしたディレクトリのファイルを再帰処理

        file_processor.py:76-84 の os.walk ループをカバー。
        2階層のディレクトリ構造で再帰処理を検証。
        """
        # Arrange
        # ルートに JSON
        (tmp_path / "root.json").write_text(json.dumps([]))
        # サブディレクトリに YAML
        sub_dir = tmp_path / "sub"
        sub_dir.mkdir()
        (sub_dir / "policy.yaml").write_text("name: test")

        detailed_results = processor._initialize_detailed_results("us-east-1", str(tmp_path))

        # Act
        processor._process_directory_files(str(tmp_path), detailed_results)

        # Assert
        assert len(detailed_results["resource_files"]) == 1  # root.json
        assert len(detailed_results["policy_files"]) == 1    # sub/policy.yaml

    def test_continues_on_per_file_error(self, processor, tmp_path):
        """NCFP-007: 個別ファイルエラーで処理を継続

        file_processor.py:85-87 の per-file except + continue をカバー。
        """
        # Arrange
        # 正常な JSON ファイル
        (tmp_path / "good.json").write_text(json.dumps([{"id": "r1"}]))
        # 不正な JSON ファイル（パース失敗を引き起こす）
        (tmp_path / "bad.json").write_text("{invalid json content")

        detailed_results = processor._initialize_detailed_results("us-east-1", str(tmp_path))

        # Act
        processor._process_directory_files(str(tmp_path), detailed_results)

        # Assert
        # bad.json はエラーでスキップ、good.json は正常処理
        assert len(detailed_results["resource_files"]) == 1
        processor.logger.warning.assert_called()
```

### 2.4 _process_single_file ディスパッチテスト

```python
class TestProcessSingleFile:
    """_process_single_file の拡張子別ディスパッチテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    @pytest.fixture
    def results(self):
        """テスト用の空の結果辞書"""
        return {
            "policy_files": [], "resource_files": [],
            "metadata_files": [], "logs": [], "total_violations": 0,
        }

    def test_json_dispatch(self, processor, results):
        """NCFP-008: .jsonファイルで_process_json_fileにディスパッチ

        file_processor.py:98-99 の `.json` 分岐をカバー。
        """
        # Arrange / Act / Assert
        with patch.object(processor, '_process_json_file') as mock:
            processor._process_single_file("/p/data.json", "data.json", "data.json", results)
            mock.assert_called_once_with("/p/data.json", "data.json", "data.json", results)

    def test_yaml_dispatch(self, processor, results):
        """NCFP-009: .yamlファイルで_process_yaml_fileにディスパッチ

        file_processor.py:100-101 の `.yaml` 分岐をカバー。
        """
        with patch.object(processor, '_process_yaml_file') as mock:
            processor._process_single_file("/p/policy.yaml", "policy.yaml", "policy.yaml", results)
            mock.assert_called_once()

    def test_yml_dispatch(self, processor, results):
        """NCFP-010: .ymlファイルで_process_yaml_fileにディスパッチ

        file_processor.py:100-101 の `.yml` 分岐をカバー。
        """
        with patch.object(processor, '_process_yaml_file') as mock:
            processor._process_single_file("/p/policy.yml", "policy.yml", "policy.yml", results)
            mock.assert_called_once()

    def test_log_dispatch(self, processor, results):
        """NCFP-011: .logファイルで_process_log_fileにディスパッチ

        file_processor.py:102-103 の `.log` 分岐をカバー。
        """
        with patch.object(processor, '_process_log_file') as mock:
            processor._process_single_file("/p/out.log", "out.log", "out.log", results)
            mock.assert_called_once()

    def test_txt_dispatch(self, processor, results):
        """NCFP-012: .txtファイルで_process_log_fileにディスパッチ

        file_processor.py:102-103 の `.txt` 分岐をカバー。
        """
        with patch.object(processor, '_process_log_file') as mock:
            processor._process_single_file("/p/notes.txt", "notes.txt", "notes.txt", results)
            mock.assert_called_once()

    def test_other_extension_dispatch(self, processor, results):
        """NCFP-013: その他拡張子で_process_metadata_fileにディスパッチ

        file_processor.py:104-105 の else 分岐をカバー。
        """
        with patch.object(processor, '_process_metadata_file') as mock:
            processor._process_single_file("/p/data.bin", "data.bin", "data.bin", results)
            mock.assert_called_once()
```

### 2.5 ファイル種別処理テスト

```python
class TestProcessFileTypes:
    """各ファイル種別の処理テスト（tmp_path使用）"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    @pytest.fixture
    def results(self):
        return {
            "policy_files": [], "resource_files": [],
            "metadata_files": [], "logs": [], "total_violations": 0,
        }

    def test_process_json_file(self, processor, results, tmp_path):
        """NCFP-014: JSONファイル読み込みと違反件数カウント

        file_processor.py:107-128 の _process_json_file をカバー。
        リスト形式JSONの場合、len(list) が violation_count となる。
        """
        # Arrange
        json_file = tmp_path / "resources.json"
        json_data = [{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]
        json_file.write_text(json.dumps(json_data))

        # Act
        processor._process_json_file(str(json_file), "resources.json", "resources.json", results)

        # Assert
        assert len(results["resource_files"]) == 1
        entry = results["resource_files"][0]
        assert entry["filename"] == "resources.json"
        assert entry["violation_count"] == 3
        assert entry["content"] == json_data
        assert entry["size"] > 0
        assert results["total_violations"] == 3

    def test_process_yaml_file(self, processor, results, tmp_path):
        """NCFP-015: YAMLファイルテキスト読み込み

        file_processor.py:130-145 の _process_yaml_file をカバー。
        """
        # Arrange
        yaml_file = tmp_path / "policy.yaml"
        yaml_content = "policies:\n  - name: test-policy"
        yaml_file.write_text(yaml_content)

        # Act
        processor._process_yaml_file(str(yaml_file), "policy.yaml", "policy.yaml", results)

        # Assert
        assert len(results["policy_files"]) == 1
        entry = results["policy_files"][0]
        assert entry["filename"] == "policy.yaml"
        assert entry["content"] == yaml_content
        assert entry["size"] > 0

    def test_process_log_file(self, processor, results, tmp_path):
        """NCFP-016: ログファイルテキスト読み込み

        file_processor.py:147-162 の _process_log_file をカバー。
        """
        # Arrange
        log_file = tmp_path / "custodian.log"
        log_content = "2024-01-01 INFO: scan started\n2024-01-01 INFO: scan completed"
        log_file.write_text(log_content)

        # Act
        processor._process_log_file(str(log_file), "custodian.log", "custodian.log", results)

        # Assert
        assert len(results["logs"]) == 1
        entry = results["logs"][0]
        assert entry["filename"] == "custodian.log"
        assert entry["content"] == log_content

    def test_process_metadata_file_text(self, processor, results, tmp_path):
        """NCFP-017: メタデータファイルテキスト読み込み

        file_processor.py:172-180 の try ブロック（テキスト読み込み成功）をカバー。
        """
        # Arrange
        meta_file = tmp_path / "info.dat"
        meta_content = "metadata information"
        meta_file.write_text(meta_content)

        # Act
        processor._process_metadata_file(str(meta_file), "info.dat", "info.dat", results)

        # Assert
        assert len(results["metadata_files"]) == 1
        entry = results["metadata_files"][0]
        assert entry["filename"] == "info.dat"
        assert entry["content"] == meta_content

    def test_process_metadata_file_binary(self, processor, results, tmp_path):
        """NCFP-018: バイナリファイルでUnicodeDecodeError処理

        file_processor.py:181-188 の UnicodeDecodeError except をカバー。
        バイナリデータはコンテンツとして格納されず、代わりにプレースホルダー文字列。
        """
        # Arrange
        bin_file = tmp_path / "image.png"
        bin_file.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe')

        # Act
        processor._process_metadata_file(str(bin_file), "image.png", "image.png", results)

        # Assert
        assert len(results["metadata_files"]) == 1
        entry = results["metadata_files"][0]
        assert entry["content"] == "[バイナリファイル: image.png]"
        assert entry["size"] > 0
```

### 2.6 _count_violations テスト

```python
class TestCountViolations:
    """_count_violations の分岐テスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_list_returns_length(self, processor):
        """NCFP-019: _count_violations: list → len

        file_processor.py:192-193 の isinstance list 分岐をカバー。
        """
        # Arrange / Act / Assert
        assert processor._count_violations([{"id": "1"}, {"id": "2"}, {"id": "3"}]) == 3

    def test_dict_with_resources_returns_resources_length(self, processor):
        """NCFP-020: _count_violations: dict+resources → len

        file_processor.py:194-195 の dict + 'resources' 分岐をカバー。
        """
        # Arrange / Act / Assert
        assert processor._count_violations({"resources": ["r1", "r2"]}) == 2

    def test_dict_without_resources_returns_zero(self, processor):
        """NCFP-021: _count_violations: dict without resources → 0

        file_processor.py:194 の 'resources' not in file_content で else へ。
        """
        # Arrange / Act / Assert
        assert processor._count_violations({"data": "value"}) == 0

    def test_other_type_returns_zero(self, processor):
        """NCFP-022: _count_violations: その他の型 → 0

        file_processor.py:196-197 の else 分岐をカバー。
        文字列、None、整数 すべて 0 を返す。
        """
        # Arrange / Act / Assert
        assert processor._count_violations("string") == 0
        assert processor._count_violations(None) == 0
        assert processor._count_violations(42) == 0
```

### 2.7 _log_scan_results_summary テスト

```python
class TestLogScanResultsSummary:
    """_log_scan_results_summary のテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_logs_summary_with_correct_context(self, processor):
        """NCFP-023: _log_scan_results_summaryがcontext付きでログ出力

        file_processor.py:199-207 の logger.info 呼び出しをカバー。
        """
        # Arrange
        detailed_results = {
            "policy_files": [{"filename": "p.yaml"}],
            "resource_files": [{"filename": "r.json"}, {"filename": "r2.json"}],
            "metadata_files": [],
            "logs": [{"filename": "c.log"}],
            "total_violations": 5,
        }

        # Act
        processor._log_scan_results_summary("us-east-1", detailed_results)

        # Assert
        processor.logger.info.assert_called_once()
        call_args = processor.logger.info.call_args
        assert "us-east-1" in call_args[0][0]
        context = call_args[1]["context"]
        assert context["policy_files"] == 1
        assert context["resource_files"] == 2
        assert context["metadata_files"] == 0
        assert context["logs"] == 1
        assert context["total_violations"] == 5
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCFP-E01 | 不正JSONファイルでJSONDecodeError | `{invalid json` | per-fileハンドラでキャッチ、warning |
| NCFP-E02 | ファイル読み込み中のPermissionError | アクセス不可ファイル | per-fileハンドラでキャッチ、warning |
| NCFP-E03 | os.walkがPermissionErrorを送出 | アクセス不可ディレクトリ | read_detailed_scan_results の except でキャッチ |

### 3.1 異常系テスト

```python
class TestFileProcessorErrors:
    """異常入力・エラー状態のテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_malformed_json_caught_by_per_file_handler(self, processor, tmp_path):
        """NCFP-E01: 不正JSONファイルでJSONDecodeError

        file_processor.py:115-116 の json.load が JSONDecodeError を送出し、
        L85-87 の per-file ハンドラでキャッチされる。
        """
        # Arrange
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{not valid json!!!")
        results = {
            "policy_files": [], "resource_files": [],
            "metadata_files": [], "logs": [], "total_violations": 0,
        }

        # Act
        processor._process_directory_files(str(tmp_path), results)

        # Assert
        # JSONDecodeError が per-file ハンドラでキャッチされ、resource_files は空
        assert len(results["resource_files"]) == 0
        processor.logger.warning.assert_called()

    def test_permission_error_on_file_caught(self, processor):
        """NCFP-E02: ファイル読み込み中のPermissionError

        file_processor.py:85-87 の per-file except をカバー。
        _process_single_file が PermissionError を送出するケース。
        """
        # Arrange
        results = {
            "policy_files": [], "resource_files": [],
            "metadata_files": [], "logs": [], "total_violations": 0,
        }
        with patch.object(processor, '_process_single_file',
                          side_effect=PermissionError("アクセス拒否")):
            with patch("app.jobs.tasks.new_custodian_scan.file_processor.os.walk",
                       return_value=[("/dir", [], ["file.json"])]):
                # Act
                processor._process_directory_files("/dir", results)

        # Assert
        processor.logger.warning.assert_called()
        assert "アクセス拒否" in processor.logger.warning.call_args[0][0]

    def test_os_walk_permission_error_caught_by_main_handler(self, processor):
        """NCFP-E03: os.walkがPermissionErrorを送出

        file_processor.py:56-58 の read_detailed_scan_results の
        メイン except ハンドラでキャッチされるケース。
        os.walk 自体がエラーを送出し、_process_directory_files を通じて伝播。
        """
        # Arrange
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.os.path.exists",
                   return_value=True):
            with patch("app.jobs.tasks.new_custodian_scan.file_processor.os.walk",
                       side_effect=PermissionError("ディレクトリアクセス拒否")):
                # Act
                result = processor.read_detailed_scan_results("/protected/dir", "us-east-1")

        # Assert
        assert "error" in result
        assert "ディレクトリアクセス拒否" in result["error"]
        processor.logger.error.assert_called()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------:|
| NCFP-SEC-01 | バイナリファイルの生データが結果に含まれない | バイナリファイル | contentは文字列プレースホルダーのみ |
| NCFP-SEC-02 | 個別ファイルエラーが他ファイルの処理を妨げない | 複数ファイル（一部エラー） | エラー以外のファイルは正常処理 |
| NCFP-SEC-03 | 例外情報にスタックトレースが含まれない | 例外発生 | results["error"]はstr(e)のみ |

### 4.1 セキュリティテスト

```python
@pytest.mark.security
class TestFileProcessorSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.file_processor.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.file_processor import FileProcessor
            return FileProcessor("test-job")

    def test_binary_content_not_leaked_as_raw_data(self, processor, tmp_path):
        """NCFP-SEC-01: バイナリファイルの生データが結果に含まれない

        file_processor.py:181-188 の UnicodeDecodeError ハンドラにより、
        バイナリデータが results のコンテンツとして漏洩しないことを検証。
        """
        # Arrange
        bin_file = tmp_path / "secret.bin"
        secret_bytes = b'\x00\x01SECRET_KEY_DATA\xff\xfe\xfd'
        bin_file.write_bytes(secret_bytes)
        results = {
            "policy_files": [], "resource_files": [],
            "metadata_files": [], "logs": [], "total_violations": 0,
        }

        # Act
        processor._process_metadata_file(str(bin_file), "secret.bin", "secret.bin", results)

        # Assert
        entry = results["metadata_files"][0]
        # バイナリの生データが content に含まれないこと
        assert isinstance(entry["content"], str)
        assert entry["content"] == "[バイナリファイル: secret.bin]"
        assert "SECRET_KEY_DATA" not in entry["content"]

    def test_per_file_error_isolation(self, processor, tmp_path):
        """NCFP-SEC-02: 個別ファイルエラーが他ファイルの処理を妨げない

        file_processor.py:85-87 の per-file except + continue により、
        1つのファイル処理失敗が後続ファイルに影響しないことを検証。
        エラー隔離によりDoS耐性を確保。
        """
        # Arrange
        # 正常な JSON → 不正な JSON → 正常な YAML の順序
        (tmp_path / "a_good.json").write_text(json.dumps([{"id": "1"}]))
        (tmp_path / "b_bad.json").write_text("not json")
        (tmp_path / "c_good.yaml").write_text("name: test")
        results = {
            "policy_files": [], "resource_files": [],
            "metadata_files": [], "logs": [], "total_violations": 0,
        }

        # Act
        processor._process_directory_files(str(tmp_path), results)

        # Assert
        # a_good.json は resource_files に追加される
        assert len(results["resource_files"]) == 1
        # c_good.yaml は policy_files に追加される
        assert len(results["policy_files"]) == 1
        # b_bad.json のエラーが他ファイルの処理を妨げていない
        processor.logger.warning.assert_called()

    def test_exception_info_contains_only_message(self, processor):
        """NCFP-SEC-03: 例外情報にスタックトレースが含まれない

        file_processor.py:57-58 で `str(e)` のみが results["error"] に格納され、
        フルスタックトレースやシステムパスが漏洩しないことを検証。
        """
        # Arrange
        error_msg = "テスト用エラーメッセージ"
        with patch.object(processor, '_process_directory_files',
                          side_effect=RuntimeError(error_msg)):
            with patch("app.jobs.tasks.new_custodian_scan.file_processor.os.path.exists",
                       return_value=True):
                # Act
                result = processor.read_detailed_scan_results("/some/dir", "us-east-1")

        # Assert
        assert result["error"] == error_msg
        # スタックトレースの特徴的な文字列が含まれないこと
        assert "Traceback" not in result["error"]
        assert "File \"" not in result["error"]
        assert "line " not in result["error"]
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------:|--------:|
| `reset_file_processor_module` | file_processorモジュールのimportキャッシュリセット | function | Yes |
| `processor` | TaskLoggerモック済みFileProcessorインスタンス（各テストクラス内で定義） | function | No |
| `results` | テスト用の空の結果辞書（一部クラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加
import sys
import pytest


@pytest.fixture(autouse=True)
def reset_file_processor_module():
    """テストごとにfile_processorモジュールのimportキャッシュをリセット

    FileProcessor 自体にグローバル状態はないが、
    import キャッシュの一貫性を保証するためリセットする。
    他モジュールへの副作用を防ぐため、対象を file_processor に限定。
    """
    yield
    mod_key = "app.jobs.tasks.new_custodian_scan.file_processor"
    if mod_key in sys.modules:
        del sys.modules[mod_key]
```

---

## 6. テスト実行例

```bash
# file_processor テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_file_processor.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_file_processor.py::TestProcessFileTypes -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_file_processor.py \
  --cov=app.jobs.tasks.new_custodian_scan.file_processor \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_file_processor.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|-----:|--------|
| 正常系 | 23 | NCFP-001 〜 NCFP-023 |
| 異常系 | 3 | NCFP-E01 〜 NCFP-E03 |
| セキュリティ | 3 | NCFP-SEC-01 〜 NCFP-SEC-03 |
| **合計** | **29** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|-----:|
| `TestFileProcessorInit` | NCFP-001 | 1 |
| `TestReadDetailedScanResults` | NCFP-002〜NCFP-004 | 3 |
| `TestInitializeDetailedResults` | NCFP-005 | 1 |
| `TestProcessDirectoryFiles` | NCFP-006〜NCFP-007 | 2 |
| `TestProcessSingleFile` | NCFP-008〜NCFP-013 | 6 |
| `TestProcessFileTypes` | NCFP-014〜NCFP-018 | 5 |
| `TestCountViolations` | NCFP-019〜NCFP-022 | 4 |
| `TestLogScanResultsSummary` | NCFP-023 | 1 |
| `TestFileProcessorErrors` | NCFP-E01〜NCFP-E03 | 3 |
| `TestFileProcessorSecurity` | NCFP-SEC-01〜NCFP-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> `FileProcessor` の全メソッドが同期で、`tmp_path` と `patch` の組み合わせにより
> ファイルI/O系テストも安定して実行可能です。

### 注意事項

- `tmp_path` はpytest組み込みフィクスチャ（追加パッケージ不要）
- `--strict-markers` 運用時は `@pytest.mark.security` を `pyproject.toml` に登録する必要あり
- NCFP-SEC-02 では `os.walk` の処理順序はOS依存で保証されないため、ファイル名に `a_`, `b_`, `c_` プレフィックスを付与しつつ、アサーションは処理済みファイル数のみで順序に依存しない
- 全メソッドが同期のため `pytest-asyncio` は不要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `os.walk` の処理順序はファイルシステム依存 | NCFP-SEC-02 等でファイル処理順が環境により異なる可能性がある | アサーションは処理済みファイル数のみで検証し、順序には依存しない設計としている |
| 2 | テストでは小さなJSONデータのみ使用 | 大きなJSONファイルでのメモリ消費やパフォーマンスは未検証 | 本テスト仕様書ではロジックの正確性を検証対象とし、大容量ファイルの負荷テストは別途実施 |
| 3 | `_process_metadata_file` の UnicodeDecodeError は `open()` の `read()` 時にのみ発生 | 部分的にデコード可能なファイルではエラーにならない可能性がある | テストではPNGヘッダバイト列を使用し確実にUnicodeDecodeErrorを発生させる |
