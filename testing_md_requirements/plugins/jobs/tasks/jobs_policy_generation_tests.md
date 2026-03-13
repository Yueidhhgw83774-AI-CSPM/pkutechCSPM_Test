# jobs/tasks/policy_generation テストケース

## 1. 概要

`app/jobs/tasks/policy_generation.py` は、ポリシー一括生成タスクの実装クラス `PolicyGenerationTask` を定義します。`BaseTask` を継承し、推奨事項データの検証・Pydanticモデルへの変換・デバッグ制限適用・バッチ処理（レート制限付き）・統計集計の一連のポリシー生成フローを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `PolicyGenerationTask.__init__` | job_id設定、TaskLogger・StatusTracker初期化 |
| `_execute_task` | メインタスク実行（検証→準備→デバッグ制限→バッチ→統計） |
| `_validate_inputs` | recommendations_dataのリスト型チェック |
| `_prepare_recommendations` | Dict→RecommendationInputDataへの変換 |
| `_apply_debug_limit` | DEBUG_MAX_ITEMS設定による処理件数制限 |
| `_process_recommendations_batch` | バッチ処理ループ（進捗追跡・レート制限付き） |
| `_process_single_recommendation` | 単一推奨事項の処理（targetClouds有無分岐） |
| `_generate_policy_for_cloud` | クラウド別ポリシー生成（run_policy_agent呼出） |
| `_apply_rate_limit` | MIN_INTERVAL_SECONDSベースのレート制限 |
| `_create_policy_result` | ポリシー結果オブジェクト作成（タイムスタンプ条件分岐） |
| `_calculate_statistics` | 成功/失敗の統計計算 |
| `run_policy_batch_generation_task` | レガシー互換ラッパー関数 |

### 1.2 カバレッジ目標: 85%

> **注記**: 269行の中規模クラス。外部ポリシーエージェント（`run_policy_agent`）はモックで検証。レート制限・デバッグ制限・統計計算の分岐を網羅的にテストする。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/jobs/tasks/policy_generation.py` |
| テストコード | `test/unit/jobs/tasks/test_policy_generation.py` |

### 1.4 補足情報

#### 依存関係（モック対象）

```
policy_generation.py ──→ base_task.BaseTask（親クラス）
                     ──→ common.error_handling.ValidationError, ExternalServiceError
                     ──→ common.logging.TaskLogger
                     ──→ common.status_tracking.StatusTracker
                     ──→ core.config.settings（settings.DEBUG_MAX_ITEMS）
                     ──→ core.config.MIN_INTERVAL_SECONDS
                     ──→ models.jobs.RecommendationInputData
                     ──→ cspm_plugin.agent.run_policy_agent
                     ──→ asyncio.sleep, time.monotonic
