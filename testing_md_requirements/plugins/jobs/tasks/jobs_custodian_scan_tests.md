# jobs/tasks/custodian_scan テストケース

## 1. 概要

`app/jobs/tasks/custodian_scan.py` は、Cloud Custodianスキャンタスクの実装クラス `CustodianScanTask` を定義します。`BaseTask` を継承し、ポリシーYAMLの検証・認証情報の復号・Custodianプロセスの実行・結果処理・AIサマリー生成までの一連のスキャンフローを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `CustodianScanTask.__init__` | job_id設定、TaskLogger・StatusTracker初期化 |
| `_execute_task` | メインタスク実行（セキュリティ検証切替あり） |
| `_validate_inputs` | 基本入力値検証（policy, credentials, provider） |
| `_validate_inputs_secure` | セキュリティ強化版入力値検証 |
| `_validate_policy_yaml_secure` | YAML構文・構造・危険キーワード・サイズ検証 |
| `_validate_aws_credentials` | AWSアクセスキー・シークレット・リージョン検証 |
| `_validate_azure_credentials` | Azure GUID・クライアントシークレット検証 |
| `_setup_environment` | AWS/Azure環境変数設定 |
| `_decrypt_credentials_if_needed` | 暗号化認証情報の復号 |
| `_sanitize_file_path` | パストラバーサル防止 |
| `_sanitize_environment_variables` | 環境変数ホワイトリスト制御 |
| `_validate_command_path` | Custodianコマンドパス検証 |
| `_run_custodian_command` | Custodianプロセス実行 |
| `_capture_process_output` | stdout/stderrキャプチャ |
| `_log_custodian_output` | Custodian出力のログ記録 |
| `_process_scan_results` | 結果の成功/失敗ルーティング |
| `_handle_successful_scan` | 成功時処理（AI要約生成含む） |
| `_handle_failed_scan` | 失敗時処理（AIエラー分析含む） |
| `_analyze_scan_error_with_ai` | AIによるエラー分析 |
| `_update_scan_history` | OpenSearch履歴更新 |
| `_handle_validation_failure` | 検証失敗時の履歴記録 |
| `run_custodian_scan_task` | レガシー互換ラッパー関数 |

### 1.2 カバレッジ目標: 85%

> **注記**: 846行の大規模クラス。外部プロセス実行（asyncio.create_subprocess_exec）やAIサマリー生成など、統合テスト寄りの部分はモック中心で検証する。セキュリティ検証メソッドは分岐が多く網羅的にテストする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/custodian_scan.py` |
| テストコード | `test/unit/jobs/tasks/test_custodian_scan.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
custodian_scan.py
  ──→ base_task.BaseTask（継承元）
  ──→ common.error_handling.ValidationError, ExternalServiceError, ProcessingError
  ──→ common.logging.TaskLogger
  ──→ common.status_tracking.StatusTracker
  ──→ utils.violations_counter.count_violations_from_custodian_output
  ──→ utils.custodian_output.store_custodian_output_to_opensearch
  ──→ utils.metadata_extractor.extract_metadata_from_output_dir, extract_scan_info_from_metadata
  ──→ utils.summary_generation.generate_scan_summary
  ──→ utils.error_analysis.analyze_custodian_error_with_ai, create_error_summary_with_ai_analysis
  ──→ models.jobs.AwsCredentials, AzureCredentials
  ──→ core.clients.get_opensearch_client
  ──→ core.crypto.decrypt_credentials_field
  ──→ asyncio.create_subprocess_exec（外部プロセス実行）
  ──→ os.environ（ENABLE_SECURITY_VALIDATION, CUSTODIAN_CMD_PATH）
```

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `_execute_task` | L46-57 | `ENABLE_SECURITY_VALIDATION == "true"` | secure版 / basic版切替 |
| `_setup_environment` | L164,176 | `cloud_provider == "aws"` / `"azure"` | AWS / Azure環境変数設定 |
| `_setup_environment` | L170 | `sessionToken` あり | AWS_SESSION_TOKEN追加 |
| `_decrypt_credentials_if_needed` | L192 | `'encryptedData' in credentials_data` | 復号実行 / そのまま返却 |
| `_validate_policy_yaml_secure` | L260-282 | YAML構造チェック（5分岐） | 各ValidationError |
| `_validate_aws_credentials` | L310,315,321,324 | フォーマット検証（4分岐） | 各ValidationError |
| `_run_custodian_command` | L468-494 | セキュリティ検証有効時のサニタイズ | パス・環境変数サニタイズ |
| `_run_custodian_command` | L503-507 | `region` あり/なし | --region引数追加 |
| `_log_custodian_output` | L585,588 | `return_code == 0` | info / error レベル |
| `_handle_successful_scan` | L652 | `violations_count > 0` | OpenSearch保存+AI要約 / メタデータ抽出 |
| `_handle_failed_scan` | L813 | `ai_error_analysis` あり/なし | メッセージ分岐 |

#### 環境変数

| 環境変数 | 用途 | デフォルト |
|---------|------|----------|
| `ENABLE_SECURITY_VALIDATION` | セキュリティ検証の有効化 | `"false"` |
| `CUSTODIAN_CMD_PATH` | Custodianコマンドパス | `"custodian"` |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JCSCAN-001 | 初期化でlogger・status_tracker設定 | `job_id="test-job"` | logger, status_tracker がそれぞれ初期化 |
| JCSCAN-002 | セキュリティ検証無効時に基本検証実行 | `ENABLE_SECURITY_VALIDATION=false` | `_validate_inputs` が呼ばれる |
| JCSCAN-003 | セキュリティ検証有効時にsecure検証実行 | `ENABLE_SECURITY_VALIDATION=true` | `_validate_inputs_secure` が呼ばれる |
| JCSCAN-004 | 基本検証でaws/azureが通過 | `cloud_provider="aws"` | 例外なし |
| JCSCAN-005 | 履歴更新成功 | 有効なOpenSearchクライアント | `os_client.update` 呼出 |
| JCSCAN-006 | 履歴更新でクライアント未取得 | `get_opensearch_client` → None | 早期return（warning出力） |
| JCSCAN-007 | AWS環境変数設定（セッショントークンなし） | AWS認証情報 | AWS_ACCESS_KEY_ID等3つ設定 |
| JCSCAN-008 | AWS環境変数設定（セッショントークンあり） | sessionToken付きAWS認証情報 | AWS_SESSION_TOKEN追加 |
| JCSCAN-009 | Azure環境変数設定 | Azure認証情報 | AZURE_TENANT_ID等4つ設定 |
| JCSCAN-010 | 暗号化認証情報の復号成功 | `encryptedData` キー含む | `decrypt_credentials_field` 呼出、JSON解析 |
| JCSCAN-011 | 暗号化なし認証情報をそのまま返却 | `encryptedData` キーなし | 入力そのまま返却 |
| JCSCAN-012 | セキュア検証の全ステップ通過 | 有効なpolicy, creds, aws | 全検証関数が順次呼ばれる |
| JCSCAN-013 | 正常YAML検証 | 有効なpoliciesフィールド付きYAML | 例外なし |
| JCSCAN-014 | 危険キーワード検出 | `eval` 含むYAML | ValidationError |
| JCSCAN-015 | AWS認証情報の正常検証 | AKIA開始20文字キー | 例外なし |
| JCSCAN-016 | AWSリージョン"all"許可 | `region="all"` | 例外なし |
| JCSCAN-017 | AWSセッショントークン検証通過 | 英数字+記号トークン | 例外なし |
| JCSCAN-018 | Azure認証情報の正常検証 | 有効なGUID形式 | 例外なし |
| JCSCAN-019 | 相対パスのサニタイズ | `"policy.yaml"`, base_dir | base_dir結合パス返却 |
| JCSCAN-020 | 絶対パスのサニタイズ（基底内） | base_dir内の絶対パス | そのまま返却 |
| JCSCAN-021 | 環境変数サニタイズ（許可リストのみ） | AWS系環境変数 | 許可された変数のみ返却 |
| JCSCAN-022 | 非許可環境変数の除外 | 不明な環境変数含む | 許可変数のみ残りwarning出力 |
| JCSCAN-023 | コマンドパス"custodian" | `"custodian"` | True |
| JCSCAN-024 | コマンドパス/usr/bin/custodian | `/usr/bin/custodian` | True |
| JCSCAN-025 | ユーザーローカルインストールパス | `/home/user/.local/bin/custodian` | True |
| JCSCAN-026 | 検証失敗時の履歴記録成功 | エラーメッセージ | `_update_scan_history` 呼出 |
| JCSCAN-027 | Custodianコマンド実行（セキュリティ検証無効） | 正常プロセス | return_code, violations等返却 |
| JCSCAN-028 | リージョン指定ありのコマンド引数 | `AWS_DEFAULT_REGION` 含む | `--region` 引数追加 |
| JCSCAN-029 | リージョン指定なしのコマンド引数 | リージョンなし | `--region` なし |
| JCSCAN-030 | stdout/stderrのログ出力（成功時） | stdout,stderr有, return_code=0 | 全行infoレベル |
| JCSCAN-031 | 空出力のログ | stdout=[], stderr=[] | "なし"ログ出力 |
| JCSCAN-032 | stderr（エラー時）のログ | stderr有, return_code=1 | errorレベルで出力 |
| JCSCAN-033 | プロセス出力キャプチャ | stdout2行, stderr1行 | プレフィックス付きリスト |
| JCSCAN-034 | 成功時の結果処理ルーティング | return_code=0 | `_handle_successful_scan` 呼出 |
| JCSCAN-035 | 失敗時の結果処理ルーティング | return_code=1 | `_handle_failed_scan` 呼出 |
| JCSCAN-036 | 成功+違反あり+AI要約成功 | violations=5, AI要約あり | completion_message含む結果 |
| JCSCAN-037 | 成功+違反なし+メタデータ抽出成功 | violations=0, metadata有 | account_id等メタデータ含む |
| JCSCAN-038 | レガシーラッパー関数 | 有効な引数 | CustodianScanTask.execute呼出 |
| JCSCAN-039 | 失敗時処理（AIエラー分析あり） | return_code=1, AI分析成功 | ExternalServiceError（AI分析完了メッセージ） |
| JCSCAN-040 | 失敗時処理（AIエラー分析なし） | return_code=1, AI分析失敗 | ExternalServiceError（AI分析失敗メッセージ） |
| JCSCAN-041 | AIエラー分析で_last_scan_results未設定 | `_last_scan_results`なし | None返却 |
| JCSCAN-042 | AIエラー分析成功 | 有効なスキャン結果保存済み | AI分析結果Dict返却 |

### 2.1 初期化・基本フロー テスト

```python
# test/unit/jobs/tasks/test_custodian_scan.py
import pytest
import asyncio
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock


