# aws_plugin テストケース

## 1. 概要

`aws_plugin` は動的AssumeRoleによるAWS操作機能を提供するプラグインです。
顧客ごとに異なるAWSアカウントに対して、リクエスト毎にAssumeRoleして操作を実行する内部MCPツールを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `get_regions_with_assume_role` | AssumeRoleでリージョン一覧を取得するAPIエンドポイント |
| `AWSExecutor.execute` | 動的AssumeRoleによるAWS操作実行 |
| `AWSExecutor._assume_role` | AssumeRoleで一時認証情報を取得 |
| `AWSExecutor.list_actions` | サービスで利用可能なアクション一覧を取得 |
| `AWSExecutor.get_help` | AWS CLIヘルプを取得 |
| `handle_aws_execute` | AWS操作実行MCPツールハンドラー |
| `handle_aws_list_actions` | アクション一覧取得MCPツールハンドラー |
| `handle_aws_get_help` | ヘルプ取得MCPツールハンドラー |
| `register_aws_internal_tools` | AWS内部ツールをMCPクライアントに登録 |

### 1.2 カバレッジ目標: 80%

> **注記**: AWS操作は重要なセキュリティ機能であり、AssumeRoleによるクロスアカウントアクセスを含むため、高いカバレッジを目標とします。boto3クライアントおよびsubprocessの外部呼び出しはモックでカバーします。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象（ルーター） | `app/aws_plugin/assume_role.py` |
| テスト対象（実行クラス） | `app/aws_plugin/executor.py` |
| テスト対象（MCPツール） | `app/aws_plugin/internal_tools.py` |
| テストコード | `test/unit/aws_plugin/test_assume_role.py` |
| テストコード | `test/unit/aws_plugin/test_executor.py` |
| テストコード | `test/unit/aws_plugin/test_internal_tools.py` |

### 1.4 補足情報

#### グローバル変数
- `REGION_NAME_MAPPING` (assume_role.py:13-31): AWSリージョンコードから日本語名へのマッピング辞書
- `aws_executor` (executor.py:233): AWSExecutorのグローバルインスタンス
- `AWS_INTERNAL_TOOLS` (internal_tools.py:174-391): MCP内部ツール定義リスト
- `AWS_TOOL_HANDLERS` (internal_tools.py:395-399): ツールハンドラーマッピング
- `AWS_INTERNAL_SERVER_NAME` (internal_tools.py:402): 内部サーバー名 "aws-internal"

#### 主要分岐
- assume_role.py:114-199: ClientErrorの詳細分析（AccessDenied, InvalidUserID, ValidationException等）
- assume_role.py:201-206: NoCredentialsError処理
- assume_role.py:208-234: BotoCoreError処理（パラメータ検証エラーの分岐）
- executor.py:87-92: アクション存在チェック
- internal_tools.py:66-78: cloud_credentialsからの認証情報取得ロジック

#### 外部依存
- boto3: STSクライアント、EC2クライアント、各種AWSサービスクライアント
- subprocess: AWS CLIヘルプ取得
- mcp_client: MCP内部ツール登録

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|----------|
| AWS-001 | AssumeRoleでリージョン一覧取得成功 | 有効なrole_arn, external_id | 200, success=true, リージョンリスト |
| AWS-002 | リージョン情報の正しいマッピング（us-east-1） | us-east-1リージョン | "US East (N. Virginia)" |
| AWS-003 | リージョン情報の正しいマッピング（ap-northeast-1） | ap-northeast-1リージョン | "Asia Pacific (Tokyo)" |
| AWS-004 | マッピングにないリージョンはコードをそのまま使用 | 未知のリージョン | リージョンコードがそのまま名前に |
| AWS-005 | opt-in-not-requiredステータス変換 | opt-in-not-required | status="available" |
| AWS-006 | opt-in-requiredステータス変換 | opted-in | status="opt-in-required" |
| AWS-007 | AWSExecutor.execute正常実行 | 有効なパラメータ | success=true, result含む |
| AWS-008 | ResponseMetadataの除去 | レスポンスにResponseMetadata含む | ResponseMetadata除去済み |
| AWS-009a | datetimeオブジェクトのISO変換 | datetimeオブジェクト | ISO形式文字列に変換 |
| AWS-009b | dateオブジェクトのISO変換 | dateオブジェクト | ISO形式文字列に変換 |
| AWS-009c | ネストした辞書内のdatetimeをISO変換 | ネストした辞書 | 再帰的にISO変換 |
| AWS-009d | リスト内のdatetimeをISO変換 | リスト | 要素ごとにISO変換 |
| AWS-009e | datetime以外の値はそのまま返す | 非datetime値 | 入力値をそのまま返却 |
| AWS-010 | list_actionsでアクション一覧取得 | 有効なサービス名 | アクション名リスト（snake_case） |
| AWS-011 | _to_snake_case変換 | "DescribeInstances" | "describe_instances" |
| AWS-012 | get_helpでサービスヘルプ取得 | サービス名のみ | ヘルプテキスト |
| AWS-013 | get_helpでアクションヘルプ取得 | サービス名+アクション名 | アクションヘルプテキスト |
| AWS-014 | handle_aws_execute正常実行 | service, action | success=true |
| AWS-015 | handle_aws_execute（contextからrole_arn取得） | context.cloud_credentials | 認証情報自動取得 |
| AWS-016 | handle_aws_list_actions正常実行 | service名 | アクション一覧 |
| AWS-017 | handle_aws_get_help正常実行 | service名 | ヘルプテキスト |
| AWS-018 | register_aws_internal_tools成功 | - | True |
| AWS-019 | ツール定義数の確認 | AWS_INTERNAL_TOOLS | 3件 |
| AWS-020 | ハンドラーマッピングの確認 | AWS_TOOL_HANDLERS | 3ハンドラー登録済み |
| AWS-021 | サーバー名の確認 | AWS_INTERNAL_SERVER_NAME | "aws-internal" |

### 2.1 AssumeRoleルーター テスト

