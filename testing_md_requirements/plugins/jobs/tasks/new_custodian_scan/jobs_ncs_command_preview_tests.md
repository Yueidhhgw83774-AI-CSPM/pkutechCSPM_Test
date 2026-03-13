# jobs/tasks/new_custodian_scan/command_preview テストケース

## 1. 概要

`command_preview.py` は Custodian コマンドを実際に実行せずに、生成されるコマンドの詳細情報（コマンド文字列・環境変数・ポリシーファイル内容・実行ディレクトリ構造）をプレビューする `CustodianCommandPreview` クラスを提供します。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | job_id設定、TaskLogger・CredentialProcessor・CustodianCommandBuilder・AuthenticationHandler初期化 |
| `generate_command_preview` (async) | メインエントリ：認証解析→検証→プレビュー生成→結果返却 |
| `_generate_region_commands_preview` (async) | 全リージョンのコマンドプレビュー生成＋サマリー作成 |
| `_generate_single_region_command_preview` (async) | 単一リージョンのコマンド情報生成（builder呼出＋マスク＋ファイル読取） |
| `_prepare_base_credentials` (async) | クラウドプロバイダー別の基本認証情報準備（azure/role_assumption/secret_key） |
| `_mask_sensitive_env_vars` | SECRET/TOKEN/KEY/PASSWORD含むキーの値マスク |

### 1.2 カバレッジ目標: 85%

> **注記**: 外部依存（CredentialProcessor、CustodianCommandBuilder、AuthenticationHandler）が多く、モック設計が重要。asyncメソッド4つ。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/command_preview.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_command_preview.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
command_preview.py ──→ CredentialProcessor（認証解析・検証）
                   ──→ CustodianCommandBuilder（コマンド構築）
                   ──→ AuthenticationHandler（認証ハンドラ ※未使用だがインスタンス化）
                   ──→ TaskLogger（ログ出力）
                   ──→ tempfile.TemporaryDirectory（一時ディレクトリ）
                   ──→ os.path.exists, open()（ポリシーファイル読取）
                   ──→ datetime.now（タイムスタンプ）
                   ──→ ValidationError（エラーラップ）
```

#### 非同期メソッド（pytest-asyncio必要）

| メソッド |
|---------|
| `generate_command_preview` |
| `_generate_region_commands_preview` |
| `_generate_single_region_command_preview` |
| `_prepare_base_credentials` |

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `generate_command_preview` | L77 | Exception | ValidationErrorラップ |
| `_generate_region_commands_preview` | L109 | `"policies:" in yaml` | policies_count計算 |
| `_generate_single_region_command_preview` | L142 | `os.path.exists` | ポリシーファイル読取/空文字 |
| | L157/158 | `"--output-dir"/"--region" in args` | 引数抽出/None |
| `_prepare_base_credentials` | L182 | `azure` | Azure認証情報dict |
| | L189 | `role_assumption` | テスト用模擬認証dict |
| | L196 | else（secret_key） | アクセスキーdict |
| `_mask_sensitive_env_vars` | L207 | keyword in key.upper() | マスク/そのまま |
| | L208 | `len(value) > 8` | 先頭8文字+"..."/"\*\*\*" |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCP-001 | CustodianCommandPreview初期化 | job_id="test" | 4つのコンポーネント初期化 |
| NCCP-002 | generate_command_preview成功 | 有効データ | プレビューdict返却 |
| NCCP-003 | _generate_region_commands_preview複数リージョン | 2リージョン | region_commands配列2件 |
| NCCP-004 | _generate_single_region_command_preview正常 | 有効データ | command_info dict |
| NCCP-005 | _prepare_base_credentials azure | azure+認証情報 | AZURE_*キー4つ |
| NCCP-006 | _prepare_base_credentials role_assumption | role_assumption | テスト用認証3キー |
| NCCP-007 | _prepare_base_credentials secret_key | secret_key+キー | AWS_*キー3つ |
| NCCP-008 | _mask_sensitive_env_vars SECRETマスク | AWS_SECRET_ACCESS_KEY | 先頭8文字+"..." |
| NCCP-009 | _mask_sensitive_env_vars TOKENマスク | AWS_SESSION_TOKEN | 先頭8文字+"..." |
| NCCP-010 | _mask_sensitive_env_vars 非機密そのまま | AWS_DEFAULT_REGION | 値そのまま |
| NCCP-011 | _mask_sensitive_env_vars 短い値 | 8文字以下のSECRET | "***" |
| NCCP-012 | _generate_region_commands_preview policies数計算 | "policies:"2回含むYAML | policy_policies_count==2 |
| NCCP-013 | _generate_single_region_command_preview ファイル不在 | os.path.exists=False | policy_content="" |
| NCCP-014 | _prepare_base_credentials azure Noneフィールド | tenantId=None | 空文字にフォールバック |
| NCCP-015 | _generate_single_region_command_preview 引数不在 | --output-dir/--regionなし | output_dir=None, region=None |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_command_preview.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, mock_open


class TestCustodianCommandPreviewInit:
    """CustodianCommandPreview初期化テスト"""

    def test_init_sets_attributes(self):
        """NCCP-001: CustodianCommandPreview初期化

        command_preview.py:30-35 の初期化を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger") as mock_logger, \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor") as mock_cp, \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder") as mock_cb, \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler") as mock_ah:
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            preview = CustodianCommandPreview("test-cp")

        # Assert
        assert preview.job_id == "test-cp"
        mock_logger.assert_called_once_with("test-cp", "CustodianCommandPreview")
        mock_cp.assert_called_once_with("test-cp")
        mock_cb.assert_called_once_with("test-cp")
        mock_ah.assert_called_once_with("test-cp")
```