```

#### 主要分岐

| メソッド | 行 | 条件 | 結果 |
|---------|-----|------|------|
| `_execute_task` | L37 | `not recommendation_inputs` | 空の早期リターン |
| `_validate_inputs` | L84 | `not isinstance(recommendations_data, list)` | ValidationError |
| `_prepare_recommendations` | L98 | except Exception | ValidationError再ラップ |
| `_apply_debug_limit` | L106 | `settings.DEBUG_MAX_ITEMS and > 0` | 件数制限適用 |
| `_process_single_recommendation` | L152 | `not rec_input.targetClouds` | Skipped結果 |
| `_generate_policy_for_cloud` | L199 | except Exception | エラー結果返却 |
| `_apply_rate_limit` | L216 | `wait_time > 0` | asyncio.sleep実行 |
| `_create_policy_result` | L233-235 | `policy_content and status not in [...]` | policyGeneratedAt設定 |
| `_calculate_statistics` | L250 | `status in ["active", "requires_manual_review"] and policyContent` | succeeded+1 |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PGEN-001 | __init__でTaskLoggerとStatusTracker初期化 | job_id="test-pg-001" | logger, status_tracker属性が正しく設定 |
| PGEN-002 | _execute_task全成功パス | 有効な推奨事項リスト | message, main_payload, summary_dataを含む辞書 |
| PGEN-003 | _execute_taskで空の推奨事項リスト（準備後） | 空リスト→_prepare_recommendations→[] | "処理対象の推奨事項がありませんでした" |
| PGEN-004 | _prepare_recommendationsで有効データ変換 | 有効なDict | RecommendationInputDataリスト |
| PGEN-005 | _apply_debug_limit制限適用 | DEBUG_MAX_ITEMS=2, 推奨事項3件 | 2件に制限 |
| PGEN-006 | _apply_debug_limit制限なし（0） | DEBUG_MAX_ITEMS=0 | 全件返却 |
| PGEN-006b | _apply_debug_limit制限なし（None） | DEBUG_MAX_ITEMS=None | 全件返却（and短絡評価） |
| PGEN-007 | _process_single_recommendationでtargetCloudsあり | targetClouds=["aws"] | policyOutputsに1件 |
| PGEN-008 | _process_single_recommendationでtargetClouds空 | targetClouds=[] | Skipped結果 |
| PGEN-009 | _generate_policy_for_cloud成功 | run_policy_agent正常返却 | ポリシー結果辞書 |
| PGEN-010 | _apply_rate_limit待機あり | 前回呼出から間隔が短い | asyncio.sleep呼出 |
| PGEN-011 | _apply_rate_limit待機なし | 前回呼出から十分経過 | asyncio.sleep呼ばれない |
| PGEN-012 | _create_policy_resultで成功（タイムスタンプ付き） | content有, status="active" | policyGeneratedAtが設定される |
| PGEN-013 | _create_policy_resultでエラー（タイムスタンプなし） | content=None, status="error" | policyGeneratedAt=None |
| PGEN-014 | _calculate_statistics混合結果 | 成功2件・失敗1件 | succeeded=2, failed=1 |
| PGEN-015 | run_policy_batch_generation_taskラッパー | 全パラメータ | PolicyGenerationTask.executeが呼ばれる |

### 2.1 初期化テスト

```python
# test/unit/jobs/tasks/test_policy_generation.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestPolicyGenerationTaskInit:
    """PolicyGenerationTask初期化テスト"""

    def test_init_sets_logger_and_status_tracker(self):
        """PGEN-001: __init__でTaskLoggerとStatusTracker初期化

        policy_generation.py:23-26 の初期化処理を検証。
        """
        # Arrange & Act
        with patch("app.jobs.tasks.policy_generation.TaskLogger") as mock_logger_cls, \
             patch("app.jobs.tasks.policy_generation.StatusTracker") as mock_tracker_cls:
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            task = PolicyGenerationTask("test-pg-001")

        # Assert
        assert task.job_id == "test-pg-001"
        mock_logger_cls.assert_called_once_with("test-pg-001", "PolicyGeneration")
        mock_tracker_cls.assert_called_once_with("test-pg-001")