```python
# test/unit/aws_plugin/test_assume_role.py
"""AssumeRoleルーターのテスト

注意: app/clientフィクスチャはconftest.pyで定義済み。
このファイルでは共通フィクスチャを使用します。
"""
import pytest
from unittest.mock import patch, MagicMock

from app.aws_plugin.assume_role import REGION_NAME_MAPPING

# app, clientフィクスチャはconftest.pyから自動的に利用可能


class TestGetRegionsWithAssumeRole:
    """AssumeRoleリージョン取得エンドポイントのテスト"""

    def test_get_regions_success(self, client):
        """AWS-001: AssumeRoleでリージョン一覧取得成功"""
        # Arrange
        mock_sts_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "session-token-example"
            },
            "AssumedRoleUser": {
                "Arn": "arn:aws:sts::123456789012:assumed-role/TestRole/session"
            }
        }
        mock_ec2_response = {
            "Regions": [
                {"RegionName": "us-east-1", "OptInStatus": "opt-in-not-required"},
                {"RegionName": "ap-northeast-1", "OptInStatus": "opt-in-not-required"}
            ]
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = mock_sts_response
            mock_ec2 = MagicMock()
            mock_ec2.describe_regions.return_value = mock_ec2_response

            def client_factory(service, **kwargs):
                if service == "sts":
                    return mock_sts
                elif service == "ec2":
                    return mock_ec2
                return MagicMock()

            mock_boto3_client.side_effect = client_factory

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test-external-id",
                    "session_name": "test-session"
                }
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["totalRegions"] == 2
            assert data["method"] == "assume-role-describe-regions"
            assert len(data["availableRegions"]) == 2

    def test_region_name_mapping_us_east_1(self):
        """AWS-002: リージョン情報の正しいマッピング（us-east-1）"""
        # Arrange
        # Act
        region_name = REGION_NAME_MAPPING.get("us-east-1")

        # Assert
        assert region_name == "US East (N. Virginia)"

    def test_region_name_mapping_tokyo(self):
        """AWS-003: リージョン情報の正しいマッピング（ap-northeast-1）"""
        # Arrange
        # Act
        region_name = REGION_NAME_MAPPING.get("ap-northeast-1")

        # Assert
        assert region_name == "Asia Pacific (Tokyo)"

    def test_region_name_mapping_unknown_region(self):
        """AWS-004: マッピングにないリージョンはコードをそのまま使用"""
        # Arrange
        unknown_region = "xx-unknown-1"

        # Act
        region_name = REGION_NAME_MAPPING.get(unknown_region, unknown_region)

        # Assert
        assert region_name == "xx-unknown-1"

    def test_opt_in_status_available(self, client):
        """AWS-005: opt-in-not-requiredステータスは"available"に変換"""
        # Arrange
        mock_sts_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "session-token"
            },
            "AssumedRoleUser": {"Arn": "arn:aws:sts::123456789012:assumed-role/TestRole/session"}
        }
        mock_ec2_response = {
            "Regions": [
                {"RegionName": "us-east-1", "OptInStatus": "opt-in-not-required"}
            ]
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = mock_sts_response
            mock_ec2 = MagicMock()
            mock_ec2.describe_regions.return_value = mock_ec2_response

            def client_factory(service, **kwargs):
                return mock_sts if service == "sts" else mock_ec2

            mock_boto3_client.side_effect = client_factory

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test-external-id"
                }
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["availableRegions"][0]["status"] == "available"

    def test_opt_in_status_required(self, client):
        """AWS-006: opted-inステータスは"opt-in-required"に変換"""
        # Arrange
        mock_sts_response = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "session-token"
            },
            "AssumedRoleUser": {"Arn": "arn:aws:sts::123456789012:assumed-role/TestRole/session"}
        }
        mock_ec2_response = {
            "Regions": [
                {"RegionName": "af-south-1", "OptInStatus": "opted-in"}
            ]
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = mock_sts_response
            mock_ec2 = MagicMock()
            mock_ec2.describe_regions.return_value = mock_ec2_response

            def client_factory(service, **kwargs):
                return mock_sts if service == "sts" else mock_ec2

            mock_boto3_client.side_effect = client_factory

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test-external-id"
                }
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["availableRegions"][0]["status"] == "opt-in-required"
```

### 2.2 AWSExecutor テスト

```python
# test/unit/aws_plugin/test_executor.py
import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock, AsyncMock

from app.aws_plugin.executor import AWSExecutor, _serialize_datetime, aws_executor


class TestSerializeDatetime:
    """datetime/dateシリアライズ関数のテスト"""

    def test_serialize_datetime_object(self):
        """AWS-009a: datetimeオブジェクトのISO変換"""
        # Arrange
        dt = datetime(2026, 2, 3, 12, 30, 45)

        # Act
        result = _serialize_datetime(dt)

        # Assert
        assert result == "2026-02-03T12:30:45"

    def test_serialize_date_object(self):
        """AWS-009b: dateオブジェクトのISO変換"""
        # Arrange
        d = date(2026, 2, 3)

        # Act
        result = _serialize_datetime(d)

        # Assert
        assert result == "2026-02-03"

    def test_serialize_nested_dict(self):
        """AWS-009c: ネストした辞書内のdatetimeをISO変換"""
        # Arrange
        data = {
            "created_at": datetime(2026, 1, 1, 0, 0, 0),
            "nested": {
                "updated_at": datetime(2026, 2, 1, 12, 0, 0)
            }
        }

        # Act
        result = _serialize_datetime(data)

        # Assert
        assert result["created_at"] == "2026-01-01T00:00:00"
        assert result["nested"]["updated_at"] == "2026-02-01T12:00:00"

    def test_serialize_list_with_datetime(self):
        """AWS-009d: リスト内のdatetimeをISO変換"""
        # Arrange
        data = [datetime(2026, 1, 1), datetime(2026, 2, 1)]

        # Act
        result = _serialize_datetime(data)

        # Assert
        assert result == ["2026-01-01T00:00:00", "2026-02-01T00:00:00"]

    def test_serialize_non_datetime(self):
        """AWS-009e: datetime以外の値はそのまま返す"""
        # Arrange
        data = {"name": "test", "count": 42}

        # Act
        result = _serialize_datetime(data)

        # Assert
        assert result == {"name": "test", "count": 42}


class TestAWSExecutor:
    """AWSExecutorクラスのテスト"""

    @pytest.fixture
    def executor(self):
        """テスト用AWSExecutorインスタンス"""
        return AWSExecutor(default_region="ap-northeast-1")

    @pytest.mark.asyncio
    async def test_execute_success(self, executor):
        """AWS-007: AWSExecutor.execute正常実行"""
        # Arrange
        mock_credentials = {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "session-token"
        }
        mock_response = {
            "Buckets": [{"Name": "test-bucket"}],
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        with patch.object(executor, "_assume_role", new_callable=AsyncMock) as mock_assume:
            mock_assume.return_value = mock_credentials

            with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
                mock_s3 = MagicMock()
                mock_s3.list_buckets.return_value = mock_response
                mock_boto3_client.return_value = mock_s3

                # Act
                result = await executor.execute(
                    role_arn="arn:aws:iam::123456789012:role/TestRole",
                    service="s3",
                    action="list_buckets"
                )

                # Assert
                assert result["success"] is True
                assert "result" in result
                assert isinstance(result["result"]["Buckets"], list)
                assert result["result"]["Buckets"] == [{"Name": "test-bucket"}]

    @pytest.mark.asyncio
    async def test_execute_removes_response_metadata(self, executor):
        """AWS-008: ResponseMetadataの除去"""
        # Arrange
        mock_credentials = {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "session-token"
        }
        mock_response = {
            "Buckets": [],
            "ResponseMetadata": {"HTTPStatusCode": 200, "RequestId": "xxx"}
        }

        with patch.object(executor, "_assume_role", new_callable=AsyncMock) as mock_assume:
            mock_assume.return_value = mock_credentials

            with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
                mock_s3 = MagicMock()
                mock_s3.list_buckets.return_value = mock_response
                mock_boto3_client.return_value = mock_s3

                # Act
                result = await executor.execute(
                    role_arn="arn:aws:iam::123456789012:role/TestRole",
                    service="s3",
                    action="list_buckets"
                )

                # Assert
                assert result["success"] is True
                assert "ResponseMetadata" not in result["result"]

    def test_list_actions_success(self, executor):
        """AWS-010: list_actionsでアクション一覧取得"""
        # Arrange
        with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
            mock_client = MagicMock()
            mock_service_model = MagicMock()
            mock_service_model.operation_names = ["ListBuckets", "GetObject", "PutObject"]
            mock_client.meta.service_model = mock_service_model
            mock_boto3_client.return_value = mock_client

            # Act
            result = executor.list_actions("s3")

            # Assert
            assert "list_buckets" in result
            assert "get_object" in result
            assert "put_object" in result

    def test_to_snake_case(self, executor):
        """AWS-011: PascalCaseからsnake_caseへの変換"""
        # Arrange
        # Act
        # Assert
        assert executor._to_snake_case("DescribeInstances") == "describe_instances"
        assert executor._to_snake_case("ListBuckets") == "list_buckets"
        assert executor._to_snake_case("GetObject") == "get_object"

    def test_get_help_service_only(self, executor):
        """AWS-012: get_helpでサービスヘルプ取得"""
        # Arrange
        with patch("app.aws_plugin.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="S3 HELP\n...", stderr="")

            # Act
            result = executor.get_help("s3")

            # Assert
            assert "S3 HELP" in result
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args == ["aws", "s3", "help"]

    def test_get_help_with_action(self, executor):
        """AWS-013: get_helpでアクションヘルプ取得"""
        # Arrange
        with patch("app.aws_plugin.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="list-buckets HELP\n...", stderr="")

            # Act
            result = executor.get_help("s3", "list_buckets")

            # Assert
            assert "list-buckets HELP" in result
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args == ["aws", "s3", "list-buckets", "help"]
```

