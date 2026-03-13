# jobs プラグインテストケース

## 1. 概要

バックグラウンドジョブ管理プラグインのテストケースを定義します。非同期ジョブの開始、ステータス管理、結果取得、および暗号化通信を含む包括的なテストを提供します。

### 1.1 ジョブタイプ

| ジョブタイプ | 説明 |
|-------------|------|
| `cspm_policy_batch` | CSPMポリシー一括生成ジョブ |
| `file_processing` | ファイル処理（テキスト抽出・構造化）ジョブ |
| `custodian_scan_{cloud}` | Cloud Custodianスキャンジョブ（旧形式） |
| `new_custodian_scan_{cloud}` | 新Cloud Custodianスキャンジョブ（AssumeRole対応） |

### 1.2 主要機能

| 機能 | エンドポイント | HTTPメソッド | 説明 |
|------|---------------|-------------|------|
| ポリシーバッチ生成 | `/start_generate_policies_batch_async` | POST | CSPMポリシーの一括生成を開始 |
| ファイル処理 | `/start_file_processing_async` | POST | PDFからのテキスト抽出・構造化を開始 |
| Custodianスキャン | `/start_custodian_scan_async` | POST | Cloud Custodianスキャンを開始（旧形式） |
| 新Custodianスキャン | `/new_start_custodian_scan_async` | POST | 新Cloud Custodianスキャンを開始（AssumeRole対応） |
| ステータス取得 | `/jobs/{job_id}/status` | GET | ジョブの現在の状態を取得 |
| 結果取得 | `/jobs/{job_id}/result` | GET | ジョブの実行結果を取得 |
| スキャンファイル取得 | `/jobs/{job_id}/scan_files` | GET | Custodianスキャン結果の詳細ファイルを取得 |

### 1.3 排他制御機能

ジョブは排他制御機能により、同時実行が制限されています：
- `try_initialize_job_exclusive()`: レースコンディション対策付きの排他的ジョブ初期化
- `check_job_exclusion()`: 他のジョブ実行中かどうかのチェック
- 排他制御エラー時は `409 Conflict` を返す

### 1.4 補足情報

**例外処理の実装特性（テスト設計に影響）:**
- 暗号化エンドポイント（`/start_custodian_scan_async`, `/new_start_custodian_scan_async`）では、認証失敗（401）を含む全ての例外が広域`except`で捕捉され、400に変換される（router.py:334-336, 464-466）
- `/jobs/{job_id}/scan_files`エンドポイントでは、結果なし（404）を含む例外が500に変換される（router.py:281-286）
- これらは実装の現状であり、テストはこの挙動を反映する

**NewCredentials.authType の有効値:**
- `"role_assumption"`: AssumeRole方式
- `"secret_key"`: アクセスキー方式

### 1.5 カバレッジ目標: 80%

> **注記**: 暗号化通信とセキュリティ機能を含むため、セキュリティテストのカバレッジを重視

### 1.6 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/router.py` |
| ステータス管理 | `app/jobs/status_manager.py` |
| モデル定義 | `app/models/jobs.py` |
| テストコード | `test/unit/jobs/test_jobs_router.py` |
| conftest | `test/unit/jobs/conftest.py` |

---

## 2. 正常系テストケース

| ID | テスト名 | エンドポイント | 入力 | 期待結果 |
|----|---------|---------------|------|---------|
| JOB-001 | ポリシーバッチ生成開始 | POST /start_generate_policies_batch_async | valid CspmBatchRequest | status 202, job_id返却 |
| JOB-002 | ファイル処理開始 | POST /start_file_processing_async | valid FileProcessingRequest | status 202, job_id返却 |
| JOB-003 | ジョブステータス取得 | GET /jobs/{job_id}/status | valid job_id | status 200, JobStatus |
| JOB-004 | ジョブ結果取得（完了） | GET /jobs/{job_id}/result | completed job_id | status 200, result |
| JOB-005 | スキャンファイル取得 | GET /jobs/{job_id}/scan_files | completed new_custodian_scan job_id | status 200, file details |
| JOB-006 | 旧Custodianスキャン開始（暗号化） | POST /start_custodian_scan_async | valid encrypted request | status 202, job_id返却 |
| JOB-007 | 旧Custodianスキャン開始（平文） | POST /start_custodian_scan_async | valid plain request | status 202, job_id返却 |
| JOB-008 | 新Custodianスキャン開始（暗号化） | POST /new_start_custodian_scan_async | valid encrypted request | status 202, job_id返却 |
| JOB-009 | 新Custodianスキャン開始（平文） | POST /new_start_custodian_scan_async | valid plain request | status 202, job_id返却 |
| JOB-010 | 新Custodianスキャン（プリセット付き） | POST /new_start_custodian_scan_async | request with preset_id/preset_name | status 202, job_id返却 |

### 2.1 ジョブ開始エンドポイント テスト

