# jobs/tasks/new_custodian_scan/scan_coordinator テストケース

## 1. 概要

`scan_coordinator.py` はマルチリージョン Custodian スキャンの調整モジュール。ポリシーYAMLをグローバル/リージョナルに分離し、クラウドプロバイダー（AWS/Azure）に応じたスキャン実行を各コンポーネントに委譲するオーケストレーターである。

### 1.1 主要機能

| メソッド | 説明 |
|---------|------|
| `__init__` | 5つのコンポーネント（TaskLogger, AuthenticationHandler, CustodianExecutor, ResultProcessor, CustodianLogAnalyzer）を初期化 |
| `_extract_resource_types_from_policy` | ポリシーYAMLからリソースタイプを抽出 |
| `_has_global_resources` | グローバルリソースの有無を判定 |
| `_separate_policies_by_scope` | ポリシーをグローバル用/リージョナル用に分離 |
| `execute_multi_region_custodian_scan` | メインエントリポイント。Azure/AWS分岐とaccount_id抽出 |
| `_prepare_base_credentials` | クラウドプロバイダー別の認証情報準備（3分岐） |
| `_execute_azure_subscription_scan` | Azureサブスクリプション全体スキャン |
| `_execute_region_by_region_scan` | リージョン別スキャン（AWS分離ロジック含む） |
| `_get_assume_role_credentials` | AssumeRole認証情報取得 |

### 1.2 カバレッジ目標: 85%

> **注記**: `_execute_region_by_region_scan` は AWS ポリシー分離ロジック（4分岐）と非AWS分岐で複雑。pytest-asyncio が必要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/new_custodian_scan/scan_coordinator.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_scan_coordinator.py` |

### 1.4 補足情報

#### 依存関係（全モック対象）

```
scan_coordinator.py ──→ TaskLogger（ログ）
                    ──→ AuthenticationHandler（認証情報取得）
                    ──→ CustodianExecutor（スキャン実行）
                    ──→ ResultProcessor（結果処理）
                    ──→ CustodianLogAnalyzer（ログ分析・リソーススコープ判定）
                    ──→ yaml（ポリシーYAML解析）
                    ──→ datetime（タイムスタンプ）
                    ──→ metadata_extractor（遅延import、account_id抽出）
```

#### テスト戦略

| テストカテゴリ | 手法 |
|--------------|------|
| 初期化テスト | コンポーネントクラスを patch してインスタンス生成 |
| YAML解析テスト | 実際のYAML文字列を入力し、`_determine_resource_scope` をモック |
| ワークフローテスト | 内部メソッドを `patch.object` でモック |
| リージョン別テスト | `execute_single_region_scan` をモックし、各分岐を検証 |

#### ポリシー分離ロジック（AWS固有）

```
_execute_region_by_region_scan:
  AWS:
    ├─ global + regional → グローバル(us-east-1) + リージョナル(全リージョン)
    ├─ global のみ      → us-east-1 で実行
    ├─ regional のみ    → 通常のマルチリージョンスキャン
    └─ 空               → warning ログ
  非AWS:
    └─ 通常のマルチリージョンスキャン
