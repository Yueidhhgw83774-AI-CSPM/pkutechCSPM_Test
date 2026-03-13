# jobs/tasks/new_custodian_scan/auth_handler + credential_processor テストケース

## 1. 概要

`auth_handler.py` は AWS（AssumeRole/アクセスキー）・Azure の認証情報取得と検証を担当する `AuthenticationHandler` クラスを提供します。`credential_processor.py` はペイロードから認証情報を解析・検証し、リージョン設定を管理する `CredentialProcessor` クラスを提供します。

### 1.1 主要機能

| クラス | メソッド | 説明 |
|--------|---------|------|
| `AuthenticationHandler` | `__init__` | job_id設定、TaskLogger初期化、STSクライアント遅延初期化 |
| | `get_credentials_for_region` (async) | リージョン用認証情報取得（azure/role_assumption/secret_key分岐） |
| | `_get_assume_role_credentials` (async) | AssumeRole実行（テストARN検出あり） |
| | `_get_test_credentials` | テスト用模擬認証情報返却 |
| | `_execute_assume_role` (async) | 実際のSTS AssumeRole実行 |
| | `_get_access_key_credentials` | アクセスキー→環境変数形式変換 |
| | `_get_azure_credentials` | Azure認証情報→環境変数形式変換 |
| | `validate_authentication` | 認証情報形式検証ディスパッチャ |
| | `_validate_role_assumption_auth` | AssumeRole形式検証 |
| | `_validate_access_key_auth` | アクセスキー形式検証 |
| | `_validate_azure_auth` | Azure形式検証 |
| `CredentialProcessor` | `__init__` | job_id設定、TaskLogger/Validators初期化 |
| | `parse_credentials_payload` (async) | ペイロード解析→検証→リージョン設定 |
| | `validate_inputs` | バリデータへの委譲ラッパー |
| | `_validate_auth_type_requirements` | 認証タイプ別必須フィールド検証 |
| | `_ensure_scan_regions` | スキャンリージョンデフォルト設定 |

### 1.2 カバレッジ目標: 90%

> **注記**: 認証処理はセキュリティの中核。auth_handler.py（211行）+ credential_processor.py（131行）= 342行。asyncメソッド・boto3外部依存あり。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/auth_handler.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/credential_processor.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_auth.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
auth_handler.py ──→ boto3.client('sts')（AWS STS）
                ──→ common.error_handling.ProcessingError
                ──→ common.logging.TaskLogger
                ──→ models.jobs.NewCredentials

credential_processor.py ──→ common.error_handling.ValidationError
                        ──→ common.logging.TaskLogger
                        ──→ models.jobs.NewCredentials
                        ──→ validators.NewCustodianValidators