```

### 2.2 _execute_task テスト

```python
class TestExecuteTask:
    """_execute_taskメインフローテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-exec")

    @pytest.mark.asyncio
    async def test_execute_task_full_success(self, task):
        """PGEN-002: _execute_task全成功パス

        policy_generation.py:28-80 のメインフロー全体を検証。
        """
        # Arrange
        mock_rec = MagicMock()
        mock_rec.uuid = "uuid-001"
        mock_rec.recommendationId = "rec-001"
        mock_rec.targetClouds = ["aws"]
        mock_rec.title = "テスト推奨事項"

        task._prepare_recommendations = MagicMock(return_value=[mock_rec])
        task._process_recommendations_batch = AsyncMock(return_value=[{
            "uuid": "uuid-001",
            "policyOutputs": [{"policyGenerationStatus": "active", "policyContent": "yaml"}]
        }])

        with patch("app.jobs.tasks.policy_generation.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 0

            # Act
            result = await task._execute_task(recommendations_data=[{"uuid": "uuid-001"}])

        # Assert
        assert "ポリシー生成完了" in result["message"]
        assert result["summary_data"]["policies_succeeded"] == 1
        assert result["summary_data"]["policies_failed"] == 0

    @pytest.mark.asyncio
    async def test_execute_task_empty_after_prepare(self, task):
        """PGEN-003: _execute_taskで空の推奨事項（準備後）

        policy_generation.py:37-43 の早期リターンを検証。
        _prepare_recommendationsが空リストを返す場合。
        """
        # Arrange
        task._prepare_recommendations = MagicMock(return_value=[])

        # Act
        result = await task._execute_task(recommendations_data=[])

        # Assert
        assert result["message"] == "処理対象の推奨事項がありませんでした"
        assert result["main_payload"] == []
        assert result["summary_data"]["total_recommendations"] == 0
```

### 2.3 _prepare_recommendations テスト

```python
class TestPrepareRecommendations:
    """_prepare_recommendationsテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-prep")

    def test_prepare_recommendations_valid_data(self, task):
        """PGEN-004: _prepare_recommendationsで有効データ変換

        policy_generation.py:91-97 の正常パスを検証。
        DictデータがRecommendationInputDataインスタンスに変換される。
        """
        # Arrange
        rec_data = [{
            "uuid": "test-uuid-001",
            "title": "テスト推奨事項",
            "description": "テスト説明",
            "targetClouds": ["aws"],
        }]

        # Act
        result = task._prepare_recommendations(rec_data)

        # Assert
        assert len(result) == 1
        assert result[0].uuid == "test-uuid-001"
        assert result[0].title == "テスト推奨事項"
```

### 2.4 _apply_debug_limit テスト

```python
class TestApplyDebugLimit:
    """_apply_debug_limitテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-debug")

    def test_apply_debug_limit_with_limit(self, task):
        """PGEN-005: _apply_debug_limit制限適用

        policy_generation.py:106-109 のDEBUG_MAX_ITEMS有効時を検証。
        """
        # Arrange
        recs = [MagicMock() for _ in range(3)]

        with patch("app.jobs.tasks.policy_generation.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 2

            # Act
            limited, total = task._apply_debug_limit(recs)

        # Assert
        assert len(limited) == 2
        assert total == 2

    def test_apply_debug_limit_no_limit_zero(self, task):
        """PGEN-006: _apply_debug_limit制限なし（0）

        policy_generation.py:110 のDEBUG_MAX_ITEMS=0時を検証。
        Falsy値のため制限が適用されない。
        """
        # Arrange
        recs = [MagicMock() for _ in range(3)]

        with patch("app.jobs.tasks.policy_generation.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = 0

            # Act
            result, total = task._apply_debug_limit(recs)

        # Assert
        assert len(result) == 3
        assert total == 3

    def test_apply_debug_limit_no_limit_none(self, task):
        """PGEN-006b: _apply_debug_limit制限なし（None）

        policy_generation.py:106 のDEBUG_MAX_ITEMS=None時を検証。
        `settings.DEBUG_MAX_ITEMS and ...` の短絡評価でFalseとなり制限なし。
        """
        # Arrange
        recs = [MagicMock() for _ in range(3)]

        with patch("app.jobs.tasks.policy_generation.settings") as mock_settings:
            mock_settings.DEBUG_MAX_ITEMS = None

            # Act
            result, total = task._apply_debug_limit(recs)

        # Assert
        assert len(result) == 3
        assert total == 3
```

### 2.5 _process_single_recommendation テスト

```python
class TestProcessSingleRecommendation:
    """_process_single_recommendationテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-single")

    @pytest.mark.asyncio
    async def test_process_with_target_clouds(self, task):
        """PGEN-007: _process_single_recommendationでtargetCloudsあり

        policy_generation.py:161-167 のクラウド別処理ループを検証。
        """
        # Arrange
        mock_rec = MagicMock()
        mock_rec.uuid = "uuid-001"
        mock_rec.recommendationId = "rec-001"
        mock_rec.targetClouds = ["aws"]
        mock_rec.title = "テスト"

        task._generate_policy_for_cloud = AsyncMock(return_value={
            "cloud": "aws", "policyContent": "yaml", "policyGenerationStatus": "active"
        })

        # Act
        result = await task._process_single_recommendation(mock_rec, 0.0)

        # Assert
        assert result["uuid"] == "uuid-001"
        assert len(result["policyOutputs"]) == 1
        task._generate_policy_for_cloud.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_without_target_clouds(self, task):
        """PGEN-008: _process_single_recommendationでtargetClouds空

        policy_generation.py:152-160 のtargetClouds未指定分岐を検証。
        """
        # Arrange
        mock_rec = MagicMock()
        mock_rec.uuid = "uuid-002"
        mock_rec.recommendationId = "rec-002"
        mock_rec.targetClouds = []
        mock_rec.title = "テスト"

        # Act
        result = await task._process_single_recommendation(mock_rec, 0.0)

        # Assert
        assert len(result["policyOutputs"]) == 1
        assert result["policyOutputs"][0]["policyGenerationStatus"] == "Skipped"
        assert result["policyOutputs"][0]["policyContent"] is None