```

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SCRD-001 | __init__ が全コンポーネントを初期化 | job_id, dry_run_mode | 5属性設定 |
| SCRD-002 | _extract_resource_types_from_policy 正常抽出 | 有効なYAML | リソースタイプリスト |
| SCRD-003 | _extract_resource_types_from_policy policies キーなし | policies キーなしYAML | 空リスト |
| SCRD-004 | _extract_resource_types_from_policy resource キーなし | resource 未定義 | 空リスト |
| SCRD-005 | _has_global_resources グローバルあり | iam ポリシー | True |
| SCRD-006 | _has_global_resources グローバルなし | ec2 ポリシー | False |
| SCRD-007 | _separate_policies_by_scope 混合 | global+regional | 分離された2つのYAML |
| SCRD-008 | _separate_policies_by_scope policies キーなし | policies キーなしYAML | regional=元YAML |
| SCRD-009 | execute_multi_region_custodian_scan Azure全体 | azure, all-locations | _execute_azure 呼び出し |
| SCRD-010 | execute_multi_region_custodian_scan 通常AWS | aws, 2リージョン | _execute_region_by_region 呼び出し |
| SCRD-011 | execute_multi_region_custodian_scan account_id 抽出成功 | 成功結果 | scan_metadata に account_id |
| SCRD-012 | _prepare_base_credentials Azure | azure | auth_handler 呼び出し |
| SCRD-013 | _prepare_base_credentials role_assumption | role_assumption | _get_assume_role 呼び出し |
| SCRD-014 | _prepare_base_credentials accessKey | accessKey | 環境変数辞書 |
| SCRD-015 | _execute_azure_subscription_scan 成功 | 有効データ | completed_regions=1 |
| SCRD-016 | _execute_region_by_region_scan AWS global+regional | 混合ポリシー | グローバル+リージョナル実行 |
| SCRD-017 | _execute_region_by_region_scan AWS global のみ | globalポリシー | us-east-1 で実行 |
| SCRD-018 | _execute_region_by_region_scan AWS regional のみ | regionalポリシー | 全リージョン実行 |
| SCRD-019 | _execute_region_by_region_scan AWS 空ポリシー | 分離後空 | warning ログ |
| SCRD-020 | _execute_region_by_region_scan 非AWS | gcp | 通常マルチリージョン |
| SCRD-021 | _get_assume_role_credentials テストARN | テスト用ARN | 模擬認証情報 |
| SCRD-022 | _get_assume_role_credentials 実ARN | 実際のARN | auth_handler 呼び出し |
| SCRD-023 | _execute_region_by_region_scan AWS global us-east-1 優先 | us-east-1 含むリージョン | primary_region=us-east-1 |
| SCRD-024 | _execute_region_by_region_scan AWS global us-east-1 なし | ap-northeast-1 のみ | primary_region=先頭リージョン |
| SCRD-025 | _execute_region_by_region_scan AWS global-only us-east-1 なし | us-east-1 未含有 | 先頭リージョンで実行 |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_scan_coordinator.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

MODULE = "app.jobs.tasks.new_custodian_scan.scan_coordinator"


class TestScanCoordinatorInit:
    """__init__ のコンポーネント初期化テスト"""

    def test_init_sets_all_components(self):
        """SCRD-001: __init__ が全コンポーネントと dry_run_mode を初期化

        scan_coordinator.py:29-36 の全属性設定をカバー。
        """
        # Arrange & Act
        with patch(f"{MODULE}.TaskLogger") as mock_tl, \
             patch(f"{MODULE}.AuthenticationHandler") as mock_ah, \
             patch(f"{MODULE}.CustodianExecutor") as mock_ce, \
             patch(f"{MODULE}.ResultProcessor") as mock_rp, \
             patch(f"{MODULE}.CustodianLogAnalyzer") as mock_la:
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            coordinator = ScanCoordinator("test-job", dry_run_mode=True)

        # Assert
        assert coordinator.job_id == "test-job"
        assert coordinator.dry_run_mode is True
        mock_tl.assert_called_once_with("test-job", "ScanCoordinator")
        mock_ah.assert_called_once_with("test-job")
        mock_ce.assert_called_once_with("test-job", True)
        mock_rp.assert_called_once_with("test-job")
        mock_la.assert_called_once_with("test-job")
```

### 2.2 _extract_resource_types_from_policy テスト

```python
class TestExtractResourceTypes:
    """_extract_resource_types_from_policy のYAML解析テスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    def test_extracts_resource_types(self, coordinator):
        """SCRD-002: 有効なYAMLからリソースタイプを抽出

        scan_coordinator.py:48-58 の正常パスをカバー。
        """
        # Arrange
        yaml_content = """
policies:
  - name: check-s3
    resource: aws.s3
  - name: check-ec2
    resource: aws.ec2
"""
        # Act
        result = coordinator._extract_resource_types_from_policy(yaml_content)

        # Assert
        assert result == ["aws.s3", "aws.ec2"]

    def test_no_policies_key(self, coordinator):
        """SCRD-003: policies キーがない場合は空リスト

        scan_coordinator.py:52 の if 'policies' in policy_data が不成立の経路をカバー。
        """
        # Arrange
        yaml_content = "other_key: value"

        # Act
        result = coordinator._extract_resource_types_from_policy(yaml_content)

        # Assert
        assert result == []

    def test_no_resource_key_in_policy(self, coordinator):
        """SCRD-004: ポリシーに resource キーがない場合はスキップ

        scan_coordinator.py:54 の if 'resource' in policy が不成立の経路をカバー。
        """
        # Arrange
        yaml_content = """
policies:
  - name: no-resource-policy
    filters: []
"""
        # Act
        result = coordinator._extract_resource_types_from_policy(yaml_content)

        # Assert
        assert result == []
```

### 2.3 _has_global_resources テスト

```python
class TestHasGlobalResources:
    """_has_global_resources のグローバルリソース判定テスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    def test_global_resource_detected(self, coordinator):
        """SCRD-005: グローバルリソース検出で True を返す

        scan_coordinator.py:79 の scope == "global" 分岐をカバー。
        """
        # Arrange
        yaml_content = """
policies:
  - name: iam-check
    resource: aws.iam-role
"""
        coordinator.log_analyzer._determine_resource_scope.return_value = "global"

        # Act
        result = coordinator._has_global_resources(yaml_content)

        # Assert
        assert result is True

    def test_no_global_resource(self, coordinator):
        """SCRD-006: グローバルリソースなしで False を返す

        scan_coordinator.py:83 の ループ完了→False 分岐をカバー。
        """
        # Arrange
        yaml_content = """
policies:
  - name: ec2-check
    resource: aws.ec2
"""
        coordinator.log_analyzer._determine_resource_scope.return_value = "regional"

        # Act
        result = coordinator._has_global_resources(yaml_content)

        # Assert
        assert result is False
```