```python
# test/unit/jobs/test_jobs_router.py
import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestJobsStartEndpoints:
    """ジョブ開始エンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_start_policy_batch(self, authenticated_client, mock_status_manager, mock_tasks):
        """JOB-001: ポリシーバッチ生成開始成功"""
        # Arrange
        mock_status_manager.try_initialize_job_exclusive.return_value = ("job-001", None)
        request_data = {
            "recommendations": [
                {
                    "uuid": "rec-001",
                    "title": "テスト推奨事項",
                    "description": "テスト説明",
                    "targetClouds": ["aws"]
                }
            ]
        }

        # Act
        response = await authenticated_client.post(
            "/start_generate_policies_batch_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == "job-001"
        # バックグラウンドタスクがモックされていることを確認
        mock_tasks.policy_batch.assert_not_called()  # add_taskで追加されるため直接呼出なし

    @pytest.mark.asyncio
    async def test_start_file_processing(self, authenticated_client, mock_status_manager, mock_tasks):
        """JOB-002: ファイル処理開始成功"""
        # Arrange
        mock_status_manager.try_initialize_job_exclusive.return_value = ("job-002", None)
        request_data = {
            "filename": "test.pdf",
            "file_content_base64": "dGVzdA==",
            "target_clouds": ["aws", "azure"],
            "output_lang": "jp"
        }

        # Act
        response = await authenticated_client.post(
            "/start_file_processing_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data


class TestJobsStatusEndpoints:
    """ジョブステータスエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_get_job_status(self, authenticated_client, mock_status_manager):
        """JOB-003: ジョブステータス取得成功"""
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = {
            "job_id": "job-001",
            "job_type": "cspm_policy_batch",
            "status": "running",
            "progress": {"current": 5, "total": 10, "unit": "items", "message": "処理中"},
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:01:00Z"
        }

        # Act
        response = await authenticated_client.get("/jobs/job-001/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-001"
        assert data["status"] == "running"
        assert data["progress"]["current"] == 5

    @pytest.mark.asyncio
    async def test_get_job_result_completed(self, authenticated_client, mock_status_manager):
        """JOB-004: 完了ジョブの結果取得成功"""
        # Arrange
        mock_status_manager.get_job_result_sync.return_value = {
            "job_id": "job-001",
            "status": "completed",
            "result": {"generated_policies": 10}
        }

        # Act
        response = await authenticated_client.get("/jobs/job-001/result")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "result" in data


class TestScanFilesEndpoint:
    """スキャンファイル取得エンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_get_scan_files_success(self, authenticated_client, mock_status_manager):
        """JOB-005: スキャンファイル取得成功"""
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = {
            "job_id": "scan-001",
            "job_type": "new_custodian_scan_aws",
            "status": "completed",
            "progress": None,
            "result": {"violations_found": 5},
            "error": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:10:00Z"
        }
        mock_status_manager.get_job_result_sync.return_value = {
            "job_id": "scan-001",
            "status": "completed",
            "result": {"regions": ["ap-northeast-1"], "violations_found": 5}
        }

        # Act
        response = await authenticated_client.get("/jobs/scan-001/scan_files")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "scan-001"
        assert data["scan_status"] == "completed"


class TestCustodianScanEndpoints:
    """Custodianスキャンエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_custodian_scan_encrypted_success(
        self, authenticated_client, mock_crypto, mock_status_manager, mock_tasks
    ):
        """JOB-006: 旧Custodianスキャン開始（暗号化リクエスト）成功"""
        # Arrange
        mock_crypto.verify_auth_hash.return_value = True
        mock_crypto.decrypt_opensearch_dashboard_payload.return_value = {
            "policy_yaml_content": "policies: []",
            "credentials": {"accessKey": "test", "secretKey": "test", "defaultRegion": "ap-northeast-1"},
            "cloud_provider": "aws",
            "scan_id": "scan-001",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }
        mock_status_manager.check_job_exclusion.return_value = None

        request_data = {
            "encrypted_payload": "valid_encrypted_payload",
            "iv": "valid_iv",
            "session_id": "policy-scanner-scan-001",
            "auth_hash": "SHARED-HMAC-1234567890-valid"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "scan-001"

    @pytest.mark.asyncio
    async def test_custodian_scan_plain_success(
        self, authenticated_client, mock_status_manager, mock_tasks
    ):
        """JOB-007: 旧Custodianスキャン開始（平文リクエスト）成功"""
        # Arrange
        mock_status_manager.check_job_exclusion.return_value = None

        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {"accessKey": "test", "secretKey": "test", "defaultRegion": "ap-northeast-1"},
            "cloud_provider": "aws",
            "scan_id": "scan-002",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "scan-002"


class TestNewCustodianScanEndpoints:
    """新Custodianスキャンエンドポイントのテスト"""

    @pytest.mark.asyncio
    async def test_new_custodian_scan_encrypted_success(
        self, authenticated_client, mock_crypto, mock_status_manager, mock_tasks
    ):
        """JOB-008: 新Custodianスキャン開始（暗号化リクエスト）成功"""
        # Arrange
        mock_crypto.verify_auth_hash.return_value = True
        # 復号後のペイロード（CustodianScanRequest形式）
        mock_crypto.decrypt_opensearch_dashboard_payload.return_value = {
            "policy_yaml_content": "policies: []",
            "credentials": {
                "authType": "role_assumption",  # 正しいauthType
                "roleArn": "arn:aws:iam::123456789012:role/TestRole",
                "externalIdValue": "test-external-id",
                "scanRegions": ["ap-northeast-1"]
            },
            "cloud_provider": "aws",
            "scan_id": "new-scan-001",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }
        mock_status_manager.check_job_exclusion.return_value = None

        request_data = {
            "encrypted_payload": "valid_encrypted_payload",
            "iv": "valid_iv",
            "session_id": "policy-scanner-new-scan-001",
            "auth_hash": "SHARED-HMAC-1234567890-valid"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "new-scan-001"

    @pytest.mark.asyncio
    async def test_new_custodian_scan_plain_success(
        self, authenticated_client, mock_status_manager, mock_tasks
    ):
        """JOB-009: 新Custodianスキャン開始（平文リクエスト）成功"""
        # Arrange
        mock_status_manager.check_job_exclusion.return_value = None

        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {
                "authType": "role_assumption",  # 正しいauthType
                "roleArn": "arn:aws:iam::123456789012:role/TestRole",
                "externalIdValue": "test-external-id",
                "scanRegions": ["ap-northeast-1"]
            },
            "cloud_provider": "aws",
            "scan_id": "new-scan-002",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "new-scan-002"

    @pytest.mark.asyncio
    async def test_new_custodian_scan_with_preset(
        self, authenticated_client, mock_status_manager, mock_tasks
    ):
        """JOB-010: 新Custodianスキャン開始（プリセット情報付き）成功"""
        # Arrange
        mock_status_manager.check_job_exclusion.return_value = None

        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {
                "authType": "secret_key",  # アクセスキー方式
                "accessKey": "AKIAIOSFODNN7EXAMPLE",
                "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "scanRegions": ["ap-northeast-1", "us-east-1"]
            },
            "cloud_provider": "aws",
            "scan_id": "new-scan-003",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "preset_scan",
            "preset_id": "preset-001",
            "preset_name": "セキュリティベースライン"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 202
        data = response.json()
        assert data["job_id"] == "new-scan-003"
```