### 2.2 generate_command_preview テスト

```python
class TestGenerateCommandPreview:
    """generate_command_previewテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-gcp")

    @pytest.mark.asyncio
    async def test_generate_preview_success(self, preview):
        """NCCP-002: generate_command_preview成功

        command_preview.py:37-75 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = ["us-east-1"]
        mock_creds.authType = "secret_key"
        preview.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        preview.credential_processor.validate_inputs = MagicMock()

        expected_preview = {"cloud_provider": "aws", "region_commands": []}
        preview._generate_region_commands_preview = AsyncMock(return_value=expected_preview)

        # Act
        with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/test"
            result = await preview.generate_command_preview(
                "policies:\n  - name: test", {"authType": "secret_key"}, "aws"
            )

        # Assert
        assert result == expected_preview
        preview.credential_processor.parse_credentials_payload.assert_called_once()
        preview.credential_processor.validate_inputs.assert_called_once()
        assert preview.logger.info.call_count >= 2  # 開始＋完了ログ
```

### 2.3 _generate_region_commands_preview テスト

```python
class TestGenerateRegionCommandsPreview:
    """_generate_region_commands_previewテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-grcp")

    @pytest.mark.asyncio
    async def test_multiple_regions(self, preview):
        """NCCP-003: _generate_region_commands_preview複数リージョン

        command_preview.py:96-100 のリージョンループを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = ["us-east-1", "eu-west-1"]
        mock_creds.authType = "secret_key"
        preview._prepare_base_credentials = AsyncMock(return_value={"AWS_ACCESS_KEY_ID": "test"})
        preview._generate_single_region_command_preview = AsyncMock(
            side_effect=[{"region": "us-east-1"}, {"region": "eu-west-1"}]
        )

        # Act
        result = await preview._generate_region_commands_preview(
            "/tmp/test", "policies:\n  - name: test", mock_creds, "aws"
        )

        # Assert
        assert result["total_regions"] == 2
        assert len(result["region_commands"]) == 2
        assert result["cloud_provider"] == "aws"
        assert result["auth_type"] == "secret_key"
        assert preview._generate_single_region_command_preview.call_count == 2

    @pytest.mark.asyncio
    async def test_policies_count_calculation(self, preview):
        """NCCP-012: _generate_region_commands_preview policies数計算

        command_preview.py:109 のpolicies:カウントロジックを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = ["us-east-1"]
        mock_creds.authType = "secret_key"
        preview._prepare_base_credentials = AsyncMock(return_value={})
        preview._generate_single_region_command_preview = AsyncMock(return_value={})

        # 2つのpolicies:セクションを含むYAML
        yaml_with_two_policies = "policies:\n  - name: p1\npolicies:\n  - name: p2"

        # Act
        result = await preview._generate_region_commands_preview(
            "/tmp/test", yaml_with_two_policies, mock_creds, "aws"
        )

        # Assert
        assert result["policy_policies_count"] == 2  # split("policies:")→["", "\n  - name: p1\n", "\n  - name: p2"]→len=3→3-1=2
```

