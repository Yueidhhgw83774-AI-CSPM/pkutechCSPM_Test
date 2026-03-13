# jobs/utils 違反カウント テストケース (#17f)

## 1. 概要

`app/jobs/utils/violations_counter.py` のテスト仕様書。Custodianスキャン結果の `resources.json` ファイルから違反数・リソース数をカウントする機能を検証する。

### 1.1 主要機能

| 関数 | ファイル | 説明 |
|------|---------|------|
| `count_violations_from_custodian_output()` | violations_counter.py | 出力ディレクトリ全体の違反数を集計 |
| `count_resources_from_custodian_output()` | violations_counter.py | 出力ディレクトリ全体のリソース数を集計 |
| `_count_violations_in_file()` | violations_counter.py | 単一ファイルの違反数をカウント |
| `_extract_policy_name_from_path()` | violations_counter.py | ファイルパスからポリシー名を抽出 |
| `_log_resource_details()` | violations_counter.py | 違反リソースの詳細をログ出力 |

### 1.2 カバレッジ目標: 90%

> **注記**: スキャン結果の集計はCSPMの中核機能であり、カウント誤りは重大なセキュリティレポートの不正確さにつながるため高カバレッジを目標とする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/utils/violations_counter.py` (169行) |
| テストコード | `test/unit/jobs/utils/test_violations_counter.py` |
| conftest | `test/unit/jobs/utils/conftest.py`（#17aと共有） |

### 1.4 依存関係

| 依存先 | 用途 | モック要否 |
|--------|------|-----------|
| `TaskLogger` | ログ出力 | 要（モック） |
| `glob.glob` | ファイル検索 | 要（モック or tmp_path） |
| `json.load` | JSON読み込み | 不要（tmp_pathで実ファイル使用） |
| `os.path.relpath` | 相対パス計算 | 不要（通常は実処理） |

### 1.5 主要分岐マップ

| 関数 | 分岐数 | 主要条件 |
|------|--------|---------|
| `count_violations_from_custodian_output` | 4 | L41 ファイルなし, L46 forループ, L48 violations>0, L54 例外 |
| `count_resources_from_custodian_output` | 4 | L79 forループ, L84 isinstance list, L87 内部例外, L94 外部例外 |
| `_count_violations_in_file` | 3 | L119 not list, L125 count>0, L132 例外 |
| `_extract_policy_name_from_path` | 2 | L151 空ディレクトリ名, L152 例外 |
| `_log_resource_details` | 2 | L164 先頭3件, L169 残件表示 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VC-001 | 複数ファイルの違反数集計 | 2ファイル（各3件、2件） | 合計5 |
| VC-002 | ファイルなし → 0件 | 空ディレクトリ | 0 |
| VC-003 | 全ファイルが空リスト → 0件 | 空リストのresources.json | 0 |
| VC-004 | 複数ファイルのリソース数集計 | 2ファイル（各5件、3件） | 合計8 |
| VC-005 | リソースカウント：非リストデータはスキップ | dict形式のresources.json | 0 |
| VC-006 | 単一ファイルの違反数カウント | 3件のリソースリスト | 3 |
| VC-007 | 単一ファイル：非リストデータ → 0 | dict形式のデータ | 0 |
| VC-008 | 単一ファイル：空リスト → 0（ログなし） | 空リスト | 0 |
| VC-009 | ポリシー名抽出：正常パス | `/output/check-ec2/resources.json` | `check-ec2` |
| VC-010 | ポリシー名抽出：ルート直下 → unknown_policy | `/output/resources.json` | `unknown_policy` |
| VC-011 | ログ出力：3件以下 | 2件のリソース | debug 2回 |
| VC-012 | ログ出力：3件超 | 5件のリソース | debug 3回 + "2 more" |
| VC-013 | ログ出力：キー欠損時のデフォルト値 | キーなしリソース | `unknown`, `unknown_resource_0` |
| VC-014 | 違反あり/なしファイル混在 | 違反ありと空リスト混在 | 違反ありのみ集計 |
| VC-015 | リソースカウント：空ディレクトリ → 0 | 空ディレクトリ | 0 |
| VC-016 | 単一ファイル：リスト要素が非dict → 例外捕捉で0 | `[1, "str", null]` | 0 |
| VC-017 | ポリシー名抽出：ネストディレクトリ | `region/policy/resources.json` | `region/policy` |

### 2.1 count_violations_from_custodian_output テスト

```python
# test/unit/jobs/utils/test_violations_counter.py
import json
import os
import pytest
from unittest.mock import patch, MagicMock