```

### 2.6 _generate_policy_for_cloud テスト

```python
class TestGeneratePolicyForCloud:
    """_generate_policy_for_cloudテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-gen")

    @pytest.mark.asyncio
    async def test_generate_policy_success(self, task):
        """PGEN-009: _generate_policy_for_cloud成功

        policy_generation.py:188-197 の正常パスを検証。
        run_policy_agentが正常に返却する場合。
        """
        # Arrange
        mock_rec = MagicMock()
        mock_rec.uuid = "uuid-001"
        mock_rec.recommendationId = "rec-001"
        mock_rec.model_dump = MagicMock(return_value={"uuid": "uuid-001"})
        task._apply_rate_limit = AsyncMock()

        with patch("app.jobs.tasks.policy_generation.run_policy_agent",
                   new_callable=AsyncMock,
                   return_value=("policies:\n  - name: test", None, "active")):
            # Act
            result = await task._generate_policy_for_cloud(mock_rec, "aws", 0.0)

        # Assert
        assert result["cloud"] == "aws"
        assert result["policyContent"] == "policies:\n  - name: test"
        assert result["policyGenerationStatus"] == "active"
        assert result["policyGeneratedAt"] is not None
```

### 2.7 _apply_rate_limit テスト

```python
class TestApplyRateLimit:
    """_apply_rate_limitテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-rate")

    @pytest.mark.asyncio
    async def test_rate_limit_waits_when_needed(self, task):
        """PGEN-010: _apply_rate_limit待機あり

        policy_generation.py:214-217 のwait_time > 0分岐を検証。
        """
        # Arrange
        with patch("app.jobs.tasks.policy_generation.time") as mock_time, \
             patch("app.jobs.tasks.policy_generation.asyncio") as mock_asyncio, \
             patch("app.jobs.tasks.policy_generation.MIN_INTERVAL_SECONDS", 2.0):
            mock_time.monotonic.return_value = 10.5  # 前回10.0 → 0.5秒経過
            mock_asyncio.sleep = AsyncMock()

            # Act
            await task._apply_rate_limit(10.0)

        # Assert（1.5秒待機が必要: 2.0 - 0.5 = 1.5）
        mock_asyncio.sleep.assert_called_once_with(1.5)

    @pytest.mark.asyncio
    async def test_rate_limit_no_wait_when_elapsed(self, task):
        """PGEN-011: _apply_rate_limit待機なし

        policy_generation.py:216 のwait_time <= 0分岐を検証。
        """
        # Arrange
        with patch("app.jobs.tasks.policy_generation.time") as mock_time, \
             patch("app.jobs.tasks.policy_generation.asyncio") as mock_asyncio, \
             patch("app.jobs.tasks.policy_generation.MIN_INTERVAL_SECONDS", 1.0):
            mock_time.monotonic.return_value = 15.0  # 前回10.0 → 5秒経過
            mock_asyncio.sleep = AsyncMock()

            # Act
            await task._apply_rate_limit(10.0)

        # Assert（待機不要）
        mock_asyncio.sleep.assert_not_called()