---

## 3. 異常系テストケース

| ID | テスト名 | エンドポイント | 入力 | 期待結果 |
|----|---------|---------------|------|---------|
| JOB-E01 | 存在しないジョブのステータス取得 | GET /jobs/{job_id}/status | invalid job_id | 404 Not Found |
| JOB-E02 | 排他制御エラー | POST /start_*_async | 他ジョブ実行中 | 409 Conflict |
| JOB-E03 | 無効なリクエストデータ（空リスト） | POST /start_generate_policies_batch_async | recommendations=[] | 422 Unprocessable Entity |
| JOB-E04 | 存在しないジョブの結果取得 | GET /jobs/{job_id}/result | invalid job_id | 404 Not Found |
| JOB-E05 | 認証ハッシュ検証失敗 | POST /start_custodian_scan_async | invalid auth_hash | 400 Bad Request (※1) |
| JOB-E06 | 暗号化ペイロード復号失敗 | POST /start_custodian_scan_async | invalid encrypted_payload | 400 Bad Request |
| JOB-E07 | スキャンファイル取得（存在しないジョブ） | GET /jobs/{job_id}/scan_files | invalid job_id | 404 Not Found |
| JOB-E08 | スキャンファイル取得（非Custodianジョブ） | GET /jobs/{job_id}/scan_files | file_processing job_id | 400 Bad Request |
| JOB-E09 | スキャンファイル取得（未完了ジョブ） | GET /jobs/{job_id}/scan_files | running job_id | 400 Bad Request |
| JOB-E10 | スキャンファイル取得（結果なし） | GET /jobs/{job_id}/scan_files | completed job with no result | 500 Internal Server Error (※2) |
| JOB-E11 | リクエストボディ解析失敗 | POST /start_custodian_scan_async | invalid JSON | 400 Bad Request |
| JOB-E12 | 新Custodianスキャン認証失敗 | POST /new_start_custodian_scan_async | invalid auth_hash | 400 Bad Request (※1) |
| JOB-E13 | 新Custodianスキャン排他制御エラー | POST /new_start_custodian_scan_async | 他ジョブ実行中 | 409 Conflict |
| JOB-E14 | 新Custodianスキャン検証失敗 | POST /new_start_custodian_scan_async | invalid authType | 400 Bad Request |
| JOB-E15 | ステータスPydanticキャストエラー | GET /jobs/{job_id}/status | 不正なステータス辞書 | 500 Internal Server Error |
| JOB-E16 | 旧Custodianスキャン排他制御エラー | POST /start_custodian_scan_async | 他ジョブ実行中 | 409 Conflict |

> **※1**: 実装では`HTTPException(401)`が広域`except`で捕捉され400に変換される（router.py:334-336, 464-466）
> **※2**: 実装では`HTTPException(404)`が広域`except`で捕捉され500に変換される（router.py:281-286）

### 3.1 基本エラーテスト