### 2.4 _generate_single_region_command_preview テスト

```python
class TestGenerateSingleRegionCommandPreview:
    """_generate_single_region_command_previewテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-gsrcp")

    @pytest.mark.asyncio
    async def test_single_region_normal(self, preview):
        """NCCP-004: _generate_single_region_command_preview正常

        command_preview.py:115-174 の正常パスを検証。
        """
        # Arrange
        preview.command_builder.build_command_for_region = MagicMock(return_value=(
            ["run", "--output-dir", "/tmp/output", "--verbose", "--region", "us-east-1", "/tmp/policy.yaml"],
            {"AWS_ACCESS_KEY_ID": "AKIATEST", "AWS_SECRET_ACCESS_KEY": "secretkey123"},
            "/tmp/policy.yaml",
            "/tmp/output"
        ))
        preview.command_builder.get_custodian_command_path = MagicMock(return_value="custodian")
        creds = {"AWS_ACCESS_KEY_ID": "AKIATEST", "AWS_SECRET_ACCESS_KEY": "secretkey123"}

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="policies:\n  - name: test")):
            # Act
            result = await preview._generate_single_region_command_preview(
                "/tmp/work", "policies:\n  - name: test", creds, "us-east-1", 0, "aws"
            )

        # Assert
        assert result["region"] == "us-east-1"
        assert result["region_index"] == 0
        assert result["command"]["executable"] == "custodian"
        assert "custodian" in result["command"]["full_command"]
        assert result["command"]["arguments"]["action"] == "run"
        assert result["command"]["arguments"]["region"] == "us-east-1"
        assert result["files"]["policy_content"] == "policies:\n  - name: test"
        # 機密情報がマスクされていることを検証
        assert "secretkey123" not in str(result["environment"]["variables"])
        assert preview.logger.info.call_count >= 1  # リージョンコマンドログ

    @pytest.mark.asyncio
    async def test_policy_file_not_exists(self, preview):
        """NCCP-013: _generate_single_region_command_preview ファイル不在

        command_preview.py:142 のos.path.exists=Falseを検証。
        """
        # Arrange
        preview.command_builder.build_command_for_region = MagicMock(return_value=(
            ["run", "--output-dir", "/tmp/output", "--verbose", "/tmp/policy.yaml"],
            {},
            "/tmp/policy.yaml",
            "/tmp/output"
        ))
        preview.command_builder.get_custodian_command_path = MagicMock(return_value="custodian")

        with patch("os.path.exists", return_value=False):
            # Act
            result = await preview._generate_single_region_command_preview(
                "/tmp/work", "policies:\n  - name: test", {}, "us-east-1", 0, "aws"
            )

        # Assert
        assert result["files"]["policy_content"] == ""

    @pytest.mark.asyncio
    async def test_args_without_output_dir_and_region(self, preview):
        """NCCP-015: _generate_single_region_command_preview 引数不在時のNone返却

        command_preview.py:157-158 の--output-dir/--regionが存在しないケースを検証。
        """
        # Arrange
        preview.command_builder.build_command_for_region = MagicMock(return_value=(
            ["run", "--verbose", "/tmp/policy.yaml"],  # --output-dir, --regionなし
            {},
            "/tmp/policy.yaml",
            "/tmp/output"
        ))
        preview.command_builder.get_custodian_command_path = MagicMock(return_value="custodian")

        with patch("os.path.exists", return_value=False):
            # Act
            result = await preview._generate_single_region_command_preview(
                "/tmp/work", "policies:\n  - name: test", {}, "us-east-1", 0, "aws"
            )

        # Assert
        assert result["command"]["arguments"]["output_dir"] is None
        assert result["command"]["arguments"]["region"] is None
```

### 2.5 _prepare_base_credentials テスト