```

#### 非同期メソッド（pytest-asyncio必要）

| メソッド | クラス |
|---------|--------|
| `get_credentials_for_region` | AuthenticationHandler |
| `_get_assume_role_credentials` | AuthenticationHandler |
| `_execute_assume_role` | AuthenticationHandler |
| `parse_credentials_payload` | CredentialProcessor |

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `get_credentials_for_region` | L34 | `cloud_provider == "azure"` | _get_azure_credentials |
| | L36 | `authType == "role_assumption"` | _get_assume_role_credentials |
| | L38 | `authType == "secret_key"` | _get_access_key_credentials |
| | L40 | else | ProcessingError |
| `_get_assume_role_credentials` | L51 | テストARN検出 | _get_test_credentials |
| | L55 | else | _execute_assume_role |
| | L57 | Exception | ProcessingError |
| `_execute_assume_role` | L90 | `not self._sts_client` | boto3.client作成 |
| | L100 | `externalIdValue` | ExternalIdをパラメータに追加 |
| `_get_access_key_credentials` | L134 | `sessionToken` | AWS_SESSION_TOKEN追加 |
| `validate_authentication` | L163-168 | azure/role_assumption/secret_key | 各検証メソッド |
| `parse_credentials_payload` | L35 | `not credentials_data` | ValidationError |
| | L61 | Exception | ValidationError（ラップ） |
| `_validate_auth_type_requirements` | L80 | azure+secret_key | フィールド検証 |
| | L95 | azure+非secret_key | ValidationError |
| | L97-98 | role_assumption+roleArnなし | ValidationError |
| | L106-108 | secret_key+キーなし | ValidationError |
| | L114 | else | ValidationError |
| `_ensure_scan_regions` | L123-131 | empty+azure/aws/region有無 | デフォルト設定 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCSA-001 | AuthenticationHandler初期化 | job_id="test" | logger・_sts_client=None |
| NCSA-002 | get_credentials_for_region azure | azure+creds | _get_azure_credentials呼出 |
| NCSA-003 | get_credentials_for_region role_assumption | role_assumption+creds | _get_assume_role_credentials呼出 |
| NCSA-004 | get_credentials_for_region secret_key | secret_key+creds | _get_access_key_credentials呼出 |
| NCSA-005 | _get_assume_role_credentials テストARN | arn:aws:iam::123456789012:... | _get_test_credentials呼出 |
| NCSA-005b | _get_assume_role_credentials 実ARN | 非テストARN | _execute_assume_role呼出 |
| NCSA-006 | _get_test_credentials 模擬認証情報 | テストARN | 4キーのdict返却 |
| NCSA-007 | _execute_assume_role externalId付き | externalId有 | ExternalIdパラメータ含む |
| NCSA-007b | _execute_assume_role STSクライアント再利用 | 2回呼び出し | boto3.client 1回のみ |
| NCSA-008 | _execute_assume_role externalIdなし | externalId無 | ExternalIdパラメータなし |
| NCSA-009 | _get_access_key_credentials sessionTokenなし | sessionToken=None | 3キーのdict |
| NCSA-010 | _get_access_key_credentials sessionToken付き | sessionToken有 | 4キーのdict |
| NCSA-011 | _get_azure_credentials | 有効Azure認証 | 4キーのdict |
| NCSA-011b | _get_azure_credentials Noneフィールドのログ処理 | tenantId=None等 | ログcontextにNone値 |
| NCSA-012 | validate_authentication azure dispatch | azure | _validate_azure_auth呼出 |
| NCSA-012b | validate_authentication 未対応authType（silent failure） | authType="oauth" | 例外なし・ログ出力のみ |
| NCSA-013 | validate_authentication role_assumption dispatch | role_assumption | _validate_role_assumption_auth呼出 |
| NCSA-014 | validate_authentication secret_key dispatch | secret_key | _validate_access_key_auth呼出 |
| NCSA-015 | _validate_role_assumption_auth正常 | 有効ARN | 例外なし |
| NCSA-016 | _validate_access_key_auth正常 | 有効キー | 例外なし |
| NCSA-017 | _validate_azure_auth正常 | 有効4フィールド | 例外なし |
| NCSA-018 | CredentialProcessor初期化 | job_id="test" | logger・validators設定 |
| NCSA-019 | parse_credentials_payload成功（role_assumption） | 有効データ | NewCredentials返却 |
| NCSA-020 | validate_inputs委譲 | 引数3つ | validators.validate_inputs呼出 |
| NCSA-021 | _validate_auth_type_requirements azure+secret_key | azure+有効フィールド | 例外なし |
| NCSA-022 | _validate_auth_type_requirements role_assumption | roleArn有 | 例外なし |
| NCSA-023 | _validate_auth_type_requirements secret_key | キー有 | 例外なし |
| NCSA-024 | _ensure_scan_regions既設定（no-op） | scanRegions=["us-east-1"] | 変更なし |
| NCSA-025 | _ensure_scan_regions空→azure | azure+empty | ["all-locations"]設定 |
| NCSA-026 | _ensure_scan_regions空→aws region有 | aws+region="ap-northeast-1" | ["ap-northeast-1"]設定 |
| NCSA-027 | _ensure_scan_regions空→aws regionなし | aws+region=None | ["us-east-1"]設定 |

### 2.1 AuthenticationHandler初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_auth.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestAuthenticationHandlerInit:
    """AuthenticationHandler初期化テスト"""

    def test_init_sets_attributes(self):
        """NCSA-001: AuthenticationHandler初期化

        auth_handler.py:22-25 の初期化を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger") as mock_logger_cls:
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            handler = AuthenticationHandler("test-auth")

        # Assert
        assert handler.job_id == "test-auth"
        mock_logger_cls.assert_called_once_with("test-auth", "AuthenticationHandler")
        assert handler._sts_client is None
        assert handler.logger == mock_logger_cls.return_value
```

### 2.2 get_credentials_for_region テスト

```python
class TestGetCredentialsForRegion:
    """get_credentials_for_regionディスパッチテスト"""

    @pytest.fixture
    def handler(self):
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            return AuthenticationHandler("test-gcr")

    @pytest.mark.asyncio
    async def test_azure_dispatch(self, handler):
        """NCSA-002: get_credentials_for_region azure

        auth_handler.py:34-35 のAzure分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        handler._get_azure_credentials = MagicMock(return_value={"AZURE_TENANT_ID": "test"})

        # Act
        result = await handler.get_credentials_for_region(mock_creds, "japaneast", "azure")

        # Assert
        handler._get_azure_credentials.assert_called_once_with(mock_creds)
        assert "AZURE_TENANT_ID" in result

    @pytest.mark.asyncio
    async def test_role_assumption_dispatch(self, handler):
        """NCSA-003: get_credentials_for_region role_assumption

        auth_handler.py:36-37 のrole_assumption分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"
        handler._get_assume_role_credentials = AsyncMock(return_value={"AWS_ACCESS_KEY_ID": "test"})

        # Act
        result = await handler.get_credentials_for_region(mock_creds, "us-east-1", "aws")

        # Assert
        handler._get_assume_role_credentials.assert_called_once_with(mock_creds, "us-east-1")
        assert result == {"AWS_ACCESS_KEY_ID": "test"}

    @pytest.mark.asyncio
    async def test_secret_key_dispatch(self, handler):
        """NCSA-004: get_credentials_for_region secret_key

        auth_handler.py:38-39 のsecret_key分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        handler._get_access_key_credentials = MagicMock(return_value={"AWS_ACCESS_KEY_ID": "test"})

        # Act
        result = await handler.get_credentials_for_region(mock_creds, "us-east-1", "aws")

        # Assert
        handler._get_access_key_credentials.assert_called_once_with(mock_creds, "us-east-1")
        assert result == {"AWS_ACCESS_KEY_ID": "test"}
```

### 2.3 AssumeRole認証テスト