class TestCustodianScanTaskInit:
    """CustodianScanTask初期化テスト"""

    @patch("app.jobs.tasks.custodian_scan.StatusTracker")
    @patch("app.jobs.tasks.custodian_scan.TaskLogger")
    def test_init_sets_logger_and_status_tracker(self, mock_logger_cls, mock_tracker_cls):
        """JCSCAN-001: 初期化でlogger・status_tracker設定"""
        # Arrange
        from app.jobs.tasks.custodian_scan import CustodianScanTask

        # Act
        task = CustodianScanTask("test-job-123")

        # Assert
        assert task.job_id == "test-job-123"
        mock_logger_cls.assert_called_once_with("test-job-123", "CustodianScan")
        mock_tracker_cls.assert_called_once_with("test-job-123")
```

### 2.2 _execute_task テスト

```python
class TestExecuteTask:
    """メインタスク実行テスト"""

    @pytest.fixture
    def mock_task(self):
        """テスト用CustodianScanTaskインスタンス"""
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            task = CustodianScanTask("test-job")
            task._validate_inputs = MagicMock()
            task._validate_inputs_secure = AsyncMock()
            task._execute_custodian_scan = AsyncMock(return_value={"return_code": 0, "violations_count": 0})
            task._process_scan_results = AsyncMock(return_value={"message": "完了"})
            task.logger = MagicMock()
            return task

    @pytest.mark.asyncio
    async def test_security_validation_disabled_uses_basic(self, mock_task):
        """JCSCAN-002: セキュリティ検証無効時に基本検証実行

        custodian_scan.py:46-57 の分岐をカバー（ENABLE_SECURITY_VALIDATION=false）。
        """
        # Arrange
        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}):
            # Act
            await mock_task._execute_task(
                policy_yaml_content="policies: []",
                credentials_data={"accessKey": "test"},
                cloud_provider="aws"
            )

        # Assert
        mock_task._validate_inputs.assert_called_once()
        mock_task._validate_inputs_secure.assert_not_called()

    @pytest.mark.asyncio
    async def test_security_validation_enabled_uses_secure(self, mock_task):
        """JCSCAN-003: セキュリティ検証有効時にsecure検証実行

        custodian_scan.py:46-50 の分岐をカバー（ENABLE_SECURITY_VALIDATION=true）。
        """
        # Arrange
        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "true"}):
            # Act
            await mock_task._execute_task(
                policy_yaml_content="policies: []",
                credentials_data={"accessKey": "test"},
                cloud_provider="aws"
            )

        # Assert
        mock_task._validate_inputs_secure.assert_called_once()
        mock_task._validate_inputs.assert_not_called()
```

### 2.3 _validate_inputs テスト

```python
class TestValidateInputs:
    """基本入力値検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_valid_aws_inputs(self, task):
        """JCSCAN-004: 基本検証でaws/azureが通過"""
        # Arrange & Act & Assert（例外なし）
        task._validate_inputs("policies:\n  - name: test", {"accessKey": "key"}, "aws")
        task._validate_inputs("policies:\n  - name: test", {"tenantId": "id"}, "azure")
```

### 2.4 _update_scan_history テスト

```python
class TestUpdateScanHistory:
    """履歴更新テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_successful_update(self, task):
        """JCSCAN-005: 履歴更新成功"""
        # Arrange
        mock_client = AsyncMock()
        with patch("app.jobs.tasks.custodian_scan.get_opensearch_client", return_value=mock_client):
            # Act
            await task._update_scan_history({"message": "完了", "summary_data": {}})

        # Assert
        mock_client.update.assert_called_once()
        call_kwargs = mock_client.update.call_args
        assert call_kwargs.kwargs["index"] == "cspm-scan-history-v2"
        assert call_kwargs.kwargs["id"] == "test-job"

    @pytest.mark.asyncio
    async def test_client_unavailable_skips(self, task):
        """JCSCAN-006: 履歴更新でクライアント未取得

        custodian_scan.py:83-84 の分岐をカバー。
        """
        # Arrange
        with patch("app.jobs.tasks.custodian_scan.get_opensearch_client", return_value=None):
            # Act
            await task._update_scan_history({"message": "完了"})

        # Assert
        task.logger.warning.assert_called_once()
```

### 2.5 _setup_environment テスト

```python
class TestSetupEnvironment:
    """環境変数設定テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._decrypt_credentials_if_needed = MagicMock(side_effect=lambda x: x)
            return t

    def test_aws_without_session_token(self, task):
        """JCSCAN-007: AWS環境変数設定（セッショントークンなし）

        custodian_scan.py:164-174 の分岐をカバー。
        """
        # Arrange
        creds = {"accessKey": "AKIAIOSFODNN7EXAMPLE", "secretKey": "secret123", "defaultRegion": "us-east-1"}

        # Act
        result = task._setup_environment(creds, "aws")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIAIOSFODNN7EXAMPLE"
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret123"
        assert result["AWS_DEFAULT_REGION"] == "us-east-1"
        assert "AWS_SESSION_TOKEN" not in result

    def test_aws_with_session_token(self, task):
        """JCSCAN-008: AWS環境変数設定（セッショントークンあり）

        custodian_scan.py:170-172 の分岐をカバー。
        """
        # Arrange
        creds = {
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "secret123",
            "defaultRegion": "us-east-1",
            "sessionToken": "token123"
        }

        # Act
        result = task._setup_environment(creds, "aws")

        # Assert
        assert result["AWS_SESSION_TOKEN"] == "token123"

    def test_azure_environment(self, task):
        """JCSCAN-009: Azure環境変数設定

        custodian_scan.py:176-183 の分岐をカバー。
        """
        # Arrange
        creds = {
            "tenantId": "tenant-id",
            "clientId": "client-id",
            "clientSecret": "secret",
            "subscriptionId": "sub-id"
        }

        # Act
        result = task._setup_environment(creds, "azure")

        # Assert
        assert result["AZURE_TENANT_ID"] == "tenant-id"
        assert result["AZURE_CLIENT_ID"] == "client-id"
        assert result["AZURE_CLIENT_SECRET"] == "secret"
        assert result["AZURE_SUBSCRIPTION_ID"] == "sub-id"
```

### 2.6 _decrypt_credentials_if_needed テスト

```python
class TestDecryptCredentials:
    """認証情報復号テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_encrypted_data_decrypted(self, task):
        """JCSCAN-010: 暗号化認証情報の復号成功

        custodian_scan.py:192-204 の分岐をカバー。
        """
        # Arrange
        decrypted_json = json.dumps({"accessKey": "AKIA1234", "secretKey": "secret"})
        with patch("app.jobs.tasks.custodian_scan.decrypt_credentials_field", return_value=decrypted_json):
            # Act
            result = task._decrypt_credentials_if_needed({"encryptedData": "base64data"})

        # Assert
        assert result["accessKey"] == "AKIA1234"

    def test_unencrypted_data_passthrough(self, task):
        """JCSCAN-011: 暗号化なし認証情報をそのまま返却

        custodian_scan.py:210-212 の分岐をカバー。
        """
        # Arrange
        creds = {"accessKey": "AKIA1234", "secretKey": "secret"}

        # Act
        result = task._decrypt_credentials_if_needed(creds)

        # Assert
        assert result is creds