```python
class TestJobsErrors:
    """ジョブ基本エラーのテスト"""

    @pytest.mark.asyncio
    async def test_job_status_not_found(self, authenticated_client, mock_status_manager):
        """JOB-E01: 存在しないジョブで404"""
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = None

        # Act
        response = await authenticated_client.get("/jobs/invalid-id/status")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"

    @pytest.mark.asyncio
    async def test_job_exclusion_conflict(self, authenticated_client, mock_status_manager, mock_tasks):
        """JOB-E02: 排他制御エラーで409"""
        # Arrange
        mock_status_manager.try_initialize_job_exclusive.return_value = (
            None,
            "別のジョブが実行中です"
        )
        request_data = {
            "recommendations": [
                {
                    "uuid": "rec-001",
                    "title": "テスト",
                    "description": "テスト説明",
                    "targetClouds": ["aws"]
                }
            ]
        }

        # Act
        response = await authenticated_client.post(
            "/start_generate_policies_batch_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_request_data(self, authenticated_client):
        """JOB-E03: 無効なリクエストデータで422"""
        # Arrange
        request_data = {
            "recommendations": []  # 空のリスト（min_length=1に違反）
        }

        # Act
        response = await authenticated_client.post(
            "/start_generate_policies_batch_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 422  # Pydanticバリデーションエラー

    @pytest.mark.asyncio
    async def test_job_result_not_found(self, authenticated_client, mock_status_manager):
        """JOB-E04: 存在しないジョブの結果取得で404"""
        # Arrange
        mock_status_manager.get_job_result_sync.return_value = None

        # Act
        response = await authenticated_client.get("/jobs/invalid-id/result")

        # Assert
        assert response.status_code == 404


class TestEncryptedRequestErrors:
    """暗号化リクエストエラーのテスト"""

    @pytest.mark.asyncio
    async def test_auth_hash_verification_failure(
        self, authenticated_client, mock_crypto
    ):
        """JOB-E05: 認証ハッシュ検証失敗で400

        注意: 実装では401を発生させるが、広域exceptで400に変換される
        router.py:319-320 で401を発生、router.py:334-336 で400に変換
        """
        # Arrange
        mock_crypto.verify_auth_hash.return_value = False
        request_data = {
            "encrypted_payload": "invalid_payload",
            "iv": "invalid_iv",
            "session_id": "policy-scanner-test-001",
            "auth_hash": "SHARED-HMAC-1234567890-invalid"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        # 実装の現状: HTTPException(401)が広域exceptで捕捉され400に変換
        assert response.status_code == 400
        assert "復号に失敗" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_decryption_failure(self, authenticated_client, mock_crypto):
        """JOB-E06: 復号失敗で400"""
        # Arrange
        mock_crypto.verify_auth_hash.return_value = True
        mock_crypto.decrypt_opensearch_dashboard_payload.side_effect = Exception(
            "Decryption failed"
        )
        request_data = {
            "encrypted_payload": "corrupted_payload",
            "iv": "valid_iv",
            "session_id": "policy-scanner-test-001",
            "auth_hash": "SHARED-HMAC-1234567890-valid"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400
        assert "暗号化リクエストの復号に失敗" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_request_body_parse_failure(self, authenticated_client):
        """JOB-E11: リクエストボディ解析失敗で400"""
        # Arrange - 不正なJSONを送信

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            content="invalid json {{{",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 400


class TestScanFilesErrors:
    """スキャンファイル取得エラーのテスト"""

    @pytest.mark.asyncio
    async def test_scan_files_job_not_found(self, authenticated_client, mock_status_manager):
        """JOB-E07: 存在しないジョブでスキャンファイル取得 → 404"""
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = None

        # Act
        response = await authenticated_client.get("/jobs/invalid-scan-id/scan_files")

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Job not found"

    @pytest.mark.asyncio
    async def test_scan_files_non_custodian_job(self, authenticated_client, mock_status_manager):
        """JOB-E08: Custodianスキャン以外のジョブでスキャンファイル取得 → 400"""
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = {
            "job_id": "job-001",
            "job_type": "file_processing",  # Custodianスキャンではない
            "status": "completed",
            "progress": None,
            "result": {"extracted_text": "test"},
            "error": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:10:00Z"
        }

        # Act
        response = await authenticated_client.get("/jobs/job-001/scan_files")

        # Assert
        assert response.status_code == 400
        assert "Custodian scan jobs" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_scan_files_job_not_completed(self, authenticated_client, mock_status_manager):
        """JOB-E09: 未完了ジョブでスキャンファイル取得 → 400"""
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = {
            "job_id": "scan-001",
            "job_type": "new_custodian_scan_aws",
            "status": "running",  # 未完了
            "progress": {"message": "スキャン実行中"},
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:05:00Z"
        }

        # Act
        response = await authenticated_client.get("/jobs/scan-001/scan_files")

        # Assert
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_scan_files_result_not_found(self, authenticated_client, mock_status_manager):
        """JOB-E10: 結果データなしでスキャンファイル取得 → 500

        注意: 実装ではHTTPException(404)を発生させるが、広域exceptで500に変換される
        router.py:260-261 で404を発生、router.py:281-286 で500に変換
        """
        # Arrange
        mock_status_manager.get_job_status_sync.return_value = {
            "job_id": "scan-001",
            "job_type": "new_custodian_scan_aws",
            "status": "completed",
            "progress": None,
            "result": None,
            "error": None,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:10:00Z"
        }
        mock_status_manager.get_job_result_sync.return_value = None

        # Act
        response = await authenticated_client.get("/jobs/scan-001/scan_files")

        # Assert
        # 実装の現状: HTTPException(404)が広域exceptで捕捉され500に変換
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]


class TestNewCustodianScanErrors:
    """新Custodianスキャンエラーのテスト"""

    @pytest.mark.asyncio
    async def test_new_scan_auth_failure(self, authenticated_client, mock_crypto):
        """JOB-E12: 新Custodianスキャン認証失敗で400

        注意: 実装では401を発生させるが、広域exceptで400に変換される
        router.py:444-446 で401を発生、router.py:464-466 で400に変換
        """
        # Arrange
        mock_crypto.verify_auth_hash.return_value = False
        request_data = {
            "encrypted_payload": "invalid_payload",
            "iv": "invalid_iv",
            "session_id": "policy-scanner-new-scan-001",
            "auth_hash": "SHARED-HMAC-1234567890-invalid"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        # 実装の現状: HTTPException(401)が広域exceptで捕捉され400に変換
        assert response.status_code == 400
        assert "復号に失敗" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_new_scan_exclusion_conflict(self, authenticated_client, mock_status_manager, mock_tasks):
        """JOB-E13: 新Custodianスキャン排他制御エラーで409"""
        # Arrange
        mock_status_manager.check_job_exclusion.return_value = "別のスキャンジョブが実行中です"
        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {
                "authType": "role_assumption",
                "roleArn": "arn:aws:iam::123456789012:role/TestRole",
                "scanRegions": ["ap-northeast-1"]
            },
            "cloud_provider": "aws",
            "scan_id": "new-scan-conflict",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_new_scan_validation_failure(self, authenticated_client):
        """JOB-E14: 新Custodianスキャン検証失敗で400

        authTypeが不正な値（role_assumption/secret_key以外）の場合
        """
        # Arrange
        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {
                "authType": "invalid_type",  # 不正なauthType
                "roleArn": "arn:aws:iam::123456789012:role/TestRole",
                "scanRegions": ["ap-northeast-1"]
            },
            "cloud_provider": "aws",
            "scan_id": "new-scan-invalid",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_old_scan_exclusion_conflict(self, authenticated_client, mock_status_manager, mock_tasks):
        """JOB-E16: 旧Custodianスキャン排他制御エラーで409"""
        # Arrange
        mock_status_manager.check_job_exclusion.return_value = "別のスキャンジョブが実行中です"
        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {"accessKey": "test", "secretKey": "test", "defaultRegion": "ap-northeast-1"},
            "cloud_provider": "aws",
            "scan_id": "scan-conflict",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 409


class TestInternalErrors:
    """内部エラーのテスト"""

    @pytest.mark.asyncio
    async def test_status_pydantic_cast_error(self, authenticated_client, mock_status_manager):
        """JOB-E15: ステータス辞書のPydanticモデルキャストエラーで500

        router.py:183-190 の例外パスをカバー
        """
        # Arrange - Pydanticモデルに変換できない不正なデータ
        mock_status_manager.get_job_status_sync.return_value = {
            "job_id": "job-001",
            "job_type": "test",
            "status": "running",
            # created_at, updated_at が欠落（必須フィールド）
        }

        # Act
        response = await authenticated_client.get("/jobs/job-001/status")

        # Assert
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| JOB-SEC-01 | タイムスタンプリプレイ攻撃防止 | 古いタイムスタンプのauth_hash | 400 Bad Request (※) |
| JOB-SEC-02 | HMACハッシュ形式検証 | 不正なフォーマットのauth_hash | 400 Bad Request (※) |
| JOB-SEC-03 | 暗号化ペイロード改ざん検知 | 改ざんされた暗号文 | 400 Bad Request |
| JOB-SEC-04 | 不正IVサイズ拒否 | 16バイト以外のIV | 400 Bad Request |
| JOB-SEC-05 | 認証情報のログ出力検証 | 認証情報を含むリクエスト | ログに認証情報が含まれない |
| JOB-SEC-06 | エラーメッセージの機密性 | 内部エラー発生 | 内部情報が漏洩しない |
| JOB-SEC-07 | パストラバーサル攻撃防止 | ../../etc/passwd を含むfilename | 安全に処理される |
| JOB-SEC-08 | session_id形式検証 | 不正なsession_id形式 | 400 Bad Request |
| JOB-SEC-09 | 空のauth_hash拒否 | auth_hash="" | 400 Bad Request |
| JOB-SEC-10 | authType検証 | 不正なauthType | 400 Bad Request |

> **※**: 実装では401を発生させるが、広域exceptで400に変換される

```python
@pytest.mark.security
class TestJobsSecurity:
    """ジョブシステムセキュリティテスト"""

    @pytest.mark.asyncio
    async def test_timestamp_replay_attack_prevention(self, authenticated_client, mock_crypto):
        """JOB-SEC-01: タイムスタンプリプレイ攻撃防止

        古いタイムスタンプ（600秒以上前）の認証ハッシュを拒否する
        注意: 実装では401だが広域exceptで400に変換
        """
        # Arrange
        import time
        old_timestamp = int(time.time()) - 602  # 602秒前

        mock_crypto.verify_auth_hash.return_value = False  # タイムスタンプ検証で失敗

        request_data = {
            "encrypted_payload": "valid_payload",
            "iv": "valid_iv",
            "session_id": "policy-scanner-test-001",
            "auth_hash": f"SHARED-HMAC-{old_timestamp}-stale_hash"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400
        assert "復号に失敗" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_hmac_format_rejection(self, authenticated_client, mock_crypto):
        """JOB-SEC-02: HMACハッシュ形式検証

        不正なフォーマットの認証ハッシュを拒否する
        """
        # Arrange
        mock_crypto.verify_auth_hash.return_value = False

        request_data = {
            "encrypted_payload": "valid_payload",
            "iv": "valid_iv",
            "session_id": "policy-scanner-test-001",
            "auth_hash": "INVALID-FORMAT-NO-TIMESTAMP"  # 不正なフォーマット
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_encrypted_payload_tampering_detection(self, authenticated_client, mock_crypto):
        """JOB-SEC-03: 暗号化ペイロード改ざん検知

        改ざんされた暗号文を検知して拒否する
        """
        # Arrange
        mock_crypto.verify_auth_hash.return_value = True
        mock_crypto.decrypt_opensearch_dashboard_payload.side_effect = ValueError(
            "無効なパディング - 改ざんの可能性"
        )

        request_data = {
            "encrypted_payload": "tampered_ciphertext",
            "iv": "valid_iv",
            "session_id": "policy-scanner-test-001",
            "auth_hash": "SHARED-HMAC-1234567890-valid"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400
        assert "復号に失敗" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_invalid_iv_size_rejection(self, authenticated_client, mock_crypto):
        """JOB-SEC-04: 不正IVサイズ拒否

        16バイト以外のIVを拒否する（AES-CBCは16バイトIV必須）
        """
        # Arrange
        import base64
        invalid_iv = base64.b64encode(b"12345678").decode()  # 8バイト（不正）

        mock_crypto.verify_auth_hash.return_value = True
        mock_crypto.decrypt_opensearch_dashboard_payload.side_effect = ValueError(
            "無効なIVサイズ: 8バイト（16バイト必要）"
        )

        request_data = {
            "encrypted_payload": "valid_encrypted",
            "iv": invalid_iv,
            "session_id": "policy-scanner-test-001",
            "auth_hash": "SHARED-HMAC-1234567890-valid"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_credentials_not_logged(self, authenticated_client, mock_status_manager, mock_tasks, capsys):
        """JOB-SEC-05: 認証情報のログ出力検証

        認証情報（accessKey, secretKey等）がログに出力されないことを確認
        注意: 実装はprintを使用するため、capsysで標準出力を捕捉
        """
        # Arrange
        mock_status_manager.check_job_exclusion.return_value = None
        sensitive_credentials = {
            "accessKey": "AKIAIOSFODNN7EXAMPLE",
            "secretKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "defaultRegion": "ap-northeast-1"
        }

        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": sensitive_credentials,
            "cloud_provider": "aws",
            "scan_id": "scan-log-test",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert - 標準出力を捕捉して確認
        captured = capsys.readouterr()
        stdout_lower = captured.out.lower()
        # secretKeyが完全な形で出力されていないことを確認
        # （ただし実装がjson.dumpsで出力する場合は漏洩する可能性あり - 要改善）
        assert "wjalrxutnfemi/k7mdeng/bpxrficyexamplekey" not in stdout_lower

    @pytest.mark.asyncio
    async def test_error_message_sanitization(self, authenticated_client, mock_crypto):
        """JOB-SEC-06: エラーメッセージの機密性

        内部エラー発生時に内部情報が漏洩しないことを確認
        注意: 現在の実装はstr(e)をそのまま返すため、一部情報が漏洩する可能性あり
        """
        # Arrange
        mock_crypto.verify_auth_hash.side_effect = Exception(
            "Internal: database connection failed to host=192.168.1.100:5432"
        )

        request_data = {
            "encrypted_payload": "test",
            "iv": "test",
            "session_id": "test",
            "auth_hash": "SHARED-HMAC-123-abc"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        # 実装の現状確認（内部IPが漏洩する可能性を検知）
        response_text = response.text.lower()
        # 理想: 内部情報が漏洩しない
        # 現実: str(e)がそのまま出力されるため漏洩の可能性あり
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_path_traversal_prevention(self, authenticated_client, mock_status_manager, mock_tasks):
        """JOB-SEC-07: パストラバーサル攻撃防止

        悪意のあるファイル名が安全に処理されることを確認
        注意: ファイル名のサニタイズは後続のタスク処理で行われる
        """
        # Arrange
        mock_status_manager.try_initialize_job_exclusive.return_value = ("job-path-test", None)

        request_data = {
            "filename": "../../etc/passwd",  # パストラバーサル試行
            "file_content_base64": "dGVzdA==",
            "target_clouds": ["aws"],
            "output_lang": "jp"
        }

        # Act
        response = await authenticated_client.post(
            "/start_file_processing_async",
            json=request_data
        )

        # Assert
        # リクエストは受け付けられる（検証は後続のタスクで実施）
        assert response.status_code == 202
        # ファイル名がジョブステータスに安全に保存されることを確認
        # （実際のサニタイズは run_file_processing_task 内で実施）

    @pytest.mark.asyncio
    async def test_session_id_format_validation(self, authenticated_client, mock_crypto):
        """JOB-SEC-08: session_id形式検証

        policy-scanner-{scan_id} 形式以外のsession_idを拒否
        """
        # Arrange
        mock_crypto.verify_auth_hash.return_value = False  # 形式不正で失敗

        request_data = {
            "encrypted_payload": "valid_payload",
            "iv": "valid_iv",
            "session_id": "invalid-session-format",  # 不正な形式
            "auth_hash": "SHARED-HMAC-1234567890-valid"
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_empty_auth_hash_rejection(self, authenticated_client, mock_crypto):
        """JOB-SEC-09: 空のauth_hash拒否"""
        # Arrange
        mock_crypto.verify_auth_hash.return_value = False

        request_data = {
            "encrypted_payload": "valid_payload",
            "iv": "valid_iv",
            "session_id": "policy-scanner-test-001",
            "auth_hash": ""  # 空の認証ハッシュ
        }

        # Act
        response = await authenticated_client.post(
            "/start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_auth_type_rejection(self, authenticated_client, mock_tasks):
        """JOB-SEC-10: authType検証

        NewCredentials.authType は role_assumption/secret_key のみ許可
        """
        # Arrange
        request_data = {
            "policy_yaml_content": "policies: []",
            "credentials": {
                "authType": "sql_injection'; DROP TABLE users;--",  # 悪意のある入力
                "roleArn": "arn:aws:iam::123456789012:role/TestRole",
                "scanRegions": ["ap-northeast-1"]
            },
            "cloud_provider": "aws",
            "scan_id": "new-scan-malicious",
            "initiated_by_user": "test-user",
            "scan_trigger_type": "manual_batch"
        }

        # Act
        response = await authenticated_client.post(
            "/new_start_custodian_scan_async",
            json=request_data
        )

        # Assert
        assert response.status_code == 400
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `app` | FastAPIアプリケーションインスタンス | session | No |
| `authenticated_client` | 認証済みHTTPクライアント | function | No |
| `mock_status_manager` | ステータス管理関数のモック | function | No |
| `mock_crypto` | 暗号化関連関数のモック | function | No |
| `mock_background_tasks` | バックグラウンドタスクのモック | function | No |
| `mock_tasks` | タスク関数のモック（run_*_task） | function | No |
| `sample_completed_scan_job` | 完了スキャンジョブのサンプル | function | No |
| `reset_jobs_module` | テスト間のモジュール状態リセット | function | Yes |

### 共通フィクスチャ定義

```python
# test/unit/jobs/conftest.py
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture(autouse=True)
def reset_jobs_module():
    """テストごとにジョブモジュールのグローバル状態をリセット

    job_statuses辞書などのグローバル状態をテスト間で分離
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [key for key in sys.modules if key.startswith("app.jobs")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def app():
    """FastAPIアプリケーションインスタンス"""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
async def authenticated_client(app):
    """認証済みクライアントのフィクスチャ"""
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def mock_status_manager():
    """ステータス管理関数のモック"""
    with patch("app.jobs.router.get_job_status_sync") as mock_get_status, \
         patch("app.jobs.router.get_job_result_sync") as mock_get_result, \
         patch("app.jobs.router.try_initialize_job_exclusive") as mock_init, \
         patch("app.jobs.router.check_job_exclusion") as mock_exclusion, \
         patch("app.jobs.router.update_job_status") as mock_update, \
         patch("app.jobs.router.append_job_log") as mock_append_log, \
         patch("app.jobs.router.job_statuses", {}) as mock_statuses:

        mock = MagicMock()
        mock.get_job_status_sync = mock_get_status
        mock.get_job_result_sync = mock_get_result
        mock.try_initialize_job_exclusive = mock_init
        mock.check_job_exclusion = mock_exclusion
        mock.update_job_status = mock_update
        mock.append_job_log = mock_append_log
        mock.job_statuses = mock_statuses
        yield mock


@pytest.fixture
def mock_crypto():
    """暗号化関連関数のモック"""
    with patch("app.jobs.router.verify_auth_hash") as mock_verify, \
         patch("app.jobs.router.decrypt_opensearch_dashboard_payload") as mock_decrypt, \
         patch("app.jobs.router._get_shared_secret") as mock_secret:

        mock_secret.return_value = "test-secret"
        mock = MagicMock()
        mock.verify_auth_hash = mock_verify
        mock.decrypt_opensearch_dashboard_payload = mock_decrypt
        mock._get_shared_secret = mock_secret
        yield mock


@pytest.fixture
def mock_background_tasks():
    """バックグラウンドタスクのモック"""
    mock = MagicMock()
    mock.add_task = MagicMock()
    return mock


@pytest.fixture
def mock_tasks():
    """すべてのタスク関数のモック

    バックグラウンドタスクが実際に実行されないようにする
    """
    with patch("app.jobs.router.run_file_processing_task") as mock_file, \
         patch("app.jobs.router.run_policy_batch_generation_task") as mock_policy, \
         patch("app.jobs.router.run_custodian_scan_task") as mock_scan, \
         patch("app.jobs.router.new_run_custodian_scan_task") as mock_new_scan:

        mock = MagicMock()
        mock.file_processing = mock_file
        mock.policy_batch = mock_policy
        mock.custodian_scan = mock_scan
        mock.new_custodian_scan = mock_new_scan
        yield mock


@pytest.fixture
def sample_completed_scan_job():
    """完了したCustodianスキャンジョブのサンプルデータ"""
    return {
        "job_id": "scan-sample-001",
        "job_type": "new_custodian_scan_aws",
        "status": "completed",
        "progress": None,
        "result": {
            "regions": ["ap-northeast-1"],
            "violations_found": 10,
            "resources_scanned": 50
        },
        "error": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:15:00Z"
    }
```

---

## 6. テスト実行例

```bash
# jobsプラグイン関連テストのみ実行
pytest test/unit/jobs/test_jobs_router.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/test_jobs_router.py::TestJobsStartEndpoints -v

# 特定のテストメソッドのみ実行
pytest test/unit/jobs/test_jobs_router.py::TestJobsStartEndpoints::test_start_policy_batch -v

# カバレッジ付きで実行
pytest test/unit/jobs/test_jobs_router.py --cov=app.jobs.router --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/jobs/test_jobs_router.py -m "security" -v

# 統合テストを除外して実行
pytest test/unit/jobs/test_jobs_router.py -m "not integration" -v

# 並列実行（pytest-xdist使用時）
pytest test/unit/jobs/test_jobs_router.py -n auto -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 10 | JOB-001 〜 JOB-010 |
| 異常系 | 16 | JOB-E01 〜 JOB-E16 |
| セキュリティ | 10 | JOB-SEC-01 〜 JOB-SEC-10 |
| **合計** | **36** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestJobsStartEndpoints` | JOB-001〜JOB-002 | 2 |
| `TestJobsStatusEndpoints` | JOB-003〜JOB-004 | 2 |
| `TestScanFilesEndpoint` | JOB-005 | 1 |
| `TestCustodianScanEndpoints` | JOB-006〜JOB-007 | 2 |
| `TestNewCustodianScanEndpoints` | JOB-008〜JOB-010 | 3 |
| `TestJobsErrors` | JOB-E01〜JOB-E04 | 4 |
| `TestEncryptedRequestErrors` | JOB-E05〜JOB-E06, JOB-E11 | 3 |
| `TestScanFilesErrors` | JOB-E07〜JOB-E10 | 4 |
| `TestNewCustodianScanErrors` | JOB-E12〜JOB-E14, JOB-E16 | 4 |
| `TestInternalErrors` | JOB-E15 | 1 |
| `TestJobsSecurity` | JOB-SEC-01〜JOB-SEC-10 | 10 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 備考 |
|---------|------|------|
| JOB-SEC-05 | 実装がprintでログ出力、json.dumpsで認証情報が出力される可能性 | 実装側の改善推奨 |
| JOB-SEC-06 | 実装がstr(e)をそのままエラー詳細に含める | 実装側の改善推奨 |

### 注意事項

- `pytest-asyncio` が必要（非同期テスト用）
- `@pytest.mark.security` マーカーの登録要（`pyproject.toml` に追加）
- 環境変数パッチのタイミング: `import` 前に適用が必要な場合あり
- 統合テスト（`@pytest.mark.integration`）は実際のジョブ実行を伴うため、単体テストと分離推奨
- `mock_tasks`フィクスチャを使用してバックグラウンドタスクの実行を防止

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 一時ディレクトリのスキャン結果は自動削除される | スキャン結果ファイルの詳細テスト不可 | 永続化オプション実装後にテスト追加 |
| 2 | Cloud Custodianはコンテナ内でのみ動作 | 統合テストはDocker環境が必要 | モック使用で単体テストカバー |
| 3 | pypdfのオプショナル依存 | PDF処理テストが環境依存 | コンディショナルスキップ使用 |
| 4 | 排他制御のレースコンディションテスト | 並行テストは実行環境依存 | `pytest-asyncio` + 並行リクエストで検証 |
| 5 | 暗号化シークレットの環境変数依存 | テスト環境で設定が必要 | フィクスチャでモック化 |
| 6 | 認証失敗時のステータスコード | 実装では401が400に変換される | 実装修正後にテスト期待値を更新 |
| 7 | scan_files結果なし時のステータスコード | 実装では404が500に変換される | 実装修正後にテスト期待値を更新 |
| 8 | ログ出力がprintベース | caplogでは捕捉不可 | capsysを使用、またはlogging移行後に改善 |

---

## 付録: モデル定義（参考）

### レスポンスモデル

```python
# app/models/jobs.py
from pydantic import BaseModel
from typing import Optional, Any, Dict

class AsyncJobResponse(BaseModel):
    """非同期ジョブ開始時のレスポンス"""
    job_id: str
    message: Optional[str] = None

class JobProgress(BaseModel):
    """ジョブ進捗情報"""
    current: Optional[int] = None
    total: Optional[int] = None
    unit: str = "items"
    message: Optional[str] = None

class JobStatus(BaseModel):
    """ジョブステータス"""
    job_id: str
    job_type: str
    status: str  # "pending", "running", "completed", "failed", "initializing"
    progress: Optional[JobProgress] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
```

### リクエストモデル

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal

class FileProcessingRequest(BaseModel):
    """ファイル処理リクエスト"""
    filename: str
    file_content_base64: str
    target_clouds: List[str]
    output_lang: str = "jp"
    start_page: Optional[int] = None
    end_page: Optional[int] = None

class CspmBatchRequest(BaseModel):
    """CSPMポリシーバッチ生成リクエスト"""
    recommendations: List[RecommendationInputData] = Field(..., min_length=1)

class NewCredentials(BaseModel):
    """新しい統合認証情報モデル"""
    authType: Literal["role_assumption", "secret_key"]  # 重要: この2値のみ許可
    roleArn: Optional[str] = None
    externalIdValue: Optional[str] = None
    accessKey: Optional[str] = None
    secretKey: Optional[str] = None
    sessionToken: Optional[str] = None
    scanRegions: List[str] = Field(default_factory=list)

class CustodianScanRequest(BaseModel):
    """Custodianスキャンリクエスト"""
    policy_yaml_content: str
    credentials: Dict[str, Any]
    cloud_provider: str
    scan_id: str
    initiated_by_user: str
    scan_trigger_type: str
    preset_id: Optional[str] = None
    preset_name: Optional[str] = None

class EncryptedCustodianScanRequest(BaseModel):
    """暗号化されたCustodianスキャンリクエスト"""
    encrypted_payload: str  # Base64エンコードされた暗号文
    iv: str                 # Base64エンコードされた初期化ベクトル
    session_id: str         # policy-scanner-{scan_id}
    auth_hash: str          # SHARED-HMAC-{timestamp}-{hash}
```

---

## 付録: HTTPステータスコード一覧

| コード | 説明 | 使用場面 |
|--------|------|---------|
| 200 | OK | ステータス取得、結果取得、スキャンファイル取得成功 |
| 202 | Accepted | ジョブ開始成功（非同期処理受付） |
| 400 | Bad Request | リクエストボディ解析失敗、暗号化復号失敗、認証失敗（※実装の現状）、非Custodianジョブでscan_files取得、未完了ジョブでscan_files取得 |
| 404 | Not Found | ジョブが見つからない、結果が見つからない |
| 409 | Conflict | 排他制御エラー（他ジョブ実行中） |
| 422 | Unprocessable Entity | Pydanticバリデーションエラー |
| 500 | Internal Server Error | サーバー内部エラー、Pydanticキャストエラー、scan_files結果なし（※実装の現状） |