```python
class TestAssumeRoleCredentials:
    """AssumeRole認証テスト"""

    @pytest.fixture
    def handler(self):
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            return AuthenticationHandler("test-ar")

    @pytest.mark.asyncio
    async def test_test_arn_detection(self, handler):
        """NCSA-005: _get_assume_role_credentials テストARN

        auth_handler.py:51-52 のテストARN検出分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::123456789012:role/test-role"
        handler._get_test_credentials = MagicMock(return_value={"AWS_ACCESS_KEY_ID": "test"})

        # Act
        result = await handler._get_assume_role_credentials(mock_creds, "us-east-1")

        # Assert
        handler._get_test_credentials.assert_called_once_with(mock_creds, "us-east-1")
        assert result == {"AWS_ACCESS_KEY_ID": "test"}

    @pytest.mark.asyncio
    async def test_real_arn_calls_execute(self, handler):
        """NCSA-005b: _get_assume_role_credentials 実ARN

        auth_handler.py:55 の非テストARN→_execute_assume_role分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/prod-role"
        handler._execute_assume_role = AsyncMock(return_value={"AWS_ACCESS_KEY_ID": "ASIA..."})

        # Act
        result = await handler._get_assume_role_credentials(mock_creds, "us-east-1")

        # Assert
        handler._execute_assume_role.assert_called_once_with(mock_creds, "us-east-1")
        assert result == {"AWS_ACCESS_KEY_ID": "ASIA..."}

    def test_get_test_credentials_returns_mock(self, handler):
        """NCSA-006: _get_test_credentials 模擬認証情報

        auth_handler.py:74-82 のテスト認証情報を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::123456789012:role/short"
        mock_creds.externalIdValue = "ext-id"

        # Act
        result = handler._get_test_credentials(mock_creds, "ap-northeast-1")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST123456789012"
        assert result["AWS_SECRET_ACCESS_KEY"] == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        assert result["AWS_SESSION_TOKEN"] == "test-session-token"
        assert result["AWS_DEFAULT_REGION"] == "ap-northeast-1"

    @pytest.mark.asyncio
    async def test_execute_assume_role_with_external_id(self, handler):
        """NCSA-007: _execute_assume_role externalId付き

        auth_handler.py:100-101 のExternalIdパラメータ追加を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/prod-role"
        mock_creds.externalIdValue = "ext-123"

        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIA...",
                "SecretAccessKey": "secret...",
                "SessionToken": "token...",
            }
        }

        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_sts
            result = await handler._execute_assume_role(mock_creds, "us-east-1")

        # Assert
        call_kwargs = mock_sts.assume_role.call_args.kwargs
        assert call_kwargs["ExternalId"] == "ext-123"
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"
        # externalIdの実際の値がログに含まれないこと
        assert "ext-123" not in str(handler.logger.info.call_args_list)

    @pytest.mark.asyncio
    async def test_sts_client_reuse(self, handler):
        """NCSA-007b: _execute_assume_role STSクライアント再利用

        auth_handler.py:90 のnot self._sts_client条件を検証。
        2回呼び出し時にboto3.clientが1回のみ呼ばれることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/prod-role"
        mock_creds.externalIdValue = None

        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIA...",
                "SecretAccessKey": "secret...",
                "SessionToken": "token...",
            }
        }

        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_sts

            # 初回呼び出し前の状態確認
            assert handler._sts_client is None

            # Act（初回呼び出し：クライアント作成）
            await handler._execute_assume_role(mock_creds, "us-east-1")
            assert handler._sts_client is not None

            # Act（2回目呼び出し：クライアント再利用）
            await handler._execute_assume_role(mock_creds, "ap-northeast-1")

        # Assert（boto3.clientは初回のみ呼ばれる）
        mock_boto3.client.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_assume_role_without_external_id(self, handler):
        """NCSA-008: _execute_assume_role externalIdなし

        auth_handler.py:94-109 のExternalIdなしパスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/prod-role"
        mock_creds.externalIdValue = None

        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "ASIA...",
                "SecretAccessKey": "secret...",
                "SessionToken": "token...",
            }
        }

        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_sts
            result = await handler._execute_assume_role(mock_creds, "us-east-1")

        # Assert（ExternalIdがパラメータに含まれないこと）
        call_kwargs = mock_sts.assume_role.call_args.kwargs
        assert "ExternalId" not in call_kwargs
```

### 2.4 アクセスキー・Azure認証テスト

```python
class TestAccessKeyAndAzureCredentials:
    """アクセスキー・Azure認証情報テスト"""

    @pytest.fixture
    def handler(self):
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            return AuthenticationHandler("test-ak")

    def test_access_key_without_session_token(self, handler):
        """NCSA-009: _get_access_key_credentials sessionTokenなし

        auth_handler.py:128-132 の基本パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"
        mock_creds.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        mock_creds.sessionToken = None

        # Act
        result = handler._get_access_key_credentials(mock_creds, "us-east-1")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"
        assert "AWS_SESSION_TOKEN" not in result

    def test_access_key_with_session_token(self, handler):
        """NCSA-010: _get_access_key_credentials sessionToken付き

        auth_handler.py:134-135 のsessionToken分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"
        mock_creds.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        mock_creds.sessionToken = "test-session-token"

        # Act
        result = handler._get_access_key_credentials(mock_creds, "us-east-1")

        # Assert
        assert result["AWS_SESSION_TOKEN"] == "test-session-token"

    def test_azure_credentials(self, handler):
        """NCSA-011: _get_azure_credentials

        auth_handler.py:145-159 のAzure認証情報変換を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "secret-value"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act
        result = handler._get_azure_credentials(mock_creds)

        # Assert
        assert result["AZURE_TENANT_ID"] == mock_creds.tenantId
        assert result["AZURE_CLIENT_ID"] == mock_creds.clientId
        assert result["AZURE_CLIENT_SECRET"] == mock_creds.clientSecret
        assert result["AZURE_SUBSCRIPTION_ID"] == mock_creds.subscriptionId

    def test_azure_credentials_none_fields_log(self, handler):
        """NCSA-011b: _get_azure_credentials Noneフィールドのログ処理

        auth_handler.py:153-155 の三項演算子でNone時の分岐を検証。
        tenantId等がNoneの場合、ログcontextにNoneが設定されることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = None
        mock_creds.clientId = None
        mock_creds.clientSecret = "secret-value"
        mock_creds.subscriptionId = None

        # Act
        result = handler._get_azure_credentials(mock_creds)

        # Assert（ログcontextのNone値を検証）
        log_call = handler.logger.info.call_args
        context = log_call.kwargs.get("context", {})
        assert context["tenant_id"] is None
        assert context["client_id"] is None
        assert context["subscription_id"] is None
        # 戻り値もNone値が含まれる
        assert result["AZURE_TENANT_ID"] is None
```