### 2.4 _separate_policies_by_scope テスト

```python
class TestSeparatePoliciesByScope:
    """_separate_policies_by_scope のポリシー分離テスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    def test_mixed_policies_separated(self, coordinator):
        """SCRD-007: グローバル+リージョナルの混合ポリシーを分離

        scan_coordinator.py:103-115 のグローバル/リージョナル分岐をカバー。
        """
        # Arrange
        yaml_content = """
policies:
  - name: iam-check
    resource: aws.iam-role
  - name: ec2-check
    resource: aws.ec2
"""
        # グローバル→リージョナルの順で返す
        coordinator.log_analyzer._determine_resource_scope.side_effect = ["global", "regional"]

        # Act
        result = coordinator._separate_policies_by_scope(yaml_content)

        # Assert
        assert result['global'] != ''
        assert result['regional'] != ''
        # YAML構造を検証
        import yaml as yaml_mod
        global_data = yaml_mod.safe_load(result['global'])
        regional_data = yaml_mod.safe_load(result['regional'])
        assert len(global_data['policies']) == 1
        assert global_data['policies'][0]['name'] == 'iam-check'
        assert len(regional_data['policies']) == 1
        assert regional_data['policies'][0]['name'] == 'ec2-check'

    def test_no_policies_key(self, coordinator):
        """SCRD-008: policies キーがない場合は regional に元YAMLを返す

        scan_coordinator.py:97-98 の早期リターンをカバー。
        """
        # Arrange
        yaml_content = "other_key: value"

        # Act
        result = coordinator._separate_policies_by_scope(yaml_content)

        # Assert
        assert result['global'] == ''
        assert result['regional'] == yaml_content
```

### 2.5 execute_multi_region_custodian_scan テスト

```python
class TestExecuteMultiRegionCustodianScan:
    """execute_multi_region_custodian_scan のメインフローテスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_azure_all_locations(self, coordinator):
        """SCRD-009: Azure all-locations で _execute_azure_subscription_scan が呼ばれる

        scan_coordinator.py:169-174 の Azure 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.scanRegions = ["all-locations"]

        with patch.object(coordinator, '_prepare_base_credentials',
                          new_callable=AsyncMock, return_value={"key": "val"}) as mock_prep, \
             patch.object(coordinator, '_execute_azure_subscription_scan',
                          new_callable=AsyncMock, return_value={"violations_count": 0}) as mock_azure:
            coordinator.result_processor.aggregate_multi_region_results.return_value = {
                "scan_metadata": {}
            }

            # Act
            result = await coordinator.execute_multi_region_custodian_scan(
                "/tmp", "policies: []", credentials, "azure"
            )

        # Assert
        mock_azure.assert_awaited_once()
        mock_prep.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_aws_normal_regions(self, coordinator):
        """SCRD-010: AWS 通常リージョンで _execute_region_by_region_scan が呼ばれる

        scan_coordinator.py:175-180 の else 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.scanRegions = ["us-east-1", "ap-northeast-1"]

        with patch.object(coordinator, '_prepare_base_credentials',
                          new_callable=AsyncMock, return_value={"key": "val"}), \
             patch.object(coordinator, '_execute_region_by_region_scan',
                          new_callable=AsyncMock, return_value=[]) as mock_region:
            coordinator.result_processor.aggregate_multi_region_results.return_value = {
                "scan_metadata": {}
            }

            # Act
            await coordinator.execute_multi_region_custodian_scan(
                "/tmp", "policies: []", credentials, "aws"
            )

        # Assert
        mock_region.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_account_id_extraction_success(self, coordinator):
        """SCRD-011: 成功した結果から account_id を抽出

        scan_coordinator.py:188-199 の account_id 抽出ループをカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.scanRegions = ["us-east-1"]
        region_result = {"output_dir": "/tmp/output", "violations_count": 0}

        with patch.object(coordinator, '_prepare_base_credentials',
                          new_callable=AsyncMock, return_value={}), \
             patch.object(coordinator, '_execute_region_by_region_scan',
                          new_callable=AsyncMock, return_value=[region_result]):
            coordinator.result_processor.aggregate_multi_region_results.return_value = {
                "scan_metadata": {}
            }
            # 遅延import のモック
            with patch("app.jobs.utils.metadata_extractor.extract_metadata_from_output_dir",
                       return_value={"account_id": "123456789012"}), \
                 patch("app.jobs.utils.metadata_extractor.extract_scan_info_from_metadata",
                       return_value={"account_id": "123456789012"}):
                # Act
                result = await coordinator.execute_multi_region_custodian_scan(
                    "/tmp", "policies: []", credentials, "aws"
                )

        # Assert
        assert result["scan_metadata"]["account_id"] == "123456789012"
```

### 2.6 _prepare_base_credentials テスト