```

### 2.7 セキュア検証テスト

```python
class TestValidateInputsSecure:
    """セキュリティ強化版検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._validate_policy_yaml_secure = MagicMock()
            t._validate_credentials_secure = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_all_validations_pass(self, task):
        """JCSCAN-012: セキュア検証の全ステップ通過"""
        # Arrange & Act
        await task._validate_inputs_secure("policies:\n  - name: test", {"key": "val"}, "aws")

        # Assert
        task._validate_policy_yaml_secure.assert_called_once()
        task._validate_credentials_secure.assert_called_once()
```

### 2.8 _validate_policy_yaml_secure テスト

```python
class TestValidatePolicyYamlSecure:
    """YAML安全性検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_valid_yaml(self, task):
        """JCSCAN-013: 正常YAML検証"""
        # Arrange
        yaml_content = "policies:\n  - name: test-policy\n    resource: aws.ec2"

        # Act & Assert（例外なし）
        task._validate_policy_yaml_secure(yaml_content)

    def test_dangerous_keyword_detected(self, task):
        """JCSCAN-014: 危険キーワード検出

        custodian_scan.py:277-279 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        yaml_content = "policies:\n  - name: test\n    description: use eval here"

        # Act & Assert
        with pytest.raises(ValidationError, match="危険なキーワードが検出されました"):
            task._validate_policy_yaml_secure(yaml_content)
```

### 2.9 AWS/Azure認証情報検証テスト

```python
class TestValidateAwsCredentials:
    """AWS認証情報検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_valid_aws_credentials(self, task):
        """JCSCAN-015: AWS認証情報の正常検証"""
        # Arrange
        creds = {
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "defaultRegion": "us-east-1"
        }

        # Act & Assert（例外なし）
        task._validate_aws_credentials(creds)

    def test_region_all_keyword(self, task):
        """JCSCAN-016: AWSリージョン"all"許可

        custodian_scan.py:321-323 の分岐をカバー。
        """
        # Arrange
        creds = {
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "defaultRegion": "all"
        }

        # Act & Assert（例外なし）
        task._validate_aws_credentials(creds)

    def test_valid_session_token(self, task):
        """JCSCAN-017: AWSセッショントークン検証通過

        custodian_scan.py:328-330 の分岐をカバー。
        """
        # Arrange
        creds = {
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "defaultRegion": "us-east-1",
            "sessionToken": "FwoGZXIvYXdzEBYaDH+ABC123/token+value=="
        }

        # Act & Assert（例外なし）
        task._validate_aws_credentials(creds)


class TestValidateAzureCredentials:
    """Azure認証情報検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_valid_azure_credentials(self, task):
        """JCSCAN-018: Azure認証情報の正常検証"""
        # Arrange
        creds = {
            "tenantId": "12345678-1234-1234-1234-123456789abc",
            "clientId": "abcdef01-2345-6789-abcd-ef0123456789",
            "clientSecret": "MySecret~Value_123",
            "subscriptionId": "11111111-2222-3333-4444-555555555555"
        }

        # Act & Assert（例外なし）
        task._validate_azure_credentials(creds)
```

### 2.10 サニタイズ・パス検証テスト

```python
class TestSanitizeFilePath:
    """ファイルパスサニタイズテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_relative_path(self, task):
        """JCSCAN-019: 相対パスのサニタイズ

        custodian_scan.py:368-371 の分岐をカバー。
        """
        # Arrange & Act
        result = task._sanitize_file_path("policy.yaml", "/tmp/scan")

        # Assert
        assert result == os.path.join("/tmp/scan", "policy.yaml")

    def test_absolute_path_within_base(self, task):
        """JCSCAN-020: 絶対パスのサニタイズ（基底内）

        custodian_scan.py:363-367 の分岐をカバー。
        """
        # Arrange & Act
        result = task._sanitize_file_path("/tmp/scan/policy.yaml", "/tmp/scan")

        # Assert
        assert result == "/tmp/scan/policy.yaml"


class TestSanitizeEnvironmentVariables:
    """環境変数サニタイズテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_allowed_vars_only(self, task):
        """JCSCAN-021: 環境変数サニタイズ（許可リストのみ）"""
        # Arrange
        env = {"AWS_ACCESS_KEY_ID": "AKIATEST", "AWS_DEFAULT_REGION": "us-east-1"}

        # Act
        result = task._sanitize_environment_variables(env)

        # Assert
        assert result == env

    def test_excludes_non_whitelisted(self, task):
        """JCSCAN-022: 非許可環境変数の除外

        custodian_scan.py:392-394 の分岐をカバー。
        """
        # Arrange
        env = {"AWS_ACCESS_KEY_ID": "AKIATEST", "HOME": "/root", "MALICIOUS_VAR": "bad"}

        # Act
        result = task._sanitize_environment_variables(env)

        # Assert
        assert "AWS_ACCESS_KEY_ID" in result
        assert "HOME" not in result
        assert "MALICIOUS_VAR" not in result


class TestValidateCommandPath:
    """コマンドパス検証テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_simple_custodian(self, task):
        """JCSCAN-023: コマンドパス"custodian" """
        # Act & Assert
        assert task._validate_command_path("custodian") is True

    def test_usr_bin_custodian(self, task):
        """JCSCAN-024: コマンドパス/usr/bin/custodian"""
        # Act & Assert
        assert task._validate_command_path("/usr/bin/custodian") is True

    def test_user_local_install(self, task):
        """JCSCAN-025: ユーザーローカルインストールパス

        custodian_scan.py:409 の正規表現パターンをカバー。
        """
        # Act & Assert
        assert task._validate_command_path("/home/user/.local/bin/custodian") is True
```

### 2.11 検証失敗ハンドリングテスト

```python
class TestHandleValidationFailure:
    """検証失敗時の履歴記録テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._update_scan_history = AsyncMock()
            t._cloud_provider = "aws"
            return t

    @pytest.mark.asyncio
    async def test_records_failure_to_history(self, task):
        """JCSCAN-026: 検証失敗時の履歴記録成功"""
        # Act
        await task._handle_validation_failure("テストエラー")

        # Assert
        task._update_scan_history.assert_called_once()
        call_args = task._update_scan_history.call_args[0][0]
        assert "セキュリティ検証失敗" in call_args["message"]
```

### 2.12 _run_custodian_command テスト

```python
class TestRunCustodianCommand:
    """Custodianコマンド実行テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._log_custodian_output = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_execution_without_security_validation(self, task):
        """JCSCAN-027: Custodianコマンド実行（セキュリティ検証無効）

        custodian_scan.py:490-494 の分岐をカバー。
        """
        # Arrange
        mock_process = AsyncMock()
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()

        task._capture_process_output = AsyncMock(return_value=(["line1"], ["err1"]))

        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}, clear=False), \
             patch("asyncio.create_subprocess_exec", return_value=mock_process), \
             patch("app.jobs.tasks.custodian_scan.count_violations_from_custodian_output", return_value=3), \
             patch("os.path.exists", return_value=True):
            # Act
            result = await task._run_custodian_command(
                "/tmp/policy.yaml", "/tmp/output", {"AWS_DEFAULT_REGION": "us-east-1"}, "aws"
            )

        # Assert
        assert result["return_code"] == 0
        assert result["violations_count"] == 3

    @pytest.mark.asyncio
    async def test_region_argument_added(self, task):
        """JCSCAN-028: リージョン指定ありのコマンド引数

        custodian_scan.py:503-505 の分岐をカバー。
        """
        # Arrange
        mock_process = AsyncMock()
        mock_process.wait = AsyncMock(return_value=0)

        task._capture_process_output = AsyncMock(return_value=([], []))

        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}, clear=False), \
             patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec, \
             patch("app.jobs.tasks.custodian_scan.count_violations_from_custodian_output", return_value=0), \
             patch("os.path.exists", return_value=True):
            # Act
            await task._run_custodian_command(
                "/tmp/policy.yaml", "/tmp/output",
                {"AWS_DEFAULT_REGION": "us-east-1"}, "aws"
            )

        # Assert
        call_args = mock_exec.call_args[0]
        assert "--region" in call_args
        assert "us-east-1" in call_args

    @pytest.mark.asyncio
    async def test_no_region_argument(self, task):
        """JCSCAN-029: リージョン指定なしのコマンド引数

        custodian_scan.py:507 の分岐をカバー。
        """
        # Arrange
        mock_process = AsyncMock()
        mock_process.wait = AsyncMock(return_value=0)
        task._capture_process_output = AsyncMock(return_value=([], []))

        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}, clear=False), \
             patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec, \
             patch("app.jobs.tasks.custodian_scan.count_violations_from_custodian_output", return_value=0), \
             patch("os.path.exists", return_value=True):
            # Act
            await task._run_custodian_command(
                "/tmp/policy.yaml", "/tmp/output", {}, "aws"
            )

        # Assert
        call_args = mock_exec.call_args[0]
        assert "--region" not in call_args