### 2.5 validate_authentication テスト

```python
class TestValidateAuthentication:
    """validate_authenticationテスト"""

    @pytest.fixture
    def handler(self):
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            return AuthenticationHandler("test-va")

    def test_azure_dispatch(self, handler):
        """NCSA-012: validate_authentication azure dispatch

        auth_handler.py:163-164 のAzure分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        handler._validate_azure_auth = MagicMock()

        # Act
        handler.validate_authentication(mock_creds, "azure")

        # Assert
        handler._validate_azure_auth.assert_called_once_with(mock_creds)

    def test_role_assumption_dispatch(self, handler):
        """NCSA-013: validate_authentication role_assumption dispatch

        auth_handler.py:165-166 のrole_assumption分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"
        handler._validate_role_assumption_auth = MagicMock()

        # Act
        handler.validate_authentication(mock_creds, "aws")

        # Assert
        handler._validate_role_assumption_auth.assert_called_once_with(mock_creds)

    def test_secret_key_dispatch(self, handler):
        """NCSA-014: validate_authentication secret_key dispatch

        auth_handler.py:167-168 のsecret_key分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        handler._validate_access_key_auth = MagicMock()

        # Act
        handler.validate_authentication(mock_creds, "aws")

        # Assert
        handler._validate_access_key_auth.assert_called_once_with(mock_creds)

    def test_unsupported_auth_type_silent(self, handler):
        """NCSA-012b: validate_authentication 未対応authType（silent failure）

        auth_handler.py:161-170 にはelse分岐がなく、未対応authTypeでも例外が発生せず
        ログ出力のみで処理が完了する（silent failure）。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "oauth"

        # Act（例外が発生しないことを確認）
        handler.validate_authentication(mock_creds, "aws")

        # Assert（ログが出力されていること、かつL170の1回のみ）
        handler.logger.info.assert_called()
        assert handler.logger.info.call_count == 1

    def test_validate_role_assumption_valid(self, handler):
        """NCSA-015: _validate_role_assumption_auth正常

        auth_handler.py:172-184 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/test"

        # Act（例外が発生しないことを確認）
        handler._validate_role_assumption_auth(mock_creds)

        # Assert（ログ出力を検証）
        handler.logger.info.assert_called()

    def test_validate_access_key_valid(self, handler):
        """NCSA-016: _validate_access_key_auth正常

        auth_handler.py:186-194 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"
        mock_creds.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        mock_creds.sessionToken = None

        # Act（例外が発生しないことを確認）
        handler._validate_access_key_auth(mock_creds)

        # Assert（ログ出力を検証）
        handler.logger.info.assert_called()

    def test_validate_azure_valid(self, handler):
        """NCSA-017: _validate_azure_auth正常

        auth_handler.py:196-212 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "secret"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act（例外が発生しないことを確認）
        handler._validate_azure_auth(mock_creds)

        # Assert（ログ出力を検証）
        handler.logger.info.assert_called()
```

### 2.6 CredentialProcessor テスト

```python
class TestCredentialProcessorInit:
    """CredentialProcessor初期化テスト"""

    def test_init_sets_attributes(self):
        """NCSA-018: CredentialProcessor初期化

        credential_processor.py:24-27 の初期化を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger") as mock_logger, \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators") as mock_val:
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            processor = CredentialProcessor("test-cp")

        # Assert
        assert processor.job_id == "test-cp"
        mock_logger.assert_called_once_with("test-cp", "CredentialProcessor")
        mock_val.assert_called_once_with("test-cp")


class TestParseCredentialsPayload:
    """parse_credentials_payloadテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators"):
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            return CredentialProcessor("test-pcp")

    @pytest.mark.asyncio
    async def test_parse_role_assumption_success(self, processor):
        """NCSA-019: parse_credentials_payload成功（role_assumption）

        credential_processor.py:29-59 の成功パスを検証。
        _validate_auth_type_requirementsと_ensure_scan_regionsも実際に実行される。
        """
        # Arrange
        credentials_data = {
            "authType": "role_assumption",
            "roleArn": "arn:aws:iam::999999999999:role/test",
            "scanRegions": ["us-east-1"],
        }

        # Act（NewCredentialsはモックだが、_validate_auth_type_requirementsと_ensure_scan_regionsは実際に実行される）
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCredentials") as mock_nc:
            mock_instance = MagicMock()
            mock_instance.authType = "role_assumption"
            mock_instance.roleArn = "arn:aws:iam::999999999999:role/test"
            mock_instance.scanRegions = ["us-east-1"]
            mock_nc.return_value = mock_instance
            result = await processor.parse_credentials_payload(credentials_data, "aws")

        # Assert
        assert result == mock_instance
        mock_nc.assert_called_once()


class TestValidateInputsWrapper:
    """validate_inputsラッパーテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators"):
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            return CredentialProcessor("test-vi")

    def test_validate_inputs_delegates(self, processor):
        """NCSA-020: validate_inputs委譲

        credential_processor.py:65-72 の委譲を検証。
        """
        # Arrange
        mock_creds = MagicMock()

        # Act
        processor.validate_inputs("yaml_content", mock_creds, "aws")

        # Assert
        processor.validators.validate_inputs.assert_called_once_with("yaml_content", mock_creds, "aws")
```