```python
class TestPrepareBaseCredentials:
    """_prepare_base_credentials の3分岐テスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_azure_credentials(self, coordinator):
        """SCRD-012: Azure の場合は auth_handler を使用

        scan_coordinator.py:211-218 の azure 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        coordinator.auth_handler.get_credentials_for_region = AsyncMock(
            return_value={"AZURE_SUBSCRIPTION_ID": "sub-123"}
        )

        # Act
        result = await coordinator._prepare_base_credentials(credentials, "azure")

        # Assert
        assert result == {"AZURE_SUBSCRIPTION_ID": "sub-123"}
        coordinator.auth_handler.get_credentials_for_region.assert_awaited_once_with(
            credentials, "not-applicable", "azure"
        )

    @pytest.mark.asyncio
    async def test_role_assumption_credentials(self, coordinator):
        """SCRD-013: role_assumption の場合は _get_assume_role_credentials を呼ぶ

        scan_coordinator.py:219-221 の role_assumption 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.authType = "role_assumption"

        with patch.object(coordinator, '_get_assume_role_credentials',
                          new_callable=AsyncMock, return_value={"key": "val"}) as mock_assume:
            # Act
            result = await coordinator._prepare_base_credentials(credentials, "aws")

        # Assert
        mock_assume.assert_awaited_once_with(credentials)

    @pytest.mark.asyncio
    async def test_access_key_credentials(self, coordinator):
        """SCRD-014: accessKey の場合は環境変数辞書を直接返す

        scan_coordinator.py:222-227 の else 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.authType = "accessKey"
        credentials.accessKey = "AKIATEST"
        credentials.secretKey = "secret"
        credentials.sessionToken = "token"

        # Act
        result = await coordinator._prepare_base_credentials(credentials, "aws")

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST"
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret"
        assert result["AWS_SESSION_TOKEN"] == "token"
```

### 2.7 _execute_azure_subscription_scan テスト

```python
class TestExecuteAzureSubscriptionScan:
    """_execute_azure_subscription_scan のテスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_success(self, coordinator):
        """SCRD-015: Azure サブスクリプション全体スキャン成功

        scan_coordinator.py:237-247 の正常パスをカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 3}
        )

        # Act
        result = await coordinator._execute_azure_subscription_scan(
            "/tmp", "policies: []", {"key": "val"}, scan_metadata
        )

        # Assert
        assert result == {"violations_count": 3}
        assert scan_metadata["completed_regions"] == 1
```

### 2.8 _execute_region_by_region_scan テスト

```python
class TestExecuteRegionByRegionScan:
    """_execute_region_by_region_scan のポリシー分離テスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_aws_global_and_regional(self, coordinator):
        """SCRD-016: AWS 混合ポリシーでグローバル+リージョナル両方実行

        scan_coordinator.py:274-316 の global_yaml and regional_yaml 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        # グローバル→リージョナル×2の順で呼ばれる（毎回新規 dict を返す）
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=[
                {"violations_count": 1},  # グローバル
                {"violations_count": 0},  # リージョナル us-east-1
                {"violations_count": 2},  # リージョナル ap-northeast-1
            ]
        )

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1", "ap-northeast-1"], "aws", scan_metadata
        )

        # Assert
        # グローバル(1回) + リージョナル(2リージョン) = 3回
        assert coordinator.custodian_executor.execute_single_region_scan.await_count == 3
        assert len(result) == 3
        # グローバル結果にフラグが付く
        assert result[0].get('is_global_scan') is True
        # scan_metadata: 混合分岐では completed_regions = len(scan_regions)、failed_regions は更新されない
        assert scan_metadata["completed_regions"] == 2
        assert scan_metadata["failed_regions"] == 0

    @pytest.mark.asyncio
    async def test_aws_global_only(self, coordinator):
        """SCRD-017: AWS グローバルポリシーのみで us-east-1 実行

        scan_coordinator.py:319-335 の global_yaml のみ分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': ''
        })
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 2}
        )

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1"], "aws", scan_metadata
        )

        # Assert
        assert len(result) == 1
        assert scan_metadata["completed_regions"] == 1

    @pytest.mark.asyncio
    async def test_aws_regional_only(self, coordinator):
        """SCRD-018: AWS リージョナルポリシーのみで全リージョン実行

        scan_coordinator.py:338-354 の regional_yaml のみ分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': '',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 0}
        )

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1", "ap-northeast-1"], "aws", scan_metadata
        )

        # Assert
        assert len(result) == 2
        assert scan_metadata["completed_regions"] == 2

    @pytest.mark.asyncio
    async def test_aws_no_valid_policies(self, coordinator):
        """SCRD-019: AWS 分離後に有効なポリシーがない場合

        scan_coordinator.py:356-357 の else（空ポリシー）分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': '',
            'regional': ''
        })

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1"], "aws", scan_metadata
        )

        # Assert
        assert result == []
        coordinator.logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_non_aws_multi_region(self, coordinator):
        """SCRD-020: 非AWS（GCP等）の通常マルチリージョンスキャン

        scan_coordinator.py:359-380 の else（非AWS）分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 0}
        )

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-central1", "asia-east1"], "gcp", scan_metadata
        )

        # Assert
        assert len(result) == 2
        assert scan_metadata["completed_regions"] == 2

    @pytest.mark.asyncio
    async def test_aws_global_primary_region_us_east_1(self, coordinator):
        """SCRD-023: us-east-1 がリージョンリストにある場合は優先選択

        scan_coordinator.py:279 の us-east-1 in scan_regions 条件をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 0}
        )

        # Act
        await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["ap-northeast-1", "us-east-1"], "aws", scan_metadata
        )

        # Assert
        # 最初の呼び出し（グローバル）が us-east-1 で実行されること
        first_call = coordinator.custodian_executor.execute_single_region_scan.call_args_list[0]
        assert first_call[0][3] == "us-east-1"  # 4番目の位置引数 = region

    @pytest.mark.asyncio
    async def test_aws_global_fallback_first_region(self, coordinator):
        """SCRD-024: us-east-1 がない場合は先頭リージョンを選択

        scan_coordinator.py:279 の else → scan_regions[0] 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 0}
        )

        # Act
        await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["ap-northeast-1", "eu-west-1"], "aws", scan_metadata
        )

        # Assert
        first_call = coordinator.custodian_executor.execute_single_region_scan.call_args_list[0]
        assert first_call[0][3] == "ap-northeast-1"

    @pytest.mark.asyncio
    async def test_aws_global_only_fallback_first_region(self, coordinator):
        """SCRD-025: AWS global-only で us-east-1 がない場合は先頭リージョンを選択

        scan_coordinator.py:320 の global-only 分岐における
        primary_region = scan_regions[0] の else パスをカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': ''
        })
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={"violations_count": 1}
        )

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["ap-northeast-1", "eu-west-1"], "aws", scan_metadata
        )

        # Assert
        assert len(result) == 1
        first_call = coordinator.custodian_executor.execute_single_region_scan.call_args_list[0]
        assert first_call[0][3] == "ap-northeast-1"  # 先頭リージョンが選択される
        assert scan_metadata["completed_regions"] == 1
```