```

### 2.13 _log_custodian_output テスト

```python
class TestLogCustodianOutput:
    """Custodian出力ログテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_stdout_stderr_with_success(self, task):
        """JCSCAN-030: stdout/stderrのログ出力（成功時）

        custodian_scan.py:574-591, return_code=0 の分岐をカバー。
        """
        # Arrange
        stdout = ["[STDOUT] line1"]
        stderr = ["[STDERR] warning"]

        # Act
        task._log_custodian_output(stdout, stderr, 0)

        # Assert（stderrもinfoレベルで出力される）
        info_calls = [str(c) for c in task.logger.info.call_args_list]
        assert any("line1" in c for c in info_calls)
        task.logger.error.assert_not_called()

    def test_empty_output(self, task):
        """JCSCAN-031: 空出力のログ

        custodian_scan.py:579-580, 592-593 の分岐をカバー。
        """
        # Act
        task._log_custodian_output([], [], 0)

        # Assert
        info_calls = [str(c) for c in task.logger.info.call_args_list]
        assert any("なし" in c for c in info_calls)

    def test_stderr_with_error_return_code(self, task):
        """JCSCAN-032: stderr（エラー時）のログ

        custodian_scan.py:588-589 の分岐をカバー（return_code != 0）。
        """
        # Arrange
        stderr = ["[STDERR] error occurred"]

        # Act
        task._log_custodian_output([], stderr, 1)

        # Assert
        task.logger.error.assert_called()
```

### 2.14 _capture_process_output テスト

```python
class TestCaptureProcessOutput:
    """プロセス出力キャプチャテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    @pytest.mark.asyncio
    async def test_captures_both_streams(self, task):
        """JCSCAN-033: プロセス出力キャプチャ"""
        # Arrange
        mock_process = MagicMock()
        stdout_lines = [b"stdout line1\n", b"stdout line2\n", b""]
        stderr_lines = [b"stderr line1\n", b""]
        mock_process.stdout.readline = AsyncMock(side_effect=stdout_lines)
        mock_process.stderr.readline = AsyncMock(side_effect=stderr_lines)

        # Act
        stdout, stderr = await task._capture_process_output(mock_process)

        # Assert
        assert len(stdout) == 2
        assert len(stderr) == 1
        assert "[CUSTODIAN_STDOUT]" in stdout[0]
        assert "[CUSTODIAN_STDERR]" in stderr[0]
```

### 2.15 _process_scan_results テスト

```python
class TestProcessScanResults:
    """スキャン結果処理テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._handle_successful_scan = AsyncMock(return_value={"message": "成功"})
            t._handle_failed_scan = AsyncMock(side_effect=Exception("失敗"))
            return t

    @pytest.mark.asyncio
    async def test_routes_to_success_handler(self, task):
        """JCSCAN-034: 成功時の結果処理ルーティング

        custodian_scan.py:636-638 の分岐をカバー。
        """
        # Arrange
        scan_results = {"return_code": 0, "violations_count": 5}

        # Act
        await task._process_scan_results(scan_results, "aws")

        # Assert
        task._handle_successful_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_routes_to_failure_handler(self, task):
        """JCSCAN-035: 失敗時の結果処理ルーティング

        custodian_scan.py:639-641 の分岐をカバー。
        """
        # Arrange
        scan_results = {"return_code": 1, "violations_count": 0}

        # Act & Assert
        with pytest.raises(Exception):
            await task._process_scan_results(scan_results, "aws")
        task._handle_failed_scan.assert_called_once()
```

### 2.16 _handle_successful_scan テスト

```python
class TestHandleSuccessfulScan:
    """成功時スキャン結果処理テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._update_scan_history = AsyncMock()
            return t

    @pytest.mark.asyncio
    async def test_violations_with_ai_summary(self, task):
        """JCSCAN-036: 成功+違反あり+AI要約成功

        custodian_scan.py:652-687 の分岐をカバー。
        """
        # Arrange
        base_summary = {"violations_found": 5, "scan_metadata": {"cloud_provider": "aws"}}
        scan_results = {"output_dir": "/tmp/output", "cloud_provider": "aws"}

        with patch("app.jobs.tasks.custodian_scan.store_custodian_output_to_opensearch", return_value=5), \
             patch("app.jobs.tasks.custodian_scan.generate_scan_summary", return_value={"summary": "テスト"}):
            # Act
            result = await task._handle_successful_scan(base_summary, 5, scan_results)

        # Assert
        assert "正常完了" in result["message"]
        assert result["summary_data"]["scan_metadata"]["has_ai_summary"] is True
        assert "ai_scan_summary" in result["summary_data"]

    @pytest.mark.asyncio
    async def test_no_violations_with_metadata(self, task):
        """JCSCAN-037: 成功+違反なし+メタデータ抽出成功

        custodian_scan.py:688-734 の分岐をカバー。
        """
        # Arrange
        base_summary = {"violations_found": 0, "scan_metadata": {"cloud_provider": "aws"}}
        scan_results = {"output_dir": "/tmp/output", "cloud_provider": "aws"}
        mock_metadata = {"some": "data"}
        mock_scan_info = {
            "account_id": "123456789012",
            "region": "us-east-1",
            "policy_count": 3,
            "execution_duration": "10s",
            "custodian_version": "0.9.35",
            "scan_start_time": "2026-01-01T00:00:00Z",
            "scan_end_time": "2026-01-01T00:00:10Z"
        }

        with patch("app.jobs.tasks.custodian_scan.extract_metadata_from_output_dir", return_value=mock_metadata), \
             patch("app.jobs.tasks.custodian_scan.extract_scan_info_from_metadata", return_value=mock_scan_info):
            # Act
            result = await task._handle_successful_scan(base_summary, 0, scan_results)

        # Assert
        assert "違反なし" in result["message"]
        assert result["summary_data"]["scan_metadata"]["metadata_extracted"] is True
        assert result["summary_data"]["scan_metadata"]["account_id"] == "123456789012"
```

### 2.17 レガシーラッパー テスト

```python
class TestRunCustodianScanTask:
    """レガシー互換ラッパー関数テスト"""

    @pytest.mark.asyncio
    async def test_legacy_wrapper(self):
        """JCSCAN-038: レガシーラッパー関数

        custodian_scan.py:834-846 をカバー。
        """
        # Arrange
        with patch("app.jobs.tasks.custodian_scan.CustodianScanTask") as mock_cls:
            mock_task = MagicMock()
            mock_task.execute = AsyncMock()
            mock_cls.return_value = mock_task

            from app.jobs.tasks.custodian_scan import run_custodian_scan_task

            # Act
            await run_custodian_scan_task("job-1", "yaml", {"key": "val"}, "aws")

        # Assert
        mock_cls.assert_called_once_with("job-1")
        mock_task.execute.assert_called_once_with(
            policy_yaml_content="yaml",
            credentials_data={"key": "val"},
            cloud_provider="aws"
        )