### 2.7 _validate_auth_type_requirements テスト

```python
class TestValidateAuthTypeRequirements:
    """_validate_auth_type_requirementsテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators"):
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            return CredentialProcessor("test-vatr")

    def test_azure_secret_key_valid(self, processor):
        """NCSA-021: _validate_auth_type_requirements azure+secret_key

        credential_processor.py:80-94 のAzure正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "secret"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act（例外が発生しないことを確認）
        processor._validate_auth_type_requirements(mock_creds, "azure")

        # Assert（ログ出力を検証）
        processor.logger.info.assert_called()

    def test_role_assumption_valid(self, processor):
        """NCSA-022: _validate_auth_type_requirements role_assumption

        credential_processor.py:97-104 のrole_assumption正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/test"
        mock_creds.externalIdValue = None
        mock_creds.scanRegions = ["us-east-1"]

        # Act（例外が発生しないことを確認）
        processor._validate_auth_type_requirements(mock_creds, "aws")

        # Assert（ログ出力を検証）
        processor.logger.info.assert_called()

    def test_secret_key_valid(self, processor):
        """NCSA-023: _validate_auth_type_requirements secret_key

        credential_processor.py:106-112 のsecret_key正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"
        mock_creds.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        mock_creds.sessionToken = None
        mock_creds.scanRegions = ["us-east-1"]

        # Act（例外が発生しないことを確認）
        processor._validate_auth_type_requirements(mock_creds, "aws")

        # Assert（ログ出力を検証）
        processor.logger.info.assert_called()
```

### 2.8 _ensure_scan_regions テスト