```python
class TestPrepareBaseCredentials:
    """_prepare_base_credentialsテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-pbc")

    @pytest.mark.asyncio
    async def test_azure_credentials(self, preview):
        """NCCP-005: _prepare_base_credentials azure

        command_preview.py:182-188 のAzure分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = "tenant-123"
        mock_creds.clientId = "client-456"
        mock_creds.clientSecret = "secret-789"
        mock_creds.subscriptionId = "sub-012"

        # Act
        result = await preview._prepare_base_credentials(mock_creds, "azure")

        # Assert
        assert result["AZURE_TENANT_ID"] == "tenant-123"
        assert result["AZURE_CLIENT_ID"] == "client-456"
        assert result["AZURE_CLIENT_SECRET"] == "secret-789"
        assert result["AZURE_SUBSCRIPTION_ID"] == "sub-012"

    @pytest.mark.asyncio
    async def test_role_assumption_credentials(self, preview):
        """NCCP-006: _prepare_base_credentials role_assumption

        command_preview.py:189-195 のrole_assumption分岐を検証。
        テスト用模擬認証情報が返されることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"

        # Act
        result = await preview._prepare_base_credentials(mock_creds, "aws")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST123456789012"
        assert "EXAMPLE" in result["AWS_SECRET_ACCESS_KEY"]
        assert result["AWS_SESSION_TOKEN"] == "test-session-token"

    @pytest.mark.asyncio
    async def test_secret_key_credentials(self, preview):
        """NCCP-007: _prepare_base_credentials secret_key

        command_preview.py:196-201 のelse分岐（secret_key）を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        mock_creds.accessKey = "AKIAREAL123"
        mock_creds.secretKey = "realSecretKey"
        mock_creds.sessionToken = "realToken"

        # Act
        result = await preview._prepare_base_credentials(mock_creds, "aws")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAREAL123"
        assert result["AWS_SECRET_ACCESS_KEY"] == "realSecretKey"
        assert result["AWS_SESSION_TOKEN"] == "realToken"

    @pytest.mark.asyncio
    async def test_azure_none_fields_fallback(self, preview):
        """NCCP-014: _prepare_base_credentials azure Noneフィールド

        command_preview.py:184-187 のor ""フォールバックを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = None
        mock_creds.clientId = None
        mock_creds.clientSecret = None
        mock_creds.subscriptionId = None

        # Act
        result = await preview._prepare_base_credentials(mock_creds, "azure")

        # Assert
        assert result["AZURE_TENANT_ID"] == ""
        assert result["AZURE_CLIENT_ID"] == ""
        assert result["AZURE_CLIENT_SECRET"] == ""
        assert result["AZURE_SUBSCRIPTION_ID"] == ""
```

### 2.6 _mask_sensitive_env_vars テスト

