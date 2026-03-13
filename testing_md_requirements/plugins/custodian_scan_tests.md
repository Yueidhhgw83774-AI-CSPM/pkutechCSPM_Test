# custodian_scan プラグインテストケース

## 1. 概要

Cloud Custodianスキャン機能のテストケースを定義します。AWS/Azureのクラウドリソースをポリシーベースでスキャンし、セキュリティ違反を検出する重要機能です。

### 1.1 主要機能

| 機能 | エンドポイント | 説明 |
|------|---------------|------|
| スキャン開始（旧） | POST /api/custodian/start_custodian_scan_async | 従来形式のスキャン実行 |
| コマンドプレビュー | POST /api/custodian/preview_custodian_command | 実行コマンドの事前確認 |
| ジョブステータス | GET /api/custodian/jobs/{job_id}/status | ジョブ状態取得 |
| ジョブ結果 | GET /api/custodian/jobs/{job_id}/result | スキャン結果取得 |
| 新スキャン開始 | POST /api/jobs/new_start_custodian_scan_async | 新形式のマルチリージョンスキャン |

> **注記**: エンドポイントは main.py でルーターをマウントする際のプレフィックス（`/api/custodian`）を含む

### 1.2 カバレッジ目標: 80%

> セキュリティ重要機能を含むため、カバレッジ目標を75%から80%に引き上げ

### 1.3 主要ファイル

| ファイル | 説明 |
|---------|------|
| `app/custodian_scan/router.py` | エンドポイント定義 |
| `app/jobs/tasks/custodian_scan.py` | 旧スキャンタスク実装 |
| `app/jobs/tasks/new_custodian_scan/main_task.py` | 新スキャンタスク実装 |
| `app/jobs/tasks/new_custodian_scan/validators.py` | 入力検証ロジック |
| `app/jobs/tasks/new_custodian_scan/credential_processor.py` | 認証情報処理 |
| `app/jobs/tasks/new_custodian_scan/scan_coordinator.py` | スキャン調整 |
| `app/jobs/tasks/new_custodian_scan/executor/security_sanitizer.py` | セキュリティサニタイズ |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SCAN-001 | スキャン開始成功 | valid policy + credentials | job_id返却、status: started |
| SCAN-002 | コマンドプレビュー成功 | valid policy + credentials | preview data |
| SCAN-003 | ジョブステータス取得 | valid job_id | status情報 |
| SCAN-004 | 新スキャン開始成功 | NewCredentials + policy | job_id返却 |
| SCAN-005 | マルチリージョンスキャン | multiple regions | 全リージョン結果 |
| SCAN-006 | 違反検出時のOpenSearch保存 | policy with violations | 違反データ保存成功 |
| SCAN-007 | 違反なし時の正常完了 | compliant resources | no_violations_detected: true |