```python
class TestEnsureScanRegions:
    """_ensure_scan_regionsテスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators"):
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            return CredentialProcessor("test-esr")

    def test_regions_already_set(self, processor):
        """NCSA-024: _ensure_scan_regions既設定（no-op）

        credential_processor.py:123 のnot条件が偽の場合。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = ["us-east-1", "eu-west-1"]

        # Act
        processor._ensure_scan_regions(mock_creds, "aws")

        # Assert（変更なし）
        assert mock_creds.scanRegions == ["us-east-1", "eu-west-1"]

    def test_empty_azure_defaults_to_all_locations(self, processor):
        """NCSA-025: _ensure_scan_regions空→azure

        credential_processor.py:124-127 のAzureデフォルト設定を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = []

        # Act
        processor._ensure_scan_regions(mock_creds, "azure")

        # Assert
        assert mock_creds.scanRegions == ["all-locations"]

    def test_empty_aws_with_region(self, processor):
        """NCSA-026: _ensure_scan_regions空→aws region有

        credential_processor.py:130-131 のAWSデフォルト（region指定あり）を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = []
        mock_creds.region = "ap-northeast-1"

        # Act
        processor._ensure_scan_regions(mock_creds, "aws")

        # Assert
        assert mock_creds.scanRegions == ["ap-northeast-1"]

    def test_empty_aws_without_region(self, processor):
        """NCSA-027: _ensure_scan_regions空→aws regionなし

        credential_processor.py:131 のregion=None時のus-east-1フォールバックを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = []
        mock_creds.region = None

        # Act
        processor._ensure_scan_regions(mock_creds, "aws")

        # Assert
        assert mock_creds.scanRegions == ["us-east-1"]
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCSA-E01 | get_credentials_for_region未対応authType | authType="oauth" | ProcessingError |
| NCSA-E02 | _get_assume_role_credentials例外 | STS失敗 | ProcessingError("AssumeRole認証エラー") |
| NCSA-E03 | _validate_role_assumption_auth roleArn欠落 | roleArn=None | ProcessingError |
| NCSA-E04 | _validate_role_assumption_auth ARN不正 | roleArn="invalid" | ProcessingError |
| NCSA-E05 | _validate_access_key_auth キー欠落 | accessKey=None | ProcessingError |
| NCSA-E06 | _validate_azure_auth フィールド欠落 | tenantId=None | ProcessingError |
| NCSA-E07 | parse_credentials_payload空データ | {} | ValidationError("認証情報が空です") |
| NCSA-E08 | parse_credentials_payload解析例外 | 不正データ | ValidationError("認証情報の解析に失敗") |
| NCSA-E09 | _validate_auth_type_requirements azure非secret_key | azure+role_assumption | ValidationError |
| NCSA-E10 | _validate_auth_type_requirements azure欠落フィールド | azure+tenantId=None | ValidationError |
| NCSA-E11 | _validate_auth_type_requirements role_assumption roleArn欠落 | roleArn=None | ValidationError |
| NCSA-E12 | _validate_auth_type_requirements secret_keyキー欠落 | accessKey=None | ValidationError |
| NCSA-E13 | _validate_auth_type_requirements未対応タイプ | authType="oauth" | ValidationError |

### 3.1 AuthenticationHandler異常系

```python
class TestAuthHandlerErrors:
    """AuthenticationHandler異常系テスト"""

    @pytest.fixture
    def handler(self):
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            return AuthenticationHandler("test-ah-err")

    @pytest.mark.asyncio
    async def test_unsupported_auth_type(self, handler):
        """NCSA-E01: get_credentials_for_region未対応authType

        auth_handler.py:40-41 のelse分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        mock_creds = MagicMock()
        mock_creds.authType = "oauth"

        # Act & Assert
        with pytest.raises(ProcessingError, match="サポートされていない認証タイプ"):
            await handler.get_credentials_for_region(mock_creds, "us-east-1", "aws")

    @pytest.mark.asyncio
    async def test_assume_role_exception(self, handler):
        """NCSA-E02: _get_assume_role_credentials例外

        auth_handler.py:57-59 のException分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::999999999999:role/prod"
        handler._execute_assume_role = AsyncMock(side_effect=Exception("STS failure"))

        # Act & Assert
        with pytest.raises(ProcessingError, match="AssumeRole認証エラー"):
            await handler._get_assume_role_credentials(mock_creds, "us-east-1")

    def test_validate_role_missing_arn(self, handler):
        """NCSA-E03: _validate_role_assumption_auth roleArn欠落

        auth_handler.py:174-175 のroleArn必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        mock_creds = MagicMock()
        mock_creds.roleArn = None

        # Act & Assert
        with pytest.raises(ProcessingError, match="roleArnが必要です"):
            handler._validate_role_assumption_auth(mock_creds)

    def test_validate_role_invalid_arn(self, handler):
        """NCSA-E04: _validate_role_assumption_auth ARN不正

        auth_handler.py:178-179 のARN形式チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        mock_creds = MagicMock()
        mock_creds.roleArn = "invalid-arn-format"

        # Act & Assert
        with pytest.raises(ProcessingError, match="無効なIAMロールARN形式"):
            handler._validate_role_assumption_auth(mock_creds)

    def test_validate_access_key_missing(self, handler):
        """NCSA-E05: _validate_access_key_auth キー欠落

        auth_handler.py:188-189 のキー必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        mock_creds = MagicMock()
        mock_creds.accessKey = None
        mock_creds.secretKey = None

        # Act & Assert
        with pytest.raises(ProcessingError, match="accessKeyとsecretKeyが必要です"):
            handler._validate_access_key_auth(mock_creds)

    def test_validate_azure_missing_fields(self, handler):
        """NCSA-E06: _validate_azure_auth フィールド欠落

        auth_handler.py:205-206 のmissing_fieldsチェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        mock_creds = MagicMock()
        mock_creds.tenantId = None
        mock_creds.clientId = "valid"
        mock_creds.clientSecret = None
        mock_creds.subscriptionId = "valid"

        # Act & Assert
        with pytest.raises(ProcessingError, match="Azure認証には以下のフィールドが必要です"):
            handler._validate_azure_auth(mock_creds)
