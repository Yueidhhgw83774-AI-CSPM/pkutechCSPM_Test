# jobs/tasks/new_custodian_scan/validators テストケース

## 1. 概要

`app/jobs/tasks/new_custodian_scan/validators.py` は、新しいCustodianスキャンの入力バリデーション機能を提供するクラス `NewCustodianValidators` を定義します。YAML構文・セキュリティ検証、AWSリージョン・Azure ロケーション検証、AWS/Azure認証情報形式検証、Custodianスキーマ検証を包括的に行います。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `__init__` | job_id設定、TaskLogger初期化 |
| `validate_inputs` | メイン検証エントリ（YAML→リージョン→認証、cloud_provider分岐） |
| `_validate_policy_yaml` | YAML構文解析・構造チェック・セキュリティ・Custodianスキーマ検証 |
| `_validate_individual_policies` | 個別ポリシー構造検証（name/resource必須、ネスト禁止） |
| `_check_yaml_security` | 危険キーワード・サイズ制限チェック |
| `_validate_regions` | AWSリージョン形式検証 |
| `validate_credentials_format` | 認証情報形式ディスパッチャ（role_assumption/secret_key） |
| `_validate_assume_role_format` | AssumeRole形式検証（roleArn、externalId） |
| `_validate_access_key_format` | アクセスキー形式検証（accessKey/secretKey/sessionToken） |
| `_validate_azure_regions` | Azureロケーション形式検証（all-locations対応） |
| `_validate_azure_credentials_format` | Azure認証情報形式検証（4必須フィールド、GUID形式） |
| `_prepare_policy_for_validation` | ポリシーフォーマット検出（JSON/YAML） |
| `_prepare_json_policy` | JSON形式ポリシー準備（3分岐） |
| `_prepare_yaml_policy` | YAML形式ポリシー準備（3分岐） |
| `_validate_with_custodian_tool` | CSPMプラグインvalidate_policy実行 |
| `_extract_readable_error` | エラーメッセージ日本語化（5パターン＋汎用） |

### 1.2 カバレッジ目標: 90%

> **注記**: 437行のバリデーション専用クラス。入力検証はセキュリティの最前線であり高カバレッジが必要。CSPMプラグイン依存部分はモックで検証。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/validators.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_validators.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
validators.py ──→ yaml.safe_load（YAML解析）
              ──→ json.loads, json.dumps（JSON処理）
              ──→ re.match（正規表現検証）
              ──→ common.error_handling.ValidationError
              ──→ common.logging.TaskLogger
              ──→ models.jobs.NewCredentials（Pydanticモデル）
              ──→ cspm_plugin.tools.validate_policy（動的インポート）