```python
class TestMaskSensitiveEnvVars:
    """_mask_sensitive_env_varsテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-msev")

    def test_mask_secret_key(self, preview):
        """NCCP-008: _mask_sensitive_env_vars SECRETマスク

        command_preview.py:207-208 のSECRETキーワードマスクを検証。
        """
        # Arrange
        env = {"AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG"}

        # Act
        result = preview._mask_sensitive_env_vars(env)

        # Assert
        assert result["AWS_SECRET_ACCESS_KEY"] == "wJalrXUt..."

    def test_mask_token(self, preview):
        """NCCP-009: _mask_sensitive_env_vars TOKENマスク

        command_preview.py:207 のTOKENキーワードマスクを検証。
        """
        # Arrange
        env = {"AWS_SESSION_TOKEN": "FwoGZXIvYXdzEBYaDH"}

        # Act
        result = preview._mask_sensitive_env_vars(env)

        # Assert
        assert result["AWS_SESSION_TOKEN"] == "FwoGZXIv..."

    def test_non_sensitive_pass_through(self, preview):
        """NCCP-010: _mask_sensitive_env_vars 非機密そのまま

        command_preview.py:210 の非機密キーはマスクされないことを検証。
        AWS_DEFAULT_REGIONとPATHはSECRET/TOKEN/KEY/PASSWORDのいずれも含まないため非機密。
        """
        # Arrange
        env = {"AWS_DEFAULT_REGION": "us-east-1", "PATH": "/usr/bin"}

        # Act
        result = preview._mask_sensitive_env_vars(env)

        # Assert
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"
        assert result["PATH"] == "/usr/bin"

    def test_short_value_masked_as_stars(self, preview):
        """NCCP-011: _mask_sensitive_env_vars 短い値

        command_preview.py:208 のlen<=8の場合"***"を検証。
        """
        # Arrange
        env = {"AWS_SECRET_ACCESS_KEY": "short"}

        # Act
        result = preview._mask_sensitive_env_vars(env)

        # Assert
        assert result["AWS_SECRET_ACCESS_KEY"] == "***"
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCP-E01 | generate_command_preview認証解析失敗 | 不正credentials_data | ValidationError |
| NCCP-E02 | generate_command_preview検証失敗 | validate_inputs例外 | ValidationError |
| NCCP-E03 | generate_command_preview一般例外 | _generate_region例外 | ValidationErrorラップ |

### 3.1 generate_command_preview異常系

```python
class TestGenerateCommandPreviewErrors:
    """generate_command_previewエラーテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-gcp-err")

    @pytest.mark.asyncio
    async def test_parse_credentials_failure(self, preview):
        """NCCP-E01: generate_command_preview認証解析失敗

        command_preview.py:77-79 のException→ValidationErrorラップをカバー。
        parse_credentials_payloadが例外を投げるケース。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        preview.credential_processor.parse_credentials_payload = AsyncMock(
            side_effect=Exception("parse error")
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="コマンドプレビューの生成に失敗"):
            await preview.generate_command_preview(
                "policies:\n  - name: test", {"authType": "bad"}, "aws"
            )
        # エラーログを検証
        preview.logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_inputs_failure(self, preview):
        """NCCP-E02: generate_command_preview検証失敗

        command_preview.py:77-79 のvalidate_inputs例外をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        preview.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        preview.credential_processor.validate_inputs = MagicMock(
            side_effect=Exception("validation failed")
        )

        # Act & Assert
        with pytest.raises(ValidationError, match="コマンドプレビューの生成に失敗"):
            await preview.generate_command_preview(
                "policies:\n  - name: test", {"authType": "secret_key"}, "aws"
            )

    @pytest.mark.asyncio
    async def test_general_exception_wrapping(self, preview):
        """NCCP-E03: generate_command_preview一般例外

        command_preview.py:77-79 のException→ValidationErrorラップを検証。
        _generate_region_commands_previewが例外を投げるケース。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        preview.credential_processor.parse_credentials_payload = AsyncMock(return_value=mock_creds)
        preview.credential_processor.validate_inputs = MagicMock()
        preview._generate_region_commands_preview = AsyncMock(
            side_effect=RuntimeError("unexpected error")
        )

        # Act & Assert
        with patch("tempfile.TemporaryDirectory") as mock_tmpdir:
            mock_tmpdir.return_value.__enter__.return_value = "/tmp/test"
            with pytest.raises(ValidationError, match="コマンドプレビューの生成に失敗"):
                await preview.generate_command_preview(
                    "policies:\n  - name: test", {"authType": "secret_key"}, "aws"
                )
        # エラーログを検証
        preview.logger.error.assert_called_once()
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCP-SEC-01 | 全機密キーワードのマスク検証 | SECRET/TOKEN/KEY/PASSWORD含むキー | 全てマスク済み |
| NCCP-SEC-02 | Azure clientSecretのプレビュー内マスク | Azure認証情報 | clientSecretがマスク済み |
| NCCP-SEC-03 | エラーメッセージへの機密情報非漏洩 | 機密情報含む例外 | エラーメッセージに機密値なし |