```

### 3.2 CredentialProcessor異常系

```python
class TestCredentialProcessorErrors:
    """CredentialProcessor異常系テスト"""

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators"):
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            return CredentialProcessor("test-cp-err")

    @pytest.mark.asyncio
    async def test_empty_credentials_data(self, processor):
        """NCSA-E07: parse_credentials_payload空データ

        credential_processor.py:35-36 の空チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="認証情報が空です"):
            await processor.parse_credentials_payload({}, "aws")

    @pytest.mark.asyncio
    async def test_parse_exception_wrapping(self, processor):
        """NCSA-E08: parse_credentials_payload解析例外

        credential_processor.py:61-63 のException→ValidationErrorラッピングをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（不正なデータでNewCredentialsパースが失敗）
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCredentials",
                   side_effect=Exception("parse error")):
            with pytest.raises(ValidationError, match="認証情報の解析に失敗"):
                await processor.parse_credentials_payload({"authType": "bad"}, "aws")

    def test_azure_non_secret_key(self, processor):
        """NCSA-E09: _validate_auth_type_requirements azure非secret_key

        credential_processor.py:95-96 のAzure+非secret_keyエラーをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"

        # Act & Assert
        with pytest.raises(ValidationError, match="secret_key認証タイプが必要です"):
            processor._validate_auth_type_requirements(mock_creds, "azure")

    def test_azure_missing_fields(self, processor):
        """NCSA-E10: _validate_auth_type_requirements azure欠落フィールド

        credential_processor.py:88-89 のAzure必須フィールド欠落をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        mock_creds.tenantId = None
        mock_creds.clientId = "valid"
        mock_creds.clientSecret = None
        mock_creds.subscriptionId = "valid"

        # Act & Assert
        with pytest.raises(ValidationError, match="Azure認証には以下のフィールドが必要です"):
            processor._validate_auth_type_requirements(mock_creds, "azure")

    def test_role_assumption_missing_arn(self, processor):
        """NCSA-E11: _validate_auth_type_requirements role_assumption roleArn欠落

        credential_processor.py:98-99 のroleArn必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"
        mock_creds.roleArn = None

        # Act & Assert
        with pytest.raises(ValidationError, match="roleArnが必要です"):
            processor._validate_auth_type_requirements(mock_creds, "aws")

    def test_secret_key_missing_keys(self, processor):
        """NCSA-E12: _validate_auth_type_requirements secret_keyキー欠落

        credential_processor.py:107-108 のキー必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        mock_creds.accessKey = None
        mock_creds.secretKey = None

        # Act & Assert
        with pytest.raises(ValidationError, match="accessKeyとsecretKeyが必要です"):
            processor._validate_auth_type_requirements(mock_creds, "aws")

    def test_unsupported_auth_type(self, processor):
        """NCSA-E13: _validate_auth_type_requirements未対応タイプ

        credential_processor.py:114-115 の未対応認証タイプをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.authType = "oauth"

        # Act & Assert
        with pytest.raises(ValidationError, match="サポートされていない認証タイプ"):
            processor._validate_auth_type_requirements(mock_creds, "aws")
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCSA-SEC-01 | Azure認証情報ログマスク（auth_handler） | 有効Azure認証 | ログにID先頭8文字+"..."のみ |
| NCSA-SEC-02 | アクセスキーログマスク（auth_handler） | 有効アクセスキー | ログにキー先頭4文字+"..."のみ |
| NCSA-SEC-03 | Azure認証情報ログマスク（credential_processor） | 有効Azure認証 | ログにID先頭8文字+"..."のみ |

```python
@pytest.mark.security
class TestAuthSecurityLogMasking:
    """認証情報ログマスクセキュリティテスト"""

    @pytest.fixture
    def handler(self):
        with patch("app.jobs.tasks.new_custodian_scan.auth_handler.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.auth_handler import AuthenticationHandler
            return AuthenticationHandler("test-sec")

    @pytest.fixture
    def processor(self):
        with patch("app.jobs.tasks.new_custodian_scan.credential_processor.TaskLogger"), \
             patch("app.jobs.tasks.new_custodian_scan.credential_processor.NewCustodianValidators"):
            from app.jobs.tasks.new_custodian_scan.credential_processor import CredentialProcessor
            return CredentialProcessor("test-sec-cp")

    def test_azure_log_masking_auth_handler(self, handler):
        """NCSA-SEC-01: Azure認証情報ログマスク（auth_handler）

        auth_handler.py:152-156 のログ出力を検証。
        認証情報がログに完全な形で記録されないことを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "super-secret-do-not-leak"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act
        handler._get_azure_credentials(mock_creds)

        # Assert（ログ呼出引数を検査）
        log_call = handler.logger.info.call_args
        context = log_call.kwargs.get("context", {})
        assert context["tenant_id"] == "12345678..."
        assert context["client_id"] == "abcdefab..."
        # clientSecretはログに含まれない
        assert "super-secret-do-not-leak" not in str(log_call)

    def test_access_key_log_masking(self, handler):
        """NCSA-SEC-02: アクセスキーログマスク（auth_handler）

        auth_handler.py:191-193 のログ出力を検証。
        アクセスキーの先頭4文字のみが記録されることを確認。
        secretKeyがログに一切含まれないことも検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"
        mock_creds.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        mock_creds.sessionToken = None

        # Act
        handler._validate_access_key_auth(mock_creds)

        # Assert
        log_call = handler.logger.info.call_args
        context = log_call.kwargs.get("context", {})
        assert context["access_key_prefix"] == "AKIA..."
        # 完全なアクセスキーが含まれないこと
        assert "AKIAIOSFODNN7EXAMPLE" not in str(log_call)
        # secretKeyがログに一切含まれないこと
        assert mock_creds.secretKey not in str(log_call)
        assert "secret_key" not in context

    def test_azure_log_masking_credential_processor(self, processor):
        """NCSA-SEC-03: Azure認証情報ログマスク（credential_processor）

        credential_processor.py:90-93 のログ出力を検証。
        credential_processorでもIDがマスクされることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "secret-value"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act
        processor._validate_auth_type_requirements(mock_creds, "azure")

        # Assert
        log_call = processor.logger.info.call_args
        context = log_call.kwargs.get("context", {})
        assert context["tenant_id"] == "12345678..."
        assert "secret-value" not in str(log_call)
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `handler` | 各テストクラス内のAuthenticationHandlerインスタンス（TaskLoggerモック済み） | function | No |
| `processor` | 各テストクラス内のCredentialProcessorインスタンス（TaskLogger/Validatorsモック済み） | function | No |

### フィクスチャ方針

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py
import pytest
from unittest.mock import patch

# フィクスチャ方針:
# - auth_handler.pyとcredential_processor.pyはステートレスなクラスのため、
#   autouseリセットフィクスチャは不要。
# - 各テストクラスでTaskLoggerをモックしたhandler/processorフィクスチャを個別に定義。
# - asyncメソッドのテストには @pytest.mark.asyncio が必要。
# - boto3はテストメソッド内で個別にパッチ（conftest不要）。
#   対象: _execute_assume_role関連テスト（NCSA-007, 007b, 008）のみ。
```

---

## 6. テスト実行例

```bash
# auth関連テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_auth.py -v

# 特定クラスのみ
pytest test/unit/jobs/tasks/new_custodian_scan/test_auth.py::TestGetCredentialsForRegion -v

