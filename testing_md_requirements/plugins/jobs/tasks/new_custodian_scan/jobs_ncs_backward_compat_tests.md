# jobs/tasks/new_custodian_scan/custodian_executor + backward_compat テストケース

## 1. 概要

`custodian_executor.py` は `CustodianExecutor` クラスの再エクスポートモジュール（互換性レイヤー）です。`backward_compat.py` は `BackwardCompatMixin` クラスを提供し、旧インターフェースから新モジュール構造への委譲メソッド6つを実装します。

### 1.1 主要機能

| メソッド/モジュール | ファイル | 説明 |
|-------------------|---------|------|
| `CustodianExecutor` 再エクスポート | `custodian_executor.py` | `.executor.CustodianExecutor` のインポート互換性維持 |
| `_parse_credentials_payload` (async) | `backward_compat.py` | `credential_processor.parse_credentials_payload` への委譲 |
| `_validate_inputs` | `backward_compat.py` | `credential_processor.validate_inputs` への委譲 |
| `_execute_multi_region_custodian_scan` (async) | `backward_compat.py` | `scan_coordinator.execute_multi_region_custodian_scan` への委譲 |
| `_execute_single_region_scan` (async) | `backward_compat.py` | `scan_coordinator.custodian_executor.execute_single_region_scan` への委譲 |
| `_get_assume_role_credentials` (async) | `backward_compat.py` | `scan_coordinator._get_assume_role_credentials` への委譲 |
| `_assume_role_and_get_credentials` (async) | `backward_compat.py` | `_get_assume_role_credentials` への自己委譲 |

### 1.2 カバレッジ目標: 95%

> **注記**: 全メソッドが薄いラッパーのため、高カバレッジが容易に達成可能。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/jobs/tasks/new_custodian_scan/custodian_executor.py` |
| テスト対象2 | `app/jobs/tasks/new_custodian_scan/backward_compat.py` |
| テストコード | `test/unit/jobs/tasks/new_custodian_scan/test_backward_compat.py` |

### 1.4 補足情報

#### BackwardCompatMixin の利用パターン

```
BackwardCompatMixin は Mixin クラスであり、単独ではインスタンス化されない。
使用側クラスが以下の属性を提供する前提:
  - self.credential_processor  → CredentialProcessor インスタンス
  - self.scan_coordinator       → ScanCoordinator インスタンス
```

#### 委譲先一覧

| メソッド | 委譲先 |
|---------|--------|
| `_parse_credentials_payload` | `self.credential_processor.parse_credentials_payload` |
| `_validate_inputs` | `self.credential_processor.validate_inputs` |
| `_execute_multi_region_custodian_scan` | `self.scan_coordinator.execute_multi_region_custodian_scan` |
| `_execute_single_region_scan` | `self.scan_coordinator.custodian_executor.execute_single_region_scan` |
| `_get_assume_role_credentials` | `self.scan_coordinator._get_assume_role_credentials` |
| `_assume_role_and_get_credentials` | `self._get_assume_role_credentials` (自己委譲) |

#### 非同期メソッド（pytest-asyncio必要）

5つ: `_parse_credentials_payload`, `_execute_multi_region_custodian_scan`, `_execute_single_region_scan`, `_get_assume_role_credentials`, `_assume_role_and_get_credentials`

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCCE-001 | CustodianExecutor再エクスポート成功 | import | CustodianExecutorクラスが取得可能 |
| NCCE-002 | __all__にCustodianExecutor含む | __all__参照 | ['CustodianExecutor'] |
| NCBC-001 | _parse_credentials_payload委譲 | credentials_data, cloud_provider | credential_processor.parse_credentials_payloadに委譲 |
| NCBC-002 | _validate_inputs委譲 | policy, credentials, provider | credential_processor.validate_inputsに委譲 |
| NCBC-003 | _execute_multi_region_custodian_scan委譲 | temp_dir, yaml, creds, provider | scan_coordinator.execute_multi_region_custodian_scanに委譲 |
| NCBC-004 | _execute_single_region_scan委譲 | 全引数指定 | scan_coordinator.custodian_executor.execute_single_region_scanに委譲 |
| NCBC-005 | _execute_single_region_scanデフォルト引数 | region_index/cloud_provider省略 | デフォルト値0/"aws"で委譲 |
| NCBC-006 | _get_assume_role_credentials委譲 | credentials | scan_coordinator._get_assume_role_credentialsに委譲 |
| NCBC-007 | _assume_role_and_get_credentials自己委譲 | credentials | _get_assume_role_credentialsに委譲 |

### 2.1 custodian_executor.py テスト

```python
# test/unit/jobs/tasks/new_custodian_scan/test_backward_compat.py
import pytest
from unittest.mock import MagicMock, AsyncMock