```python
# test/unit/custodian_scan/test_router.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

class TestCustodianScanRouter:
    """POST /custodian/start_custodian_scan_async のテスト"""

    @pytest.mark.asyncio
    async def test_scan_start_success(
        self,
        async_client: AsyncClient,
        valid_policy_yaml: str,
        valid_aws_credentials: dict
    ):
        """SCAN-001: スキャン開始成功"""
        # Arrange
        request_data = {
            "policy_yaml_content": valid_policy_yaml,
            "credentials_data": valid_aws_credentials,
            "cloud_provider": "aws"
        }

        # Act
        with patch("app.custodian_scan.router.run_custodian_scan_task"):
            response = await async_client.post(
                "/api/custodian/start_custodian_scan_async",
                json=request_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_command_preview_success(
        self,
        async_client: AsyncClient,
        valid_policy_yaml: str,
        valid_aws_credentials: dict
    ):
        """SCAN-002: コマンドプレビュー成功"""
        # Arrange
        request_data = {
            "policy_yaml_content": valid_policy_yaml,
            "credentials_data": valid_aws_credentials,
            "cloud_provider": "aws"
        }

        # Act
        with patch(
            "app.custodian_scan.router.CustodianCommandPreview"
        ) as mock_preview:
            mock_instance = AsyncMock()
            mock_instance.generate_command_preview.return_value = {
                "command": "custodian run ...",
                "regions": ["ap-northeast-1"]
            }
            mock_preview.return_value = mock_instance

            response = await async_client.post(
                "/api/custodian/preview_custodian_command",
                json=request_data
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "preview" in data

    @pytest.mark.asyncio
    async def test_get_job_status(self, async_client: AsyncClient):
        """SCAN-003: ジョブステータス取得"""
        # Act
        response = await async_client.get(
            "/api/custodian/jobs/test-job-123/status"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-123"
        assert "status" in data
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SCAN-E01 | 空のポリシーYAML | empty policy | ValidationError |
| SCAN-E02 | 無効なYAML形式 | malformed YAML | ValidationError |
| SCAN-E03 | 認証情報なし | empty credentials | ValidationError |
| SCAN-E04 | 無効なクラウドプロバイダー | cloud_provider: "invalid" | ValidationError |
| SCAN-E05 | 無効なAWSアクセスキー形式 | invalid access key | ValidationError |
| SCAN-E06 | 無効なAzure GUID形式 | invalid tenant_id | ValidationError |
| SCAN-E07 | ポリシーに危険なキーワード | exec in policy | ValidationError |
| SCAN-E08 | ポリシーサイズ超過 | >1MB policy | ValidationError |
| SCAN-E09 | 無効なリージョン形式 | invalid region | ValidationError |
| SCAN-E10 | Custodian実行タイムアウト | long running scan | ProcessingError |

```python
class TestCustodianScanErrors:
    """スキャンエラーのテスト"""

    @pytest.mark.asyncio
    async def test_empty_policy_error(
        self,
        async_client: AsyncClient,
        valid_aws_credentials: dict
    ):
        """SCAN-E01: 空のポリシーYAMLで検証エラー"""
        # Arrange
        request_data = {
            "policy_yaml_content": "",
            "credentials_data": valid_aws_credentials,
            "cloud_provider": "aws"
        }

        # Act
        response = await async_client.post(
            "/api/custodian/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 500
        assert "ポリシーYAMLが空です" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_yaml_error(
        self,
        async_client: AsyncClient,
        valid_aws_credentials: dict
    ):
        """SCAN-E02: 無効なYAML形式で検証エラー"""
        # Arrange
        request_data = {
            "policy_yaml_content": "invalid: yaml: content: [",
            "credentials_data": valid_aws_credentials,
            "cloud_provider": "aws"
        }

        # Act
        response = await async_client.post(
            "/api/custodian/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_unsupported_cloud_provider(
        self,
        async_client: AsyncClient,
        valid_policy_yaml: str,
        valid_aws_credentials: dict
    ):
        """SCAN-E04: サポートされていないクラウドプロバイダー"""
        # Arrange
        request_data = {
            "policy_yaml_content": valid_policy_yaml,
            "credentials_data": valid_aws_credentials,
            "cloud_provider": "gcp"  # 未サポート
        }

        # Act
        response = await async_client.post(
            "/api/custodian/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 500
        assert "サポートされていない" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_custodian_timeout_error(
        self,
        async_client: AsyncClient,
        valid_policy_yaml: str,
        valid_aws_credentials: dict
    ):
        """SCAN-E10: Custodian実行タイムアウト"""
        # Arrange
        request_data = {
            "policy_yaml_content": valid_policy_yaml,
            "credentials_data": valid_aws_credentials,
            "cloud_provider": "aws"
        }

        # Act
        with patch(
            "app.jobs.tasks.custodian_scan.CustodianScanTask._run_custodian_command",
            new_callable=AsyncMock
        ) as mock_run:
            from app.jobs.common.error_handling import ProcessingError
            mock_run.side_effect = ProcessingError(
                "Custodianスキャンがタイムアウトしました（30分）"
            )

            response = await async_client.post(
                "/api/custodian/start_custodian_scan_async",
                json=request_data
            )

        # Assert - バックグラウンドタスクなので即座にエラーにならない
        # タイムアウトはジョブ結果取得時に確認される
        assert response.status_code == 200
```

---

## 4. バリデーションテスト

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| SCAN-VAL-001 | YAML構文検証 | yaml.safe_loadで解析可能 |
| SCAN-VAL-002 | policiesキー存在検証 | policies配列が存在 |
| SCAN-VAL-003 | ポリシー必須フィールド | name, resource必須 |
| SCAN-VAL-004 | 危険キーワード検出 | exec, systemなど除外 |
| SCAN-VAL-005 | AWSアクセスキー形式 | AKIA開始、20文字 |
| SCAN-VAL-006 | AWSシークレットキー形式 | 40文字 |
| SCAN-VAL-007 | AWSリージョン形式 | 6-20文字、小文字・数字・ハイフン |
| SCAN-VAL-008 | Azure GUID形式 | UUID形式検証 |
| SCAN-VAL-009 | AssumeRole ARN形式 | arn:aws:iam::開始 |
| SCAN-VAL-010 | Azureリージョン検証 | all-locations特別値、一般ロケーション |

```python
# test/unit/custodian_scan/test_validators.py
import pytest
from app.jobs.tasks.new_custodian_scan.validators import NewCustodianValidators
from app.jobs.common.error_handling import ValidationError

class TestNewCustodianValidators:
    """バリデーションロジックのテスト"""

    @pytest.fixture
    def validators(self):
        return NewCustodianValidators("test-job-001")

    def test_valid_policy_yaml(self, validators, valid_policy_yaml):
        """SCAN-VAL-001: 有効なYAML構文"""
        # Act & Assert - 例外が発生しなければOK
        validators._validate_policy_yaml(valid_policy_yaml)

    def test_policy_missing_policies_key(self, validators):
        """SCAN-VAL-002: policiesキーがないYAML"""
        # Arrange
        invalid_yaml = """
        name: test-policy
        resource: aws.ec2
        """

        # Act & Assert
        with pytest.raises(ValidationError, match="有効なCustodianポリシー"):
            validators._validate_policy_yaml(invalid_yaml)

    def test_policy_missing_required_fields(self, validators):
        """SCAN-VAL-003: 必須フィールド不足"""
        # Arrange
        invalid_yaml = """
policies:
  - description: missing name and resource
        """

        # Act & Assert
        with pytest.raises(ValidationError, match="'name'フィールドが必要"):
            validators._validate_policy_yaml(invalid_yaml)

    def test_dangerous_keyword_detection(self, validators):
        """SCAN-VAL-004: 危険なキーワード検出"""
        # Arrange
        dangerous_yaml = """
policies:
  - name: dangerous-policy
    resource: aws.ec2
    actions:
      - type: exec
        command: rm -rf /
        """

        # Act & Assert
        with pytest.raises(ValidationError, match="危険なキーワード"):
            validators._validate_policy_yaml(dangerous_yaml)

    def test_aws_access_key_format(self, validators, mock_credentials_access_key):
        """SCAN-VAL-005: 無効なAWSアクセスキー形式"""
        # Arrange
        mock_credentials_access_key.accessKey = "INVALID_KEY"

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なAWSアクセスキー"):
            validators._validate_access_key_format(mock_credentials_access_key)

    def test_aws_secret_key_length(self, validators, mock_credentials_access_key):
        """SCAN-VAL-006: AWSシークレットキーの長さ検証"""
        # Arrange
        mock_credentials_access_key.secretKey = "short"

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なAWSシークレットキー"):
            validators._validate_access_key_format(mock_credentials_access_key)

    def test_azure_guid_format(self, validators, mock_azure_credentials):
        """SCAN-VAL-008: 無効なAzure GUID形式"""
        # Arrange
        mock_azure_credentials.tenantId = "not-a-guid"

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なAzureテナントID"):
            validators._validate_azure_credentials_format(mock_azure_credentials)

    def test_assume_role_arn_format(self, validators, mock_credentials_assume_role):
        """SCAN-VAL-009: 無効なIAMロールARN"""
        # Arrange
        mock_credentials_assume_role.roleArn = "invalid-arn"

        # Act & Assert
        with pytest.raises(ValidationError, match="無効なIAMロールARN"):
            validators._validate_assume_role_format(mock_credentials_assume_role)

    def test_azure_regions_all_locations(self, validators):
        """SCAN-VAL-010: Azureリージョン検証（all-locations特別値）"""
        # Arrange
        regions = ["all-locations"]

        # Act & Assert - 例外が発生しなければOK
        validators._validate_azure_regions(regions)

    def test_azure_regions_valid_locations(self, validators):
        """SCAN-VAL-010: Azureリージョン検証（一般ロケーション）"""
        # Arrange
        regions = ["japaneast", "japanwest"]

        # Act & Assert - 例外が発生しなければOK
        validators._validate_azure_regions(regions)

    def test_azure_regions_invalid_format(self, validators):
        """SCAN-VAL-010: Azureリージョン検証（無効な形式）"""
        # Arrange
        regions = ["INVALID!!"]

        # Act & Assert
        with pytest.raises(ValidationError, match="不正なAzureロケーション"):
            validators._validate_azure_regions(regions)
```

---

## 5. タスク実行テスト

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| SCAN-TASK-001 | CustodianScanTask初期化 | logger, status_tracker設定 |
| SCAN-TASK-002 | _execute_task正常実行 | スキャン完了、結果返却 |
| SCAN-TASK-003 | 環境変数設定 | AWS/Azure認証情報設定 |
| SCAN-TASK-004 | Custodianコマンド実行 | subprocess正常実行 |
| SCAN-TASK-005 | 違反カウント | violations_count正確 |
| SCAN-TASK-006 | OpenSearch保存 | 結果インデックス保存 |
| SCAN-TASK-007 | 履歴インデックス更新 | cspm-scan-history-v2更新 |
| SCAN-TASK-008 | エラー時の履歴保存 | 失敗時もhistory保存 |
| SCAN-TASK-009 | 暗号化認証情報復号化 | encryptedData処理 |
| SCAN-TASK-010 | タイムアウト処理 | 30分タイムアウト後ProcessingError |

```python
# test/unit/custodian_scan/test_custodian_scan_task.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.jobs.tasks.custodian_scan import CustodianScanTask

class TestCustodianScanTask:
    """CustodianScanTaskのテスト"""

    @pytest.fixture
    def task(self):
        return CustodianScanTask("test-job-001")

    def test_task_initialization(self, task):
        """SCAN-TASK-001: タスク初期化"""
        # Assert
        assert task.job_id == "test-job-001"
        assert task.logger is not None
        assert task.status_tracker is not None

    @pytest.mark.asyncio
    async def test_execute_task_success(
        self,
        task,
        valid_policy_yaml,
        valid_aws_credentials
    ):
        """SCAN-TASK-002: タスク正常実行"""
        # Arrange
        with patch.object(task, '_execute_custodian_scan') as mock_scan:
            mock_scan.return_value = {
                "return_code": 0,
                "violations_count": 5,
                "output_dir": "/tmp/test",
                "stdout_output": [],
                "stderr_output": [],
                "cloud_provider": "aws"
            }
            with patch.object(task, '_process_scan_results') as mock_process:
                mock_process.return_value = {
                    "message": "スキャン完了",
                    "summary_data": {"violations_found": 5}
                }

                # Act
                result = await task._execute_task(
                    policy_yaml_content=valid_policy_yaml,
                    credentials_data=valid_aws_credentials,
                    cloud_provider="aws"
                )

        # Assert
        assert result["message"] == "スキャン完了"

    def test_setup_aws_environment(self, task, valid_aws_credentials):
        """SCAN-TASK-003: AWS環境変数設定"""
        # Act
        env = task._setup_environment(valid_aws_credentials, "aws")

        # Assert
        assert "AWS_ACCESS_KEY_ID" in env
        assert "AWS_SECRET_ACCESS_KEY" in env
        assert "AWS_DEFAULT_REGION" in env

    def test_setup_azure_environment(self, task, valid_azure_credentials):
        """SCAN-TASK-003: Azure環境変数設定"""
        # Act
        env = task._setup_environment(valid_azure_credentials, "azure")

        # Assert
        assert "AZURE_TENANT_ID" in env
        assert "AZURE_CLIENT_ID" in env
        assert "AZURE_CLIENT_SECRET" in env
        assert "AZURE_SUBSCRIPTION_ID" in env

    @pytest.mark.asyncio
    async def test_decrypt_credentials_success(self, task):
        """SCAN-TASK-009: 暗号化認証情報の復号化成功"""
        # Arrange
        encrypted_credentials = {
            "encryptedData": "base64_encoded_encrypted_data"
        }

        with patch("app.jobs.tasks.custodian_scan.decrypt_credentials_field") as mock_decrypt:
            mock_decrypt.return_value = '{"accessKey": "AKIAIOSFODNN7EXAMPLE", "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "defaultRegion": "ap-northeast-1"}'

            # Act
            result = task._decrypt_credentials_if_needed(encrypted_credentials)

        # Assert
        assert result["accessKey"] == "AKIAIOSFODNN7EXAMPLE"
        assert result["defaultRegion"] == "ap-northeast-1"

    def test_decrypt_credentials_not_needed(self, task, valid_aws_credentials):
        """SCAN-TASK-009: 暗号化されていない認証情報はそのまま返す"""
        # Act
        result = task._decrypt_credentials_if_needed(valid_aws_credentials)

        # Assert
        assert result == valid_aws_credentials

    @pytest.mark.asyncio
    async def test_custodian_execution_timeout(self, task):
        """SCAN-TASK-010: Custodian実行タイムアウト"""
        # Arrange
        from app.jobs.common.error_handling import ProcessingError

        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError()):
            with patch("asyncio.create_subprocess_exec") as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.kill = MagicMock()
                mock_process.wait = AsyncMock()
                mock_subprocess.return_value = mock_process

                # Act & Assert
                with pytest.raises(ProcessingError, match="タイムアウト"):
                    await task._run_custodian_command(
                        "/tmp/policy.yaml",
                        "/tmp/output",
                        {"AWS_ACCESS_KEY_ID": "test"},
                        "aws"
                    )
```

---

## 6. 新スキャンタスク（NewCustodianScanTask）テスト

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| NSCAN-001 | 認証情報解析 | CredentialProcessor動作 |
| NSCAN-002 | マルチリージョン実行 | ScanCoordinator動作 |
| NSCAN-003 | 結果処理 | ResultProcessor動作 |
| NSCAN-004 | エラー履歴保存 | ErrorHistoryHandler動作 |
| NSCAN-005 | AssumeRole認証 | role_assumption処理 |
| NSCAN-006 | アクセスキー認証 | secret_key処理 |
| NSCAN-007 | プリセット情報保存 | preset_id, preset_name保存 |

```python
# test/unit/custodian_scan/test_new_custodian_scan_task.py
import pytest
from unittest.mock import patch, AsyncMock
from app.jobs.tasks.new_custodian_scan.main_task import NewCustodianScanTask

class TestNewCustodianScanTask:
    """NewCustodianScanTaskのテスト"""

    @pytest.fixture
    def task(self):
        return NewCustodianScanTask("test-job-001")

    def test_task_has_components(self, task):
        """NSCAN-001: コンポーネント初期化確認"""
        # Assert
        assert task.credential_processor is not None
        assert task.scan_coordinator is not None
        assert task.result_processor is not None
        assert task.error_history_handler is not None

    @pytest.mark.asyncio
    async def test_execute_with_assume_role(
        self,
        task,
        valid_policy_yaml,
        assume_role_credentials
    ):
        """NSCAN-005: AssumeRole認証でのスキャン実行"""
        # Arrange
        with patch.object(
            task.credential_processor,
            'parse_credentials_payload',
            new_callable=AsyncMock
        ) as mock_parse:
            mock_parse.return_value = assume_role_credentials

            with patch.object(
                task.credential_processor,
                'validate_inputs'
            ):
                with patch.object(
                    task.scan_coordinator,
                    'execute_multi_region_custodian_scan',
                    new_callable=AsyncMock
                ) as mock_scan:
                    mock_scan.return_value = {
                        "violations_count": 0,
                        "return_code": 0,
                        "scan_metadata": {}
                    }

                    with patch.object(
                        task,
                        '_process_scan_results',
                        new_callable=AsyncMock
                    ) as mock_process:
                        mock_process.return_value = {"status": "success"}

                        # Act
                        result = await task._execute_task(
                            policy_yaml_content=valid_policy_yaml,
                            credentials_data={"authType": "role_assumption"},
                            cloud_provider="aws",
                            initiated_by_user="test-user",
                            scan_trigger_type="manual"
                        )

        # Assert
        mock_parse.assert_called_once()
        mock_scan.assert_called_once()
```

---

## 7. セキュリティテスト

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| SCAN-SEC-001 | パストラバーサル防止 | ..を含むパス拒否、システムディレクトリ拒否 |
| SCAN-SEC-002 | 環境変数サニタイズ | ホワイトリスト以外除外、コマンドインジェクション防止 |
| SCAN-SEC-003 | コマンドパス検証 | 許可されたパスのみ実行 |
| SCAN-SEC-004 | 認証情報マスキング | ログに機密情報非出力、内部IPマスキング |
| SCAN-SEC-005 | YAMLインジェクション防止 | 危険な構文除外 |
| SCAN-SEC-006 | ReDoS攻撃防止 | 正規表現タイムアウト、入力長制限 |
| SCAN-SEC-007 | 大容量ファイルDoS防止 | 50MBログファイル制限 |
| SCAN-SEC-008 | セキュリティ検証トグル | 環境変数による有効/無効化 |

```python
class TestCustodianScanSecurity:
    """セキュリティテスト"""

    @pytest.fixture
    def task(self):
        return CustodianScanTask("test-job-001")

    def test_path_traversal_prevention(self, task):
        """SCAN-SEC-001: パストラバーサル攻撃防止"""
        # Arrange
        malicious_path = "../../../etc/passwd"
        base_dir = "/tmp/custodian"

        # Act & Assert
        with pytest.raises(ValidationError, match="パストラバーサル"):
            task._sanitize_file_path(malicious_path, base_dir)

    def test_environment_variable_sanitization(self, task):
        """SCAN-SEC-002: 環境変数サニタイズ"""
        # Arrange
        env = {
            "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "MALICIOUS_VAR": "rm -rf /"
        }

        # Act
        sanitized = task._sanitize_environment_variables(env)

        # Assert
        assert "AWS_ACCESS_KEY_ID" in sanitized
        assert "MALICIOUS_VAR" not in sanitized

    def test_command_path_validation(self, task):
        """SCAN-SEC-003: コマンドパス検証"""
        # Act & Assert
        assert task._validate_command_path("custodian") is True
        assert task._validate_command_path("/usr/bin/custodian") is True
        assert task._validate_command_path("/usr/local/bin/custodian") is True
        assert task._validate_command_path("../custodian") is False

    def test_error_message_credential_masking(self):
        """SCAN-SEC-004: エラーメッセージ内の認証情報マスキング"""
        # Arrange
        from app.jobs.tasks.new_custodian_scan.executor.security_sanitizer import SecuritySanitizer
        sanitizer = SecuritySanitizer("test-job-001")

        error_with_secrets = (
            "Error: AKIAIOSFODNN7EXAMPLE failed to auth with "
            "arn:aws:iam::123456789012:role/TestRole from 192.168.1.100"
        )

        # Act
        sanitized = sanitizer.sanitize_error_message(error_with_secrets)

        # Assert
        assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
        assert "123456789012" not in sanitized
        assert "192.168.1.100" not in sanitized
        assert "***" in sanitized

    def test_internal_ip_masking(self):
        """SCAN-SEC-004: 内部IPアドレスのマスキング"""
        # Arrange
        from app.jobs.tasks.new_custodian_scan.executor.security_sanitizer import SecuritySanitizer
        sanitizer = SecuritySanitizer("test-job-001")

        # 10.x.x.x, 172.16-31.x.x, 192.168.x.x は内部IP
        error_with_internal_ip = "Connection to 10.0.0.5 and 172.16.0.1 failed"

        # Act
        sanitized = sanitizer.sanitize_error_message(error_with_internal_ip)

        # Assert
        assert "10.0.0.5" not in sanitized
        assert "172.16.0.1" not in sanitized
        assert "***PRIVATE_IP***" in sanitized or "***IP_ADDRESS***" in sanitized


class TestSecuritySanitizer:
    """security_sanitizer.py専用セキュリティテスト"""

    @pytest.fixture
    def sanitizer(self):
        from app.jobs.tasks.new_custodian_scan.executor.security_sanitizer import SecuritySanitizer
        return SecuritySanitizer("test-job-001")

    def test_redos_attack_prevention_input_limit(self, sanitizer):
        """SCAN-SEC-006: ReDoS攻撃防止（入力長制限）"""
        # Arrange - 10KB以上の悪意ある入力
        malicious_input = "a" * 15000

        # Act
        result = sanitizer.sanitize_error_message(malicious_input)

        # Assert - トランケートされる
        assert len(result) <= 10000 + 50  # 余白分を考慮
        assert "truncated" in result.lower()

    def test_redos_attack_prevention_output_limit(self, sanitizer):
        """SCAN-SEC-006: ReDoS攻撃防止（出力長制限）"""
        # Arrange - 長い正常入力
        long_input = "error message " * 100

        # Act
        result = sanitizer.sanitize_error_message(long_input)

        # Assert - 500文字に制限
        assert len(result) <= 550  # 余白分を考慮

    def test_large_file_dos_prevention(self, sanitizer, tmp_path):
        """SCAN-SEC-007: 大容量ファイルDoS攻撃防止"""
        # Arrange - 50MB超えのファイル
        large_file = tmp_path / "large.log"
        # 実際には50MB書き込まず、サイズチェックのロジックをテスト

        # Act & Assert - 50MB制限
        with pytest.raises(ValueError, match="ファイルサイズが制限"):
            # 50MB超えのファイルがあると仮定
            sanitizer.safe_read_log_file(str(large_file), max_size=100)

    def test_path_traversal_in_log_file(self, sanitizer):
        """SCAN-SEC-007: ログファイル読み込み時のパストラバーサル防止"""
        # Arrange
        malicious_path = "/tmp/../../../etc/passwd"

        # Act & Assert
        with pytest.raises(ValueError, match="危険なファイルパス"):
            sanitizer.safe_read_log_file(malicious_path)

    def test_dangerous_system_directories(self, sanitizer):
        """SCAN-SEC-001: システムディレクトリアクセス拒否"""
        # Arrange
        dangerous_paths = [
            "/etc/passwd",
            "/proc/self/environ",
            "/sys/class/net",
            "/dev/null",
            "/root/.ssh/id_rsa"
        ]

        # Act & Assert
        for path in dangerous_paths:
            assert sanitizer._is_safe_path(path) is False

    def test_command_injection_in_env_value(self, sanitizer):
        """SCAN-SEC-002: 環境変数値のコマンドインジェクション防止"""
        # Arrange
        dangerous_values = [
            "$(rm -rf /)",
            "`cat /etc/passwd`",
            "value; rm -rf /",
            "value | cat /etc/passwd",
            "value\necho hacked"
        ]

        # Act & Assert
        for value in dangerous_values:
            result = sanitizer.sanitize_env_value(value)
            assert result == "***DANGEROUS_VALUE_DETECTED***"


class TestSecurityValidationToggle:
    """セキュリティ検証トグルのテスト"""

    @pytest.fixture
    def task(self):
        return CustodianScanTask("test-job-001")

    @pytest.mark.asyncio
    async def test_security_validation_enabled(self, task, valid_policy_yaml, valid_aws_credentials):
        """SCAN-SEC-008: セキュリティ検証有効時"""
        # Arrange
        import os
        original = os.environ.get("ENABLE_SECURITY_VALIDATION")
        os.environ["ENABLE_SECURITY_VALIDATION"] = "true"

        try:
            with patch.object(task, '_validate_inputs_secure') as mock_validate:
                with patch.object(task, '_execute_custodian_scan', new_callable=AsyncMock) as mock_scan:
                    mock_scan.return_value = {"return_code": 0, "violations_count": 0}
                    with patch.object(task, '_process_scan_results', new_callable=AsyncMock) as mock_process:
                        mock_process.return_value = {"message": "done"}

                        # Act
                        await task._execute_task(
                            policy_yaml_content=valid_policy_yaml,
                            credentials_data=valid_aws_credentials,
                            cloud_provider="aws"
                        )

            # Assert - セキュア検証が呼ばれる
            mock_validate.assert_called_once()

        finally:
            if original is None:
                os.environ.pop("ENABLE_SECURITY_VALIDATION", None)
            else:
                os.environ["ENABLE_SECURITY_VALIDATION"] = original

    @pytest.mark.asyncio
    async def test_security_validation_disabled(self, task, valid_policy_yaml, valid_aws_credentials):
        """SCAN-SEC-008: セキュリティ検証無効時"""
        # Arrange
        import os
        original = os.environ.get("ENABLE_SECURITY_VALIDATION")
        os.environ["ENABLE_SECURITY_VALIDATION"] = "false"

        try:
            with patch.object(task, '_validate_inputs') as mock_validate:
                with patch.object(task, '_execute_custodian_scan', new_callable=AsyncMock) as mock_scan:
                    mock_scan.return_value = {"return_code": 0, "violations_count": 0}
                    with patch.object(task, '_process_scan_results', new_callable=AsyncMock) as mock_process:
                        mock_process.return_value = {"message": "done"}

                        # Act
                        await task._execute_task(
                            policy_yaml_content=valid_policy_yaml,
                            credentials_data=valid_aws_credentials,
                            cloud_provider="aws"
                        )

            # Assert - 基本検証が呼ばれる
            mock_validate.assert_called_once()

        finally:
            if original is None:
                os.environ.pop("ENABLE_SECURITY_VALIDATION", None)
            else:
                os.environ["ENABLE_SECURITY_VALIDATION"] = original
```

---

## 8. モデル定義

```python
# app/custodian_scan/router.py

class CustodianScanRequest(BaseModel):
    """スキャンリクエスト"""
    policy_yaml_content: str
    credentials_data: Dict[str, Any]
    cloud_provider: str = "aws"

class CommandPreviewRequest(BaseModel):
    """コマンドプレビューリクエスト"""
    policy_yaml_content: str
    credentials_data: Dict[str, Any]
    cloud_provider: str = "aws"

# app/models/jobs.py

class NewCredentials(BaseModel):
    """統合認証情報モデル"""
    authType: Literal["role_assumption", "secret_key"]

    # AssumeRole方式
    roleArn: Optional[str] = None
    externalIdValue: Optional[str] = None

    # AWS アクセスキー方式
    accessKey: Optional[str] = None
    secretKey: Optional[str] = None
    sessionToken: Optional[str] = None

    # Azure認証
    tenantId: Optional[str] = None
    clientId: Optional[str] = None
    clientSecret: Optional[str] = None
    subscriptionId: Optional[str] = None

    # スキャン設定
    scanRegions: List[str] = []
```

---

## 9. フィクスチャ

```python
# test/unit/custodian_scan/conftest.py
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.models.jobs import NewCredentials


@pytest.fixture
async def async_client():
    """非同期HTTPクライアントのフィクスチャ"""
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.fixture
def valid_policy_yaml():
    """有効なCustodianポリシーYAML"""
    return """
policies:
  - name: ec2-require-tags
    resource: aws.ec2
    filters:
      - "tag:Environment": absent
    actions:
      - type: mark-for-op
        tag: c7n_cleanup
        op: stop
        days: 7
"""

@pytest.fixture
def valid_aws_credentials():
    """有効なAWS認証情報"""
    return {
        "accessKey": "AKIAIOSFODNN7EXAMPLE",
        "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "defaultRegion": "ap-northeast-1"
    }

@pytest.fixture
def valid_azure_credentials():
    """有効なAzure認証情報"""
    return {
        "tenantId": "12345678-1234-1234-1234-123456789012",
        "clientId": "12345678-1234-1234-1234-123456789012",
        "clientSecret": "your-client-secret-value",
        "subscriptionId": "12345678-1234-1234-1234-123456789012"
    }

@pytest.fixture
def assume_role_credentials():
    """AssumeRole認証情報"""
    return NewCredentials(
        authType="role_assumption",
        roleArn="arn:aws:iam::123456789012:role/CustodianScanRole",
        externalIdValue="external-id-123",
        scanRegions=["ap-northeast-1", "us-east-1"]
    )

@pytest.fixture
def mock_credentials_access_key():
    """アクセスキー認証情報のモック"""
    return NewCredentials(
        authType="secret_key",
        accessKey="AKIAIOSFODNN7EXAMPLE",
        secretKey="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        scanRegions=["ap-northeast-1"]
    )

@pytest.fixture
def mock_azure_credentials():
    """Azure認証情報のモック"""
    return NewCredentials(
        authType="secret_key",
        tenantId="12345678-1234-1234-1234-123456789012",
        clientId="12345678-1234-1234-1234-123456789012",
        clientSecret="test-secret",
        subscriptionId="12345678-1234-1234-1234-123456789012",
        scanRegions=["all-locations"]
    )

@pytest.fixture
def mock_credentials_assume_role():
    """AssumeRole認証情報のモック"""
    return NewCredentials(
        authType="role_assumption",
        roleArn="arn:aws:iam::123456789012:role/TestRole",
        scanRegions=["ap-northeast-1"]
    )

@pytest.fixture
def mock_opensearch_client():
    """OpenSearchクライアントのモック（非同期対応）"""
    client = AsyncMock()
    client.index = AsyncMock(return_value={"result": "created"})
    client.update = AsyncMock(return_value={"result": "updated"})
    client.search = AsyncMock(return_value={"hits": {"hits": []}})
    return client

@pytest.fixture
def mock_custodian_output():
    """Custodian出力のモック"""
    return {
        "return_code": 0,
        "violations_count": 3,
        "output_dir": "/tmp/custodian-output",
        "stdout_output": ["[CUSTODIAN_STDOUT] Scanning..."],
        "stderr_output": [],
        "cloud_provider": "aws"
    }
```

---

## 10. テスト実行例

```bash
# Custodianスキャンテストの実行
cd /usr/share/osd/python-fastapi

# 全テスト実行
pytest test/unit/custodian_scan/ -v

# 特定のテストファイル
pytest test/unit/custodian_scan/test_router.py -v
pytest test/unit/custodian_scan/test_validators.py -v
pytest test/unit/custodian_scan/test_custodian_scan_task.py -v

# カバレッジ付き
pytest test/unit/custodian_scan/ -v --cov=app.custodian_scan --cov=app.jobs.tasks.custodian_scan --cov-report=html
```

---

## 11. スキャンフロー図

```
┌─────────────────┐     ┌────────────────────┐     ┌─────────────────┐
│   クライアント   │     │   FastAPI Router   │     │  CustodianTask  │
└────────┬────────┘     └─────────┬──────────┘     └────────┬────────┘
         │                        │                         │
         │ POST /start_scan_async │                         │
         ├───────────────────────>│                         │
         │                        │ BackgroundTask登録       │
         │                        ├────────────────────────>│
         │  {job_id, status}      │                         │
         │<───────────────────────┤                         │
         │                        │                         │
         │                        │     ┌──────────────────────────────────┐
         │                        │     │ バックグラウンド処理               │
         │                        │     ├──────────────────────────────────┤
         │                        │     │ 1. 入力検証                       │
         │                        │     │ 2. 認証情報設定                   │
         │                        │     │ 3. Custodian実行                  │
         │                        │     │ 4. 結果解析・違反カウント          │
         │                        │     │ 5. OpenSearch保存                 │
         │                        │     │ 6. 履歴インデックス更新            │
         │                        │     └──────────────────────────────────┘
         │                        │                         │
         │ GET /jobs/{id}/status  │                         │
         ├───────────────────────>│                         │
         │    {status, result}    │                         │
         │<───────────────────────┤                         │
```

---

## 12. テストケース一覧

### カウントサマリー

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 7 | SCAN-001 〜 SCAN-007 |
| 異常系 | 10 | SCAN-E01 〜 SCAN-E10 |
| バリデーション | 10 | SCAN-VAL-001 〜 SCAN-VAL-010 |
| タスク実行 | 10 | SCAN-TASK-001 〜 SCAN-TASK-010 |
| 新スキャン | 7 | NSCAN-001 〜 NSCAN-007 |
| セキュリティ | 8 | SCAN-SEC-001 〜 SCAN-SEC-008 |
| **合計** | **52** | - |

### テストクラス構成

```
test/unit/custodian_scan/
├── conftest.py               # フィクスチャ定義
├── test_router.py            # SCAN-001~007, SCAN-E01~E10
│   ├── TestCustodianScanRouter
│   └── TestCustodianScanErrors
├── test_validators.py        # SCAN-VAL-001~010
│   └── TestNewCustodianValidators
├── test_custodian_scan_task.py # SCAN-TASK-001~010
│   └── TestCustodianScanTask
├── test_new_custodian_scan_task.py # NSCAN-001~007
│   └── TestNewCustodianScanTask
└── test_security.py          # SCAN-SEC-001~008
    ├── TestCustodianScanSecurity
    ├── TestSecuritySanitizer
    └── TestSecurityValidationToggle
```

### 注記

- **SCAN-SEC-001〜005**: 旧 `CustodianScanTask` のセキュリティメソッドテスト
- **SCAN-SEC-006〜007**: `SecuritySanitizer` クラスのDoS対策テスト
- **SCAN-SEC-008**: 環境変数 `ENABLE_SECURITY_VALIDATION` によるトグルテスト
- **SCAN-TASK-009〜010**: 暗号化認証情報復号化とタイムアウト処理のテスト追加

---

## 13. 既知の制限事項

| 制限 | 理由 | 回避策 |
|------|------|--------|
| 実際のCustodian実行テストは統合テストで実施 | ユニットテストでは外部依存を避ける | test/custodian_test_cases/ で統合テスト |
| AWS/Azureへの実際の認証テストは除外 | テスト環境での認証情報漏洩リスク | モックで認証フローを検証 |
| 50MB以上のログファイルテストは時間制約のため省略 | テスト実行時間への影響 | サイズチェックロジックのみテスト |
| AIエラー分析のテストはモック前提 | LLM呼び出しのコスト・遅延 | analyze_custodian_error_with_ai のモック化 |