# カバレッジ付き
pytest test/unit/jobs/tasks/new_custodian_scan/test_auth.py \
  --cov=app.jobs.tasks.new_custodian_scan.auth_handler \
  --cov=app.jobs.tasks.new_custodian_scan.credential_processor \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_auth.py -m "security" -v

# asyncテストのみ
pytest test/unit/jobs/tasks/new_custodian_scan/test_auth.py -k "async" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 31 | NCSA-001 〜 NCSA-027（005b, 007b, 011b, 012b含む） |
| 異常系 | 13 | NCSA-E01 〜 NCSA-E13 |
| セキュリティ | 3 | NCSA-SEC-01 〜 NCSA-SEC-03 |
| **合計** | **47** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestAuthenticationHandlerInit` | NCSA-001 | 1 |
| `TestGetCredentialsForRegion` | NCSA-002〜NCSA-004 | 3 |
| `TestAssumeRoleCredentials` | NCSA-005〜NCSA-008（NCSA-005b, NCSA-007b含む） | 6 |
| `TestAccessKeyAndAzureCredentials` | NCSA-009〜NCSA-011（NCSA-011b含む） | 4 |
| `TestValidateAuthentication` | NCSA-012〜NCSA-017（NCSA-012b含む） | 7 |
| `TestCredentialProcessorInit` | NCSA-018 | 1 |
| `TestParseCredentialsPayload` | NCSA-019 | 1 |
| `TestValidateInputsWrapper` | NCSA-020 | 1 |
| `TestValidateAuthTypeRequirements` | NCSA-021〜NCSA-023 | 3 |
| `TestEnsureScanRegions` | NCSA-024〜NCSA-027 | 4 |
| `TestAuthHandlerErrors` | NCSA-E01〜NCSA-E06 | 6 |
| `TestCredentialProcessorErrors` | NCSA-E07〜NCSA-E13 | 7 |
| `TestAuthSecurityLogMasking` | NCSA-SEC-01〜NCSA-SEC-03 | 3 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 確定対応手順 |
|---------|------|-------------|
| NCSA-007/007b/008 | `_execute_assume_role`はboto3.client('sts')を使用。テスト環境にAWS認証情報がない場合、STSクライアント作成自体が失敗する可能性 | `boto3`モジュールをパッチし、`mock_boto3.client.return_value`でSTSクライアントをモック（テストコードでは対応済み） |
| NCSA-E08 | `NewCredentials`のパース失敗をExceptionラップで検証。Pydantic v2の`ValidationError`がExceptionベースであるため、catchされてValidationErrorに変換される前提 | Pydantic ValidationErrorがException分岐で正しくキャッチされることをテスト実行時に確認 |
| NCSA-SEC-01/02/03 | ログ呼び出しの`context`パラメータ構造が実装と異なる場合、アサーションが失敗する | 実装のlogger.info呼び出しのkwargs構造に合わせてアサーションを調整 |
| NCSA-E01/E03/E04/E05/E06 | `ProcessingError`のコンストラクタは`processing_stage`を第2引数として必須とするが、auth_handler.py L41/L175/L179/L189/L206では第2引数が省略されている。テスト実行時にTypeErrorが発生する可能性 | 実装コードで`processing_stage`引数を追加するか、`ProcessingError`の`processing_stage`にデフォルト値を設定。テスト実行前に確認必要 |

### 注意事項

- テストID命名: `NCSA-XXX`（連番）を基本とし、既存テストの補足ケースには`NCSA-XXXb`サフィックスを使用（例: NCSA-005b は NCSA-005 の補足テスト）
- `get_credentials_for_region`、`_get_assume_role_credentials`、`_execute_assume_role`、`parse_credentials_payload`はasyncメソッド → `@pytest.mark.asyncio`必須
- `boto3.client('sts')`は必ずモックすること（実際のAWS呼び出しを防止）
- `_sts_client`は遅延初期化（L90）のため、初回呼び出し時のみboto3.client作成
- `@pytest.mark.security`マーカーの登録が必要（`pyproject.toml`に`markers = ["security: セキュリティテスト"]`を追加）
- ProcessingError（auth_handler）とValidationError（credential_processor）は異なるエラー型

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_execute_assume_role`のSTS呼び出しはboto3依存 | 実際のAWS環境がなくてもテスト可能だがモック設計が重要 | boto3.clientをモジュールレベルでパッチ |
| 2 | テストARN検出（L51）はハードコードされたパターン | テスト用ARNが変更されるとテスト失敗 | テスト定数として定義し一元管理を推奨 |
| 3 | `validate_authentication`は未対応authTypeに対してエラーを投げない（L168後にログのみ） | silent failureの可能性 | NCSA-012bでこの挙動をテストで明示化。実装修正は別途検討 |
| 4 | `parse_credentials_payload`のException catch（L61）が広すぎる | Pydantic ValidationErrorを含む全例外をValidationErrorに変換 | 本番コードの改善を将来的に検討 |
| 5 | auth_handlerのARN形式チェック（L178）とcredential_processorのARN検証は検証レベルが異なる | auth_handlerは`arn:aws:iam::`プレフィックスのみ検査、credential_processorはroleArn有無のみ検査 | 必要に応じてARN検証の厳格化を本番コードで統一 |
| 6 | エラーメッセージにauthTypeの値が含まれる場合がある | 認証タイプ名は機密情報ではないが、列挙攻撃の手がかりになる可能性 | 現時点では許容範囲。将来的にジェネリックなメッセージへの変更を検討 |