```

### 2.18 _handle_failed_scan / _analyze_scan_error_with_ai テスト

```python
class TestHandleFailedScan:
    """失敗時スキャン結果処理テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._update_scan_history = AsyncMock()
            t._analyze_scan_error_with_ai = AsyncMock()
            return t

    @pytest.mark.asyncio
    async def test_failed_scan_with_ai_analysis(self, task):
        """JCSCAN-039: 失敗時処理（AIエラー分析あり）

        custodian_scan.py:813-814 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ExternalServiceError
        task._analyze_scan_error_with_ai.return_value = {"error_type": "permission"}
        base_summary = {"violations_found": 0, "scan_metadata": {"cloud_provider": "aws"}}

        with patch("app.jobs.tasks.custodian_scan.create_error_summary_with_ai_analysis",
                   return_value={"summary": "エラー分析"}):
            # Act & Assert
            with pytest.raises(ExternalServiceError, match="AIエラー分析完了"):
                await task._handle_failed_scan(base_summary, 1, 0)

        # Assert
        task._update_scan_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_scan_without_ai_analysis(self, task):
        """JCSCAN-040: 失敗時処理（AIエラー分析なし）

        custodian_scan.py:815-816 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ExternalServiceError
        task._analyze_scan_error_with_ai.return_value = None
        base_summary = {"violations_found": 0, "scan_metadata": {"cloud_provider": "aws"}}

        with patch("app.jobs.tasks.custodian_scan.create_error_summary_with_ai_analysis",
                   return_value={"summary": "基本エラー"}):
            # Act & Assert
            with pytest.raises(ExternalServiceError, match="AIエラー分析失敗"):
                await task._handle_failed_scan(base_summary, 2, 0)


class TestAnalyzeScanErrorWithAi:
    """AIエラー分析テスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_no_last_scan_results(self, task):
        """JCSCAN-041: AIエラー分析で_last_scan_results未設定

        custodian_scan.py:750-752 の分岐をカバー。
        """
        # Arrange（_last_scan_resultsを設定しない）

        # Act
        result = await task._analyze_scan_error_with_ai(1)

        # Assert
        assert result is None
        task.logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_ai_analysis(self, task):
        """JCSCAN-042: AIエラー分析成功

        custodian_scan.py:754-769 の正常パスをカバー。
        """
        # Arrange
        task._last_scan_results = {
            "stdout_output": ["[STDOUT] line1"],
            "stderr_output": ["[STDERR] error"]
        }
        task._policy_yaml_content = "policies:\n  - name: test"
        task._cloud_provider = "aws"
        mock_analysis = {"error_type": "permission", "suggestion": "IAMロール確認"}

        with patch("app.jobs.tasks.custodian_scan.analyze_custodian_error_with_ai",
                   return_value=mock_analysis):
            # Act
            result = await task._analyze_scan_error_with_ai(1)

        # Assert
        assert result == mock_analysis
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JCSCAN-E01 | 空ポリシーで検証失敗 | `policy_yaml_content=""` | ValidationError("ポリシーYAMLが空です") |
| JCSCAN-E02 | 空認証情報で検証失敗 | `credentials_data={}` | ValidationError("認証情報が空です") |
| JCSCAN-E03 | 非対応プロバイダー | `cloud_provider="gcp"` | ValidationError("サポートされていない") |
| JCSCAN-E04 | 復号失敗 | 不正な暗号化データ | ProcessingError("復号化エラー") |
| JCSCAN-E05 | セキュア検証で予期しない例外ラップ | 内部例外発生 | ValidationError("セキュリティ検証中にエラー") |
| JCSCAN-E06 | 不正YAML構文 | `"{ invalid yaml"` | ValidationError("不正なYAML形式") |
| JCSCAN-E07 | YAMLが辞書でない | `"- list item"` | ValidationError("辞書形式である必要") |
| JCSCAN-E08 | policiesフィールド欠落 | `"name: test"` | ValidationError("policiesフィールドが必要") |
| JCSCAN-E09 | policies空リスト | `"policies: []"` | ValidationError("空でないリスト") |
| JCSCAN-E10 | YAMLサイズ超過（1MB） | 1MB超のYAML | ValidationError("サイズが制限") |
| JCSCAN-E11 | AWS必須フィールド欠落 | `accessKey`なし | ValidationError("必須フィールドが不足") |
| JCSCAN-E12 | 不正AWSアクセスキー形式 | `"INVALID_KEY"` | ValidationError("不正なAWSアクセスキー形式") |
| JCSCAN-E13 | 不正AWSシークレットキー形式 | 40文字未満 | ValidationError("不正なAWSシークレットキー形式") |
| JCSCAN-E14 | 不正AWSリージョン形式 | `"INVALID!"` | ValidationError("不正なAWSリージョン形式") |
| JCSCAN-E15 | Azure必須フィールド欠落 | `tenantId`なし | ValidationError("必須フィールドが不足") |
| JCSCAN-E16 | 不正Azure GUID形式 | `"not-a-guid"` | ValidationError("不正なAzure") |
| JCSCAN-E17 | パストラバーサル攻撃 | `"../../etc/passwd"` | ValidationError("パストラバーサル") |
| JCSCAN-E18 | 基底ディレクトリ外アクセス | `/etc/passwd` | ValidationError("ベースディレクトリ外") |
| JCSCAN-E19 | 不正な環境変数値 | 空白・特殊記号含む値 | ValidationError("不正な環境変数値") |
| JCSCAN-E20 | コマンドファイル不存在 | 存在しない絶対パス | ProcessingError("コマンドが見つかりません") |
| JCSCAN-E21 | ポリシーファイル不存在 | 存在しないパス | ValidationError("ポリシーファイルが存在しません") |
| JCSCAN-E22 | Custodianタイムアウト | 30分超過 | ProcessingError("タイムアウト") |
| JCSCAN-E23 | 履歴更新で例外発生（継続） | `os_client.update` が例外 | warning出力のみでメインタスク継続 |
| JCSCAN-E24 | 違反なし時メタデータ抽出例外 | `extract_metadata_from_output_dir` が例外 | metadata_extracted=False, エラーログ |

### 3.1 入力検証 異常系

```python
class TestValidateInputsErrors:
    """入力検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_empty_policy(self, task):
        """JCSCAN-E01: 空ポリシーで検証失敗

        custodian_scan.py:119-120 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="ポリシーYAMLが空です"):
            task._validate_inputs("", {"key": "val"}, "aws")

    def test_empty_credentials(self, task):
        """JCSCAN-E02: 空認証情報で検証失敗

        custodian_scan.py:122-123 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="認証情報が空です"):
            task._validate_inputs("policies: []", {}, "aws")

    def test_unsupported_provider(self, task):
        """JCSCAN-E03: 非対応プロバイダー

        custodian_scan.py:125-126 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="サポートされていないクラウドプロバイダー"):
            task._validate_inputs("policies: []", {"key": "val"}, "gcp")
```

### 3.2 認証情報復号 異常系

```python
class TestDecryptCredentialsErrors:
    """認証情報復号エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_decryption_failure(self, task):
        """JCSCAN-E04: 復号失敗

        custodian_scan.py:206-208 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ProcessingError
        with patch("app.jobs.tasks.custodian_scan.decrypt_credentials_field",
                   side_effect=Exception("復号失敗")):
            # Act & Assert
            with pytest.raises(ProcessingError, match="復号化エラー"):
                task._decrypt_credentials_if_needed({"encryptedData": "bad-data"})
```

### 3.3 セキュア検証 異常系

```python
class TestValidateInputsSecureErrors:
    """セキュア検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_unexpected_exception_wrapped(self, task):
        """JCSCAN-E05: セキュア検証で予期しない例外ラップ

        custodian_scan.py:249-251 の分岐をカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        task._validate_policy_yaml_secure = MagicMock(side_effect=RuntimeError("予期しない"))

        # Act & Assert
        with pytest.raises(ValidationError, match="セキュリティ検証中にエラーが発生しました"):
            await task._validate_inputs_secure("policies:\n  - name: t", {"k": "v"}, "aws")
```

### 3.4 YAML検証 異常系

```python
class TestValidatePolicyYamlSecureErrors:
    """YAML安全性検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_invalid_yaml_syntax(self, task):
        """JCSCAN-E06: 不正YAML構文

        custodian_scan.py:287-288 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="不正なYAML形式"):
            task._validate_policy_yaml_secure("{ invalid: yaml: [")

    def test_yaml_not_dict(self, task):
        """JCSCAN-E07: YAMLが辞書でない

        custodian_scan.py:260-261 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="辞書形式である必要"):
            task._validate_policy_yaml_secure("- list item\n- another")

    def test_no_policies_field(self, task):
        """JCSCAN-E08: policiesフィールド欠落

        custodian_scan.py:264-265 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="policiesフィールドが必要"):
            task._validate_policy_yaml_secure("name: test\nresource: aws.ec2")

    def test_empty_policies_list(self, task):
        """JCSCAN-E09: policies空リスト

        custodian_scan.py:269-270 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="空でないリスト"):
            task._validate_policy_yaml_secure("policies: []")

    def test_oversized_yaml(self, task):
        """JCSCAN-E10: YAMLサイズ超過（1MB）

        custodian_scan.py:282-283 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        # 1MB超のYAMLを生成
        large_yaml = "policies:\n  - name: test\n    description: " + "A" * (1024 * 1024 + 1)
        with pytest.raises(ValidationError, match="サイズが制限"):
            task._validate_policy_yaml_secure(large_yaml)
```