### 2.9 _get_assume_role_credentials テスト

```python
class TestGetAssumeRoleCredentials:
    """_get_assume_role_credentials のテスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_test_role_arn(self, coordinator):
        """SCRD-021: テスト用ARNで模擬認証情報を返す

        scan_coordinator.py:387-397 の テストARN分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.roleArn = "arn:aws:iam::123456789012:role/test-role"
        credentials.externalIdValue = "ext-123"

        # Act
        result = await coordinator._get_assume_role_credentials(credentials)

        # Assert
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST123456789012"
        assert "AWS_SECRET_ACCESS_KEY" in result
        assert "AWS_SESSION_TOKEN" in result

    @pytest.mark.asyncio
    async def test_real_role_arn(self, coordinator):
        """SCRD-022: 実際のARNで auth_handler を呼ぶ

        scan_coordinator.py:399-400 の 実ARN分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.roleArn = "arn:aws:iam::987654321098:role/real-role"
        coordinator.auth_handler.get_credentials_for_region = AsyncMock(
            return_value={"key": "real-creds"}
        )

        # Act
        result = await coordinator._get_assume_role_credentials(credentials)

        # Assert
        coordinator.auth_handler.get_credentials_for_region.assert_awaited_once_with(
            credentials, "us-east-1", "aws"
        )
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SCRD-E01 | _extract_resource_types_from_policy YAML解析例外 | 不正YAML | 空リスト + error ログ |
| SCRD-E02 | _separate_policies_by_scope 例外 | 解析例外 | regional=元YAML |
| SCRD-E03 | _execute_azure_subscription_scan 例外 | スキャン失敗 | error_result + failed_regions=1 |
| SCRD-E04 | _execute_region_by_region_scan リージョン失敗 | 1リージョン例外 | error_result + failed_regions++ |
| SCRD-E05 | account_id 抽出失敗 | metadata 例外 | debug ログ、処理継続 |
| SCRD-E06 | _execute_region_by_region_scan AWS global スキャン失敗（混合） | global 例外 | error_result 追加 |
| SCRD-E07 | _execute_region_by_region_scan AWS regional スキャン失敗（混合） | regional 例外 | error_result 追加 |
| SCRD-E08 | _execute_region_by_region_scan AWS global-only 失敗 | global 例外 | failed_regions=1 |
| SCRD-E09 | _execute_region_by_region_scan AWS regional-only 失敗 | regional 例外 | failed_regions++ |

### 3.1 異常系テスト

```python
class TestScanCoordinatorErrors:
    """異常入力・エラー回復のテスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    def test_extract_yaml_parse_error(self, coordinator):
        """SCRD-E01: YAML解析例外で空リストとエラーログ

        scan_coordinator.py:59-61 の except 分岐をカバー。
        """
        # Arrange
        # yaml.safe_load を例外送出でパッチ（入力文字列に依存しない安定した検証）
        with patch(f"{MODULE}.yaml.safe_load", side_effect=Exception("YAML解析失敗")):
            # Act
            result = coordinator._extract_resource_types_from_policy("any-input")

        # Assert
        assert result == []
        error_log = coordinator.logger.error.call_args[0][0]
        assert "YAML解析失敗" in error_log

    def test_separate_policies_exception(self, coordinator):
        """SCRD-E02: 分離処理例外で regional に元YAMLを返す

        scan_coordinator.py:129-131 の except 分岐をカバー。
        """
        # Arrange
        yaml_content = "policies:\n  - name: test\n    resource: ec2"
        # safe_load がNoneを返すケース（空YAML相当）で 'policies' not in None → TypeError
        with patch(f"{MODULE}.yaml.safe_load", return_value=None):
            # Act
            result = coordinator._separate_policies_by_scope(yaml_content)

        # Assert
        assert result['global'] == ''
        assert result['regional'] == yaml_content

    @pytest.mark.asyncio
    async def test_azure_scan_exception(self, coordinator):
        """SCRD-E03: Azure スキャン失敗で error_result を返す

        scan_coordinator.py:249-252 の except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=RuntimeError("Azure接続失敗")
        )
        coordinator.result_processor.create_error_result.return_value = {"error": "接続失敗"}

        # Act
        result = await coordinator._execute_azure_subscription_scan(
            "/tmp", "yaml", {}, scan_metadata
        )

        # Assert
        assert scan_metadata["failed_regions"] == 1
        coordinator.result_processor.create_error_result.assert_called_once_with(
            "all-locations", "Azure接続失敗"
        )

    @pytest.mark.asyncio
    async def test_region_scan_failure(self, coordinator):
        """SCRD-E04: 非AWS リージョンスキャン失敗で error_result 追加

        scan_coordinator.py:375-380 の except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=RuntimeError("リージョン接続エラー")
        )
        coordinator.result_processor.create_error_result.return_value = {"error": "接続エラー"}

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1"], "gcp", scan_metadata
        )

        # Assert
        assert scan_metadata["failed_regions"] == 1
        assert len(result) == 1
        coordinator.result_processor.create_error_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_account_id_extraction_failure(self, coordinator):
        """SCRD-E05: account_id 抽出失敗で debug ログ、処理継続

        scan_coordinator.py:200-201 の except 分岐をカバー。
        """
        # Arrange
        credentials = MagicMock()
        credentials.scanRegions = ["us-east-1"]
        region_result = {"output_dir": "/tmp/output"}

        with patch.object(coordinator, '_prepare_base_credentials',
                          new_callable=AsyncMock, return_value={}), \
             patch.object(coordinator, '_execute_region_by_region_scan',
                          new_callable=AsyncMock, return_value=[region_result]):
            coordinator.result_processor.aggregate_multi_region_results.return_value = {
                "scan_metadata": {}
            }
            with patch("app.jobs.utils.metadata_extractor.extract_metadata_from_output_dir",
                       side_effect=Exception("メタデータ取得失敗")):
                # Act
                result = await coordinator.execute_multi_region_custodian_scan(
                    "/tmp", "yaml", credentials, "aws"
                )

        # Assert（例外が伝播せず、結果が返ること）
        assert "scan_metadata" in result
        coordinator.logger.debug.assert_called()

    @pytest.mark.asyncio
    async def test_aws_global_scan_failure(self, coordinator):
        """SCRD-E06: AWS グローバルスキャン失敗で error_result 追加

        scan_coordinator.py:290-293 の except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        # 最初のグローバル呼び出しで失敗、リージョナルは成功
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=[RuntimeError("グローバルスキャン失敗"), {"violations_count": 0}]
        )
        coordinator.result_processor.create_error_result.return_value = {"error": "失敗"}

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1"], "aws", scan_metadata
        )

        # Assert
        # グローバル失敗(1) + リージョナル成功(1) = 2結果
        assert len(result) == 2
        coordinator.result_processor.create_error_result.assert_called_once()
        # scan_metadata: 混合分岐では failed_regions は except 内で更新されない（L290-293）
        assert scan_metadata["completed_regions"] == 1  # len(scan_regions)
        assert scan_metadata["failed_regions"] == 0  # except ブロック内で更新なし

    @pytest.mark.asyncio
    async def test_aws_mixed_regional_scan_failure(self, coordinator):
        """SCRD-E07: AWS 混合ポリシーでリージョナルスキャン失敗

        scan_coordinator.py:308-311 の リージョナルループ内 except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        # グローバル成功 → リージョナル失敗
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=[{"violations_count": 0}, RuntimeError("リージョナル失敗")]
        )
        coordinator.result_processor.create_error_result.return_value = {"error": "失敗"}

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1"], "aws", scan_metadata
        )

        # Assert
        # グローバル成功(1) + リージョナル失敗(1) = 2結果
        assert len(result) == 2
        coordinator.result_processor.create_error_result.assert_called_once_with(
            "us-east-1", "リージョナル失敗"
        )
        # scan_metadata: 混合分岐では failed_regions は except 内で更新されない（L308-311）
        assert scan_metadata["completed_regions"] == 1  # len(scan_regions)
        assert scan_metadata["failed_regions"] == 0  # except ブロック内で更新なし

    @pytest.mark.asyncio
    async def test_aws_global_only_scan_failure(self, coordinator):
        """SCRD-E08: AWS global-only スキャン失敗で failed_regions 設定

        scan_coordinator.py:331-335 の global-only except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': 'policies:\n  - name: iam\n    resource: iam-role\n',
            'regional': ''
        })
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=RuntimeError("グローバル失敗")
        )
        coordinator.result_processor.create_error_result.return_value = {"error": "失敗"}

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1"], "aws", scan_metadata
        )

        # Assert
        assert len(result) == 1
        assert scan_metadata["failed_regions"] == 1
        coordinator.result_processor.create_error_result.assert_called_once_with(
            "us-east-1", "グローバル失敗"
        )

    @pytest.mark.asyncio
    async def test_aws_regional_only_scan_failure(self, coordinator):
        """SCRD-E09: AWS regional-only スキャン失敗で failed_regions インクリメント

        scan_coordinator.py:350-354 の regional-only except 分岐をカバー。
        """
        # Arrange
        scan_metadata = {"completed_regions": 0, "failed_regions": 0}
        coordinator._separate_policies_by_scope = MagicMock(return_value={
            'global': '',
            'regional': 'policies:\n  - name: ec2\n    resource: ec2\n'
        })
        # 1リージョン目は成功、2リージョン目は失敗
        coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=[{"violations_count": 0}, RuntimeError("リージョン失敗")]
        )
        coordinator.result_processor.create_error_result.return_value = {"error": "失敗"}

        # Act
        result = await coordinator._execute_region_by_region_scan(
            "/tmp", "yaml", {}, ["us-east-1", "ap-northeast-1"], "aws", scan_metadata
        )

        # Assert
        assert len(result) == 2
        assert scan_metadata["completed_regions"] == 1
        assert scan_metadata["failed_regions"] == 1
        coordinator.result_processor.create_error_result.assert_called_once_with(
            "ap-northeast-1", "リージョン失敗"
        )
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| SCRD-SEC-01 | yaml.safe_load を使用 | 悪意のあるYAML | safe_load で安全に解析 |
| SCRD-SEC-02 | エラーログが str(e) 形式 | 各 except ブロック | フォーマット化された出力 |
| SCRD-SEC-03 | roleArn のログ出力が50文字で切り詰め | 長いARN | 切り詰め+省略符号 |