```

### 2.8 _create_policy_result テスト

```python
class TestCreatePolicyResult:
    """_create_policy_resultテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-result")

    def test_create_result_with_timestamp(self, task):
        """PGEN-012: _create_policy_resultで成功（タイムスタンプ付き）

        policy_generation.py:233-235 のpolicy_contentありかつactiveステータスを検証。
        """
        # Arrange & Act
        result = task._create_policy_result("aws", "policies:\n  - name: test", None, "active")

        # Assert
        assert result["cloud"] == "aws"
        assert result["policyContent"] == "policies:\n  - name: test"
        assert result["error"] is None
        assert result["policyGeneratedAt"] is not None

    def test_create_result_without_timestamp_on_error(self, task):
        """PGEN-013: _create_policy_resultでエラー（タイムスタンプなし）

        policy_generation.py:233-236 のstatus="error"分岐を検証。
        """
        # Arrange & Act
        result = task._create_policy_result("aws", None, "エラー発生", "error")

        # Assert
        assert result["policyContent"] is None
        assert result["error"] == "エラー発生"
        assert result["policyGeneratedAt"] is None
```

### 2.9 _calculate_statistics テスト

```python
class TestCalculateStatistics:
    """_calculate_statisticsテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-stats")

    def test_calculate_statistics_mixed_results(self, task):
        """PGEN-014: _calculate_statistics混合結果

        policy_generation.py:240-259 の統計計算を検証。
        active/requires_manual_review+policyContent→成功、それ以外→失敗。
        """
        # Arrange
        job_results = [
            {
                "policyOutputs": [
                    {"policyGenerationStatus": "active", "policyContent": "yaml1"},
                    {"policyGenerationStatus": "requires_manual_review", "policyContent": "yaml2"},
                    {"policyGenerationStatus": "error", "policyContent": None},
                ]
            }
        ]

        # Act
        stats = task._calculate_statistics(job_results)

        # Assert
        assert stats["attempted"] == 3
        assert stats["succeeded"] == 2
        assert stats["failed"] == 1
```

### 2.10 レガシーラッパー関数テスト

```python
class TestRunPolicyBatchGenerationTask:
    """run_policy_batch_generation_taskテスト"""

    @pytest.mark.asyncio
    async def test_legacy_wrapper_creates_task_and_executes(self):
        """PGEN-015: run_policy_batch_generation_taskラッパー

        policy_generation.py:263-269 のラッパー関数を検証。
        """
        # Arrange
        with patch("app.jobs.tasks.policy_generation.PolicyGenerationTask") as mock_cls:
            mock_instance = MagicMock()
            mock_instance.execute = AsyncMock()
            mock_cls.return_value = mock_instance

            # Act
            from app.jobs.tasks.policy_generation import run_policy_batch_generation_task
            await run_policy_batch_generation_task(
                job_id="test-legacy",
                recommendations_data=[{"uuid": "uuid-001"}]
            )

        # Assert
        mock_cls.assert_called_once_with("test-legacy")
        mock_instance.execute.assert_called_once_with(
            recommendations_data=[{"uuid": "uuid-001"}]
        )
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PGEN-E01 | _validate_inputsでリスト以外 | recommendations_data="not a list" | ValidationError("推奨事項データはリストである必要があります") |
| PGEN-E02 | _prepare_recommendationsで不正データ | 必須フィールド不足のDict | ValidationError("推奨事項データの形式が不正です: ...") |
| PGEN-E03 | _generate_policy_for_cloudでエージェント例外 | run_policy_agent → Exception | エラー結果辞書返却（例外は伝搬しない） |
| PGEN-E04 | _calculate_statisticsでactive+policyContent無し | status="active", policyContent=None | failed+1（succeededにならない） |

### 3.1 _validate_inputs 異常系

```python
class TestValidateInputsErrors:
    """_validate_inputs入力検証エラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-err")

    def test_non_list_raises_validation_error(self, task):
        """PGEN-E01: _validate_inputsでリスト以外

        policy_generation.py:84-89 の型チェックをカバー。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError

        # Act & Assert
        with pytest.raises(ValidationError, match="推奨事項データはリストである必要があります"):
            task._validate_inputs("not a list")
```

### 3.2 _prepare_recommendations 異常系