class TestCountViolations:
    """count_violations_from_custodian_output のテスト"""

    def test_multiple_files(self, tmp_path):
        """VC-001: 複数ファイルの違反数を正しく集計する

        violations_counter.py:L46-49 のforループ・集計をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_violations_from_custodian_output

        # ポリシー1: 3件の違反
        policy1_dir = tmp_path / "check-ec2"
        policy1_dir.mkdir()
        (policy1_dir / "resources.json").write_text(
            json.dumps([{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]),
            encoding="utf-8"
        )

        # ポリシー2: 2件の違反
        policy2_dir = tmp_path / "check-s3"
        policy2_dir.mkdir()
        (policy2_dir / "resources.json").write_text(
            json.dumps([{"id": "r4"}, {"id": "r5"}]),
            encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_violations_from_custodian_output(str(tmp_path), "job-001")

        # Assert
        assert result == 5

    def test_empty_directory(self, tmp_path):
        """VC-002: resources.jsonファイルなし → 0を返す

        violations_counter.py:L41-43 の早期リターンをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_violations_from_custodian_output

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_violations_from_custodian_output(str(tmp_path), "job-002")

        # Assert
        assert result == 0

    def test_all_empty_lists(self, tmp_path):
        """VC-003: 全ファイルが空リスト → 0を返す

        violations_counter.py:L48 の if violations > 0 がFalseとなるパスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_violations_from_custodian_output
        policy_dir = tmp_path / "check-ec2"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(
            json.dumps([]), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_violations_from_custodian_output(str(tmp_path), "job-003")

        # Assert
        assert result == 0

    def test_mixed_violations_and_empty(self, tmp_path):
        """VC-014: 違反ありと違反なしのファイル混在 → 違反ありのみ集計

        violations_counter.py:L48 の if violations_in_file > 0 が
        True/Falseの両方を通るパスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_violations_from_custodian_output

        # 違反あり: 2件
        policy1_dir = tmp_path / "check-ec2"
        policy1_dir.mkdir()
        (policy1_dir / "resources.json").write_text(
            json.dumps([{"id": "r1"}, {"id": "r2"}]), encoding="utf-8"
        )

        # 違反なし: 空リスト
        policy2_dir = tmp_path / "check-s3"
        policy2_dir.mkdir()
        (policy2_dir / "resources.json").write_text(
            json.dumps([]), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_violations_from_custodian_output(str(tmp_path), "job-014")

        # Assert
        assert result == 2
```

### 2.2 count_resources_from_custodian_output テスト

```python
class TestCountResources:
    """count_resources_from_custodian_output のテスト"""

    def test_empty_directory(self, tmp_path):
        """VC-015: resources.jsonファイルなし → 0を返す

        violations_counter.py:L79 の for ループが空リストで
        スキップされるパスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_resources_from_custodian_output

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_resources_from_custodian_output(str(tmp_path), "job-015")

        # Assert
        assert result == 0

    def test_multiple_files(self, tmp_path):
        """VC-004: 複数ファイルのリソース数を正しく集計する

        violations_counter.py:L79-85 のforループ・isinstance・加算をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_resources_from_custodian_output

        policy1_dir = tmp_path / "check-ec2"
        policy1_dir.mkdir()
        (policy1_dir / "resources.json").write_text(
            json.dumps([{"id": f"r{i}"} for i in range(5)]),
            encoding="utf-8"
        )

        policy2_dir = tmp_path / "check-s3"
        policy2_dir.mkdir()
        (policy2_dir / "resources.json").write_text(
            json.dumps([{"id": f"r{i}"} for i in range(3)]),
            encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_resources_from_custodian_output(str(tmp_path), "job-004")

        # Assert
        assert result == 8

    def test_non_list_data_skipped(self, tmp_path):
        """VC-005: 非リストデータ（dict）はカウントされない

        violations_counter.py:L84 の isinstance チェックがFalseとなるパスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_resources_from_custodian_output
        policy_dir = tmp_path / "check-ec2"
        policy_dir.mkdir()
        (policy_dir / "resources.json").write_text(
            json.dumps({"error": "not a list"}), encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_resources_from_custodian_output(str(tmp_path), "job-005")

        # Assert
        assert result == 0
```

### 2.3 _count_violations_in_file テスト

```python
class TestCountViolationsInFile:
    """_count_violations_in_file のテスト"""

    def test_valid_file(self, tmp_path):
        """VC-006: 正常なresources.jsonファイルの違反数カウント

        violations_counter.py:L123-130 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        resources_file = tmp_path / "resources.json"
        resources_file.write_text(
            json.dumps([{"id": "r1"}, {"id": "r2"}, {"id": "r3"}]),
            encoding="utf-8"
        )

        # Act
        result = _count_violations_in_file(
            str(resources_file), str(tmp_path), logger
        )

        # Assert
        assert result == 3
        logger.info.assert_called_once()

    def test_non_list_data(self, tmp_path):
        """VC-007: 非リスト形式のデータ → 0を返す

        violations_counter.py:L119-121 の型チェック分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        resources_file = tmp_path / "resources.json"
        resources_file.write_text(
            json.dumps({"error": "not a list"}), encoding="utf-8"
        )

        # Act
        result = _count_violations_in_file(
            str(resources_file), str(tmp_path), logger
        )

        # Assert
        assert result == 0
        logger.warning.assert_called_once()

    def test_empty_list(self, tmp_path):
        """VC-008: 空リスト → 0を返す（ログ出力なし）

        violations_counter.py:L125 の if violations_count > 0 がFalseのパスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        resources_file = tmp_path / "resources.json"
        resources_file.write_text(json.dumps([]), encoding="utf-8")

        # Act
        result = _count_violations_in_file(
            str(resources_file), str(tmp_path), logger
        )

        # Assert
        assert result == 0
        # 空リスト時はinfo/warningログなし
        logger.info.assert_not_called()
        logger.warning.assert_not_called()

    def test_non_dict_elements_in_list(self, tmp_path):
        """VC-016: リスト要素が非dict → _log_resource_detailsでAttributeError → 0を返す

        violations_counter.py:L125 でcount>0判定後、L128 の _log_resource_details
        内 L165 で resource.get() が AttributeError を発生させ、
        L132 の外部 except で捕捉されて 0 を返す境界ケース。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        resources_file = tmp_path / "resources.json"
        resources_file.write_text(
            json.dumps([1, "string", None]), encoding="utf-8"
        )

        # Act
        result = _count_violations_in_file(
            str(resources_file), str(tmp_path), logger
        )

        # Assert
        assert result == 0
        logger.warning.assert_called_once()
```

### 2.4 _extract_policy_name_from_path テスト

```python
class TestExtractPolicyName:
    """_extract_policy_name_from_path のテスト"""

    def test_normal_path(self, tmp_path):
        """VC-009: 正常なパスからポリシー名を抽出

        violations_counter.py:L149-151 の正常パスをカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _extract_policy_name_from_path
        file_path = str(tmp_path / "check-ec2" / "resources.json")

        # Act
        result = _extract_policy_name_from_path(file_path, str(tmp_path))

        # Assert
        assert result == "check-ec2"

    def test_root_level_file(self, tmp_path):
        """VC-010: ルート直下のファイル → unknown_policy

        violations_counter.py:L151 の空ディレクトリ名分岐をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _extract_policy_name_from_path
        file_path = str(tmp_path / "resources.json")

        # Act
        result = _extract_policy_name_from_path(file_path, str(tmp_path))

        # Assert
        assert result == "unknown_policy"

    def test_nested_directory(self, tmp_path):
        """VC-017: ネストディレクトリのパス → region/policy を返す

        violations_counter.py:L149-150 の os.path.relpath + os.path.dirname で
        ネストされたディレクトリ構造がそのまま返される動作を固定する。
        回帰防止のため期待値を明示的に定義。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _extract_policy_name_from_path
        file_path = str(tmp_path / "us-east-1" / "check-ec2" / "resources.json")

        # Act
        result = _extract_policy_name_from_path(file_path, str(tmp_path))

        # Assert
        assert result == os.path.join("us-east-1", "check-ec2")
```

### 2.5 _log_resource_details テスト

```python
class TestLogResourceDetails:
    """_log_resource_details のテスト"""

    def test_three_or_fewer_resources(self):
        """VC-011: 3件以下のリソース → 全件ログ出力

        violations_counter.py:L164 のスライス[:3]をカバー。
        3件以下の場合は "... and N more" メッセージは出力されない。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _log_resource_details
        logger = MagicMock()
        resources = [
            {"resource_type": "ec2", "resource_id": "i-001"},
            {"resource_type": "s3", "resource_id": "bucket-001"},
        ]

        # Act
        _log_resource_details(resources, logger)

        # Assert
        assert logger.debug.call_count == 2

    def test_more_than_three_resources(self):
        """VC-012: 3件超のリソース → 先頭3件 + 残件数メッセージ

        violations_counter.py:L164 のスライスと L169-170 の残件表示をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _log_resource_details
        logger = MagicMock()
        resources = [{"resource_type": f"type_{i}", "resource_id": f"id_{i}"} for i in range(5)]

        # Act
        _log_resource_details(resources, logger)

        # Assert
        # 先頭3件 + "... and 2 more" の計4回
        assert logger.debug.call_count == 4

    def test_missing_keys_use_defaults(self):
        """VC-013: キーが欠損したリソース → デフォルト値を使用

        violations_counter.py:L165-166 の get デフォルト値をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _log_resource_details
        logger = MagicMock()
        resources = [{}]

        # Act
        _log_resource_details(resources, logger)

        # Assert
        logger.debug.assert_called_once()
        call_args = logger.debug.call_args[0][0]
        assert "unknown" in call_args
        assert "unknown_resource_0" in call_args
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VC-E01 | count_violations glob例外 | glob.glob例外 | 0 |
| VC-E02 | count_resources 外部例外 | glob.glob例外 | 0 |
| VC-E03 | count_resources ファイル読み込みエラー | 不正JSONファイル | 該当ファイルスキップ、他は集計 |
| VC-E04 | _count_violations_in_file 読み込みエラー | 存在しないファイル | 0 |
| VC-E05 | _count_violations_in_file 不正JSON | 壊れたJSON | 0 |
| VC-E06 | _extract_policy_name_from_path 例外 | relpath例外 | `unknown_policy` |

### 3.1 違反カウント 異常系

```python
class TestViolationsCounterErrors:
    """violations_counter エラーテスト"""

    def test_count_violations_glob_exception(self):
        """VC-E01: glob.globで例外発生 → 0を返す

        violations_counter.py:L54-56 の外部 except をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_violations_from_custodian_output

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"), \
             patch("app.jobs.utils.violations_counter.glob.glob",
                   side_effect=OSError("permission denied")):
            result = count_violations_from_custodian_output("/dummy", "job-e01")

        # Assert
        assert result == 0

    def test_count_resources_glob_exception(self):
        """VC-E02: count_resources でglob.glob例外 → 0を返す

        violations_counter.py:L94-96 の外部 except をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_resources_from_custodian_output

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"), \
             patch("app.jobs.utils.violations_counter.glob.glob",
                   side_effect=OSError("permission denied")):
            result = count_resources_from_custodian_output("/dummy", "job-e02")

        # Assert
        assert result == 0

    def test_count_resources_file_read_error(self, tmp_path):
        """VC-E03: 一部ファイルの読み込みエラー → スキップして残りを集計

        violations_counter.py:L87-89 の内部 except・continue をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_resources_from_custodian_output

        # 正常ファイル
        policy1_dir = tmp_path / "check-ec2"
        policy1_dir.mkdir()
        (policy1_dir / "resources.json").write_text(
            json.dumps([{"id": "r1"}, {"id": "r2"}]), encoding="utf-8"
        )

        # 壊れたJSONファイル
        policy2_dir = tmp_path / "check-s3"
        policy2_dir.mkdir()
        (policy2_dir / "resources.json").write_text(
            "{broken json", encoding="utf-8"
        )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_resources_from_custodian_output(str(tmp_path), "job-e03")

        # Assert
        # 壊れたファイルはスキップされ、正常ファイルの2件のみカウント
        assert result == 2

    def test_count_violations_in_file_read_error(self):
        """VC-E04: 存在しないファイルの読み込み → 0を返す

        violations_counter.py:L132-134 の except をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()

        # Act
        result = _count_violations_in_file(
            "/nonexistent/resources.json", "/nonexistent", logger
        )

        # Assert
        assert result == 0
        logger.warning.assert_called_once()

    def test_count_violations_in_file_invalid_json(self, tmp_path):
        """VC-E05: 不正なJSONファイル → 0を返す

        violations_counter.py:L132-134 の json.JSONDecodeError 経由の except をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        bad_file = tmp_path / "resources.json"
        bad_file.write_text("{broken json", encoding="utf-8")

        # Act
        result = _count_violations_in_file(
            str(bad_file), str(tmp_path), logger
        )

        # Assert
        assert result == 0
        logger.warning.assert_called_once()

    def test_extract_policy_name_exception(self):
        """VC-E06: os.path.relpathで例外 → unknown_policyを返す

        violations_counter.py:L152-153 の except をカバー。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _extract_policy_name_from_path

        # Act
        with patch("app.jobs.utils.violations_counter.os.path.relpath",
                   side_effect=ValueError("invalid path")):
            result = _extract_policy_name_from_path("/some/path", "/other/path")

        # Assert
        assert result == "unknown_policy"
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| VC-SEC-01 | ログインジェクション耐性 | 改行・ANSIエスケープ含むリソース | クラッシュせずカウント完了 |
| VC-SEC-02 | 大量ファイル処理の安定性 | 100ファイル | クラッシュなく集計完了 |
| VC-SEC-03 | 悪意あるJSON内容 | スクリプト埋め込みリソース | 文字列としてパススルー |

```python
@pytest.mark.security
class TestViolationsCounterSecurity:
    """violations_counter セキュリティテスト"""

    def test_log_injection_resilience(self, tmp_path):
        """VC-SEC-01: ログインジェクション耐性

        リソースデータに改行文字（\\n, \\r）やANSIエスケープシーケンスが
        含まれていた場合、_log_resource_details がクラッシュせず
        正常にカウントを返すことを確認する。
        violations_counter.py:L127 の logger.info 呼び出しと
        L164-170 の _log_resource_details 実行でクラッシュしないことを検証。

        注: ログ出力時のサニタイズはこのモジュールの責務外だが、
        悪意ある入力でプロセスが中断しないことを保証する。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        injected_resources = [
            {
                "resource_type": "ec2\nINFO: injected log line",
                "resource_id": "i-001\r\nWARNING: fake warning",
            },
            {
                "resource_type": "\x1b[31mred-text\x1b[0m",
                "resource_id": "id-with-ansi-escape",
            },
        ]
        resources_file = tmp_path / "resources.json"
        resources_file.write_text(
            json.dumps(injected_resources), encoding="utf-8"
        )

        # Act
        result = _count_violations_in_file(
            str(resources_file), str(tmp_path), logger
        )

        # Assert
        assert result == 2
        logger.info.assert_called_once()

    def test_large_file_count_stability(self, tmp_path):
        """VC-SEC-02: 大量ファイル（100件）の処理安定性

        100個のresources.jsonファイルを持つディレクトリ構造を処理し、
        メモリ枯渇やタイムアウトなく集計が正常完了することを確認する。
        """
        # Arrange
        from app.jobs.utils.violations_counter import count_violations_from_custodian_output

        for i in range(100):
            policy_dir = tmp_path / f"policy-{i:03d}"
            policy_dir.mkdir()
            (policy_dir / "resources.json").write_text(
                json.dumps([{"id": f"r-{i}"}]), encoding="utf-8"
            )

        # Act
        with patch("app.jobs.utils.violations_counter.TaskLogger"):
            result = count_violations_from_custodian_output(str(tmp_path), "job-sec-02")

        # Assert
        assert result == 100
        assert isinstance(result, int)

    def test_malicious_json_content(self, tmp_path):
        """VC-SEC-03: 悪意あるJSON内容（スクリプト埋め込み）の処理

        リソースデータにXSS風の文字列やコマンドインジェクション風の
        値が含まれていた場合、パニックせずカウントのみ行うことを確認する。
        """
        # Arrange
        from app.jobs.utils.violations_counter import _count_violations_in_file
        logger = MagicMock()
        malicious_resources = [
            {"resource_type": "<script>alert('xss')</script>", "resource_id": "'; DROP TABLE;--"},
            {"resource_type": "$(rm -rf /)", "resource_id": "../../etc/shadow"},
        ]
        resources_file = tmp_path / "resources.json"
        resources_file.write_text(
            json.dumps(malicious_resources), encoding="utf-8"
        )

        # Act
        result = _count_violations_in_file(
            str(resources_file), str(tmp_path), logger
        )

        # Assert
        # カウントは正常に行われる（内容のサニタイズはこのモジュールの責務外）
        assert result == 2
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_utils_module` | テスト間のモジュール状態リセット | function | Yes |

> **注記**: `violations_counter` はモジュールレベルの可変状態を持たないため、`sys.modules` クリーンアップは安全に動作する。テスト内で関数をインポートする方式（import-inside-method）を使用し、各テストが新しいモジュールインスタンスから関数を取得する。conftest.py は `test/unit/jobs/utils/conftest.py`（#17a で定義予定）を共有する。

### 共通フィクスチャ定義

```python
# test/unit/jobs/utils/conftest.py（#17a 仕様書で定義予定・共有）
import sys
import pytest

# 本テストファイルで使用するモジュールのみを対象とする
_TARGET_MODULES = (
    "app.jobs.utils.violations_counter",
)


@pytest.fixture(autouse=True)
def reset_utils_module():
    """テストごとにモジュールのグローバル状態をリセット

    violations_counter のモジュールキャッシュのみクリアし、
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

> **注記**: conftest.py は #17a〜#17e と共有予定。実装時には `_TARGET_MODULES` タプルに `"app.jobs.utils.violations_counter"` を追加する形で統合する。

---

## 6. テスト実行例

```bash
# 違反カウントテストのみ実行
pytest test/unit/jobs/utils/test_violations_counter.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/utils/test_violations_counter.py::TestCountViolations -v

# カバレッジ付きで実行
pytest test/unit/jobs/utils/test_violations_counter.py \
  --cov=app.jobs.utils.violations_counter \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/utils/test_violations_counter.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 17 | VC-001 〜 VC-017 |
| 異常系 | 6 | VC-E01 〜 VC-E06 |
| セキュリティ | 3 | VC-SEC-01 〜 VC-SEC-03 |
| **合計** | **26** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCountViolations` | VC-001〜VC-003, VC-014 | 4 |
| `TestCountResources` | VC-004〜VC-005, VC-015 | 3 |
| `TestCountViolationsInFile` | VC-006〜VC-008, VC-016 | 4 |
| `TestExtractPolicyName` | VC-009〜VC-010, VC-017 | 3 |
| `TestLogResourceDetails` | VC-011〜VC-013 | 3 |
| `TestViolationsCounterErrors` | VC-E01〜VC-E06 | 6 |
| `TestViolationsCounterSecurity` | VC-SEC-01〜VC-SEC-03 | 3 |

### 7.1 予想失敗テスト

現時点で失敗が予想されるテストはありません。

> **VC-SEC-01 について**: 改行文字やANSIエスケープシーケンスを含むリソースデータを処理した場合でも、`_count_violations_in_file` は正常にカウントを返す。ログ出力時のサニタイズはこのモジュールの責務外であり、制限事項 #6 として記録する。

### 注意事項

- `@pytest.mark.security` マーカーは `pyproject.toml` に `markers = ["security: セキュリティ関連テスト"]` の登録が必要
- `tmp_path` フィクスチャは pytest 組み込みのため追加パッケージ不要
- テスト内で関数をインポートする方式（import-inside-method）を使用。`reset_utils_module` の `sys.modules` クリーンアップと組み合わせてテスト間の独立性を保証
- `TaskLogger` は公開関数テスト時に `patch` でモック。プライベート関数は `logger` パラメータに `MagicMock()` を直接渡す
- `count_violations_from_custodian_output` の L54 外部 except は `_count_violations_in_file` 経由では到達不可（同関数が内部で全例外を捕捉して 0 を返すため）。`glob.glob` 自体の例外のみがこのパスに到達する（VC-E01 でカバー）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `glob.glob` の再帰検索結果の順序は OS 依存 | テストで順序依存のアサーションを使えない | 合計値のみ検証し、個別ファイルの処理順序には依存しない |
| 2 | `_log_resource_details` は先頭3件のみログ出力 | 4件目以降のリソース詳細はログに記録されない | 仕様通りの動作。カウントは全件対象のため集計には影響なし |
| 3 | エラーログにファイルパスが含まれる（L88, L133） | 本番環境でサーバー内部パスがログに露出する可能性 | 実運用時のログレベル設定で制御。テストでは現行動作の記録に留める |
| 4 | `_extract_policy_name_from_path` は OS のパス区切り文字に依存 | Windows 環境では `\` が含まれる可能性 | CI 環境は Linux のため低影響。テストは `tmp_path` で OS 依存を吸収 |
| 5 | `count_resources_from_custodian_output` は非リストデータをカウントしない | dict 形式の resources.json は無視される | 実装仕様通り。Custodian の正常出力は常にリスト形式 |
| 6 | `_log_resource_details` はリソースデータ内の改行・制御文字をサニタイズしない | ログインジェクションのリスクあり | このモジュールの責務外。ログ基盤側での制御が必要。VC-SEC-01 で動作確認済み |