### 2.3 内部ツールハンドラー テスト

```python
# test/unit/aws_plugin/test_internal_tools.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.aws_plugin.internal_tools import (
    handle_aws_execute,
    handle_aws_list_actions,
    handle_aws_get_help,
    register_aws_internal_tools,
    AWS_INTERNAL_TOOLS,
    AWS_TOOL_HANDLERS,
    AWS_INTERNAL_SERVER_NAME
)


class TestHandleAwsExecute:
    """handle_aws_execute関数のテスト"""

    @pytest.mark.asyncio
    async def test_execute_with_params(self):
        """AWS-014: handle_aws_execute正常実行（パラメータ指定）"""
        # Arrange
        params = {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "service": "s3",
            "action": "list_buckets",
            "external_id": "test-external-id",
            "region": "us-east-1"
        }

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.execute = AsyncMock(return_value={
                "success": True,
                "result": {"Buckets": []}
            })

            # Act
            result = await handle_aws_execute(params)

            # Assert
            assert result["success"] is True
            mock_executor.execute.assert_called_once_with(
                role_arn="arn:aws:iam::123456789012:role/TestRole",
                service="s3",
                action="list_buckets",
                parameters={},
                external_id="test-external-id",
                region="us-east-1"
            )

    @pytest.mark.asyncio
    async def test_execute_with_context_credentials(self):
        """AWS-015: handle_aws_execute（contextからrole_arn取得）"""
        # Arrange
        params = {
            "service": "ec2",
            "action": "describe_instances"
        }
        context = {
            "cloud_credentials": {
                "cloud_provider": "aws",
                "role_arn": "arn:aws:iam::123456789012:role/ContextRole",
                "external_id": "context-external-id",
                "regions": ["ap-northeast-1"]
            }
        }

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.execute = AsyncMock(return_value={
                "success": True,
                "result": {"Reservations": []}
            })

            # Act
            result = await handle_aws_execute(params, context)

            # Assert
            assert result["success"] is True
            mock_executor.execute.assert_called_once()
            call_kwargs = mock_executor.execute.call_args.kwargs
            assert call_kwargs["role_arn"] == "arn:aws:iam::123456789012:role/ContextRole"
            assert call_kwargs["external_id"] == "context-external-id"
            assert call_kwargs["region"] == "ap-northeast-1"


class TestHandleAwsListActions:
    """handle_aws_list_actions関数のテスト"""

    def test_list_actions_success(self):
        """AWS-016: handle_aws_list_actions正常実行"""
        # Arrange
        params = {"service": "s3"}

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.list_actions.return_value = ["list_buckets", "get_object"]

            # Act
            result = handle_aws_list_actions(params)

            # Assert
            assert result["success"] is True
            assert result["service"] == "s3"
            assert result["actions"] == ["list_buckets", "get_object"]
            assert result["count"] == 2


class TestHandleAwsGetHelp:
    """handle_aws_get_help関数のテスト"""

    def test_get_help_success(self):
        """AWS-017: handle_aws_get_help正常実行"""
        # Arrange
        params = {"service": "s3", "action": "list_buckets"}

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.get_help.return_value = "S3 list-buckets HELP"

            # Act
            result = handle_aws_get_help(params)

            # Assert
            assert result["success"] is True
            assert result["service"] == "s3"
            assert result["action"] == "list_buckets"
            assert result["help"] == "S3 list-buckets HELP"


class TestRegisterAwsInternalTools:
    """register_aws_internal_tools関数のテスト"""

    @pytest.mark.asyncio
    async def test_register_success(self):
        """AWS-018: register_aws_internal_tools成功"""
        # Arrange
        with patch("app.aws_plugin.internal_tools.mcp_client") as mock_mcp_client:
            mock_mcp_client.register_internal_tools = AsyncMock(return_value=True)

            # Act
            result = await register_aws_internal_tools()

            # Assert
            assert result is True
            mock_mcp_client.register_internal_tools.assert_called_once_with(
                server_name=AWS_INTERNAL_SERVER_NAME,
                tools=AWS_INTERNAL_TOOLS,
                tool_handlers=AWS_TOOL_HANDLERS
            )


class TestAwsToolDefinitions:
    """AWS MCPツール定義のテスト

    定数検証のため、Arrange不要。グローバル定数をそのまま検証。
    """

    def test_aws_internal_tools_count(self):
        """AWS-019: ツール定義数の確認"""
        # Arrange
        # （定数検証のため不要）

        # Act
        tool_count = len(AWS_INTERNAL_TOOLS)

        # Assert
        assert tool_count == 3

    def test_aws_tool_handlers_mapping(self):
        """AWS-020: ハンドラーマッピングの確認"""
        # Arrange
        expected_handlers = ["aws_execute", "aws_list_actions", "aws_get_help"]

        # Act
        handler_names = list(AWS_TOOL_HANDLERS.keys())

        # Assert
        for handler in expected_handlers:
            assert handler in handler_names

    def test_aws_internal_server_name(self):
        """AWS-021: サーバー名の確認"""
        # Arrange
        expected_name = "aws-internal"

        # Act
        actual_name = AWS_INTERNAL_SERVER_NAME

        # Assert
        assert actual_name == expected_name
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|----------|
| AWS-E01 | AccessDenied（ロール不存在） | does not exist含むAccessDenied | 404 Not Found |
| AWS-E02 | AccessDenied（AssumeRole権限なし） | sts:AssumeRole含むAccessDenied | 403 Forbidden |
| AWS-E03 | AccessDenied（ExternalID無効） | ExternalId含むAccessDenied | 400 Bad Request |
| AWS-E04 | AccessDenied（IP制限） | IP address含むAccessDenied | 403 Forbidden |
| AWS-E05 | AccessDenied（時間制限） | not valid at this time含むAccessDenied | 403 Forbidden |
| AWS-E06 | AccessDenied（MFA要求） | MFA含むAccessDenied | 401 Unauthorized |
| AWS-E07 | AccessDenied（その他） | 一般的なAccessDenied | 403 Forbidden |
| AWS-E08 | InvalidUserID.NotFound | InvalidUserID.NotFound | 404 Not Found |
| AWS-E09 | ValidationException（RoleArn） | RoleArn含むValidationException | 400 Bad Request |
| AWS-E10 | ValidationException（ExternalId） | ExternalId含むValidationException | 400 Bad Request |
| AWS-E11 | ValidationException（その他） | その他のValidationException | 400 Bad Request |
| AWS-E12 | MalformedPolicyDocument | MalformedPolicyDocument | 400 Bad Request |
| AWS-E13 | TokenRefreshRequired | TokenRefreshRequired | 401 Unauthorized |
| AWS-E14 | その他のClientError | 未知のエラーコード | 400 Bad Request |
| AWS-E15 | NoCredentialsError | 認証情報なし | 401 Unauthorized |
| AWS-E16 | BotoCoreError（RoleArnパラメータ検証） | RoleArn含むパラメータ検証エラー | 400 Bad Request |
| AWS-E17 | BotoCoreError（ExternalIdパラメータ検証） | ExternalId含むパラメータ検証エラー | 400 Bad Request |
| AWS-E18 | BotoCoreError（その他） | その他のBotoCoreError | 500 Internal Server Error |
| AWS-E19 | 予期しない例外 | Exception | 500 Internal Server Error |
| AWS-E20 | execute: 存在しないアクション | 無効なアクション名 | success=false, エラーメッセージ |
| AWS-E21 | execute: ClientError | AWS APIエラー | success=false, エラーコード含む |
| AWS-E22 | execute: NoCredentialsError | 認証情報なし | success=false |
| AWS-E23 | list_actions: サービス不存在 | 無効なサービス名 | 空リスト |
| AWS-E24 | get_help: タイムアウト | タイムアウト発生 | タイムアウトメッセージ |
| AWS-E25 | get_help: 例外発生 | 一般例外 | エラーメッセージ |
| AWS-E26 | handle_aws_execute: role_arnなし | role_arn未指定、contextなし | success=false, エラー |
| AWS-E27 | handle_aws_execute: serviceなし | service未指定 | success=false, エラー |
| AWS-E28 | handle_aws_execute: actionなし | action未指定 | success=false, エラー |
| AWS-E29 | handle_aws_execute: AWS以外のcloud_provider | cloud_provider="azure" | success=false, エラー |
| AWS-E30 | handle_aws_list_actions: serviceなし | service未指定 | success=false, エラー |
| AWS-E31 | handle_aws_list_actions: 空リスト | サービス見つからず | success=false, エラー |
| AWS-E32 | handle_aws_get_help: serviceなし | service未指定 | success=false, エラー |
| AWS-E33 | register_aws_internal_tools: 登録失敗 | MCPクライアント登録失敗 | False |
| AWS-E34 | register_aws_internal_tools: 例外発生 | 例外発生 | False |
| AWS-E35 | handle_aws_execute: 空regionsリスト | context.regions=[] | regionがNone、デフォルト使用 |

### 3.1 AssumeRoleエラーハンドリング テスト

```python
# test/unit/aws_plugin/test_assume_role.py（続き）
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError


class TestGetRegionsWithAssumeRoleErrors:
    """AssumeRoleリージョン取得エラーハンドリングのテスト"""

    def test_access_denied_role_not_exist(self, client):
        """AWS-E01: AccessDenied（ロール不存在）→404"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Role does not exist"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/NonExistent",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 404
            assert "指定されたロールが見つかりません" in response.json()["detail"]

    def test_access_denied_no_assume_role_permission(self, client):
        """AWS-E02: AccessDenied（AssumeRole権限なし）→403"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized to perform: sts:AssumeRole"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/NoPermission",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 403
            assert "AssumeRole権限がありません" in response.json()["detail"]

    def test_access_denied_invalid_external_id(self, client):
        """AWS-E03: AccessDenied（ExternalID無効）→400"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "The ExternalId is not valid"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "invalid"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "External IDが無効です" in response.json()["detail"]

    def test_access_denied_ip_restriction(self, client):
        """AWS-E04: AccessDenied（IP制限）→403"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Request denied due to IP address restriction"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 403
            assert "IP制限" in response.json()["detail"]

    def test_access_denied_time_restriction(self, client):
        """AWS-E05: AccessDenied（時間制限）→403"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Credential is not valid at this time"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 403
            assert "時間制限" in response.json()["detail"]

    def test_access_denied_mfa_required(self, client):
        """AWS-E06: AccessDenied（MFA要求）→401"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "MFA authentication is required"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 401
            assert "多要素認証が必要です" in response.json()["detail"]

    def test_access_denied_general(self, client):
        """AWS-E07: AccessDenied（その他）→403"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 403
            assert "アクセスが拒否されました" in response.json()["detail"]

    def test_invalid_user_id_not_found(self, client):
        """AWS-E08: InvalidUserID.NotFound→404"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "InvalidUserID.NotFound",
                "Message": "User not found"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 404

    def test_validation_exception_role_arn(self, client):
        """AWS-E09: ValidationException（RoleArn）→400"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid RoleArn format"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "invalid-arn",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "ロールARNの形式が無効です" in response.json()["detail"]

    def test_validation_exception_external_id(self, client):
        """AWS-E10: ValidationException（ExternalId）→400"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid ExternalId format"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "x"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "External IDの形式が無効です" in response.json()["detail"]

    def test_validation_exception_other(self, client):
        """AWS-E11: ValidationException（その他）→400"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "ValidationException",
                "Message": "Invalid parameter"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "パラメータが無効です" in response.json()["detail"]

    def test_malformed_policy_document(self, client):
        """AWS-E12: MalformedPolicyDocument→400"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "MalformedPolicyDocument",
                "Message": "Malformed policy document"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "ポリシー文書の形式が無効です" in response.json()["detail"]

    def test_token_refresh_required(self, client):
        """AWS-E13: TokenRefreshRequired→401"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "TokenRefreshRequired",
                "Message": "Token refresh required"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 401
            assert "認証トークンの更新が必要です" in response.json()["detail"]

    def test_unknown_client_error(self, client):
        """AWS-E14: その他のClientError→400"""
        # Arrange
        error_response = {
            "Error": {
                "Code": "UnknownError",
                "Message": "Unknown error occurred"
            }
        }

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = ClientError(error_response, "AssumeRole")
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "AWS エラー (UnknownError)" in response.json()["detail"]

    def test_no_credentials_error(self, client):
        """AWS-E15: NoCredentialsError→401"""
        # Arrange
        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_boto3_client.side_effect = NoCredentialsError()

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 401
            assert "AWS認証情報が設定されていません" in response.json()["detail"]

    def test_botocore_error_role_arn_validation(self, client):
        """AWS-E16: BotoCoreError（RoleArnパラメータ検証）→400

        assume_role.py:214-218 のBotoCoreError分岐をカバー
        """
        # Arrange
        class MockBotoCoreError(BotoCoreError):
            def __init__(self):
                self.fmt = "Parameter validation failed: RoleArn must be a valid ARN"
                super().__init__()

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = MockBotoCoreError()
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "invalid",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 400
            assert "ロールARN" in response.json()["detail"]

    def test_botocore_error_external_id_validation(self, client):
        """AWS-E17: BotoCoreError（ExternalIdパラメータ検証）→400

        assume_role.py:219-223 のBotoCoreError分岐をカバー
        """
        # Arrange
        class MockBotoCoreError(BotoCoreError):
            def __init__(self):
                self.fmt = "Parameter validation failed: ExternalId must be..."
                super().__init__()

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = MockBotoCoreError()
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": ""
                }
            )

            # Assert
            assert response.status_code == 400
            assert "External ID" in response.json()["detail"]

    def test_botocore_error_other(self, client):
        """AWS-E18: BotoCoreError（その他）→500

        assume_role.py:229-234 のBotoCoreError分岐をカバー
        """
        # Arrange
        class MockBotoCoreError(BotoCoreError):
            def __init__(self):
                self.fmt = "Connection timeout"
                super().__init__()

        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.side_effect = MockBotoCoreError()
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 500
            assert "AWS SDK エラー" in response.json()["detail"]

    def test_unexpected_exception(self, client):
        """AWS-E19: 予期しない例外→500"""
        # Arrange
        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_boto3_client.side_effect = Exception("Unexpected error")

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": "test"
                }
            )

            # Assert
            assert response.status_code == 500
            assert "予期しないエラーが発生しました" in response.json()["detail"]
```

### 3.2 AWSExecutorエラーハンドリング テスト

```python
# test/unit/aws_plugin/test_executor.py（続き）
from botocore.exceptions import ClientError, NoCredentialsError
import subprocess


class TestAWSExecutorErrors:
    """AWSExecutorエラーハンドリングのテスト"""

    @pytest.fixture
    def executor(self):
        """テスト用AWSExecutorインスタンス"""
        return AWSExecutor(default_region="ap-northeast-1")

    @pytest.mark.asyncio
    async def test_execute_action_not_found(self, executor):
        """AWS-E20: 存在しないアクション

        executor.py:87-92のアクション存在チェック分岐をカバー。
        MagicMockはspec未指定だと全属性にMagicMockを返すため、
        spec=[]を使用してgetattr()がNoneを返すようにする。
        """
        # Arrange
        mock_credentials = {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "session-token"
        }

        with patch.object(executor, "_assume_role", new_callable=AsyncMock) as mock_assume:
            mock_assume.return_value = mock_credentials

            with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
                # spec=[]を使用してgetattr(client, action, None)がNoneを返すようにする
                # MagicMockはspec未指定だと全属性に新しいMagicMockを返すため、
                # specで空リストを指定することで未定義属性へのアクセスでNoneを返す
                mock_s3 = MagicMock(spec=[])
                mock_boto3_client.return_value = mock_s3

                # Act
                result = await executor.execute(
                    role_arn="arn:aws:iam::123456789012:role/TestRole",
                    service="s3",
                    action="non_existent_action"
                )

                # Assert
                assert result["success"] is False
                assert "存在しません" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_client_error(self, executor):
        """AWS-E21: execute時のClientError"""
        # Arrange
        mock_credentials = {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "session-token"
        }
        error_response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Access Denied"
            }
        }

        with patch.object(executor, "_assume_role", new_callable=AsyncMock) as mock_assume:
            mock_assume.return_value = mock_credentials

            with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
                mock_s3 = MagicMock()
                mock_s3.list_buckets.side_effect = ClientError(error_response, "ListBuckets")
                mock_boto3_client.return_value = mock_s3

                # Act
                result = await executor.execute(
                    role_arn="arn:aws:iam::123456789012:role/TestRole",
                    service="s3",
                    action="list_buckets"
                )

                # Assert
                assert result["success"] is False
                assert "AccessDenied" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_no_credentials(self, executor):
        """AWS-E22: execute時のNoCredentialsError"""
        # Arrange
        with patch.object(executor, "_assume_role", new_callable=AsyncMock) as mock_assume:
            mock_assume.side_effect = NoCredentialsError()

            # Act
            result = await executor.execute(
                role_arn="arn:aws:iam::123456789012:role/TestRole",
                service="s3",
                action="list_buckets"
            )

            # Assert
            assert result["success"] is False
            assert "認証情報" in result["error"]

    def test_list_actions_service_not_found(self, executor):
        """AWS-E23: list_actionsでサービス不存在"""
        # Arrange
        with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
            mock_boto3_client.side_effect = Exception("Unknown service")

            # Act
            result = executor.list_actions("invalid_service")

            # Assert
            assert result == []

    def test_get_help_timeout(self, executor):
        """AWS-E24: get_helpでタイムアウト"""
        # Arrange
        with patch("app.aws_plugin.executor.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="aws", timeout=10)

            # Act
            result = executor.get_help("s3")

            # Assert
            assert "タイムアウト" in result

    def test_get_help_exception(self, executor):
        """AWS-E25: get_helpで例外発生"""
        # Arrange
        with patch("app.aws_plugin.executor.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            # Act
            result = executor.get_help("s3")

            # Assert
            assert "エラー" in result
```

### 3.3 内部ツールハンドラーエラー テスト

```python
# test/unit/aws_plugin/test_internal_tools.py（続き）

class TestHandleAwsExecuteErrors:
    """handle_aws_executeエラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_execute_missing_role_arn(self):
        """AWS-E26: handle_aws_execute: role_arnなし"""
        # Arrange
        params = {
            "service": "s3",
            "action": "list_buckets"
        }

        # Act
        result = await handle_aws_execute(params)

        # Assert
        assert result["success"] is False
        assert "role_arn は必須です" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_missing_service(self):
        """AWS-E27: handle_aws_execute: serviceなし"""
        # Arrange
        params = {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "action": "list_buckets"
        }

        # Act
        result = await handle_aws_execute(params)

        # Assert
        assert result["success"] is False
        assert "service は必須です" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_missing_action(self):
        """AWS-E28: handle_aws_execute: actionなし"""
        # Arrange
        params = {
            "role_arn": "arn:aws:iam::123456789012:role/TestRole",
            "service": "s3"
        }

        # Act
        result = await handle_aws_execute(params)

        # Assert
        assert result["success"] is False
        assert "action は必須です" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_non_aws_context(self):
        """AWS-E29: handle_aws_execute: AWS以外のcloud_provider"""
        # Arrange
        params = {
            "service": "s3",
            "action": "list_buckets"
        }
        context = {
            "cloud_credentials": {
                "cloud_provider": "azure",  # AWSではない
                "role_arn": "arn:aws:iam::123456789012:role/TestRole"
            }
        }

        # Act
        result = await handle_aws_execute(params, context)

        # Assert
        assert result["success"] is False
        assert "role_arn は必須です" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_empty_regions_list(self):
        """AWS-E35: handle_aws_execute: 空regionsリスト

        internal_tools.py:76-78のregions取得ロジックで、
        空のregionsリストが渡された場合の処理をテスト。
        regionがNoneのまま渡され、executorのdefault_regionが使用される。
        """
        # Arrange
        params = {
            "service": "ec2",
            "action": "describe_instances"
        }
        context = {
            "cloud_credentials": {
                "cloud_provider": "aws",
                "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                "external_id": "test-external-id",
                "regions": []  # 空リスト
            }
        }

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.execute = AsyncMock(return_value={
                "success": True,
                "result": {"Reservations": []}
            })

            # Act
            result = await handle_aws_execute(params, context)

            # Assert
            assert result["success"] is True
            mock_executor.execute.assert_called_once()
            call_kwargs = mock_executor.execute.call_args.kwargs
            # regionがNone（デフォルト使用）であることを確認
            assert call_kwargs["region"] is None