```python
class TestPrepareRecommendationsErrors:
    """_prepare_recommendationsエラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-prep-err")

    def test_invalid_data_raises_validation_error(self, task):
        """PGEN-E02: _prepare_recommendationsで不正データ

        policy_generation.py:98-99 のexceptブロックをカバー。
        RecommendationInputDataの必須フィールド不足で例外発生。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        invalid_data = [{"invalid_field": "value"}]  # 必須フィールド不足

        # Act & Assert
        with pytest.raises(ValidationError, match="推奨事項データの形式が不正です"):
            task._prepare_recommendations(invalid_data)
```

### 3.3 _generate_policy_for_cloud 異常系

```python
class TestGeneratePolicyForCloudErrors:
    """_generate_policy_for_cloudエラーテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-gen-err")

    @pytest.mark.asyncio
    async def test_agent_exception_returns_error_result(self, task):
        """PGEN-E03: _generate_policy_for_cloudでエージェント例外

        policy_generation.py:199-210 のexceptブロックをカバー。
        run_policy_agentが例外を発生させた場合、エラー結果辞書が返される。
        """
        # Arrange
        mock_rec = MagicMock()
        mock_rec.uuid = "uuid-err"
        mock_rec.recommendationId = "rec-err"
        mock_rec.model_dump = MagicMock(return_value={"uuid": "uuid-err"})
        task._apply_rate_limit = AsyncMock()

        with patch("app.jobs.tasks.policy_generation.run_policy_agent",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("API接続エラー")):
            # Act
            result = await task._generate_policy_for_cloud(mock_rec, "aws", 0.0)

        # Assert（例外は伝搬せずエラー結果が返される）
        assert result["policyGenerationStatus"] == "error"
        assert result["policyContent"] is None
        assert "エージェント実行エラー" in result["error"]
        assert result["policyGeneratedAt"] is None
```

### 3.4 _calculate_statistics 異常系