### 3.5 AWS/Azure認証情報検証 異常系

```python
class TestValidateAwsCredentialsErrors:
    """AWS認証情報検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_missing_required_field(self, task):
        """JCSCAN-E11: AWS必須フィールド欠落

        custodian_scan.py:304-306 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="必須フィールドが不足"):
            task._validate_aws_credentials({"secretKey": "secret", "defaultRegion": "us-east-1"})

    def test_invalid_access_key_format(self, task):
        """JCSCAN-E12: 不正AWSアクセスキー形式

        custodian_scan.py:310-311 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        creds = {"accessKey": "INVALID_KEY_FORMAT", "secretKey": "s" * 40, "defaultRegion": "us-east-1"}
        with pytest.raises(ValidationError, match="不正なAWSアクセスキー形式"):
            task._validate_aws_credentials(creds)

    def test_invalid_secret_key_format(self, task):
        """JCSCAN-E13: 不正AWSシークレットキー形式

        custodian_scan.py:315-316 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        creds = {"accessKey": "AKIAIOSFODNN7EXAMPLE", "secretKey": "too-short", "defaultRegion": "us-east-1"}
        with pytest.raises(ValidationError, match="不正なAWSシークレットキー形式"):
            task._validate_aws_credentials(creds)

    def test_invalid_region_format(self, task):
        """JCSCAN-E14: 不正AWSリージョン形式

        custodian_scan.py:324-325 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        creds = {
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "defaultRegion": "INVALID!"
        }
        with pytest.raises(ValidationError, match="不正なAWSリージョン形式"):
            task._validate_aws_credentials(creds)


class TestValidateAzureCredentialsErrors:
    """Azure認証情報検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_missing_required_field(self, task):
        """JCSCAN-E15: Azure必須フィールド欠落

        custodian_scan.py:336-338 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="必須フィールドが不足"):
            task._validate_azure_credentials({"clientId": "id", "clientSecret": "secret"})

    def test_invalid_guid_format(self, task):
        """JCSCAN-E16: 不正Azure GUID形式

        custodian_scan.py:344-346 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        creds = {
            "tenantId": "not-a-guid",
            "clientId": "abcdef01-2345-6789-abcd-ef0123456789",
            "clientSecret": "secret",
            "subscriptionId": "11111111-2222-3333-4444-555555555555"
        }
        with pytest.raises(ValidationError, match="不正なAzure tenantId形式"):
            task._validate_azure_credentials(creds)
```

### 3.6 サニタイズ・パス検証 異常系

```python
class TestSanitizeFilePathErrors:
    """ファイルパスサニタイズエラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            return CustodianScanTask("test-job")

    def test_path_traversal(self, task):
        """JCSCAN-E17: パストラバーサル攻撃

        custodian_scan.py:359-360 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="パストラバーサル"):
            task._sanitize_file_path("../../etc/passwd", "/tmp/scan")

    def test_absolute_path_outside_base(self, task):
        """JCSCAN-E18: 基底ディレクトリ外アクセス

        custodian_scan.py:365-366 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with pytest.raises(ValidationError, match="ベースディレクトリ外"):
            task._sanitize_file_path("/etc/passwd", "/tmp/scan")


class TestSanitizeEnvironmentVariablesErrors:
    """環境変数サニタイズエラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_invalid_value_pattern(self, task):
        """JCSCAN-E19: 不正な環境変数値

        custodian_scan.py:390-391 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        env = {"AWS_ACCESS_KEY_ID": "value with spaces & special!"}
        with pytest.raises(ValidationError, match="不正な環境変数値"):
            task._sanitize_environment_variables(env)
```

### 3.7 コマンド実行 異常系

```python
class TestRunCustodianCommandErrors:
    """Custodianコマンド実行エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_command_file_not_found(self, task):
        """JCSCAN-E20: コマンドファイル不存在

        custodian_scan.py:477-479 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ProcessingError
        with patch.dict(os.environ, {
            "ENABLE_SECURITY_VALIDATION": "false",
            "CUSTODIAN_CMD_PATH": "/nonexistent/custodian"
        }), patch("os.path.isfile", return_value=False):
            with pytest.raises(ProcessingError, match="コマンドが見つかりません"):
                await task._run_custodian_command("/tmp/p.yaml", "/tmp/out", {}, "aws")

    @pytest.mark.asyncio
    async def test_policy_file_not_exists(self, task):
        """JCSCAN-E21: ポリシーファイル不存在

        custodian_scan.py:517-518 の分岐をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}, clear=False), \
             patch("os.path.exists", return_value=False):
            with pytest.raises(ValidationError, match="ポリシーファイルが存在しません"):
                await task._run_custodian_command("/tmp/p.yaml", "/tmp/out", {}, "aws")

    @pytest.mark.asyncio
    async def test_timeout(self, task):
        """JCSCAN-E22: Custodianタイムアウト

        custodian_scan.py:537-540 の分岐をカバー。
        """
        import asyncio as aio
        from app.jobs.common.error_handling import ProcessingError

        mock_process = AsyncMock()
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock(return_value=-9)

        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}, clear=False), \
             patch("asyncio.create_subprocess_exec", return_value=mock_process), \
             patch("asyncio.wait_for", side_effect=aio.TimeoutError()), \
             patch("os.path.exists", return_value=True):
            with pytest.raises(ProcessingError, match="タイムアウト"):
                await task._run_custodian_command("/tmp/p.yaml", "/tmp/out", {}, "aws")

        # プロセスが確実にkillされたことを検証
        mock_process.kill.assert_called_once()
```

### 3.8 履歴更新・メタデータ抽出 異常系