class TestCustodianExecutorReexport:
    """custodian_executor.py 再エクスポートテスト"""

    def test_import_custodian_executor(self):
        """NCCE-001: CustodianExecutor再エクスポート成功

        custodian_executor.py:10 のインポートが正常に動作し、
        executor パッケージの CustodianExecutor と同一クラスであることを検証。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan.custodian_executor import CustodianExecutor
        from app.jobs.tasks.new_custodian_scan.executor import CustodianExecutor as ActualExecutor

        # Assert（再エクスポートされたクラスが元クラスと同一であること）
        assert CustodianExecutor is ActualExecutor

    def test_all_contains_custodian_executor(self):
        """NCCE-002: __all__にCustodianExecutor含む

        custodian_executor.py:13 の__all__定義を検証。
        """
        # Act
        from app.jobs.tasks.new_custodian_scan import custodian_executor

        # Assert
        assert '__all__' in dir(custodian_executor)
        assert 'CustodianExecutor' in custodian_executor.__all__
```

### 2.2 BackwardCompatMixin テスト

```python
class TestBackwardCompatMixinDelegation:
    """BackwardCompatMixin委譲テスト"""

    @pytest.fixture
    def mixin_instance(self):
        """BackwardCompatMixinを持つモックホストクラスを作成"""
        from app.jobs.tasks.new_custodian_scan.backward_compat import BackwardCompatMixin

        # Mixinをホストクラスに適用
        class MockHost(BackwardCompatMixin):
            pass

        instance = MockHost()
        # Mixinが期待する属性をモックで設定
        instance.credential_processor = MagicMock()
        instance.scan_coordinator = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_parse_credentials_payload_delegates(self, mixin_instance):
        """NCBC-001: _parse_credentials_payload委譲

        backward_compat.py:23-25 のcredential_processor.parse_credentials_payloadへの委譲を検証。
        """
        # Arrange
        expected = MagicMock()
        mixin_instance.credential_processor.parse_credentials_payload = AsyncMock(
            return_value=expected
        )
        creds_data = {"authType": "secret_key", "accessKey": "test"}

        # Act
        result = await mixin_instance._parse_credentials_payload(creds_data, "aws")

        # Assert
        assert result is expected
        mixin_instance.credential_processor.parse_credentials_payload.assert_called_once_with(
            creds_data, "aws"
        )

    def test_validate_inputs_delegates(self, mixin_instance):
        """NCBC-002: _validate_inputs委譲

        backward_compat.py:34-36 のcredential_processor.validate_inputsへの委譲を検証。
        """
        # Arrange
        mock_creds = MagicMock()

        # Act
        mixin_instance._validate_inputs("policies:\n  - name: test", mock_creds, "aws")

        # Assert
        mixin_instance.credential_processor.validate_inputs.assert_called_once_with(
            "policies:\n  - name: test", mock_creds, "aws"
        )

    @pytest.mark.asyncio
    async def test_execute_multi_region_delegates(self, mixin_instance):
        """NCBC-003: _execute_multi_region_custodian_scan委譲

        backward_compat.py:46-48 のscan_coordinator.execute_multi_region_custodian_scanへの委譲を検証。
        """
        # Arrange
        expected = {"status": "completed", "regions": 2}
        mixin_instance.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(
            return_value=expected
        )
        mock_creds = MagicMock()

        # Act
        result = await mixin_instance._execute_multi_region_custodian_scan(
            "/tmp/work", "policies:\n  - name: test", mock_creds, "aws"
        )

        # Assert
        assert result is expected
        mixin_instance.scan_coordinator.execute_multi_region_custodian_scan.assert_called_once_with(
            "/tmp/work", "policies:\n  - name: test", mock_creds, "aws"
        )

    @pytest.mark.asyncio
    async def test_execute_single_region_delegates(self, mixin_instance):
        """NCBC-004: _execute_single_region_scan委譲

        backward_compat.py:60-62 のscan_coordinator.custodian_executor.execute_single_region_scanへの委譲を検証。
        全引数を明示的に指定するケース。
        """
        # Arrange
        expected = {"region": "us-east-1", "return_code": 0}
        mixin_instance.scan_coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value=expected
        )
        aws_creds = {"AWS_ACCESS_KEY_ID": "test", "AWS_SECRET_ACCESS_KEY": "secret"}

        # Act
        result = await mixin_instance._execute_single_region_scan(
            "/tmp/work", "policies:\n  - name: test", aws_creds, "eu-west-1", 2, "aws"
        )

        # Assert
        assert result is expected
        mixin_instance.scan_coordinator.custodian_executor.execute_single_region_scan.assert_called_once_with(
            "/tmp/work", "policies:\n  - name: test", aws_creds, "eu-west-1", 2, "aws"
        )

    @pytest.mark.asyncio
    async def test_execute_single_region_default_params(self, mixin_instance):
        """NCBC-005: _execute_single_region_scanデフォルト引数

        backward_compat.py:56-57 のregion_index=0, cloud_provider="aws"デフォルト値を検証。
        """
        # Arrange
        mixin_instance.scan_coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            return_value={}
        )

        # Act
        await mixin_instance._execute_single_region_scan(
            "/tmp/work", "policies:", {}, "us-east-1"
        )

        # Assert（デフォルト値 region_index=0, cloud_provider="aws" が渡される）
        mixin_instance.scan_coordinator.custodian_executor.execute_single_region_scan.assert_called_once_with(
            "/tmp/work", "policies:", {}, "us-east-1", 0, "aws"
        )

    @pytest.mark.asyncio
    async def test_get_assume_role_credentials_delegates(self, mixin_instance):
        """NCBC-006: _get_assume_role_credentials委譲

        backward_compat.py:66 のscan_coordinator._get_assume_role_credentialsへの委譲を検証。
        """
        # Arrange
        expected = {"AWS_ACCESS_KEY_ID": "temp", "AWS_SECRET_ACCESS_KEY": "temp_secret"}
        mixin_instance.scan_coordinator._get_assume_role_credentials = AsyncMock(
            return_value=expected
        )
        mock_creds = MagicMock()

        # Act
        result = await mixin_instance._get_assume_role_credentials(mock_creds)

        # Assert
        assert result is expected
        mixin_instance.scan_coordinator._get_assume_role_credentials.assert_called_once_with(
            mock_creds
        )

    @pytest.mark.asyncio
    async def test_assume_role_and_get_credentials_self_delegates(self, mixin_instance):
        """NCBC-007: _assume_role_and_get_credentials自己委譲

        backward_compat.py:70 の_get_assume_role_credentialsへの自己委譲を検証。
        """
        # Arrange
        expected = {"AWS_ACCESS_KEY_ID": "assumed"}
        mixin_instance._get_assume_role_credentials = AsyncMock(return_value=expected)
        mock_creds = MagicMock()

        # Act
        result = await mixin_instance._assume_role_and_get_credentials(mock_creds)

        # Assert
        assert result is expected
        mixin_instance._get_assume_role_credentials.assert_called_once_with(mock_creds)
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCBC-E01 | 委譲先例外がそのまま伝播（async） | credential_processorが例外送出 | 同じ例外が呼び出し元に伝播 |
| NCBC-E02 | 委譲先属性未設定 | credential_processor=None | AttributeError |
| NCBC-E03 | 委譲先例外がそのまま伝播（sync） | validate_inputsが例外送出 | 同じ例外が呼び出し元に伝播 |
| NCBC-E04 | _execute_multi_region例外伝播 | scan_coordinatorが例外送出 | 同じ例外が呼び出し元に伝播 |
| NCBC-E05 | _execute_single_region例外伝播 | custodian_executorが例外送出 | 同じ例外が呼び出し元に伝播 |
| NCBC-E06 | _get_assume_role_credentials例外伝播 | scan_coordinatorが例外送出 | 同じ例外が呼び出し元に伝播 |
| NCBC-E07 | _assume_role_and_get_credentials例外伝播 | _get_assume_role_credentialsが例外送出 | 同じ例外が呼び出し元に伝播 |

### 3.1 例外伝播テスト

```python
class TestBackwardCompatMixinErrors:
    """BackwardCompatMixinエラーテスト"""

    @pytest.fixture
    def mixin_instance(self):
        from app.jobs.tasks.new_custodian_scan.backward_compat import BackwardCompatMixin

        class MockHost(BackwardCompatMixin):
            pass

        instance = MockHost()
        instance.credential_processor = MagicMock()
        instance.scan_coordinator = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_delegate_exception_propagates(self, mixin_instance):
        """NCBC-E01: 委譲先例外がそのまま伝播

        backward_compat.py:23-25 の委譲先が例外を投げた場合、
        ラッパーがtry/exceptしないため、そのまま呼び出し元に伝播することを検証。
        """
        # Arrange
        mixin_instance.credential_processor.parse_credentials_payload = AsyncMock(
            side_effect=ValueError("invalid credentials format")
        )

        # Act & Assert
        with pytest.raises(ValueError, match="invalid credentials format"):
            await mixin_instance._parse_credentials_payload({"bad": "data"}, "aws")

    def test_validate_inputs_exception_propagates(self, mixin_instance):
        """NCBC-E03: 同期メソッド_validate_inputsの例外伝播

        backward_compat.py:34-36 の同期ラッパーが委譲先の例外をそのまま伝播することを検証。
        """
        # Arrange
        mixin_instance.credential_processor.validate_inputs.side_effect = ValueError(
            "invalid policy content"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="invalid policy content"):
            mixin_instance._validate_inputs("", MagicMock(), "aws")

    @pytest.mark.asyncio
    async def test_missing_attribute_raises_error(self, mixin_instance):
        """NCBC-E02: 委譲先属性未設定

        credential_processorがNoneの場合、属性アクセスでAttributeErrorが発生することを検証。
        """
        # Arrange
        mixin_instance.credential_processor = None

        # Act & Assert
        with pytest.raises(AttributeError):
            await mixin_instance._parse_credentials_payload({}, "aws")

    @pytest.mark.asyncio
    async def test_execute_multi_region_exception_propagates(self, mixin_instance):
        """NCBC-E04: _execute_multi_region_custodian_scan例外伝播

        backward_compat.py:46-48 の委譲先例外がそのまま伝播することを検証。
        """
        # Arrange
        mixin_instance.scan_coordinator.execute_multi_region_custodian_scan = AsyncMock(
            side_effect=RuntimeError("scan coordinator error")
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="scan coordinator error"):
            await mixin_instance._execute_multi_region_custodian_scan(
                "/tmp", "policies:", MagicMock(), "aws"
            )

    @pytest.mark.asyncio
    async def test_execute_single_region_exception_propagates(self, mixin_instance):
        """NCBC-E05: _execute_single_region_scan例外伝播

        backward_compat.py:60-62 の委譲先例外がそのまま伝播することを検証。
        """
        # Arrange
        mixin_instance.scan_coordinator.custodian_executor.execute_single_region_scan = AsyncMock(
            side_effect=ConnectionError("region unavailable")
        )

        # Act & Assert
        with pytest.raises(ConnectionError, match="region unavailable"):
            await mixin_instance._execute_single_region_scan(
                "/tmp", "policies:", {}, "us-east-1"
            )

    @pytest.mark.asyncio
    async def test_get_assume_role_exception_propagates(self, mixin_instance):
        """NCBC-E06: _get_assume_role_credentials例外伝播

        backward_compat.py:66 の委譲先例外がそのまま伝播することを検証。
        """
        # Arrange
        mixin_instance.scan_coordinator._get_assume_role_credentials = AsyncMock(
            side_effect=PermissionError("AssumeRole denied")
        )

        # Act & Assert
        with pytest.raises(PermissionError, match="AssumeRole denied"):
            await mixin_instance._get_assume_role_credentials(MagicMock())

    @pytest.mark.asyncio
    async def test_assume_role_and_get_exception_propagates(self, mixin_instance):
        """NCBC-E07: _assume_role_and_get_credentials例外伝播

        backward_compat.py:70 の自己委譲ラッパーが例外をそのまま伝播することを検証。
        """
        # Arrange
        mixin_instance._get_assume_role_credentials = AsyncMock(
            side_effect=PermissionError("role assumption failed")
        )

        # Act & Assert
        with pytest.raises(PermissionError, match="role assumption failed"):
            await mixin_instance._assume_role_and_get_credentials(MagicMock())
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| NCBC-SEC-01 | 認証情報がラッパー内で改変されない | credentials_data | 委譲先に渡された値が元の値と一致 |
| NCBC-SEC-02 | 戻り値がラッパー内で改変されない | 委譲先の戻り値 | 返却された値が元の値と一致 |
| NCBC-SEC-03 | AssumeRole認証チェーンが_get経由 | credentials | _get_assume_role_credentialsを経由して結果返却 |

```python
@pytest.mark.security
class TestBackwardCompatSecurity:
    """BackwardCompatMixinセキュリティテスト"""

    @pytest.fixture
    def mixin_instance(self):
        from app.jobs.tasks.new_custodian_scan.backward_compat import BackwardCompatMixin

        class MockHost(BackwardCompatMixin):
            pass

        instance = MockHost()
        instance.credential_processor = MagicMock()
        instance.scan_coordinator = MagicMock()
        return instance

    @pytest.mark.asyncio
    async def test_credentials_not_modified_by_wrapper(self, mixin_instance):
        """NCBC-SEC-01: 認証情報がラッパー内で改変されない

        backward_compat.py:23-25 のラッパーが認証情報の内容を改変せずに
        委譲先に渡すことを検証。参照同一性ではなく値の一致で検証し、
        将来の正規化やコピー処理追加にも耐えるテスト設計。
        """
        # Arrange
        original_data = {"authType": "secret_key", "accessKey": "AKIA_TEST"}
        expected = MagicMock()
        mixin_instance.credential_processor.parse_credentials_payload = AsyncMock(
            return_value=expected
        )

        # Act
        await mixin_instance._parse_credentials_payload(original_data, "aws")

        # Assert（渡された値が元のデータと一致すること）
        call_args = mixin_instance.credential_processor.parse_credentials_payload.call_args
        passed_data = call_args[0][0]
        assert passed_data == original_data  # 値の一致で検証（コピーされても安全）
        assert passed_data["authType"] == "secret_key"
        assert passed_data["accessKey"] == "AKIA_TEST"

    @pytest.mark.asyncio
    async def test_return_value_not_modified_by_wrapper(self, mixin_instance):
        """NCBC-SEC-02: 戻り値がラッパー内で改変されない

        各委譲メソッドが戻り値の内容を変更せずに返すことを検証。
        ラッパーが中間処理で機密情報を変更しないことの保証。
        値の一致で検証し、将来のコピー処理にも耐える設計。
        """
        # Arrange
        original_result = {"AWS_ACCESS_KEY_ID": "AKIATEST", "AWS_SECRET_ACCESS_KEY": "secret"}
        mixin_instance.scan_coordinator._get_assume_role_credentials = AsyncMock(
            return_value=original_result
        )
        mock_creds = MagicMock()

        # Act
        result = await mixin_instance._get_assume_role_credentials(mock_creds)

        # Assert（戻り値の内容が一致すること）
        assert result == original_result  # 値の一致で検証
        assert result["AWS_ACCESS_KEY_ID"] == "AKIATEST"
        assert result["AWS_SECRET_ACCESS_KEY"] == "secret"

    @pytest.mark.asyncio
    async def test_assume_role_chain_via_get_method(self, mixin_instance):
        """NCBC-SEC-03: AssumeRole認証チェーンが_get_assume_role_credentialsを経由

        backward_compat.py:68-70 の_assume_role_and_get_credentials が
        _get_assume_role_credentials を経由して呼び出されることを検証。
        直接scan_coordinatorを呼ぶのではなく、中間メソッドを経由することを確認。
        """
        # Arrange
        expected_creds = {"AWS_ACCESS_KEY_ID": "assumed_key", "AWS_SECRET_ACCESS_KEY": "assumed_secret"}
        mock_input_creds = MagicMock()

        # _get_assume_role_credentialsをスパイ（呼び出しを記録しつつ委譲先を実行）
        mixin_instance.scan_coordinator._get_assume_role_credentials = AsyncMock(
            return_value=expected_creds
        )
        spy_get = AsyncMock(wraps=mixin_instance._get_assume_role_credentials)
        mixin_instance._get_assume_role_credentials = spy_get

        # Act
        result = await mixin_instance._assume_role_and_get_credentials(mock_input_creds)

        # Assert（_get_assume_role_credentialsを経由したことを検証）
        spy_get.assert_called_once_with(mock_input_creds)
        assert result == expected_creds
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `mixin_instance` | BackwardCompatMixinを適用したモックホストクラスインスタンス | function | No |

### フィクスチャ方針

```python
# フィクスチャ方針（各テストクラス内で個別に定義。conftest.pyへの追加は不要）:
# - BackwardCompatMixinはMixinクラスのため、テスト用ホストクラス（MockHost）を定義して適用。
# - MockHostにcredential_processorとscan_coordinatorをMagicMockで設定。
# - 各テストクラスでmixin_instanceフィクスチャを個別に定義。
# - asyncメソッド5つのテストには @pytest.mark.asyncio が必要。
# - custodian_executor.pyのテストはインポートテストのみのため、フィクスチャ不要。
```

---

## 6. テスト実行例

```bash
# backward_compat関連テストのみ実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_backward_compat.py -v

# 特定クラスのみ
pytest test/unit/jobs/tasks/new_custodian_scan/test_backward_compat.py::TestCustodianExecutorReexport -v

# カバレッジ付き（両ファイル）
pytest test/unit/jobs/tasks/new_custodian_scan/test_backward_compat.py \
  --cov=app.jobs.tasks.new_custodian_scan.custodian_executor \
  --cov=app.jobs.tasks.new_custodian_scan.backward_compat \
  --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/new_custodian_scan/test_backward_compat.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 9 | NCCE-001〜NCCE-002, NCBC-001〜NCBC-007 |
| 異常系 | 7 | NCBC-E01〜NCBC-E07 |
| セキュリティ | 3 | NCBC-SEC-01〜NCBC-SEC-03 |
| **合計** | **19** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCustodianExecutorReexport` | NCCE-001〜NCCE-002 | 2 |
| `TestBackwardCompatMixinDelegation` | NCBC-001〜NCBC-007 | 7 |
| `TestBackwardCompatMixinErrors` | NCBC-E01〜NCBC-E07 | 7 |
| `TestBackwardCompatSecurity` | NCBC-SEC-01〜NCBC-SEC-03 | 3 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 確定対応手順 |
|---------|------|-------------|
| NCCE-001 | `executor`パッケージの`CustodianExecutor`インポート時に、パッケージ内の連鎖インポート（`executor/main.py` → `CustodianCommandBuilder`, `ResultProcessor`, `CustodianLogAnalyzer`, `SubprocessRunner`等）で未解決の依存がある場合ImportErrorが発生する可能性 | テスト実行環境に必要な依存がインストールされていることを確認。または`executor/__init__.py`のインポートをパッチ |

### 注意事項

- `BackwardCompatMixin`はMixinクラスのため、テスト用ホストクラス（`MockHost`）を作成して適用
- `_validate_inputs`以外の5メソッドはasync → `@pytest.mark.asyncio`必須
- 全6メソッドがtry/exceptなしの薄いラッパーのため、例外は委譲先からそのまま伝播（NCBC-E01〜E07で全メソッド検証済み）
- テストIDプレフィックス: `NCCE`（custodian_executor用）、`NCBC`（backward_compat用）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `custodian_executor.py`は再エクスポートのみで実質ロジックなし | テスト価値が限定的（インポートテストのみ） | 互換性レイヤーとしての存在を検証する最小限のテストで対応 |
| 2 | `BackwardCompatMixin`の各メソッドにtry/exceptがない | 委譲先の例外がそのまま伝播する | 意図的な設計（ラッパーがエラー処理を追加すべきでない）。NCBC-E01〜E07で全メソッドの伝播を検証 |
| 3 | `_assume_role_and_get_credentials`と`_get_assume_role_credentials`が実質同一 | 冗長なラッパー | テスト用の後方互換メソッドとして意図的に残されている（L69 docstring参照） |