```python
class TestCalculateStatisticsEdgeCases:
    """_calculate_statisticsエッジケーステスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-stats-err")

    def test_active_without_content_counts_as_failed(self, task):
        """PGEN-E04: active+policyContent無しはfailカウント

        policy_generation.py:250 の条件をカバー。
        statusが"active"でもpolicyContentがNoneの場合はfailedに加算。
        """
        # Arrange
        job_results = [
            {
                "policyOutputs": [
                    {"policyGenerationStatus": "active", "policyContent": None},
                ]
            }
        ]

        # Act
        stats = task._calculate_statistics(job_results)

        # Assert
        assert stats["succeeded"] == 0
        assert stats["failed"] == 1
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| PGEN-SEC-01 | 【実装失敗予定】_prepare_recommendationsエラーメッセージに推奨事項値が漏洩しない | 不正データ | エラーメッセージにPydanticバリデーション情報のみ（※Pydantic v2のstr(e)がinput_value含むため失敗） |
| PGEN-SEC-02 | _generate_policy_for_cloud例外ラップで制御されたエラー返却 | agent例外 | 内部例外メッセージが"エージェント実行エラー: {str(e)}"形式でerrorフィールドに含まれ、ログにも記録 |
| PGEN-SEC-03 | レート制限がAPI呼出間隔を強制 | 連続呼出 | MIN_INTERVAL_SECONDSの間隔が保証される |

```python
@pytest.mark.security
class TestPolicyGenerationSecurity:
    """PolicyGenerationTaskセキュリティテスト"""

    @pytest.fixture
    def task(self):
        with patch("app.jobs.tasks.policy_generation.TaskLogger"), \
             patch("app.jobs.tasks.policy_generation.StatusTracker"):
            from app.jobs.tasks.policy_generation import PolicyGenerationTask
            return PolicyGenerationTask("test-pg-sec")

    @pytest.mark.xfail(reason="Pydantic v2のstr(e)がinput_valueを含むため", strict=True)
    def test_prepare_error_does_not_leak_recommendation_values(self, task):
        """PGEN-SEC-01: [EXPECTED_TO_FAIL] _prepare_recommendationsエラーメッセージに推奨事項値が漏洩しない

        policy_generation.py:98-99 の例外メッセージを検証。
        不正データのフィールド値がそのままエラーメッセージに含まれないことを確認する
        回帰テスト。

        【失敗理由】Pydantic v2のValidationErrorは str(e) に input_value（入力辞書全体）
        を含むため、L99の f"...{str(e)}" で入力値が漏洩する。
        対策として、str(e) の代わりにエラーカウント等の要約情報のみを含めるよう
        実装を修正することを推奨。
        """
        # Arrange
        from app.jobs.common.error_handling import ValidationError
        sensitive_data = [{"uuid": "secret-uuid-12345", "secretField": "top-secret-value"}]

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            task._prepare_recommendations(sensitive_data)

        error_msg = str(exc_info.value)
        assert "top-secret-value" not in error_msg, \
            "機密フィールド値がエラーメッセージに漏洩しています"

    @pytest.mark.asyncio
    async def test_agent_exception_wrapped_with_controlled_error(self, task):
        """PGEN-SEC-02: _generate_policy_for_cloud例外ラップで制御されたエラー返却

        policy_generation.py:199-210 の例外処理を検証。
        内部例外メッセージはerrorフィールドに含まれるが、
        例外が呼び出し元に伝搬せず制御された結果オブジェクトが返される。
        """
        # Arrange
        mock_rec = MagicMock()
        mock_rec.uuid = "uuid-sec"
        mock_rec.recommendationId = "rec-sec"
        mock_rec.model_dump = MagicMock(return_value={})
        task._apply_rate_limit = AsyncMock()
        internal_error = "ConnectionError: https://internal-api.example.com:9443/agent"

        with patch("app.jobs.tasks.policy_generation.run_policy_agent",
                   new_callable=AsyncMock,
                   side_effect=Exception(internal_error)):
            # Act
            result = await task._generate_policy_for_cloud(mock_rec, "aws", 0.0)

        # Assert（例外が伝搬せず、制御された結果が返される）
        assert result["policyGenerationStatus"] == "error"
        assert "エージェント実行エラー" in result["error"]
        # 内部例外メッセージが"エージェント実行エラー: {str(e)}"形式でラップされている
        assert internal_error in result["error"], \
            "内部例外メッセージがerrorフィールドにラップされていません"
        # ログにエラー詳細が記録されていることを確認
        task.logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting_enforces_minimum_interval(self, task):
        """PGEN-SEC-03: レート制限がAPI呼出間隔を強制

        policy_generation.py:212-217 のレート制限を検証。
        MIN_INTERVAL_SECONDSに基づく最小間隔が強制され、
        API乱用（DoS的な連続呼出）を防止することを確認。
        """
        # Arrange
        with patch("app.jobs.tasks.policy_generation.time") as mock_time, \
             patch("app.jobs.tasks.policy_generation.asyncio") as mock_asyncio, \
             patch("app.jobs.tasks.policy_generation.MIN_INTERVAL_SECONDS", 3.0):
            mock_time.monotonic.return_value = 100.1  # 前回100.0 → 0.1秒経過
            mock_asyncio.sleep = AsyncMock()

            # Act
            await task._apply_rate_limit(100.0)

        # Assert（2.9秒待機が必要: 3.0 - 0.1 = 2.9）
        mock_asyncio.sleep.assert_called_once()
        actual_wait = mock_asyncio.sleep.call_args[0][0]
        assert abs(actual_wait - 2.9) < 0.01, \
            f"レート制限の待機時間が不正: {actual_wait}（期待: 2.9秒）"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_policy_generation_module` | テスト間のstatus_managerグローバル状態リセット | function | Yes |
| `task` | 各テストクラス内のPolicyGenerationTaskインスタンス | function | No |

### 共通フィクスチャ定義

```python
# test/unit/jobs/tasks/conftest.py に追加
# （既存のreset_base_task_module/reset_file_processing_moduleフィクスチャと共存）
import pytest