```

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `validate_inputs` | L38 | `not policy_yaml_content` | ValidationError |
| `validate_inputs` | L41 | `cloud_provider.lower() not in ["aws","azure"]` | ValidationError |
| `validate_inputs` | L48 | `cloud_provider == "azure"` | Azure検証 / AWS検証 |
| `_validate_policy_yaml` | L61 | `not dict or "policies" not in` | ValidationError |
| `_validate_policy_yaml` | L66 | `not list or len==0` | ValidationError |
| `_validate_policy_yaml` | L88-94 | ValidationError / ImportError / Exception | 再発生 / 警告 / 警告 |
| `_validate_individual_policies` | L103 | `not isinstance(dict)` | ValidationError |
| `_validate_individual_policies` | L107 | `"policies" in policy` | ValidationError（ネスト禁止） |
| `_validate_individual_policies` | L114 | `"name" not in policy` | ValidationError |
| `_validate_individual_policies` | L117 | `"resource" not in policy` | ValidationError |
| `_check_yaml_security` | L130-132 | dangerous keyword | ValidationError |
| `_check_yaml_security` | L135 | size > 1MB | ValidationError |
| `_validate_regions` | L140 | `not regions` | 早期リターン |
| `_validate_regions` | L146 | invalid format | ValidationError |
| `validate_credentials_format` | L156-161 | role_assumption / secret_key / else | 各検証 / ValidationError |
| `_validate_assume_role_format` | L167-176 | roleArn無し / 不正ARN / 短いexternalId | ValidationError |
| `_validate_access_key_format` | L180-193 | キー無し / 不正形式 / 不正長さ / 短いtoken | ValidationError |
| `_validate_azure_regions` | L197 | `not regions` | 早期リターン |
| `_validate_azure_regions` | L201 | `"all-locations"` | 早期リターン |
| `_validate_azure_regions` | L218-224 | invalid format | ValidationError |
| `_validate_azure_credentials_format` | L239 | missing fields | ValidationError |
| `_validate_azure_credentials_format` | L245-252 | 不正GUID | ValidationError |
| `_prepare_policy_for_validation` | L276 | starts with `{` or `[` | JSON / YAML |
| `_prepare_json_policy` | L300-312 | dict+policies / list / dict+name / else | 各処理 / ValidationError |
| `_prepare_yaml_policy` | L333-341 | dict+policies / list / else | 各処理 / ValidationError |
| `_validate_with_custodian_tool` | L369-385 | success / failure / ImportError / Exception | true / false / true(fallback) |
| `_extract_readable_error` | L404-436 | 5パターン＋汎用 | 各日本語メッセージ |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCSV-001 | __init__でTaskLogger初期化 | job_id="test-val" | logger属性が正しく設定 |
| NCSV-002 | validate_inputs AWS正常パス | 有効YAML+AWS認証 | 例外なし（validate_inputs完了） |
| NCSV-003 | validate_inputs Azure正常パス | 有効YAML+Azure認証 | Azure検証メソッドが呼ばれる |
| NCSV-004 | _validate_policy_yaml有効YAML（Custodian ImportError） | 有効YAML | 基本検証のみで成功 |
| NCSV-004b | _validate_policy_yaml Custodian検証失敗→ValidationError | 無効ポリシー | ValidationError("Custodianスキーマ検証エラー") |
| NCSV-004c | _validate_policy_yaml 一般Exception→警告で継続 | 有効YAML（Exception発生） | 警告ログ出力、処理継続 |
| NCSV-005 | _validate_individual_policies有効ポリシー | name+resource | 例外なし |
| NCSV-006 | _validate_regions有効AWSリージョン | ["us-east-1","ap-northeast-1"] | 例外なし |
| NCSV-007 | _validate_regions空リスト（デフォルト許可） | [] | 早期リターン（例外なし） |
| NCSV-008 | _validate_assume_role_format正常 | 有効roleArn | 例外なし |
| NCSV-008b | validate_credentials_format role_assumptionディスパッチ | authType="role_assumption" | _validate_assume_role_formatが呼ばれる |
| NCSV-009 | _validate_access_key_format正常 | 有効accessKey+secretKey | 例外なし |
| NCSV-009b | validate_credentials_format secret_keyディスパッチ | authType="secret_key" | _validate_access_key_formatが呼ばれる |
| NCSV-010 | _validate_azure_regions有効ロケーション | ["japaneast"] | 例外なし |
| NCSV-011 | _validate_azure_regions all-locations | ["all-locations"] | 早期リターン |
| NCSV-012 | _validate_azure_credentials_format正常 | 有効GUID4フィールド | 例外なし、ログマスク確認 |
| NCSV-013 | _prepare_policy_for_validation JSON検出 | "{...}" | ("content","json") |
| NCSV-014 | _prepare_policy_for_validation YAML検出 | "policies:..." | ("content","yaml") |
| NCSV-015 | _prepare_json_policy dict+policies | {"policies":[...]} | そのまま返却 |
| NCSV-016 | _prepare_json_policy list→wrap | [{...}] | {"policies":[...]}にラップ |
| NCSV-017 | _prepare_json_policy single→wrap | {"name":"test"} | {"policies":[{...}]}にラップ |
| NCSV-018 | _prepare_yaml_policy dict+policies | policies:... | JSON変換 |
| NCSV-018b | _prepare_yaml_policy list→wrap | [- name: test] | {"policies":[...]}にラップ |
| NCSV-019 | _validate_with_custodian_tool成功 | validate_policy→"Validation successful" | (True,"") |
| NCSV-020 | _validate_with_custodian_tool ImportError通過 | ImportError | (True,"")（フォールバック） |
| NCSV-020b | _validate_with_custodian_tool検証失敗 | validate_policy→失敗メッセージ | (False, 日本語メッセージ) |
| NCSV-020c | _validate_with_custodian_tool一般Exception | validate_policy→RuntimeError | (True,"")（フォールバック）+警告ログ |
| NCSV-021 | _extract_readable_error無効リソース | "X is not a valid resource" | 日本語メッセージ |
| NCSV-021b | _extract_readable_error KeyErrorパターン | "KeyError: ..." | "スキーマエラー" |
| NCSV-021c | _extract_readable_error ValidationExceptionパターン | "ValidationException..." | "ポリシー構文エラー" |
| NCSV-021f | _extract_readable_error Invalid resource for providerパターン | "Invalid resource: x for provider: aws" | "無効なリソースタイプ（プロバイダー: aws）" |
| NCSV-021d | _extract_readable_error filterエラーパターン | "filter error occurred" | "フィルター構文エラー" |
| NCSV-021e | _extract_readable_error actionエラーパターン | "action error occurred" | "アクション構文エラー" |
| NCSV-022 | _extract_readable_error汎用エラー（200字切り詰め） | 長文エラー | 先頭200字+"..." |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_validators.py
import pytest
from unittest.mock import patch, MagicMock


class TestNewCustodianValidatorsInit:
    """NewCustodianValidators初期化テスト"""

    def test_init_sets_logger(self):
        """NCSV-001: __init__でTaskLogger初期化

        validators.py:28-29 の初期化処理を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger") as mock_logger_cls:
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            validator = NewCustodianValidators("test-val")

        # Assert
        mock_logger_cls.assert_called_once_with("test-val", "NewCustodianValidators")
        assert validator.logger == mock_logger_cls.return_value
```

### 2.2 validate_inputs テスト

```python
class TestValidateInputs:
    """validate_inputsメインエントリテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-inputs")

    def test_validate_inputs_aws_success(self, validator):
        """NCSV-002: validate_inputs AWS正常パス

        validators.py:31-55 のAWSパスを検証。
        _validate_policy_yaml, _validate_regions, validate_credentials_formatが呼ばれることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = ["us-east-1"]
        mock_creds.authType = "role_assumption"
        mock_creds.roleArn = "arn:aws:iam::123456789012:role/test"

        validator._validate_policy_yaml = MagicMock()
        validator._validate_regions = MagicMock()
        validator.validate_credentials_format = MagicMock()

        # Act
        validator.validate_inputs("policies:\n  - name: test\n    resource: aws.ec2", mock_creds, "aws")

        # Assert
        validator._validate_policy_yaml.assert_called_once()
        validator._validate_regions.assert_called_once_with(["us-east-1"])
        validator.validate_credentials_format.assert_called_once_with(mock_creds)

    def test_validate_inputs_azure_success(self, validator):
        """NCSV-003: validate_inputs Azure正常パス

        validators.py:48-50 のAzure分岐を検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.scanRegions = ["japaneast"]

        validator._validate_policy_yaml = MagicMock()
        validator._validate_azure_regions = MagicMock()
        validator._validate_azure_credentials_format = MagicMock()

        # Act
        validator.validate_inputs("policies:\n  - name: test\n    resource: azure.vm", mock_creds, "azure")

        # Assert
        validator._validate_azure_regions.assert_called_once_with(["japaneast"])
        validator._validate_azure_credentials_format.assert_called_once_with(mock_creds)
```

### 2.3 _validate_policy_yaml テスト

```python
class TestValidatePolicyYaml:
    """_validate_policy_yamlテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-yaml")

    def test_valid_yaml_with_custodian_import_error(self, validator):
        """NCSV-004: _validate_policy_yaml有効YAML（Custodian ImportError）

        validators.py:57-98 の正常パスを検証。
        Custodianツールが利用不可でも基本検証のみで成功。
        """
        # Arrange
        valid_yaml = "policies:\n  - name: test-policy\n    resource: aws.ec2"

        # L78-95のPhase 1ブロック内でImportErrorが発生するケース
        # _prepare_policy_for_validationは正常だが、Custodianツール検証不可
        validator._validate_individual_policies = MagicMock()
        validator._check_yaml_security = MagicMock()
        validator._prepare_policy_for_validation = MagicMock(return_value=("{}", "json"))
        validator._validate_with_custodian_tool = MagicMock(side_effect=ImportError)

        # Act（例外が発生しないことを確認）
        validator._validate_policy_yaml(valid_yaml)

        # Assert
        validator._validate_individual_policies.assert_called_once()
        validator._check_yaml_security.assert_called_once()

    def test_custodian_tool_returns_false_raises(self, validator):
        """NCSV-004b: _validate_policy_yaml Custodian検証失敗→ValidationError

        validators.py:82-84 のCustodianツール検証失敗パスを検証。
        _validate_with_custodian_toolが(False, msg)を返した場合にValidationErrorが発生。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        valid_yaml = "policies:\n  - name: test-policy\n    resource: aws.ec2"

        validator._validate_individual_policies = MagicMock()
        validator._check_yaml_security = MagicMock()
        validator._prepare_policy_for_validation = MagicMock(return_value=("{}", "json"))
        validator._validate_with_custodian_tool = MagicMock(return_value=(False, "無効なリソースタイプ"))

        # Act & Assert
        with pytest.raises(ValidationError, match="Custodianスキーマ検証エラー"):
            validator._validate_policy_yaml(valid_yaml)

    def test_general_exception_warns_and_continues(self, validator):
        """NCSV-004c: _validate_policy_yaml 一般Exception→警告で継続

        validators.py:93-95 の一般Exception分岐を検証。
        エラーが発生しても基本検証が成功していれば処理を継続する。
        """
        # Arrange
        valid_yaml = "policies:\n  - name: test-policy\n    resource: aws.ec2"

        validator._validate_individual_policies = MagicMock()
        validator._check_yaml_security = MagicMock()
        validator._prepare_policy_for_validation = MagicMock(side_effect=RuntimeError("unexpected"))

        # Act（例外が発生しないことを確認）
        validator._validate_policy_yaml(valid_yaml)

        # Assert（警告ログが出力される）
        validator.logger.warning.assert_called_once()
        assert "エラーが発生しました" in str(validator.logger.warning.call_args)
```

### 2.4 _validate_individual_policies テスト

```python
class TestValidateIndividualPolicies:
    """_validate_individual_policiesテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-individual")

    def test_valid_policies(self, validator):
        """NCSV-005: _validate_individual_policies有効ポリシー

        validators.py:100-120 の正常パスを検証。
        """
        # Arrange
        policies = [
            {"name": "policy-1", "resource": "aws.ec2"},
            {"name": "policy-2", "resource": "aws.s3"},
        ]

        # Act（例外が発生しないことを確認）
        validator._validate_individual_policies(policies)
```

### 2.5 _validate_regions テスト

```python
class TestValidateRegions:
    """_validate_regionsテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-regions")

    def test_valid_aws_regions(self, validator):
        """NCSV-006: _validate_regions有効AWSリージョン

        validators.py:138-152 の正常パスを検証。
        """
        # Arrange & Act（例外が発生しないことを確認）
        validator._validate_regions(["us-east-1", "ap-northeast-1"])

    def test_empty_regions_allowed(self, validator):
        """NCSV-007: _validate_regions空リスト（デフォルト許可）

        validators.py:140-141 の早期リターンを検証。
        """
        # Arrange & Act（例外が発生しないことを確認）
        validator._validate_regions([])
```

### 2.6 AWS認証情報テスト

```python
class TestAWSCredentialsFormat:
    """AWS認証情報形式テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-aws-creds")

    def test_assume_role_format_valid(self, validator):
        """NCSV-008: _validate_assume_role_format正常

        validators.py:165-176 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.roleArn = "arn:aws:iam::123456789012:role/test-role"
        mock_creds.externalIdValue = "external-id-123"

        # Act（例外が発生しないことを確認）
        validator._validate_assume_role_format(mock_creds)

    def test_credentials_dispatch_role_assumption(self, validator):
        """NCSV-008b: validate_credentials_format role_assumptionディスパッチ

        validators.py:156-157 のrole_assumption分岐を検証。
        validate_credentials_format経由で_validate_assume_role_formatが呼ばれることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "role_assumption"
        validator._validate_assume_role_format = MagicMock()

        # Act
        validator.validate_credentials_format(mock_creds)

        # Assert
        validator._validate_assume_role_format.assert_called_once_with(mock_creds)

    def test_access_key_format_valid(self, validator):
        """NCSV-009: _validate_access_key_format正常

        validators.py:178-193 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"  # 20文字、AKIA始まり
        mock_creds.secretKey = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # 40文字
        mock_creds.sessionToken = None

        # Act（例外が発生しないことを確認）
        validator._validate_access_key_format(mock_creds)

    def test_credentials_dispatch_secret_key(self, validator):
        """NCSV-009b: validate_credentials_format secret_keyディスパッチ

        validators.py:158-159 のsecret_key分岐を検証。
        validate_credentials_format経由で_validate_access_key_formatが呼ばれることを確認。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.authType = "secret_key"
        validator._validate_access_key_format = MagicMock()

        # Act
        validator.validate_credentials_format(mock_creds)

        # Assert
        validator._validate_access_key_format.assert_called_once_with(mock_creds)
```

### 2.7 Azureバリデーションテスト

```python
class TestAzureValidation:
    """Azureバリデーションテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-azure")

    def test_azure_regions_valid(self, validator):
        """NCSV-010: _validate_azure_regions有効ロケーション

        validators.py:195-227 の正常パスを検証。
        """
        # Arrange & Act（例外が発生しないことを確認）
        validator._validate_azure_regions(["japaneast", "eastus"])

    def test_azure_regions_all_locations(self, validator):
        """NCSV-011: _validate_azure_regions all-locations

        validators.py:201-203 の特別値を検証。
        """
        # Arrange & Act（例外が発生しないことを確認）
        validator._validate_azure_regions(["all-locations"])

    def test_azure_credentials_format_valid(self, validator):
        """NCSV-012: _validate_azure_credentials_format正常

        validators.py:229-258 の正常パスを検証。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "test-secret-value"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act（例外が発生しないことを確認）
        validator._validate_azure_credentials_format(mock_creds)

        # Assert（ログにマスクされた情報が記録される）
        validator.logger.info.assert_called_once()
        log_call = validator.logger.info.call_args
        context = log_call.kwargs.get("context", {})
        assert context["tenant_id"] == "12345678..."
        assert context["client_id"] == "abcdefab..."
        # clientSecretはログに含まれない
        assert "test-secret-value" not in str(log_call)
```

### 2.8 ポリシー準備テスト

```python
class TestPreparePolicy:
    """ポリシー準備テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-prepare")

    def test_detect_json_format(self, validator):
        """NCSV-013: _prepare_policy_for_validation JSON検出

        validators.py:276 のJSON判定分岐を検証。
        """
        # Arrange
        json_content = '{"policies": [{"name": "test", "resource": "aws.ec2"}]}'
        validator._prepare_json_policy = MagicMock(return_value=json_content)

        # Act
        result, fmt = validator._prepare_policy_for_validation(json_content)

        # Assert
        assert fmt == "json"
        validator._prepare_json_policy.assert_called_once()

    def test_detect_yaml_format(self, validator):
        """NCSV-014: _prepare_policy_for_validation YAML検出

        validators.py:279-281 のYAML判定分岐を検証。
        """
        # Arrange
        yaml_content = "policies:\n  - name: test"
        validator._prepare_yaml_policy = MagicMock(return_value='{"policies": []}')

        # Act
        result, fmt = validator._prepare_policy_for_validation(yaml_content)

        # Assert
        assert fmt == "yaml"
        validator._prepare_yaml_policy.assert_called_once()

    def test_prepare_json_dict_with_policies(self, validator):
        """NCSV-015: _prepare_json_policy dict+policies

        validators.py:300-302 の既存構造をそのまま返す分岐を検証。
        """
        # Arrange
        content = '{"policies": [{"name": "test", "resource": "aws.ec2"}]}'

        # Act
        result = validator._prepare_json_policy(content)

        # Assert（そのまま返却される）
        assert result == content

    def test_prepare_json_list_wraps(self, validator):
        """NCSV-016: _prepare_json_policy list→wrap

        validators.py:303-306 のリストをpoliciesキーでラップする分岐を検証。
        """
        # Arrange
        import json
        content = '[{"name": "test", "resource": "aws.ec2"}]'

        # Act
        result = validator._prepare_json_policy(content)

        # Assert
        parsed = json.loads(result)
        assert "policies" in parsed
        assert len(parsed["policies"]) == 1

    def test_prepare_json_single_wraps(self, validator):
        """NCSV-017: _prepare_json_policy single→wrap

        validators.py:307-310 の単一ポリシーをラップする分岐を検証。
        """
        # Arrange
        import json
        content = '{"name": "test", "resource": "aws.ec2"}'

        # Act
        result = validator._prepare_json_policy(content)

        # Assert
        parsed = json.loads(result)
        assert "policies" in parsed
        assert len(parsed["policies"]) == 1
        assert parsed["policies"][0]["name"] == "test"

    def test_prepare_yaml_dict_with_policies(self, validator):
        """NCSV-018: _prepare_yaml_policy dict+policies

        validators.py:333-335 のYAML→JSON変換を検証。
        """
        # Arrange
        import json
        yaml_content = "policies:\n  - name: test\n    resource: aws.ec2"

        # Act
        result = validator._prepare_yaml_policy(yaml_content)

        # Assert
        parsed = json.loads(result)
        assert "policies" in parsed

    def test_prepare_yaml_list_wraps(self, validator):
        """NCSV-018b: _prepare_yaml_policy list→wrap

        validators.py:336-339 のリストをpoliciesキーでラップする分岐を検証。
        """
        # Arrange
        import json
        yaml_list_content = "- name: test\n  resource: aws.ec2"

        # Act
        result = validator._prepare_yaml_policy(yaml_list_content)

        # Assert
        parsed = json.loads(result)
        assert "policies" in parsed
        assert isinstance(parsed["policies"], list)
```

### 2.9 Custodianツール検証テスト

```python
class TestValidateWithCustodianTool:
    """_validate_with_custodian_toolテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-custodian")

    def test_validation_success(self, validator):
        """NCSV-019: _validate_with_custodian_tool成功

        validators.py:369-371 の成功パスを検証。
        validate_policyが"Validation successful"を含む結果を返す場合。
        """
        # Arrange
        import sys
        mock_tools_module = MagicMock()
        mock_validate = MagicMock()
        mock_validate.invoke.return_value = "Validation successful - 2 policies validated"
        mock_tools_module.validate_policy = mock_validate

        # Act（動的インポートをsys.modulesでモック）
        with patch.dict(sys.modules, {
            "app.cspm_plugin": MagicMock(),
            "app.cspm_plugin.tools": mock_tools_module,
        }):
            is_valid, error = validator._validate_with_custodian_tool('{"policies":[]}')

        # Assert
        assert is_valid is True
        assert error == ""

    def test_validation_import_error_fallback(self, validator):
        """NCSV-020: _validate_with_custodian_tool ImportError通過

        validators.py:378-381 のImportErrorフォールバックを検証。
        CSPMプラグインが利用不可でも(True,"")で通過。
        """
        # Arrange & Act
        import sys
        # cspm_plugin.toolsを明示的にNoneに設定してImportErrorを強制
        with patch.dict(sys.modules, {
            "app.cspm_plugin": None,
            "app.cspm_plugin.tools": None,
        }):
            is_valid, error = validator._validate_with_custodian_tool('{"policies":[]}')

        # Assert
        assert is_valid is True
        assert error == ""

    def test_validation_failure_returns_error(self, validator):
        """NCSV-020b: _validate_with_custodian_tool検証失敗

        validators.py:372-376 の検証失敗パスを検証。
        validate_policyが"Validation successful"を含まない結果を返す場合。
        """
        # Arrange
        import sys
        mock_tools_module = MagicMock()
        mock_validate = MagicMock()
        mock_validate.invoke.return_value = "aws.invalid-type is not a valid resource"
        mock_tools_module.validate_policy = mock_validate
        validator._extract_readable_error = MagicMock(return_value="テストエラー")

        # Act
        with patch.dict(sys.modules, {
            "app.cspm_plugin": MagicMock(),
            "app.cspm_plugin.tools": mock_tools_module,
        }):
            is_valid, error = validator._validate_with_custodian_tool('{"policies":[]}')

        # Assert
        assert is_valid is False
        assert error == "テストエラー"
        validator._extract_readable_error.assert_called_once()

    def test_validation_general_exception_fallback(self, validator):
        """NCSV-020c: _validate_with_custodian_tool一般Exception

        validators.py:382-384 の一般Exceptionフォールバックを検証。
        validate_policy.invokeが予期せぬ例外を発生させても(True,"")で通過。
        """
        # Arrange
        import sys
        mock_tools_module = MagicMock()
        mock_validate = MagicMock()
        mock_validate.invoke.side_effect = RuntimeError("unexpected error")
        mock_tools_module.validate_policy = mock_validate

        # Act
        with patch.dict(sys.modules, {
            "app.cspm_plugin": MagicMock(),
            "app.cspm_plugin.tools": mock_tools_module,
        }):
            is_valid, error = validator._validate_with_custodian_tool('{"policies":[]}')

        # Assert
        assert is_valid is True
        assert error == ""
        validator.logger.warning.assert_called_once()
```

### 2.10 _extract_readable_error テスト

```python
class TestExtractReadableError:
    """_extract_readable_errorテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-error")

    def test_invalid_resource_pattern(self, validator):
        """NCSV-021: _extract_readable_error無効リソース

        validators.py:404-416 のリソースエラーパターンを検証。
        """
        # Arrange
        result_text = "aws.invalid-type is not a valid resource for policy test"

        # Act
        message = validator._extract_readable_error(result_text)

        # Assert
        assert "無効なリソースタイプ" in message
        assert "aws.invalid-type" in message

    def test_key_error_pattern(self, validator):
        """NCSV-021b: _extract_readable_error KeyErrorパターン

        validators.py:419-420 のKeyErrorパターンを検証。
        """
        # Arrange
        result_text = "Error: KeyError: 'invalid_filter'"

        # Act
        message = validator._extract_readable_error(result_text)

        # Assert
        assert "スキーマエラー" in message

    def test_validation_exception_pattern(self, validator):
        """NCSV-021c: _extract_readable_error ValidationExceptionパターン

        validators.py:422-424 のValidationExceptionパターンを検証。
        """
        # Arrange
        result_text = "ValidationException: Invalid policy structure"

        # Act
        message = validator._extract_readable_error(result_text)

        # Assert
        assert "ポリシー構文エラー" in message

    def test_invalid_resource_for_provider_pattern(self, validator):
        """NCSV-021f: _extract_readable_error Invalid resource for providerパターン

        validators.py:413-416 のプロバイダー付きリソースエラーパターンを検証。
        """
        # Arrange
        result_text = "Invalid resource: invalid-type for provider: aws"

        # Act
        message = validator._extract_readable_error(result_text)

        # Assert
        assert "無効なリソースタイプ" in message
        assert "プロバイダー: aws" in message

    def test_filter_error_pattern(self, validator):
        """NCSV-021d: _extract_readable_error filterエラーパターン

        validators.py:427-428 のフィルターエラーパターンを検証。
        """
        # Arrange
        result_text = "Filter error: unknown filter type specified"

        # Act
        message = validator._extract_readable_error(result_text)

        # Assert
        assert "フィルター構文エラー" in message

    def test_action_error_pattern(self, validator):
        """NCSV-021e: _extract_readable_error actionエラーパターン

        validators.py:430-431 のアクションエラーパターンを検証。
        """
        # Arrange
        result_text = "Action error: invalid action configuration"

        # Act
        message = validator._extract_readable_error(result_text)

        # Assert
        assert "アクション構文エラー" in message

    def test_generic_error_truncation(self, validator):
        """NCSV-022: _extract_readable_error汎用エラー（200字切り詰め）

        validators.py:433-436 の汎用エラー切り詰めを検証。
        """
        # Arrange
        long_error = "A" * 300

        # Act
        message = validator._extract_readable_error(long_error)

        # Assert
        assert message.endswith("...")
        assert "Custodian検証エラー" in message
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCSV-E01 | validate_inputs空YAML | "" | ValidationError("ポリシーYAMLが空です") |
| NCSV-E02 | validate_inputs未対応プロバイダー | cloud_provider="gcp" | ValidationError("現在サポートされているのはAWSとAzureです") |
| NCSV-E03 | _validate_policy_yaml不正YAML構文 | "{{invalid" | ValidationError("不正なYAML形式です") |
| NCSV-E04 | _validate_policy_yaml policiesキーなし | "name: test" | ValidationError("有効なCustodianポリシーYAML") |
| NCSV-E05 | _validate_policy_yaml policies空リスト | "policies: []" | ValidationError("policiesは空でないリスト") |
| NCSV-E06 | _validate_individual_policiesネスト構造 | policies内にpoliciesキー | ValidationError("不正な構造") |
| NCSV-E06b | _validate_individual_policies非dict要素 | [123] | ValidationError("ポリシーはオブジェクトである必要があります") |
| NCSV-E07 | _validate_individual_policies name不足 | {"resource":"aws.ec2"} | ValidationError("'name'フィールドが必要です") |
| NCSV-E08 | _validate_individual_policies resource不足 | {"name":"test"} | ValidationError("'resource'フィールドが必要です") |
| NCSV-E09 | _validate_regions不正形式 | ["INVALID!"] | ValidationError("不正なリージョン形式") |
| NCSV-E10 | validate_credentials_format未対応authType | authType="oauth" | ValidationError("サポートされていない認証タイプ") |
| NCSV-E11 | _validate_assume_role_format roleArn不正 | roleArn="invalid" | ValidationError("無効なIAMロールARN形式") |
| NCSV-E11b | _validate_assume_role_format roleArn欠落 | roleArn=None | ValidationError("AssumeRole認証にはroleArnが必要です") |
| NCSV-E12 | _validate_access_key_format不正形式 | accessKey="short" | ValidationError("無効なAWSアクセスキー形式") |
| NCSV-E12b | _validate_access_key_format sessionToken短すぎ | sessionToken="short" | ValidationError("無効なセッショントークン形式") |
| NCSV-E12c | _validate_access_key_format キー欠落 | accessKey=None | ValidationError("accessKeyとsecretKeyが必要です") |
| NCSV-E13 | _validate_azure_regions不正形式 | ["AB!"] | ValidationError("不正なAzureロケーション形式") |
| NCSV-E14 | _validate_azure_credentials_format不正GUID | tenantId="invalid" | ValidationError("無効なAzureテナントID形式") |
| NCSV-E14b | _validate_azure_credentials_format必須フィールド欠落 | tenantId="" | ValidationError("Azure認証には以下のフィールドが必要です") |
| NCSV-E15 | _prepare_json_policy無効構造 | {"other":"data"} | ValidationError("無効なJSON構造") |
| NCSV-E16 | _prepare_json_policy JSONDecodeError | "not json{" | ValidationError("無効なJSON形式") |
| NCSV-E16b | _prepare_yaml_policy無効構造 | "key: value"（policies/listなし） | ValidationError("無効なYAML構造です") |
| NCSV-E16c | _prepare_yaml_policy YAML構文エラー | "{{invalid" | ValidationError("無効なYAML形式です") |

### 3.1 validate_inputs 異常系

```python
class TestValidateInputsErrors:
    """validate_inputs入力検証エラーテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-err")

    def test_empty_yaml_raises(self, validator):
        """NCSV-E01: validate_inputs空YAML

        validators.py:38-39 の空YAMLチェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()

        # Act & Assert
        with pytest.raises(ValidationError, match="ポリシーYAMLが空です"):
            validator.validate_inputs("", mock_creds, "aws")

    def test_unsupported_provider_raises(self, validator):
        """NCSV-E02: validate_inputs未対応プロバイダー

        validators.py:41-42 のプロバイダーチェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()

        # Act & Assert
        with pytest.raises(ValidationError, match="現在サポートされているのはAWSとAzureです"):
            validator.validate_inputs("policies:\n  - name: test", mock_creds, "gcp")
```

### 3.2 _validate_policy_yaml 異常系

```python
class TestValidatePolicyYamlErrors:
    """_validate_policy_yaml異常系テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-yaml-err")

    def test_invalid_yaml_syntax(self, validator):
        """NCSV-E03: _validate_policy_yaml不正YAML構文

        validators.py:97-98 のYAMLErrorキャッチをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="不正なYAML形式です"):
            validator._validate_policy_yaml("{{invalid yaml: [")

    def test_no_policies_key(self, validator):
        """NCSV-E04: _validate_policy_yaml policiesキーなし

        validators.py:61-62 のpoliciesキー不在をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="有効なCustodianポリシーYAML"):
            validator._validate_policy_yaml("name: test\nresource: aws.ec2")

    def test_empty_policies_list(self, validator):
        """NCSV-E05: _validate_policy_yaml policies空リスト

        validators.py:66-67 の空リストチェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="policiesは空でないリスト"):
            validator._validate_policy_yaml("policies: []")
```

### 3.3 _validate_individual_policies 異常系

```python
class TestValidateIndividualPoliciesErrors:
    """_validate_individual_policies異常系テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-ind-err")

    def test_nested_policies_structure(self, validator):
        """NCSV-E06: _validate_individual_policiesネスト構造

        validators.py:107-111 のネスト禁止チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        policies = [{"name": "test", "resource": "aws.ec2", "policies": []}]

        # Act & Assert
        with pytest.raises(ValidationError, match="不正な構造"):
            validator._validate_individual_policies(policies)

    def test_non_dict_policy_element(self, validator):
        """NCSV-E06b: _validate_individual_policies非dict要素

        validators.py:103-104 の非dictポリシー要素をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        policies = [123]  # dictではない要素

        # Act & Assert
        with pytest.raises(ValidationError, match="ポリシーはオブジェクトである必要があります"):
            validator._validate_individual_policies(policies)

    def test_missing_name_field(self, validator):
        """NCSV-E07: _validate_individual_policies name不足

        validators.py:114-115 のname必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        policies = [{"resource": "aws.ec2"}]

        # Act & Assert
        with pytest.raises(ValidationError, match="'name'フィールドが必要です"):
            validator._validate_individual_policies(policies)

    def test_missing_resource_field(self, validator):
        """NCSV-E08: _validate_individual_policies resource不足

        validators.py:117-118 のresource必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        policies = [{"name": "test-policy"}]

        # Act & Assert
        with pytest.raises(ValidationError, match="'resource'フィールドが必要です"):
            validator._validate_individual_policies(policies)
```

### 3.4 リージョン・認証情報 異常系

```python
class TestRegionAndCredentialErrors:
    """リージョン・認証情報異常系テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-region-err")

    def test_invalid_region_format(self, validator):
        """NCSV-E09: _validate_regions不正形式

        validators.py:146-150 の不正リージョン検出をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（大文字や特殊文字を含むリージョン）
        with pytest.raises(ValidationError, match="不正なリージョン形式"):
            validator._validate_regions(["INVALID!", "us-east-1"])

    def test_unsupported_auth_type(self, validator):
        """NCSV-E10: validate_credentials_format未対応authType

        validators.py:160-161 の未対応認証タイプをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.authType = "oauth"

        # Act & Assert
        with pytest.raises(ValidationError, match="サポートされていない認証タイプ"):
            validator.validate_credentials_format(mock_creds)

    def test_invalid_role_arn_format(self, validator):
        """NCSV-E11: _validate_assume_role_format roleArn不正

        validators.py:171-172 のARN形式チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.roleArn = "invalid-arn-format"

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なIAMロールARN形式"):
            validator._validate_assume_role_format(mock_creds)

    def test_missing_role_arn(self, validator):
        """NCSV-E11b: _validate_assume_role_format roleArn欠落

        validators.py:167-168 のroleArn必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.roleArn = None

        # Act & Assert
        with pytest.raises(ValidationError, match="AssumeRole認証にはroleArnが必要です"):
            validator._validate_assume_role_format(mock_creds)

    def test_invalid_access_key_format(self, validator):
        """NCSV-E12: _validate_access_key_format不正形式

        validators.py:184-185 のアクセスキー形式チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.accessKey = "SHORT"
        mock_creds.secretKey = "x" * 40

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なAWSアクセスキー形式"):
            validator._validate_access_key_format(mock_creds)

    def test_short_session_token(self, validator):
        """NCSV-E12b: _validate_access_key_format sessionToken短すぎ

        validators.py:192-193 のsessionToken長さチェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"  # 正しい形式
        mock_creds.secretKey = "x" * 40  # 正しい長さ
        mock_creds.sessionToken = "short"  # 10文字未満（不正）

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なセッショントークン形式"):
            validator._validate_access_key_format(mock_creds)

    def test_missing_access_key_and_secret_key(self, validator):
        """NCSV-E12c: _validate_access_key_format キー欠落

        validators.py:180-181 のaccessKey/secretKey必須チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.accessKey = None
        mock_creds.secretKey = None

        # Act & Assert
        with pytest.raises(ValidationError, match="accessKeyとsecretKeyが必要です"):
            validator._validate_access_key_format(mock_creds)
```

### 3.5 Azure異常系

```python
class TestAzureValidationErrors:
    """Azure異常系テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-azure-err")

    def test_invalid_azure_region_format(self, validator):
        """NCSV-E13: _validate_azure_regions不正形式

        validators.py:218-225 の不正ロケーション検出をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（4文字未満のロケーション）
        with pytest.raises(ValidationError, match="不正なAzureロケーション形式"):
            validator._validate_azure_regions(["AB!"])

    def test_azure_missing_required_fields(self, validator):
        """NCSV-E14b: _validate_azure_credentials_format必須フィールド欠落

        validators.py:239-240 のmissing_fieldsチェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.tenantId = ""  # 空文字列
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = ""  # 空文字列
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act & Assert
        with pytest.raises(ValidationError, match="Azure認証には以下のフィールドが必要です"):
            validator._validate_azure_credentials_format(mock_creds)

    def test_invalid_azure_tenant_guid(self, validator):
        """NCSV-E14: _validate_azure_credentials_format不正GUID

        validators.py:245-246 のGUID形式チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.tenantId = "invalid-guid"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "secret"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なAzureテナントID形式"):
            validator._validate_azure_credentials_format(mock_creds)
```

### 3.6 ポリシー準備 異常系

```python
class TestPreparePolicyErrors:
    """ポリシー準備異常系テスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-prep-err")

    def test_json_invalid_structure(self, validator):
        """NCSV-E15: _prepare_json_policy無効構造

        validators.py:311-312 のelse分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（policiesキーもnameキーもないdict）
        with pytest.raises(ValidationError, match="無効なJSON構造"):
            validator._prepare_json_policy('{"other": "data"}')

    def test_json_decode_error(self, validator):
        """NCSV-E16: _prepare_json_policy JSONDecodeError

        validators.py:314-315 のJSONDecodeErrorをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なJSON形式"):
            validator._prepare_json_policy("not json{")

    def test_yaml_invalid_structure(self, validator):
        """NCSV-E16b: _prepare_yaml_policy無効構造

        validators.py:340-341 のelse分岐をカバー。
        policiesキーもリストも持たないdict。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（policiesキーなし、リストでもないYAML）
        with pytest.raises(ValidationError, match="無効なYAML構造です"):
            validator._prepare_yaml_policy("key: value\nother: data")

    def test_yaml_syntax_error(self, validator):
        """NCSV-E16c: _prepare_yaml_policy YAML構文エラー

        validators.py:343-344 のYAMLError分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert（不正なYAML構文）
        with pytest.raises(ValidationError, match="無効なYAML形式です"):
            validator._prepare_yaml_policy("{{invalid yaml: [")
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCSV-SEC-01 | 危険YAMLキーワード検出（コード実行防止） | "exec"含むYAML | ValidationError("危険なキーワードが検出") |
| NCSV-SEC-02 | YAMLサイズ制限（DoS対策） | 1MB超YAML | ValidationError("サイズが制限を超えています") |
| NCSV-SEC-03 | Azure認証情報ログマスク確認 | 有効Azure認証 | ログにIDの先頭8文字+"..."のみ記録 |
| NCSV-SEC-04 | AWSシークレットキー長の厳密検証 | 39文字シークレットキー | ValidationError（不正長さ） |

```python
@pytest.mark.security
class TestValidatorsSecurity:
    """NewCustodianValidatorsセキュリティテスト"""

    @pytest.fixture
    def validator(self):
        with patch("app.jobs.tasks.new_custodian_scan.validators.TaskLogger"):
            from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
            return NewCustodianValidators("test-val-sec")

    def test_dangerous_keyword_detection(self, validator):
        """NCSV-SEC-01: 危険YAMLキーワード検出（コード実行防止）

        validators.py:122-132 のセキュリティチェックを検証。
        YAML内にexec/system/eval等のコード実行キーワードが含まれていないことを確認。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        # 各危険キーワードをテスト
        dangerous_yamls = [
            "policies:\n  exec: true",
            "policies:\n  cmd: os.system('rm -rf /')",
            "policies:\n  code: eval('malicious')",
            "policies:\n  hack: __import__('os')",
        ]

        # Act & Assert
        for yaml_content in dangerous_yamls:
            with pytest.raises(ValidationError, match="危険なキーワードが検出されました"):
                validator._check_yaml_security(yaml_content)

    def test_yaml_size_limit_dos_prevention(self, validator):
        """NCSV-SEC-02: YAMLサイズ制限（DoS対策）

        validators.py:134-136 のサイズ制限を検証。
        1MBを超えるYAMLが拒否されることを確認（大容量攻撃の防止）。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        # 1MB超のYAMLを生成
        large_yaml = "a" * (1024 * 1024 + 1)

        # Act & Assert
        with pytest.raises(ValidationError, match="サイズが制限.*を超えています"):
            validator._check_yaml_security(large_yaml)

    def test_azure_credentials_log_masking(self, validator):
        """NCSV-SEC-03: Azure認証情報ログマスク確認

        validators.py:254-258 のログ出力を検証。
        認証情報がログに完全な形で記録されないことを確認する回帰テスト。
        """
        # Arrange
        mock_creds = MagicMock()
        mock_creds.tenantId = "12345678-1234-1234-1234-123456789012"
        mock_creds.clientId = "abcdefab-abcd-abcd-abcd-abcdefabcdef"
        mock_creds.clientSecret = "super-secret-value-do-not-leak"
        mock_creds.subscriptionId = "99999999-9999-9999-9999-999999999999"

        # Act
        validator._validate_azure_credentials_format(mock_creds)

        # Assert（ログ呼出の引数を検査）
        log_call = validator.logger.info.call_args
        context = log_call.kwargs.get("context", {})

        # IDは先頭8文字+"..."でマスクされている
        assert context["tenant_id"] == "12345678..."
        assert context["client_id"] == "abcdefab..."
        # clientSecretはログに含まれない
        assert "super-secret-value" not in str(log_call)

    def test_aws_secret_key_strict_length(self, validator):
        """NCSV-SEC-04: AWSシークレットキー長の厳密検証

        validators.py:188-189 の長さ検証を確認。
        シークレットキーが40文字でない場合に拒否されることで、
        不正な認証情報の使用を防止。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        mock_creds = MagicMock()
        mock_creds.accessKey = "AKIAIOSFODNN7EXAMPLE"  # 正しい形式
        mock_creds.secretKey = "x" * 39  # 39文字（不正）

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なAWSシークレットキー形式"):
            validator._validate_access_key_format(mock_creds)
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `validator` | 各テストクラス内のNewCustodianValidatorsインスタンス（TaskLoggerモック済み） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py
import pytest
from unittest.mock import patch


# 注: validators.pyはステートレスなクラスのため、
# status_managerリセット等のautouseフィクスチャは不要。
# 各テストクラスではTaskLoggerをモックしたvalidatorフィクスチャを
# 個別に定義して使用する。
```

---

## 6. テスト実行例

```bash
# validators関連テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_validators.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_validators.py::TestValidateInputs -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_validators.py --cov=app.jobs.tasks.new_custodian_scan.validators --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_validators.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 34 | NCSV-001 〜 NCSV-022（008b, 009b, 004b, 004c, 018b, 020b, 020c, 021b〜021f含む） |
| 異常系 | 23 | NCSV-E01 〜 NCSV-E16c（E06b, E11b, E12b, E12c, E14b, E16b含む） |
| セキュリティ | 4 | NCSV-SEC-01 〜 NCSV-SEC-04 |
| **合計** | **61** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestNewCustodianValidatorsInit` | NCSV-001 | 1 |
| `TestValidateInputs` | NCSV-002〜NCSV-003 | 2 |
| `TestValidatePolicyYaml` | NCSV-004, 004b, 004c | 3 |
| `TestValidateIndividualPolicies` | NCSV-005 | 1 |
| `TestValidateRegions` | NCSV-006〜NCSV-007 | 2 |
| `TestAWSCredentialsFormat` | NCSV-008〜NCSV-009b（008b含む） | 4 |
| `TestAzureValidation` | NCSV-010〜NCSV-012 | 3 |
| `TestPreparePolicy` | NCSV-013〜NCSV-018b | 7 |
| `TestValidateWithCustodianTool` | NCSV-019〜NCSV-020c | 4 |
| `TestExtractReadableError` | NCSV-021〜NCSV-022（021b〜021f含む） | 7 |
| `TestValidateInputsErrors` | NCSV-E01〜NCSV-E02 | 2 |
| `TestValidatePolicyYamlErrors` | NCSV-E03〜NCSV-E05 | 3 |
| `TestValidateIndividualPoliciesErrors` | NCSV-E06, E06b〜NCSV-E08 | 4 |
| `TestRegionAndCredentialErrors` | NCSV-E09〜NCSV-E12c（E11b, E12b含む） | 7 |
| `TestAzureValidationErrors` | NCSV-E13〜NCSV-E14b | 3 |
| `TestPreparePolicyErrors` | NCSV-E15〜NCSV-E16c | 4 |
| `TestValidatorsSecurity` | NCSV-SEC-01〜NCSV-SEC-04 | 4 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 確定対応手順 |
|---------|------|-------------|
| NCSV-019/020 | `_validate_with_custodian_tool`の動的インポート（L361）のモックはsys.modulesパッチで対応。CSPMプラグインがインストール済みの環境では、既存のインポートキャッシュが干渉する可能性がある | **手順**: (1) `sys.modules`から`app.cspm_plugin`関連キーを`pop`で削除 → (2) `patch.dict(sys.modules, {...})`で注入 → (3) テスト後にコンテキストマネージャが自動復元。成功パス(NCSV-019)は`MagicMock()`を注入、失敗パス(NCSV-020)は`None`を設定してImportError強制 |

### 注意事項

- `_validate_with_custodian_tool` のテストではCSPMプラグインの動的インポート（L361）をモックする必要あり
- `_check_yaml_security` は大文字小文字を区別しない検査（L129: `yaml_lower`）
- `_validate_azure_regions` の `valid_azure_locations` リストは実装内にハードコードされた参考値（L207-213）
- `@pytest.mark.security` マーカーの登録が必要（`pyproject.toml` の `[tool.pytest.ini_options]` に `markers = ["security: セキュリティテスト"]` を追加すること）
- テストID命名規則: サフィックス付きID（例: 004b, E12b）はレビュー過程で追加されたテストを示す

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_validate_with_custodian_tool` はCSPMプラグインに依存 | 動的インポートのモックが複雑 | builtins.__import__パッチまたはsys.modulesパッチで対応 |
| 2 | `valid_azure_locations` リストは不完全（参考情報） | 新しいAzureリージョンが追加されても警告のみ | ログ警告を検証し、ValidationErrorにならないことを確認 |
| 3 | `_check_yaml_security` のキーワードリストは基本的なもの | 高度な難読化攻撃は検出不可 | より堅牢なセキュリティスキャナーの導入を将来的に検討 |
| 4 | AWS ARN形式検証は`arn:aws:iam::`プレフィックスのみ | GovCloudやChinaリージョンの`arn:aws-*`は検証不可 | 実際のARN検証はAssumeRole実行時にAWSが行う |