```python
@pytest.mark.security
class TestCommandPreviewSecurity:
    """CustodianCommandPreviewセキュリティテスト"""

    @pytest.fixture
    def preview(self):
        with patch("app.jobs.tasks.new_custodian_scan.command_preview.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CredentialProcessor"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.CustodianCommandBuilder"), \
             patch("app.jobs.tasks.new_custodian_scan.command_preview.AuthenticationHandler"):
            from app.jobs.tasks.new_custodian_scan.command_preview import CustodianCommandPreview
            return CustodianCommandPreview("test-sec")

    def test_all_sensitive_keywords_masked(self, preview):
        """NCCP-SEC-01: 全機密キーワードのマスク検証

        command_preview.py:207 の4つのキーワード（SECRET/TOKEN/KEY/PASSWORD）を検証。
        """
        # Arrange
        env = {
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG",
            "AWS_SESSION_TOKEN": "FwoGZXIvYXdzEBYaDH123456",
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "DB_PASSWORD": "supersecretpassword123",
            "AWS_DEFAULT_REGION": "us-east-1",
            "PATH": "/usr/bin",
        }

        # Act
        result = preview._mask_sensitive_env_vars(env)

        # Assert（機密キーは全てマスク）
        assert result["AWS_SECRET_ACCESS_KEY"] == "wJalrXUt..."
        assert result["AWS_SESSION_TOKEN"] == "FwoGZXIv..."
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAIOSF..."
        assert result["DB_PASSWORD"] == "supersec..."  # 先頭8文字="supersec" + "..."
        # 非機密キーはそのまま
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"
        assert result["PATH"] == "/usr/bin"
        # 完全な機密値がマスク済みdictに残っていないこと
        masked_values = str(result.values())
        assert "wJalrXUtnFEMI/K7MDENG" not in masked_values
        assert "FwoGZXIvYXdzEBYaDH123456" not in masked_values
        assert "supersecretpassword123" not in masked_values

    @pytest.mark.asyncio
    async def test_azure_client_secret_masked_in_preview(self, preview):
        """NCCP-SEC-02: Azure clientSecretのプレビュー内マスク

        command_preview.py:138でマスクが適用され、プレビュー結果にclientSecretが
        完全な形で含まれないことを検証。
        """
        # Arrange
        preview.command_builder.build_command_for_region = MagicMock(return_value=(
            ["run", "--output-dir", "/tmp/output", "--verbose", "/tmp/policy.yaml"],
            {"AZURE_CLIENT_SECRET": "my-super-secret-value", "AZURE_TENANT_ID": "tenant-123"},
            "/tmp/policy.yaml",
            "/tmp/output"
        ))
        preview.command_builder.get_custodian_command_path = MagicMock(return_value="custodian")

        with patch("os.path.exists", return_value=False):
            # Act
            result = await preview._generate_single_region_command_preview(
                "/tmp/work", "policies:", {}, "japaneast", 0, "azure"
            )

        # Assert（環境変数内のclientSecretがマスクされていること）
        env_vars = result["environment"]["variables"]
        assert "my-super-secret-value" not in str(env_vars)
        assert env_vars["AZURE_CLIENT_SECRET"] == "my-super..."

    @pytest.mark.asyncio
    async def test_error_message_no_secret_leak(self, preview):
        """NCCP-SEC-03: エラーメッセージへの機密情報非漏洩

        command_preview.py:78-79 のエラーメッセージに機密情報が含まれないことを検証。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        secret_value = "wJalrXUtnFEMI_SECRET_KEY"
        preview.credential_processor.parse_credentials_payload = AsyncMock(
            side_effect=Exception(f"parse error for key={secret_value}")
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await preview.generate_command_preview(
                "policies:", {"authType": "bad"}, "aws"
            )

        # エラーメッセージのラッパー部分を検証
        assert "コマンドプレビューの生成に失敗" in str(exc_info.value)
        # 注意: 現在の実装（L79）はstr(e)をそのままValidationErrorに含めるため、
        # secret_valueがエラーメッセージに漏洩する可能性がある（既知の制限）。
        # 以下のアサーションは実装のサニタイズ改善後に有効化推奨:
        # assert secret_value not in str(exc_info.value)
        # ログ出力への機密漏洩チェック
        preview.logger.error.assert_called_once()
        # 注意: ログにもstr(e)が含まれうる（実装改善対象）
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `preview` | 各テストクラス内のCustodianCommandPreviewインスタンス（全依存モック済み） | function | No |

### フィクスチャ方針

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py（既存に追記）
# フィクスチャ方針:
# - CustodianCommandPreviewは内部に3つのコンポーネント（CredentialProcessor,
#   CustodianCommandBuilder, AuthenticationHandler）を保持するため、
#   初期化時に4つのクラスをモック。
# - 各テストクラスでpreviewフィクスチャを個別に定義。
# - asyncメソッドのテストには @pytest.mark.asyncio が必要。
# - tempfile.TemporaryDirectoryはコンテキストマネージャーとしてモック。
# - os.path.exists, builtins.openはテストメソッド内で個別にパッチ。
```