```python
class TestUpdateScanHistoryErrors:
    """履歴更新エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    @pytest.mark.asyncio
    async def test_update_exception_continues(self, task):
        """JCSCAN-E23: 履歴更新で例外発生（継続）

        custodian_scan.py:108-110 の分岐をカバー。
        エラーが発生してもメインタスクは継続する。
        """
        # Arrange
        mock_client = AsyncMock()
        mock_client.update = AsyncMock(side_effect=Exception("OpenSearch接続エラー"))
        with patch("app.jobs.tasks.custodian_scan.get_opensearch_client", return_value=mock_client):
            # Act（例外は発生しない）
            await task._update_scan_history({"message": "テスト"})

        # Assert
        task.logger.warning.assert_called_once()
        assert "失敗しました" in str(task.logger.warning.call_args)


class TestHandleSuccessfulScanErrors:
    """成功時スキャン結果処理のエラーケースのテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            t._update_scan_history = AsyncMock()
            return t

    @pytest.mark.asyncio
    async def test_metadata_extraction_exception(self, task):
        """JCSCAN-E24: 違反なし時メタデータ抽出例外

        custodian_scan.py:727-730 の except Exception 分岐をカバー。
        """
        # Arrange
        base_summary = {"violations_found": 0, "scan_metadata": {"cloud_provider": "aws"}}
        scan_results = {"output_dir": "/tmp/output", "cloud_provider": "aws"}

        with patch("app.jobs.tasks.custodian_scan.extract_metadata_from_output_dir",
                   side_effect=Exception("メタデータ読取エラー")):
            # Act
            result = await task._handle_successful_scan(base_summary, 0, scan_results)

        # Assert
        assert result["summary_data"]["scan_metadata"]["metadata_extracted"] is False
        assert "メタデータ読取エラー" in result["summary_data"]["scan_metadata"]["metadata_extraction_error"]
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JCSCAN-SEC-01 | YAMLインジェクション防止 | `exec`, `system`, `__import__` 含むYAML | ValidationError発生 |
| JCSCAN-SEC-02 | パストラバーサル防止 | `../`, 絶対パス攻撃 | ValidationError発生 |
| JCSCAN-SEC-03 | 環境変数ホワイトリスト強制 | 非許可環境変数 | 除外される |
| JCSCAN-SEC-04 | AWSアクセスキーフォーマット強制 | AKIA以外開始・長さ不正 | ValidationError発生 |
| JCSCAN-SEC-05 | Azure GUID形式強制 | 不正フォーマット | ValidationError発生 |
| JCSCAN-SEC-06 | コマンドインジェクション防止 | `".."` 含むパス・不正パス | False返却 |
| JCSCAN-SEC-07 | ログのマスキング確認 | Custodianコマンド実行 | ファイルパスがマスクされたログ |
| JCSCAN-SEC-08 | YAMLサイズ制限 | 1MB超YAML | ValidationError発生 |
| JCSCAN-SEC-09 | バリデーションエラーメッセージ内認証情報非漏洩 | 不正形式の認証情報でValidationError発生 | エラーメッセージに実際の認証情報値が含まれない |
| JCSCAN-SEC-10 | AI分析関数引数に認証情報非送信 | AI分析呼出 | 位置引数がjob_id/return_code/stdout/stderr/provider/policyの6個（credentialsなし） |
| JCSCAN-SEC-11 | OpenSearch履歴更新データに認証情報非混入 | _update_scan_history呼出 | 送信データに認証情報キーワードが含まれない |

```python
@pytest.mark.security
class TestCustodianScanSecurity:
    """CustodianScanTaskセキュリティテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.custodian_scan.TaskLogger"), \
             patch("app.jobs.tasks.custodian_scan.StatusTracker"):
            from app.jobs.tasks.custodian_scan import CustodianScanTask
            t = CustodianScanTask("test-job")
            t.logger = MagicMock()
            return t

    def test_yaml_injection_all_keywords(self, task):
        """JCSCAN-SEC-01: YAMLインジェクション防止

        custodian_scan.py:273-279 の危険キーワードリスト全件をカバー。
        """
        from app.jobs.common.error_handling import ValidationError
        dangerous_keywords = ["exec", "system", "subprocess", "eval", "__import__"]

        for keyword in dangerous_keywords:
            yaml_content = f"policies:\n  - name: test\n    description: {keyword}"
            with pytest.raises(ValidationError, match="危険なキーワードが検出されました"):
                task._validate_policy_yaml_secure(yaml_content)

    def test_path_traversal_variants(self, task):
        """JCSCAN-SEC-02: パストラバーサル防止

        custodian_scan.py:359-366 のパストラバーサル防止を複数パターンで検証。
        """
        from app.jobs.common.error_handling import ValidationError
        traversal_paths = [
            "../../etc/passwd",
            "../../../root/.ssh/id_rsa",
            "subdir/../../etc/shadow",
        ]
        for path in traversal_paths:
            with pytest.raises(ValidationError, match="パストラバーサル"):
                task._sanitize_file_path(path, "/tmp/scan")

    def test_env_var_whitelist_enforcement(self, task):
        """JCSCAN-SEC-03: 環境変数ホワイトリスト強制

        custodian_scan.py:378-394 のホワイトリスト制御を検証。
        攻撃者が注入可能な環境変数が除外されることを確認。
        """
        # Arrange
        malicious_env = {
            "AWS_ACCESS_KEY_ID": "AKIATEST1234567890",
            "LD_PRELOAD": "/tmp/malicious.so",
            "PATH": "/tmp/evil:/usr/bin",
            "PYTHONPATH": "/tmp/evil"
        }

        # Act
        result = task._sanitize_environment_variables(malicious_env)

        # Assert
        assert "AWS_ACCESS_KEY_ID" in result
        assert "LD_PRELOAD" not in result
        assert "PATH" not in result
        assert "PYTHONPATH" not in result

    def test_aws_key_format_enforcement(self, task):
        """JCSCAN-SEC-04: AWSアクセスキーフォーマット強制

        custodian_scan.py:310-311 のフォーマット検証を攻撃パターンで検証。
        """
        from app.jobs.common.error_handling import ValidationError
        invalid_keys = [
            {"accessKey": "ASIA1234567890123456", "secretKey": "s" * 40, "defaultRegion": "us-east-1"},  # ASIAは不可
            {"accessKey": "AKIA12345", "secretKey": "s" * 40, "defaultRegion": "us-east-1"},  # 短すぎ
            {"accessKey": "AKIA" + "a" * 16, "secretKey": "s" * 40, "defaultRegion": "us-east-1"},  # 小文字含む
        ]
        for creds in invalid_keys:
            with pytest.raises(ValidationError, match="不正なAWSアクセスキー形式"):
                task._validate_aws_credentials(creds)

    def test_azure_guid_format_enforcement(self, task):
        """JCSCAN-SEC-05: Azure GUID形式強制

        custodian_scan.py:344-346 のGUID検証を攻撃パターンで検証。
        """
        from app.jobs.common.error_handling import ValidationError
        creds = {
            "tenantId": "'; DROP TABLE users; --",
            "clientId": "abcdef01-2345-6789-abcd-ef0123456789",
            "clientSecret": "secret",
            "subscriptionId": "11111111-2222-3333-4444-555555555555"
        }
        with pytest.raises(ValidationError, match="不正なAzure tenantId形式"):
            task._validate_azure_credentials(creds)

    def test_command_injection_prevention(self, task):
        """JCSCAN-SEC-06: コマンドインジェクション防止

        custodian_scan.py:398-426 のコマンドパス検証を攻撃パターンで検証。
        """
        # Arrange
        malicious_paths = [
            "",
            "custodian; rm -rf /",
            "../../../bin/sh",
            "/tmp/malicious_custodian",
        ]

        # Act & Assert
        for path in malicious_paths:
            result = task._validate_command_path(path)
            assert result is False, f"悪意あるパスが許可されました: {path}"

    @pytest.mark.asyncio
    async def test_log_masking(self, task):
        """JCSCAN-SEC-07: ログのマスキング確認

        custodian_scan.py:510-514 のログマスキングを検証。
        実際のファイルパスがログに含まれないことを確認。
        """
        # Arrange
        mock_process = AsyncMock()
        mock_process.wait = AsyncMock(return_value=0)
        task._capture_process_output = AsyncMock(return_value=([], []))

        with patch.dict(os.environ, {"ENABLE_SECURITY_VALIDATION": "false"}, clear=False), \
             patch("asyncio.create_subprocess_exec", return_value=mock_process), \
             patch("app.jobs.tasks.custodian_scan.count_violations_from_custodian_output", return_value=0), \
             patch("os.path.exists", return_value=True):
            # Act
            await task._run_custodian_command(
                "/tmp/secret/policy.yaml", "/tmp/secret/output", {}, "aws"
            )

        # Assert（ログにマスクされたコマンドが含まれる）
        log_messages = [str(c) for c in task.logger.info.call_args_list]
        # 実際のパスがマスクされていること
        assert any("<output_dir>" in msg for msg in log_messages)
        assert any("<policy_file>" in msg for msg in log_messages)

    def test_yaml_size_limit(self, task):
        """JCSCAN-SEC-08: YAMLサイズ制限

        custodian_scan.py:282-283 のサイズ制限をDoS攻撃パターンで検証。
        """
        from app.jobs.common.error_handling import ValidationError
        # 1MB超の巨大YAMLでDoS攻撃を模倣
        large_yaml = "policies:\n  - name: test\n    tags:\n" + "      key: " + "X" * (1024 * 1024) + "\n"
        with pytest.raises(ValidationError, match="サイズが制限"):
            task._validate_policy_yaml_secure(large_yaml)

    def test_validation_error_does_not_leak_credential_values(self, task):
        """JCSCAN-SEC-09: バリデーションエラーメッセージ内認証情報非漏洩

        custodian_scan.py:301-331 の認証情報検証メソッドを検証。
        ValidationErrorメッセージに実際の認証情報値が含まれないことを確認する回帰テスト。
        将来のコード変更でエラーメッセージに認証情報値を含めてしまうリグレッションを防止。
        """
        # Arrange
        secret_value = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        invalid_access_key = "INVALID_KEY_FORMAT"
        creds = {
            "accessKey": invalid_access_key,  # 不正形式でValidationError発生
            "secretKey": secret_value,
            "defaultRegion": "us-east-1"
        }

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            task._validate_aws_credentials(creds)

        # エラーメッセージに認証情報の実際の値が含まれないことを確認
        error_msg = str(exc_info.value)
        assert secret_value not in error_msg, "シークレットキーがエラーメッセージに漏洩しています"
        assert invalid_access_key not in error_msg, "アクセスキーがエラーメッセージに漏洩しています"

    @pytest.mark.asyncio
    async def test_ai_analysis_called_without_credentials(self, task):
        """JCSCAN-SEC-10: AI分析関数引数に認証情報非送信

        custodian_scan.py:762-768 のAI分析呼び出しを検証。
        analyze_custodian_error_with_aiに渡される位置引数が
        (job_id, return_code, stdout, stderr, provider, policy) の6個のみで、
        認証情報オブジェクトが含まれないことを位置引数レベルで確認。
        """
        # Arrange
        task._last_scan_results = {
            "stdout_output": ["[STDOUT] Running policy"],
            "stderr_output": ["[STDERR] Error: AccessDenied"]
        }
        task._policy_yaml_content = "policies:\n  - name: test"
        task._cloud_provider = "aws"

        with patch("app.jobs.tasks.custodian_scan.analyze_custodian_error_with_ai",
                   return_value={"analysis": "テスト"}) as mock_analyze:
            # Act
            await task._analyze_scan_error_with_ai(1)

        # Assert（位置引数を厳密に検証: credentials は含まれない）
        mock_analyze.assert_called_once()
        args = mock_analyze.call_args[0]  # 位置引数のタプル
        assert len(args) == 6, f"AI分析関数の引数数が想定外: {len(args)}（認証情報が混入している可能性）"
        assert args[0] == task.job_id       # job_id
        assert args[1] == 1                 # return_code
        assert args[2] == ["[STDOUT] Running policy"]   # stdout_output
        assert args[3] == ["[STDERR] Error: AccessDenied"]  # stderr_output
        assert args[4] == "aws"             # cloud_provider
        assert args[5] == "policies:\n  - name: test"  # policy_yaml

    @pytest.mark.asyncio
    async def test_opensearch_history_does_not_contain_credentials(self, task):
        """JCSCAN-SEC-11: OpenSearch履歴更新データに認証情報非混入

        custodian_scan.py:79-110 のOpenSearch履歴更新を検証。
        _update_scan_historyに渡されるデータがos_client.updateに送信される際、
        認証情報キーワードが含まれないことを確認。
        """
        # Arrange
        mock_os_client = AsyncMock()
        summary_data = {
            "message": "スキャン完了",
            "summary_data": {
                "violations_found": 3,
                "scan_metadata": {
                    "cloud_provider": "aws",
                    "scan_completed_at": "2025-01-01T00:00:00Z"
                }
            }
        }

        with patch("app.jobs.tasks.custodian_scan.get_opensearch_client",
                   return_value=mock_os_client):
            # Act
            await task._update_scan_history(summary_data)

        # Assert（OpenSearchに送信されるデータに認証情報が含まれない）
        mock_os_client.update.assert_called_once()
        update_body = str(mock_os_client.update.call_args)
        credential_keywords = [
            "accessKey", "secretKey", "sessionToken",
            "clientSecret", "AWS_SECRET_ACCESS_KEY", "AZURE_CLIENT_SECRET"
        ]
        for keyword in credential_keywords:
            assert keyword not in update_body, \
                f"認証情報キーワード '{keyword}' がOpenSearch更新データに含まれています"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_custodian_scan_module` | テスト間のstatus_managerグローバル状態リセット | function | Yes |
| `task` | 各テストクラス内のCustodianScanTaskインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/conftest.py に追加
# （既存のreset_base_task_moduleフィクスチャと共存）
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def reset_custodian_scan_module():
    """テストごとにstatus_managerのグローバル状態をリセット

    CustodianScanTaskはBaseTask経由でstatus_managerを使用するため、
    テスト間のグローバル状態汚染を防止する。
    """
    yield
    try:
        from app.jobs.status_manager import job_statuses
        job_statuses.clear()
    except ImportError:
        pass
```

> **注記**: `test/unit/jobs/tasks/conftest.py` には既に `reset_base_task_module` フィクスチャが存在する。同一の `job_statuses.clear()` ロジックのため、既存フィクスチャがあれば `reset_custodian_scan_module` の追加は不要。conftest.pyを新規作成する場合のみ上記コードを使用すること。

---

## 6. テスト実行例

```bash
# custodian_scan関連テストのみ実行
pytest test/unit/jobs/tasks/test_custodian_scan.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/test_custodian_scan.py::TestValidateAwsCredentials -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/test_custodian_scan.py \
    --cov=app.jobs.tasks.custodian_scan --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/jobs/tasks/test_custodian_scan.py -m "security" -v

# 非同期テスト実行（pytest-asyncioが必要）
# pyproject.toml: asyncio_mode = "auto"
pytest test/unit/jobs/tasks/test_custodian_scan.py -v --asyncio-mode=auto
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 42 | JCSCAN-001 〜 JCSCAN-042 |
| 異常系 | 24 | JCSCAN-E01 〜 JCSCAN-E24 |
| セキュリティ | 11 | JCSCAN-SEC-01 〜 JCSCAN-SEC-11 |
| **合計** | **77** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCustodianScanTaskInit` | JCSCAN-001 | 1 |
| `TestExecuteTask` | JCSCAN-002〜003 | 2 |
| `TestValidateInputs` | JCSCAN-004 | 1 |
| `TestUpdateScanHistory` | JCSCAN-005〜006 | 2 |
| `TestSetupEnvironment` | JCSCAN-007〜009 | 3 |
| `TestDecryptCredentials` | JCSCAN-010〜011 | 2 |
| `TestValidateInputsSecure` | JCSCAN-012 | 1 |
| `TestValidatePolicyYamlSecure` | JCSCAN-013〜014 | 2 |
| `TestValidateAwsCredentials` | JCSCAN-015〜017 | 3 |
| `TestValidateAzureCredentials` | JCSCAN-018 | 1 |
| `TestSanitizeFilePath` | JCSCAN-019〜020 | 2 |
| `TestSanitizeEnvironmentVariables` | JCSCAN-021〜022 | 2 |
| `TestValidateCommandPath` | JCSCAN-023〜025 | 3 |
| `TestHandleValidationFailure` | JCSCAN-026 | 1 |
| `TestRunCustodianCommand` | JCSCAN-027〜029 | 3 |
| `TestLogCustodianOutput` | JCSCAN-030〜032 | 3 |
| `TestCaptureProcessOutput` | JCSCAN-033 | 1 |
| `TestProcessScanResults` | JCSCAN-034〜035 | 2 |
| `TestHandleSuccessfulScan` | JCSCAN-036〜037 | 2 |
| `TestRunCustodianScanTask` | JCSCAN-038 | 1 |
| `TestHandleFailedScan` | JCSCAN-039〜040 | 2 |
| `TestAnalyzeScanErrorWithAi` | JCSCAN-041〜042 | 2 |
| `TestValidateInputsErrors` | JCSCAN-E01〜E03 | 3 |
| `TestDecryptCredentialsErrors` | JCSCAN-E04 | 1 |
| `TestValidateInputsSecureErrors` | JCSCAN-E05 | 1 |
| `TestValidatePolicyYamlSecureErrors` | JCSCAN-E06〜E10 | 5 |
| `TestValidateAwsCredentialsErrors` | JCSCAN-E11〜E14 | 4 |
| `TestValidateAzureCredentialsErrors` | JCSCAN-E15〜E16 | 2 |
| `TestSanitizeFilePathErrors` | JCSCAN-E17〜E18 | 2 |
| `TestSanitizeEnvironmentVariablesErrors` | JCSCAN-E19 | 1 |
| `TestRunCustodianCommandErrors` | JCSCAN-E20〜E22 | 3 |
| `TestUpdateScanHistoryErrors` | JCSCAN-E23 | 1 |
| `TestHandleSuccessfulScanErrors` | JCSCAN-E24 | 1 |
| `TestCustodianScanSecurity` | JCSCAN-SEC-01〜JCSCAN-SEC-11 | 11 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 注意事項

- `pytest-asyncio` が必要（async テストメソッドが多数）
- `pyproject.toml` に `asyncio_mode = "auto"` 設定推奨
- `@pytest.mark.security` マーカーの登録が必要
- 環境変数パッチは `patch.dict(os.environ, ...)` で実行時に適用（import前不要）
- `_run_custodian_command` のテストは `asyncio.create_subprocess_exec` のモックが複雑なため、統合テストでの補完を推奨

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `asyncio.create_subprocess_exec` の完全モックが困難 | `_run_custodian_command` のプロセス実行部分のテストが複雑 | `_capture_process_output` を別途モックし、プロセス実行ロジックを分離してテスト |
| 2 | AI分析関数（`generate_scan_summary`, `analyze_custodian_error_with_ai`）は外部LLM依存 | 実際のAI応答は単体テストで検証不可 | モックで返却値を制御し、呼び出しの有無と結果ハンドリングを検証 |
| 3 | `_handle_successful_scan` のメタデータ抽出部分が `extract_metadata_from_output_dir` に依存 | 実ファイルシステムへのアクセスが発生 | ユーティリティ関数をモックして返却値を制御 |
| 4 | OpenSearch履歴更新（`_update_scan_history`）は実インデックスへのアクセスが必要 | 単体テストでは接続不可 | `get_opensearch_client` をモックしてクライアント操作を検証 |
| 5 | `_validate_command_path` の実ファイル存在チェック（L420）はテスト環境依存 | テスト環境にCustodianがインストールされていない場合パターンマッチのみ検証 | `os.path.isfile` と `os.access` をモックして制御 |
| 6 | セキュリティ検証は `ENABLE_SECURITY_VALIDATION=true` でのみ有効 | デフォルト無効のため本番環境でのセキュリティ検証が実行されない可能性 | テストでは両方のパスを検証するが、本番設定の確認は運用チームに委ねる |