### 4.1 セキュリティテスト

```python
@pytest.mark.security
class TestScanCoordinatorSecurity:
    """セキュリティ関連テスト"""

    @pytest.fixture
    def coordinator(self):
        with patch(f"{MODULE}.TaskLogger"), \
             patch(f"{MODULE}.AuthenticationHandler"), \
             patch(f"{MODULE}.CustodianExecutor"), \
             patch(f"{MODULE}.ResultProcessor"), \
             patch(f"{MODULE}.CustodianLogAnalyzer"):
            from app.jobs.tasks.new_custodian_scan.scan_coordinator import ScanCoordinator
            instance = ScanCoordinator("test-job")
        instance.logger = MagicMock()
        return instance

    def test_yaml_safe_load_used(self, coordinator):
        """SCRD-SEC-01: _extract_resource_types_from_policy が yaml.safe_load を使用

        scan_coordinator.py:49 の yaml.safe_load 使用を代表検証。
        yaml.load（unsafe）ではなく safe_load でデシリアライゼーション攻撃を防止。
        _separate_policies_by_scope（L96）も同一パターンで safe_load を使用する。
        """
        # Arrange
        yaml_content = "policies: []"

        with patch(f"{MODULE}.yaml.safe_load", return_value={"policies": []}) as mock_safe:
            # Act
            coordinator._extract_resource_types_from_policy(yaml_content)

        # Assert
        mock_safe.assert_called_once_with(yaml_content)

    def test_error_log_format(self, coordinator):
        """SCRD-SEC-02: エラーログが所定プレフィックス + str(e) 形式で出力

        scan_coordinator.py:60 の logger.error を代表検証。
        他の except ブロック（L130, L250 等）でも同様のパターンを使用。
        """
        # Arrange
        with patch(f"{MODULE}.yaml.safe_load", side_effect=Exception("test-error-msg")):
            # Act
            coordinator._extract_resource_types_from_policy("dummy")

        # Assert
        error_log = coordinator.logger.error.call_args[0][0]
        assert "ポリシーYAMLからのリソースタイプ抽出に失敗:" in error_log
        assert "test-error-msg" in error_log

    @pytest.mark.asyncio
    async def test_role_arn_truncated_in_log(self, coordinator):
        """SCRD-SEC-03: 長い roleArn がログ出力で50文字に切り詰められる

        scan_coordinator.py:389 の role_arn 切り詰めロジックを検証。
        長い ARN がログに全文記録されないことでセキュリティリスクを低減。
        """
        # Arrange
        credentials = MagicMock()
        credentials.roleArn = "arn:aws:iam::123456789012:role/very-long-role-name-that-exceeds-fifty-characters-limit"
        credentials.externalIdValue = "ext-123"

        # Act
        await coordinator._get_assume_role_credentials(credentials)

        # Assert
        log_call = coordinator.logger.info.call_args
        context = log_call[1]["context"]
        assert len(context["role_arn"]) <= 53  # 50文字 + "..."
        assert context["role_arn"].endswith("...")
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `coordinator` | 全依存をモック化した ScanCoordinator（各テストクラス内で定義） | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/new_custodian_scan/conftest.py に追加（必要に応じて）
#
# coordinator フィクスチャの共通パターン:
#   MODULE = "app.jobs.tasks.new_custodian_scan.scan_coordinator"
#   with patch(f"{MODULE}.TaskLogger"), \
#        patch(f"{MODULE}.AuthenticationHandler"), \
#        patch(f"{MODULE}.CustodianExecutor"), \
#        patch(f"{MODULE}.ResultProcessor"), \
#        patch(f"{MODULE}.CustodianLogAnalyzer"):
#       instance = ScanCoordinator("test-job")
#   instance.logger = MagicMock()  # アサーション用に差し替え
#
# 注: log_analyzer は _determine_resource_scope メソッドが
#     モック化されるため、スコープ判定の返り値を side_effect で制御する。
```