@pytest.fixture(autouse=True)
def reset_policy_generation_module():
    """テストごとにstatus_managerのグローバル状態をリセット

    status_manager.job_statusesはモジュールレベルの辞書であり、
    テスト間で状態が共有されるのを防止する。
    """
    from app.jobs.status_manager import job_statuses
    job_statuses.clear()
    yield
    job_statuses.clear()
```

---

## 6. テスト実行例

```bash
# policy_generation関連テストのみ実行
pytest test/unit/jobs/tasks/test_policy_generation.py -v

# 特定のテストクラスのみ実行
pytest test/unit/jobs/tasks/test_policy_generation.py::TestExecuteTask -v

# カバレッジ付きで実行
pytest test/unit/jobs/tasks/test_policy_generation.py --cov=app.jobs.tasks.policy_generation --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/jobs/tasks/test_policy_generation.py -m "security" -v

# 非同期テスト実行（pytest-asyncioが必要）
pytest test/unit/jobs/tasks/test_policy_generation.py -v --asyncio-mode=auto
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 16 | PGEN-001 〜 PGEN-015（PGEN-006bを含む） |
| 異常系 | 4 | PGEN-E01 〜 PGEN-E04 |
| セキュリティ | 3 | PGEN-SEC-01 〜 PGEN-SEC-03 |
| **合計** | **23** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestPolicyGenerationTaskInit` | PGEN-001 | 1 |
| `TestExecuteTask` | PGEN-002〜PGEN-003 | 2 |
| `TestPrepareRecommendations` | PGEN-004 | 1 |
| `TestApplyDebugLimit` | PGEN-005〜PGEN-006b | 3 |
| `TestProcessSingleRecommendation` | PGEN-007〜PGEN-008 | 2 |
| `TestGeneratePolicyForCloud` | PGEN-009 | 1 |
| `TestApplyRateLimit` | PGEN-010〜PGEN-011 | 2 |
| `TestCreatePolicyResult` | PGEN-012〜PGEN-013 | 2 |
| `TestCalculateStatistics` | PGEN-014 | 1 |
| `TestRunPolicyBatchGenerationTask` | PGEN-015 | 1 |
| `TestValidateInputsErrors` | PGEN-E01 | 1 |
| `TestPrepareRecommendationsErrors` | PGEN-E02 | 1 |
| `TestGeneratePolicyForCloudErrors` | PGEN-E03 | 1 |
| `TestCalculateStatisticsEdgeCases` | PGEN-E04 | 1 |
| `TestPolicyGenerationSecurity` | PGEN-SEC-01〜PGEN-SEC-03 | 3 |

### 実装失敗が予想されるテスト

| テストID | 理由 | 推奨修正 |
|---------|------|---------|
| PGEN-SEC-01 | Pydantic v2の`str(e)`は`input_value`に入力辞書全体を含むため、L99の`f"...{str(e)}"`で入力値が漏洩する | `str(e)`の代わりにエラーカウント等の要約情報のみを含めるよう実装修正 |

### 注意事項

- `pytest-asyncio` が必要（async テストメソッドが多数）
- `pyproject.toml` に `asyncio_mode = "auto"` 設定推奨
- `@pytest.mark.security` マーカーの登録が必要
- `run_policy_agent` のモックは `new_callable=AsyncMock` を使用（async関数のため）
- `time.monotonic` と `asyncio.sleep` のモックはレート制限テストで必要

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | `run_policy_agent` は外部LLMエージェント依存 | 実際のポリシー生成は単体テストで検証不可 | AsyncMockで返却値を制御し、呼び出し引数と結果ハンドリングを検証 |
| 2 | `RecommendationInputData` のPydantic検証は複雑 | 全フィールドの組み合わせテストは非現実的 | 最小限の必須フィールド（uuid, title, description, targetClouds）での検証に絞る |
| 3 | `_process_recommendations_batch` のループ全体テストは統合テスト寄り | 複数推奨事項のバッチ処理は単体テストでは検証困難 | `_process_single_recommendation` と `_generate_policy_for_cloud` を個別にテストし、バッチ処理は統合テストで補完 |
| 4 | `time.monotonic` のモックはタイミング依存 | テスト実行環境の速度に影響されない | 固定値でモックし、計算結果のみ検証 |