class TestHandleAwsListActionsErrors:
    """handle_aws_list_actionsエラーハンドリングのテスト"""

    def test_list_actions_missing_service(self):
        """AWS-E30: handle_aws_list_actions: serviceなし"""
        # Arrange
        params = {}

        # Act
        result = handle_aws_list_actions(params)

        # Assert
        assert result["success"] is False
        assert "service は必須です" in result["error"]

    def test_list_actions_empty_result(self):
        """AWS-E31: handle_aws_list_actions: 空リスト"""
        # Arrange
        params = {"service": "invalid_service"}

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.list_actions.return_value = []

            # Act
            result = handle_aws_list_actions(params)

            # Assert
            assert result["success"] is False
            assert "見つからない" in result["error"]


class TestHandleAwsGetHelpErrors:
    """handle_aws_get_helpエラーハンドリングのテスト"""

    def test_get_help_missing_service(self):
        """AWS-E32: handle_aws_get_help: serviceなし"""
        # Arrange
        params = {}

        # Act
        result = handle_aws_get_help(params)

        # Assert
        assert result["success"] is False
        assert "service は必須です" in result["error"]


class TestRegisterAwsInternalToolsErrors:
    """register_aws_internal_toolsエラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_register_failure(self):
        """AWS-E33: register_aws_internal_tools: 登録失敗"""
        # Arrange
        with patch("app.aws_plugin.internal_tools.mcp_client") as mock_mcp_client:
            mock_mcp_client.register_internal_tools = AsyncMock(return_value=False)

            # Act
            result = await register_aws_internal_tools()

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_register_exception(self):
        """AWS-E34: register_aws_internal_tools: 例外発生"""
        # Arrange
        with patch("app.aws_plugin.internal_tools.mcp_client") as mock_mcp_client:
            mock_mcp_client.register_internal_tools = AsyncMock(
                side_effect=Exception("Registration failed")
            )

            # Act
            result = await register_aws_internal_tools()

            # Assert
            assert result is False
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|----------|
| AWS-SEC-01 | ロールARNインジェクション防止 | 悪意あるARN文字列 | バリデーションエラーまたは安全な処理 |
| AWS-SEC-02 | External IDインジェクション防止 | 悪意あるExternal ID | バリデーションエラーまたは安全な処理 |
| AWS-SEC-03 | 認証情報のログ出力防止 | 任意のリクエスト | ログにSecretAccessKey等が含まれない |
| AWS-SEC-04 | コマンドインジェクション防止（get_help） | 悪意あるサービス名 | shell=Falseでリスト形式呼び出し |
| AWS-SEC-05 | セッション名の安全性 | デフォルトセッション名 | 安全な文字列のみ使用 |
| AWS-SEC-06 | 一時認証情報の有効期限設定 | AssumeRole実行 | DurationSecondsが適切に設定 |
| AWS-SEC-07 | 一時認証情報のログ出力防止 | AssumeRole実行 | Credentialsがログに出力されない |

### OWASP Top 10 カバレッジ

| OWASP Category | テストID | カバー内容 |
|----------------|----------|-----------|
| A01:2021 – Broken Access Control | AWS-E01〜AWS-E07 | AssumeRole権限チェック |
| A02:2021 – Cryptographic Failures | - | （該当なし：AWS SDKが処理） |
| A03:2021 – Injection | AWS-SEC-01, AWS-SEC-02, AWS-SEC-04 | ARN/ExternalID/コマンドインジェクション |
| A04:2021 – Insecure Design | AWS-SEC-05, AWS-SEC-06 | セッション設計、有効期限 |
| A05:2021 – Security Misconfiguration | AWS-E15, AWS-E16 | 認証情報設定エラー |
| A06:2021 – Vulnerable Components | - | （該当なし：依存関係管理は別途） |
| A07:2021 – Auth Failures | AWS-E06, AWS-E13, AWS-E15 | MFA、トークン更新、認証情報なし |
| A08:2021 – Software/Data Integrity | - | （該当なし） |
| A09:2021 – Security Logging | AWS-SEC-03, AWS-SEC-07 | 認証情報のログ出力防止 |
| A10:2021 – SSRF | - | （該当なし：直接URLアクセスなし） |

```python
# test/unit/aws_plugin/test_security.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import logging

from app.aws_plugin.assume_role import router
from app.aws_plugin.executor import AWSExecutor
from app.aws_plugin.internal_tools import handle_aws_execute


@pytest.mark.security
class TestAwsPluginSecurity:
    """aws_pluginセキュリティテスト

    conftest.pyのapp/clientフィクスチャを使用。
    """

    @pytest.mark.parametrize("malicious_arn", [
        "arn:aws:iam::123456789012:role/Test; rm -rf /",
        "arn:aws:iam::123456789012:role/Test\n--malicious-flag",
        "arn:aws:iam::123456789012:role/Test$(whoami)",
        "arn:aws:iam::123456789012:role/Test`id`",
    ])
    def test_role_arn_injection_prevention(self, client, malicious_arn):
        """AWS-SEC-01: ロールARNインジェクション防止

        assume_role.py:61 のAssumeRole呼び出しで
        悪意あるARN文字列が安全に処理されることを確認。
        """
        # Arrange
        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            from botocore.exceptions import ClientError
            mock_sts.assume_role.side_effect = ClientError(
                {"Error": {"Code": "ValidationException", "Message": "Invalid RoleArn"}},
                "AssumeRole"
            )
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": malicious_arn,
                    "external_id": "test"
                }
            )

            # Assert
            # エラーが返されるが、インジェクションは発生しない
            assert response.status_code in [400, 422, 500]

    @pytest.mark.parametrize("malicious_id", [
        "test; rm -rf /",
        "test\n--malicious",
        "test$(whoami)",
        "test`id`",
        "test' OR '1'='1",
    ])
    def test_external_id_injection_prevention(self, client, malicious_id):
        """AWS-SEC-02: External IDインジェクション防止

        assume_role.py:64 のExternalIdパラメータで
        悪意ある文字列が安全に処理されることを確認。
        """
        # Arrange
        with patch("app.aws_plugin.assume_role.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            from botocore.exceptions import ClientError
            mock_sts.assume_role.side_effect = ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "ExternalId invalid"}},
                "AssumeRole"
            )
            mock_boto3_client.return_value = mock_sts

            # Act
            response = client.post(
                "/assume-role/regions",
                json={
                    "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                    "external_id": malicious_id
                }
            )

            # Assert
            assert response.status_code in [400, 403, 422, 500]

    @pytest.mark.asyncio
    async def test_credentials_not_logged(self, caplog):
        """AWS-SEC-03: 認証情報のログ出力防止

        internal_tools.py:53-54 でcloud_credentialsのキーのみログ出力し、
        認証情報自体（SecretAccessKey等）はログに含まれないことを確認。
        """
        # Arrange
        params = {
            "service": "s3",
            "action": "list_buckets"
        }
        context = {
            "cloud_credentials": {
                "cloud_provider": "aws",
                "role_arn": "arn:aws:iam::123456789012:role/TestRole",
                "external_id": "secret-external-id-12345",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "regions": ["us-east-1"]
            }
        }

        with patch("app.aws_plugin.internal_tools.aws_executor") as mock_executor:
            mock_executor.execute = AsyncMock(return_value={"success": True, "result": {}})

            with caplog.at_level(logging.INFO):
                # Act
                await handle_aws_execute(params, context)

                # Assert
                log_output = caplog.text
                # SecretAccessKeyがログに含まれないことを確認
                assert "wJalrXUtnFEMI" not in log_output
                # キーのリストはログに出力される（値は出力されない）
                assert "cloud_credentials keys:" in log_output

    def test_command_injection_prevention_get_help(self):
        """AWS-SEC-04: コマンドインジェクション防止（get_help）

        executor.py:203-205 のsubprocess.run呼び出しで
        shell=Falseでリスト形式呼び出しされることを確認。
        """
        # Arrange
        executor = AWSExecutor()
        malicious_services = [
            "s3; rm -rf /",
            "s3 && whoami",
            "s3 | cat /etc/passwd",
            "$(malicious)",
            "`malicious`",
        ]

        with patch("app.aws_plugin.executor.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="Unknown command")

            for malicious_service in malicious_services:
                # Act
                executor.get_help(malicious_service)

                # Assert
                # subprocess.runがリスト形式で呼び出されることを確認
                call_args = mock_run.call_args[0][0]
                assert isinstance(call_args, list)
                # shell引数がFalse（デフォルト）であることを確認
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs.get("shell", False) is False

    @pytest.mark.asyncio
    async def test_session_name_safety(self):
        """AWS-SEC-05: セッション名の安全性

        executor.py:149 のRoleSessionNameが安全な文字列のみ使用していることを確認。
        """
        # Arrange
        executor = AWSExecutor()

        with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "secret",
                    "SessionToken": "token"
                }
            }
            mock_boto3_client.return_value = mock_sts

            # Act
            await executor._assume_role("arn:aws:iam::123456789012:role/TestRole")

            # Assert
            call_kwargs = mock_sts.assume_role.call_args.kwargs
            session_name = call_kwargs["RoleSessionName"]
            # セッション名が安全な文字のみで構成されていることを確認
            assert all(c.isalnum() or c in "-_" for c in session_name)
            assert len(session_name) <= 64  # AWS制限

    @pytest.mark.asyncio
    async def test_credential_duration_setting(self):
        """AWS-SEC-06: 一時認証情報の有効期限設定

        executor.py:150 のDurationSecondsが適切に設定されていることを確認。
        """
        # Arrange
        executor = AWSExecutor()

        with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "secret",
                    "SessionToken": "token"
                }
            }
            mock_boto3_client.return_value = mock_sts

            # Act
            await executor._assume_role("arn:aws:iam::123456789012:role/TestRole")

            # Assert
            call_kwargs = mock_sts.assume_role.call_args.kwargs
            duration = call_kwargs["DurationSeconds"]
            # 有効期限が1時間（3600秒）に設定されていることを確認
            assert duration == 3600
            # 最大12時間を超えていないことを確認
            assert duration <= 43200

    @pytest.mark.asyncio
    async def test_credentials_not_logged_after_assume_role(self, caplog):
        """AWS-SEC-07: 一時認証情報のログ出力防止

        executor.py:75 で_assume_roleの返却値がログに出力されないことを確認。
        """
        # Arrange
        executor = AWSExecutor()
        mock_credentials = {
            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "SessionToken": "AQoDYXdzEJr..."
        }

        with patch("app.aws_plugin.executor.boto3.client") as mock_boto3_client:
            mock_sts = MagicMock()
            mock_sts.assume_role.return_value = {"Credentials": mock_credentials}
            mock_boto3_client.return_value = mock_sts

            with caplog.at_level(logging.INFO):
                # Act
                await executor._assume_role("arn:aws:iam::123456789012:role/TestRole")

                # Assert
                log_output = caplog.text
                # SecretAccessKeyがログに含まれないことを確認
                assert "wJalrXUtnFEMI" not in log_output
                assert "SecretAccessKey" not in log_output
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_aws_plugin_module` | テスト間のモジュール状態リセット | function | Yes |
| `app` | テスト用FastAPIアプリケーション | function | No |
| `client` | テスト用HTTPクライアント（TestClient） | function | No |
| `mock_boto3_client` | boto3クライアントのモック | function | No |
| `mock_sts_credentials` | STS認証情報のモック | function | No |
| `sample_assume_role_request` | サンプルAssumeRoleリクエスト | function | No |
| `mock_ec2_regions_response` | EC2リージョン一覧レスポンスのモック | function | No |
| `mock_mcp_client` | MCPクライアントのモック（非同期） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/aws_plugin/conftest.py
import sys
import importlib
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_aws_plugin_module():
    """テストごとにモジュールのグローバル状態をリセット

    aws_executorがグローバルインスタンスとして存在するため、
    テスト間での状態共有を防ぐためにモジュールをリセットします。

    注意: モジュール削除後、テスト内で再importが必要な場合があります。
    各テストでは対象モジュールを明示的にimportしてください。
    """
    # テスト前に現在のモジュール状態を保存
    original_modules = set(sys.modules.keys())

    yield

    # テスト後にクリーンアップ
    # aws_plugin関連のモジュールを削除
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.aws_plugin")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def app():
    """テスト用FastAPIアプリケーション

    各テストクラスで共通して使用するアプリケーションインスタンス。
    assume_roleルーターを含む。
    """
    from app.aws_plugin.assume_role import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """テスト用HTTPクライアント

    FastAPIアプリケーションに対するTestClientを返します。
    """
    return TestClient(app)


@pytest.fixture
def mock_boto3_client():
    """boto3クライアントのモック"""
    with patch("app.aws_plugin.assume_role.boto3.client") as mock_assume_role_client, \
         patch("app.aws_plugin.executor.boto3.client") as mock_executor_client:
        yield {
            "assume_role": mock_assume_role_client,
            "executor": mock_executor_client
        }


@pytest.fixture
def mock_sts_credentials():
    """STS認証情報のモック"""
    return {
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "SessionToken": "AQoDYXdzEJr...",
        "Expiration": "2026-02-03T12:00:00Z"
    }


@pytest.fixture
def sample_assume_role_request():
    """サンプルAssumeRoleリクエスト"""
    return {
        "role_arn": "arn:aws:iam::123456789012:role/TestRole",
        "external_id": "test-external-id-12345",
        "session_name": "test-session"
    }


@pytest.fixture
def mock_ec2_regions_response():
    """EC2リージョン一覧レスポンスのモック"""
    return {
        "Regions": [
            {"RegionName": "us-east-1", "OptInStatus": "opt-in-not-required"},
            {"RegionName": "us-west-2", "OptInStatus": "opt-in-not-required"},
            {"RegionName": "ap-northeast-1", "OptInStatus": "opt-in-not-required"},
            {"RegionName": "eu-west-1", "OptInStatus": "opt-in-not-required"},
            {"RegionName": "af-south-1", "OptInStatus": "opted-in"}
        ]
    }


@pytest_asyncio.fixture
async def mock_mcp_client():
    """MCPクライアントのモック（非同期フィクスチャ）

    register_internal_toolsは非同期関数のため、
    pytest_asyncioフィクスチャとして定義。
    """
    with patch("app.aws_plugin.internal_tools.mcp_client") as mock:
        mock.register_internal_tools = AsyncMock(return_value=True)
        yield mock
```

---

## 6. テスト実行例

```bash
# aws_plugin関連テストのみ実行
pytest test/unit/aws_plugin/ -v

# 特定のテストクラスのみ実行
pytest test/unit/aws_plugin/test_assume_role.py::TestGetRegionsWithAssumeRole -v

# 特定のテストファイルのみ実行
pytest test/unit/aws_plugin/test_executor.py -v

# カバレッジ付きで実行
pytest test/unit/aws_plugin/ --cov=app.aws_plugin --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/aws_plugin/ -m "security" -v

# 非同期テストのみ実行
pytest test/unit/aws_plugin/ -m "asyncio" -v

# エラーハンドリングテストのみ実行
pytest test/unit/aws_plugin/test_assume_role.py::TestGetRegionsWithAssumeRoleErrors -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 25 | AWS-001 〜 AWS-021（AWS-009a〜009eを含む） |
| 異常系 | 35 | AWS-E01 〜 AWS-E35 |
| セキュリティ | 7 | AWS-SEC-01 〜 AWS-SEC-07 |
| **合計** | **67** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestGetRegionsWithAssumeRole` | AWS-001〜AWS-006 | 6 |
| `TestSerializeDatetime` | AWS-009a〜AWS-009e | 5 |
| `TestAWSExecutor` | AWS-007〜AWS-013 | 7 |
| `TestHandleAwsExecute` | AWS-014〜AWS-015 | 2 |
| `TestHandleAwsListActions` | AWS-016 | 1 |
| `TestHandleAwsGetHelp` | AWS-017 | 1 |
| `TestRegisterAwsInternalTools` | AWS-018 | 1 |
| `TestAwsToolDefinitions` | AWS-019〜AWS-021 | 3 |
| `TestGetRegionsWithAssumeRoleErrors` | AWS-E01〜AWS-E19 | 19 |
| `TestAWSExecutorErrors` | AWS-E20〜AWS-E25 | 6 |
| `TestHandleAwsExecuteErrors` | AWS-E26〜AWS-E29, AWS-E35 | 5 |
| `TestHandleAwsListActionsErrors` | AWS-E30〜AWS-E31 | 2 |
| `TestHandleAwsGetHelpErrors` | AWS-E32 | 1 |
| `TestRegisterAwsInternalToolsErrors` | AWS-E33〜AWS-E34 | 2 |
| `TestAwsPluginSecurity` | AWS-SEC-01〜AWS-SEC-07 | 7 |

### 実装失敗が予想されるテスト

以下のテストは実装との整合性確認が必要です：

| テストID | リスク | 対策 |
|----------|--------|------|
| AWS-E20 | MagicMockの挙動により`getattr`がNoneを返さない可能性 | `spec=[]`を使用（修正済み） |
| AWS-SEC-03 | ログ出力形式が実装と異なる場合、アサーションが失敗する可能性 | 実装のログフォーマットを確認してテストを調整 |
| AWS-SEC-07 | ログレベルの設定によりcaplogでキャプチャできない可能性 | `caplog.at_level(logging.DEBUG)`の使用を検討 |

**注意**: テスト実行前に実装ファイルのログ出力フォーマットを確認し、必要に応じてテストを調整してください。

### 注意事項

- テスト実行には `pytest-asyncio` パッケージが必要です
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録してください：
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "security: セキュリティ関連テスト",
  ]
  ```
- boto3クライアントはすべてモック化し、実際のAWS接続は行いません
- subprocess.runもモック化し、実際のAWS CLI実行は行いません

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 実際のAWS接続をテストしない | 実環境での動作は別途統合テストが必要 | モックでカバー、統合テストは別途実施 |
| 2 | BotoCoreErrorの一部パターンは再現困難 | 特定のエラーパスがカバーされない可能性 | 代表的なパターンのみテスト |
| 3 | AWS CLIヘルプのANSIエスケープ除去は簡易的 | 一部の装飾が残る可能性 | 機能に影響なし |
| 4 | 認証情報キャッシュ機能は未実装 | キャッシュ関連のテストなし | 将来の拡張用として空のdictのみ存在 |
| 5 | クロスアカウント権限昇格の制御 | role_arnのアカウントIDホワイトリストチェックなし | アプリケーション要件に応じて実装検討 |