---

## 6. テスト実行例

```bash
# scan_coordinator テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_scan_coordinator.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_scan_coordinator.py::TestExecuteRegionByRegionScan -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_scan_coordinator.py \
  --cov=app.jobs.tasks.new_custodian_scan.scan_coordinator \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_scan_coordinator.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 25 | SCRD-001〜SCRD-025 |
| 異常系 | 9 | SCRD-E01〜SCRD-E09 |
| セキュリティ | 3 | SCRD-SEC-01〜SCRD-SEC-03 |
| **合計** | **37** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestScanCoordinatorInit` | SCRD-001 | 1 |
| `TestExtractResourceTypes` | SCRD-002〜004 | 3 |
| `TestHasGlobalResources` | SCRD-005〜006 | 2 |
| `TestSeparatePoliciesByScope` | SCRD-007〜008 | 2 |
| `TestExecuteMultiRegionCustodianScan` | SCRD-009〜011 | 3 |
| `TestPrepareBaseCredentials` | SCRD-012〜014 | 3 |
| `TestExecuteAzureSubscriptionScan` | SCRD-015 | 1 |
| `TestExecuteRegionByRegionScan` | SCRD-016〜020, 023〜025 | 8 |
| `TestGetAssumeRoleCredentials` | SCRD-021〜022 | 2 |
| `TestScanCoordinatorErrors` | SCRD-E01〜E09 | 9 |
| `TestScanCoordinatorSecurity` | SCRD-SEC-01〜SCRD-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> 全メソッドの依存をモックするため、実装の内部ロジックのみを検証。外部サービスの状態に依存しない安定したテスト設計。