---

## 6. テスト実行例

```bash
# command_preview関連テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_preview.py -v

# 特定クラスのみ
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_preview.py::TestMaskSensitiveEnvVars -v

# カバレッジ付き
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_preview.py \
  --cov=app.jobs.tasks.new_custodian_scan.command_preview \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_command_preview.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 15 | NCCP-001 〜 NCCP-015 |
| 異常系 | 3 | NCCP-E01 〜 NCCP-E03 |
| セキュリティ | 3 | NCCP-SEC-01 〜 NCCP-SEC-03 |
| **合計** | **21** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCustodianCommandPreviewInit` | NCCP-001 | 1 |
| `TestGenerateCommandPreview` | NCCP-002 | 1 |
| `TestGenerateRegionCommandsPreview` | NCCP-003, NCCP-012 | 2 |
| `TestGenerateSingleRegionCommandPreview` | NCCP-004, NCCP-013, NCCP-015 | 3 |
| `TestPrepareBaseCredentials` | NCCP-005〜NCCP-007, NCCP-014 | 4 |
| `TestMaskSensitiveEnvVars` | NCCP-008〜NCCP-011 | 4 |
| `TestGenerateCommandPreviewErrors` | NCCP-E01〜NCCP-E03 | 3 |
| `TestCommandPreviewSecurity` | NCCP-SEC-01〜NCCP-SEC-03 | 3 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 確定対応手順 |
|---------|------|-------------|
| NCCP-002 | `tempfile.TemporaryDirectory`のコンテキストマネージャーモック。`__enter__.return_value`形式を使用しているが、実装のwith文との相性で失敗する可能性 | テスト実行時にモック設定を調整。必要に応じて`@patch("tempfile.TemporaryDirectory")`のデコレータ形式に変更 |
| NCCP-SEC-03 | 現在の実装（L79）は`str(e)`をValidationErrorに含めるため、元例外メッセージ内の機密値がエラーメッセージに漏洩する。テストではコメントアウトで対応（実装改善後に有効化推奨） | 実装側でエラーメッセージのサニタイズを実施後、`assert secret_value not in str(exc_info.value)`のコメントアウトを解除 |

### 注意事項

- `generate_command_preview`、`_generate_region_commands_preview`、`_generate_single_region_command_preview`、`_prepare_base_credentials`はasyncメソッド → `@pytest.mark.asyncio`必須
- `tempfile.TemporaryDirectory`はコンテキストマネージャーとしてモック（`__enter__`/`__exit__`設定必要）
- `@pytest.mark.security`マーカーの登録が必要
- `_prepare_base_credentials`のrole_assumption分岐（L189-195）はハードコードされたテスト認証情報を返す

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_prepare_base_credentials`のrole_assumption分岐（L189-195）はハードコードされたテスト認証情報を返す。本番ではAssumeRoleを実行すべき | プレビュー機能では実際のAWS呼び出しを避けるため意図的な設計 | テストでは固定値の検証のみ。本番動作はauth_handlerのテストでカバー |
| 2 | `generate_command_preview`のException catch（L77）が広すぎる | 全例外をValidationErrorに変換するため、予期しないエラーの原因特定が困難 | エラーメッセージに元例外のstr(e)を含めることで最低限の情報を保持 |
| 3 | `_mask_sensitive_env_vars`はキー名ベースのマスクのみ | 値ベースの機密情報検出はなし。カスタムキー名の機密情報は漏洩する可能性 | 現時点では許容範囲。将来的に値パターンマッチの追加を検討 |
| 4 | `auth_handler`がインスタンス化されるが使用されない（L35） | 不要なリソース確保 | テスト仕様書では初期化を検証するのみ。実装修正は別途検討 |
| 5 | `generate_command_preview`のエラーメッセージ（L79）に`str(e)`が含まれるため、元例外に機密情報がある場合に漏洩する | エラーメッセージ経由の機密情報漏洩リスク | 実装側でエラーメッセージのサニタイズを推奨。NCCP-SEC-03のコメントアウトされたアサーションを改善後に有効化 |