### 注意事項

- 全 async メソッドのテストに `pytest-asyncio` パッケージが必要
- `--strict-markers` 運用時は `@pytest.mark.security` を `pyproject.toml` に登録
- `_determine_resource_scope` は `log_analyzer` のモック経由で制御（`side_effect` でグローバル/リージョナルを返す）
- `metadata_extractor` は遅延 import（L192）のため、定義元モジュール `app.jobs.utils.metadata_extractor` を patch
- `yaml.safe_load` の patch 先は `f"{MODULE}.yaml.safe_load"` （モジュールレベル import のため）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `_execute_region_by_region_scan` は複雑な条件分岐（AWS: 4パターン + 非AWS: 1パターン）を持つため、テストの組み合わせが多い | テストケース数が多くなる | 各分岐パターンを独立したテストケースとし、`_separate_policies_by_scope` をモックして入力を制御 |
| 2 | `_has_global_resources` と `_separate_policies_by_scope` は `log_analyzer._determine_resource_scope` に依存する | スコープ判定ロジック自体はテスト対象外 | `_determine_resource_scope` の返り値をモックで制御し、呼び出しのみ検証 |
| 3 | `_get_assume_role_credentials` のテストARN判定（L387）はハードコードされたプレフィックス比較 | 実際の AssumeRole フローは未テスト | 統合テストで実際の AssumeRole フローを検証 |
