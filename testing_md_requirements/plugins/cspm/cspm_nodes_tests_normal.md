# cspm_plugin ノード群 テストケース — 正常系

> 本ファイルは [cspm_nodes_tests.md](cspm_nodes_tests.md) のセクション2を分割したものです。
> 概要・フィクスチャ・実行例・サマリー・制限事項については本体を参照してください。

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-ND-001 | format_field: リスト型変換 | `["item1", "item2"]` | `"item1\nitem2"` |
| CSPM-ND-002 | format_field: 辞書型変換 | `{"key": "value"}` | JSON文字列 |
| CSPM-ND-003 | format_field: None変換 | `None` | `""` |
| CSPM-ND-004 | format_field: 文字列透過 | `"test"` | `"test"` |
| CSPM-ND-005 | ポリシー生成成功 | 有効な推奨事項 + LLMモック | current_policy_content有り, validation_error=None |
| CSPM-ND-006 | 強化版ポリシー生成成功 | 有効な推奨事項 + 強化LLMモック | current_policy_content有り |
| CSPM-ND-007 | check_generation_success: 成功 | current_policy有り, error=None | "validate_policy" |
| CSPM-ND-008 | check_generation_success: エラーあり | current_policy有り, error有り | "validate_policy" |
| CSPM-ND-009 | validate_policy_node: 検証成功 | 有効なポリシー + ツールモック | validation_error=None |
| CSPM-ND-010 | validate_policy_node: 検証失敗 | 不正なポリシー + ツールモック | validation_error有り |
| CSPM-ND-011 | check_validation_node: 成功→レビュー | validation_error=None | "final_review" |
| CSPM-ND-012 | check_validation_node: 失敗→修正 | error有り, retry < MAX | "search_schema" |
| CSPM-ND-013 | search_schema_node: リソースタイプ抽出 | "resource:aws.s3" エラー | get_custodian_schema呼出 |
| CSPM-ND-014 | search_schema_node: 無効リソース検出 | "invalid resource" エラー | list_resources呼出 |
| CSPM-ND-015 | fix_policy_node: 修正成功 | ポリシー + エラー + LLMモック | 修正済みポリシー, retry+1 |
| CSPM-ND-016 | handle_failure_node: 通常失敗 [legacy] | retry=5, remaining=∞ | final_error有り, status="generation_failed" |
| CSPM-ND-017 | final_review_node: 承認 | 検証済みポリシー + レビュー承認 | status="active" |
| CSPM-ND-018 | final_review_node: アクション含有 | actions有りポリシー | status="requires_manual_review" |
| CSPM-ND-019 | check_final_review_node: 承認→END | status="active" | "END" |
| CSPM-ND-020 | check_final_review_node: 再生成 | status="needs_regeneration" | "generate_policy" |
| CSPM-ND-021 | レビューフィードバック付き生成 | review_feedback有り | プロンプトにフィードバック含む |
| CSPM-ND-022 | search_schema_node: フィルターエラー解析 | "filter" 含むエラー | component_type="filters" |
| CSPM-ND-023 | search_schema_node: アクションエラー解析 | "action" 含むエラー | component_type="actions" |
| CSPM-ND-024 | LLMレスポンスがリスト型content | content=[{"text":"..."}] | テキスト連結して処理 |
| CSPM-ND-025 | レビュー: policies辞書形式パース | `{"policies":[{...}]}` | 正常にパースされること |
| CSPM-ND-026 | レビュー: 単一オブジェクト形式パース | `{"name":"test",...}` | 正常にパースされること |
| CSPM-ND-027 | fix_policy_node: リスト型content | content=[{"text":"..."}] | テキスト連結して修正 |
| CSPM-ND-028 | レビュー: RAGエラーレスポンス時の継続 | retrieve_reference→"Error:..." | reference_contextにエラー記録、レビュー継続 |
| CSPM-ND-029 | check_validation: 上限直前リトライ | retry_count=4, error有り | "search_schema" |

### 2.1 format_field テスト

```python
# test/unit/cspm_nodes/test_nodes.py
import pytest
import json
import yaml
from unittest.mock import patch, MagicMock, AsyncMock
# conftest.py のヘルパー関数を明示的にインポート
# NOTE: make_chainable_mock は通常の関数（フィクスチャではない）のため、
# pytest の自動ロードでは利用不可。明示的 import が必要。
from conftest import make_chainable_mock


class TestFormatField:
    """型変換ヘルパー関数のテスト"""

    def test_list_conversion(self):
        """CSPM-ND-001: リスト型が改行区切り文字列に変換されること"""
        # Arrange
        data = ["item1", "item2", "item3"]

        # Act
        from app.cspm_plugin.nodes.policy_generation import format_field
        result = format_field(data)

        # Assert
        assert result == "item1\nitem2\nitem3"

    def test_dict_conversion(self):
        """CSPM-ND-002: 辞書型がJSON文字列に変換されること

        nodes/policy_generation.py:49-54 の分岐をカバーする。
        """
        # Arrange
        data = {"key": "value", "nested": {"inner": 1}}

        # Act
        from app.cspm_plugin.nodes.policy_generation import format_field
        result = format_field(data)

        # Assert
        parsed = json.loads(result)
        assert parsed["key"] == "value"
        assert parsed["nested"]["inner"] == 1

    def test_none_conversion(self):
        """CSPM-ND-003: Noneが空文字列に変換されること

        nodes/policy_generation.py:57 の (data or "") をカバーする。
        """
        # Act
        from app.cspm_plugin.nodes.policy_generation import format_field
        result = format_field(None)

        # Assert
        assert result == ""

    def test_string_passthrough(self):
        """CSPM-ND-004: 文字列がそのまま返されること"""
        # Act
        from app.cspm_plugin.nodes.policy_generation import format_field
        result = format_field("test string")

        # Assert
        assert result == "test string"
```

### 2.2 generate_policy_node テスト

```python
class TestGeneratePolicyNode:
    """ポリシー生成ノードのテスト"""

    @pytest.fixture
    def base_state(self):
        """基本的なState辞書"""
        return {
            "input_recommendation": {
                "recommendationId": "REC-001",
                "uuid": "test-uuid-001",
                "title": "Enable S3 Encryption",
                "description": "Ensure S3 bucket encryption",
                "rationale": "Data protection",
                "audit": "Check encryption settings",
                "remediation": "Enable default encryption",
                "impact": "Low",
                "severity": "High",
            },
            "cloud_provider": "aws",
            "messages": [],
            "retrieved_schema": "Schema info here",
            "review_feedback": None,
        }

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.policy_generation.retrieve_reference")
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    @patch("app.cspm_plugin.nodes.policy_generation.extract_and_format_policy_json")
    async def test_generate_policy_success(
        self, mock_extract, mock_init_llm, mock_identify, mock_rag, base_state
    ):
        """CSPM-ND-005: ポリシーが正常に生成されること"""
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_identify.return_value = ("aws.s3", None)
        mock_rag.ainvoke = AsyncMock(return_value="RAG context data")
        mock_extract.return_value = ('[{"name":"test","resource":"aws.s3"}]', None)

        # LLMチェーンのモック（make_chainable_mock でテスト間干渉を防止）
        mock_response = MagicMock()
        mock_response.content = '```json\n[{"name":"test"}]\n```'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)
        with patch(
            "app.cspm_plugin.nodes.policy_generation.initial_generation_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            # Act
            from app.cspm_plugin.nodes.policy_generation import generate_policy_node
            result = await generate_policy_node(base_state)

        # Assert
        assert isinstance(result["current_policy_content"], str)
        assert len(result["current_policy_content"]) > 0, "ポリシーJSONが空文字列です"
        # JSON構造として有効であること
        parsed = json.loads(result["current_policy_content"])
        assert isinstance(parsed, list), "ポリシーはリスト形式であるべき"
        assert result["validation_error"] is None
        assert result["retry_count"] == 0
        assert result["identified_resource"] == "aws.s3"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.policy_generation.retrieve_reference")
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_enhanced_llm")
    @patch("app.cspm_plugin.nodes.policy_generation.extract_and_format_policy_json")
    async def test_enhanced_generate_policy_success(
        self, mock_extract, mock_init_llm, mock_identify, mock_rag, base_state
    ):
        """CSPM-ND-006: 強化版ポリシー生成が正常に実行されること

        nodes/policy_generation.py:328-356 の強化版生成ノードをカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_identify.return_value = ("aws.s3", None)
        mock_rag.ainvoke = AsyncMock(return_value="RAG context data")
        mock_extract.return_value = ('[{"name":"enhanced-test","resource":"aws.s3"}]', None)

        mock_response = MagicMock()
        mock_response.content = '```json\n[{"name":"enhanced-test"}]\n```'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)
        with patch(
            "app.cspm_plugin.nodes.policy_generation.initial_generation_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            # Act
            from app.cspm_plugin.nodes.policy_generation import enhanced_generate_policy_node
            result = await enhanced_generate_policy_node(base_state)

        # Assert
        assert isinstance(result["current_policy_content"], str)
        assert len(result["current_policy_content"]) > 0, "ポリシーJSONが空文字列です"
        parsed = json.loads(result["current_policy_content"])
        assert isinstance(parsed, list), "ポリシーはリスト形式であるべき"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.policy_generation.retrieve_reference")
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    @patch("app.cspm_plugin.nodes.policy_generation.extract_and_format_policy_json")
    async def test_generate_policy_with_review_feedback(
        self, mock_extract, mock_init_llm, mock_identify, mock_rag, base_state
    ):
        """CSPM-ND-021: レビューフィードバック付きでポリシーが再生成されること

        nodes/policy_generation.py:212-221 のフィードバックセクション構築をカバーする。
        """
        # Arrange
        base_state["review_feedback"] = "フィルター条件が不適切です"
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_identify.return_value = ("aws.s3", None)
        mock_rag.ainvoke = AsyncMock(return_value="RAG context")
        mock_extract.return_value = ('[{"name":"fixed"}]', None)

        mock_response = MagicMock()
        mock_response.content = '```json\n[{"name":"fixed"}]\n```'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)
        with patch(
            "app.cspm_plugin.nodes.policy_generation.initial_generation_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            # Act
            from app.cspm_plugin.nodes.policy_generation import generate_policy_node
            result = await generate_policy_node(base_state)

        # Assert
        assert isinstance(result["current_policy_content"], str)
        assert len(result["current_policy_content"]) > 0, "ポリシーJSONが空文字列です"
        parsed = json.loads(result["current_policy_content"])
        assert isinstance(parsed, list), "ポリシーはリスト形式であるべき"
        assert result["validation_error"] is None
        # LLM呼び出し時にフィードバックが入力データに含まれることを確認
        call_args = mock_chain.ainvoke.call_args
        input_data = call_args[0][0]
        assert "フィルター条件が不適切です" in input_data["review_feedback_section"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    @patch("app.cspm_plugin.nodes.policy_generation.extract_and_format_policy_json")
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    async def test_generate_policy_list_content(
        self, mock_identify, mock_extract, mock_init_llm, base_state
    ):
        """CSPM-ND-024: LLMレスポンスがリスト型contentの場合にテキスト連結されること

        nodes/policy_generation.py:249-253 の分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_identify.return_value = ("aws.s3", None)
        mock_extract.return_value = ('[{"name":"test"}]', None)

        # content がリスト型のレスポンス
        mock_response = MagicMock()
        mock_response.content = [
            {"type": "text", "text": '```json\n[{"name":"test"}]'},
            {"type": "text", "text": "\n```"},
        ]
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "app.cspm_plugin.nodes.policy_generation.initial_generation_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt, patch(
            "app.cspm_plugin.nodes.policy_generation.TOOLS_AVAILABLE", False
        ):
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            # Act
            from app.cspm_plugin.nodes.policy_generation import generate_policy_node
            result = await generate_policy_node(base_state)

        # Assert - リスト型contentがextract_and_format_policy_jsonに渡され、
        # JSON抽出に必要な内容が保持されていること
        mock_extract.assert_called_once()
        raw_text_arg = mock_extract.call_args[0][0]
        # JSON抽出に必要な内容が連結結果に含まれること（実装の結合方式に依存しない）
        assert '[{"name":"test"}]' in raw_text_arg, "JSONペイロードが連結結果に含まれていません"
        assert "```json" in raw_text_arg, "JSONコードブロック開始タグが含まれていません"
        assert "```" in raw_text_arg, "コードブロック終了タグが含まれていません"
        assert result["current_policy_content"] is not None
```

### 2.3 条件ノードテスト

```python
class TestCheckGenerationSuccess:
    """生成成功/失敗の条件分岐ノードテスト"""

    def test_success_to_validate(self):
        """CSPM-ND-007: ポリシー有り・エラーなしで"validate_policy"を返すこと"""
        # Arrange
        state = {"current_policy_content": "[{}]", "validation_error": None}

        # Act
        from app.cspm_plugin.nodes.policy_generation import check_generation_success
        result = check_generation_success(state)

        # Assert
        assert result == "validate_policy"

    def test_with_error_to_validate(self):
        """CSPM-ND-008: ポリシー有り・エラーありでも"validate_policy"を返すこと

        nodes/policy_generation.py:558-560 の分岐をカバーする。
        """
        # Arrange
        state = {"current_policy_content": "[{}]", "validation_error": "some error"}

        # Act
        from app.cspm_plugin.nodes.policy_generation import check_generation_success
        result = check_generation_success(state)

        # Assert
        assert result == "validate_policy"


class TestCheckValidationNode:
    """検証結果の条件分岐ノードテスト"""

    def test_validation_passed(self):
        """CSPM-ND-011: 検証成功時に"final_review"を返すこと"""
        # Arrange
        state = {
            "validation_error": None,
            "retry_count": 0,
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import check_validation_node
        result = check_validation_node(state)

        # Assert
        assert result == "final_review"

    def test_validation_failed_retry(self):
        """CSPM-ND-012: 検証失敗でリトライ可能な場合に"search_schema"を返すこと"""
        # Arrange
        state = {
            "validation_error": "Invalid filter",
            "retry_count": 2,
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import check_validation_node
        result = check_validation_node(state)

        # Assert
        assert result == "search_schema"


class TestCheckFinalReviewNode:
    """レビュー結果の条件分岐ノードテスト"""

    def test_approved_to_end(self):
        """CSPM-ND-019: 承認時に"END"を返すこと"""
        # Arrange
        state = {
            "final_determined_status": "active",
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.review import check_final_review_node
        result = check_final_review_node(state)

        # Assert
        assert result == "END"

    def test_needs_regeneration(self):
        """CSPM-ND-020: 再生成が必要な場合に"generate_policy"を返すこと"""
        # Arrange
        state = {
            "final_determined_status": "needs_regeneration",
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.review import check_final_review_node
        result = check_final_review_node(state)

        # Assert
        assert result == "generate_policy"

    def test_early_termination(self):
        """CSPM-ND-E30: 早期終了時に"END"を返すこと

        nodes/review.py:281-284 の早期終了分岐をカバーする。
        NOTE: 異常系IDだが、条件ノードの境界値テストとして
        TestCheckFinalReviewNode に同居させている。
        """
        # Arrange
        state = {
            "final_determined_status": "needs_regeneration",
            "remaining_steps": 3,
        }

        # Act
        from app.cspm_plugin.nodes.review import check_final_review_node
        result = check_final_review_node(state)

        # Assert
        assert result == "END"
```

### 2.4 validate_policy_node テスト

```python
class TestValidatePolicyNode:
    """ポリシー検証ノードのテスト"""

    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.validate_policy")
    def test_validation_success(self, mock_validate):
        """CSPM-ND-009: ポリシー検証が成功した場合"""
        # Arrange
        mock_validate.invoke.return_value = "Validation successful."
        state = {"current_policy_content": '[{"name":"test","resource":"aws.s3"}]'}

        # Act
        from app.cspm_plugin.nodes.validation import validate_policy_node
        result = validate_policy_node(state)

        # Assert
        assert result["validation_error"] is None

    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.validate_policy")
    def test_validation_failure(self, mock_validate):
        """CSPM-ND-010: ポリシー検証が失敗した場合"""
        # Arrange
        mock_validate.invoke.return_value = "Error: resource:aws.invalid is not valid"
        state = {"current_policy_content": '[{"name":"test","resource":"aws.invalid"}]'}

        # Act
        from app.cspm_plugin.nodes.validation import validate_policy_node
        result = validate_policy_node(state)

        # Assert
        assert result["validation_error"] is not None
        assert "aws.invalid" in result["validation_error"]
```

### 2.5 search_schema_node テスト

```python
class TestSearchSchemaNode:
    """スキーマ検索ノードのテスト"""

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.get_custodian_schema")
    async def test_resource_type_extraction(self, mock_schema):
        """CSPM-ND-013: エラーメッセージからリソースタイプを抽出してスキーマ検索すること

        validation.py:140-143 のリソースタイプ抽出分岐をカバーする。
        NOTE: validation_errorに "filter"/"action" を含めないことで、
        純粋なリソースタイプ抽出パスのみをテストする。
        フィルター/アクション解析はND-022/ND-023で別途カバー。
        """
        # Arrange
        mock_schema.invoke.return_value = "schema for aws.s3"
        state = {
            "validation_error": "Error: resource:aws.s3 - additional properties not allowed",
            "cloud_provider": "aws",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        assert isinstance(result["retrieved_schema"], str)
        assert len(result["retrieved_schema"]) > 0, "スキーマ結果が空文字列です"
        assert result["retrieved_schema"] == "schema for aws.s3"
        mock_schema.invoke.assert_called_once()
        # target がリソースタイプのみであること（filter/action未指定）
        call_args = mock_schema.invoke.call_args[0][0]
        assert call_args.get("target", "") == "aws.s3"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.list_available_resources")
    async def test_invalid_resource_detection(self, mock_list):
        """CSPM-ND-014: 無効リソースエラーでlist_available_resourcesが呼ばれること

        validation.py:146-152 の無効リソース検出分岐をカバーする。
        """
        # Arrange
        mock_list.invoke.return_value = "resources:\n- aws.s3\n- aws.ec2"
        state = {
            "validation_error": "Error: aws.invalid is not a valid resource",
            "cloud_provider": "aws",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        assert isinstance(result["retrieved_schema"], str)
        assert result["retrieved_schema"] == "resources:\n- aws.s3\n- aws.ec2"
        mock_list.invoke.assert_called_once()
        # cloud パラメータが渡されること
        call_args = mock_list.invoke.call_args[0][0]
        assert call_args.get("cloud") == "aws"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.get_custodian_schema")
    async def test_filter_error_analysis(self, mock_schema):
        """CSPM-ND-022: filterエラー時にcomponent_type="filters"が設定されること

        validation.py:155-156 の分岐をカバーする。
        """
        # Arrange
        mock_schema.invoke.return_value = '{"filters": ["value", "marked-for-op"]}'
        state = {
            "validation_error": "Error: resource:aws.ec2 - unknown filter 'invalid-filter'",
            "cloud_provider": "aws",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        # get_custodian_schema が filters を含む target で呼ばれること
        call_args = mock_schema.invoke.call_args[0][0]
        assert "filters" in call_args["target"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.get_custodian_schema")
    async def test_action_error_analysis(self, mock_schema):
        """CSPM-ND-023: actionエラー時にcomponent_type="actions"が設定されること

        validation.py:157-158 の分岐をカバーする。
        """
        # Arrange
        mock_schema.invoke.return_value = '{"actions": ["stop", "terminate"]}'
        state = {
            "validation_error": "Error: resource:aws.ec2 - unknown action 'invalid-action'",
            "cloud_provider": "aws",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        call_args = mock_schema.invoke.call_args[0][0]
        assert "actions" in call_args["target"]
```

### 2.6 fix_policy_node テスト

```python
class TestFixPolicyNode:
    """ポリシー修正ノードのテスト"""

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.extract_and_format_policy_json")
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm")
    async def test_fix_policy_success(self, mock_init_llm, mock_extract):
        """CSPM-ND-015: ポリシーが正常に修正されること"""
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_extract.return_value = ('[{"name":"fixed","resource":"aws.s3"}]', None)

        mock_response = MagicMock()
        mock_response.content = '```json\n[{"name":"fixed"}]\n```'
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "app.cspm_plugin.nodes.validation.fix_policy_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": '[{"name":"broken"}]',
                "validation_error": "Invalid filter",
                "retrieved_schema": "Schema data",
                "retry_count": 1,
            }

            # Act
            from app.cspm_plugin.nodes.validation import fix_policy_node
            result = await fix_policy_node(state)

        # Assert
        assert result["current_policy_content"] is not None
        assert result["retry_count"] == 2
        assert result["validation_error"] is None

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.extract_and_format_policy_json")
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm")
    async def test_fix_policy_list_content(self, mock_init_llm, mock_extract):
        """CSPM-ND-027: fix_policy_nodeでLLMレスポンスがリスト型contentの場合

        validation.py:291-298 のリスト型content分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_extract.return_value = ('[{"name":"fixed"}]', None)

        # content がリスト型のレスポンス
        # NOTE: fix_policy_node (validation.py:298) は '\n'.join で連結する。
        # policy_generation.py:251 の "".join とは異なるため、
        # ND-024 とは期待値が異なる点に注意。
        mock_response = MagicMock()
        mock_response.content = [
            {"type": "text", "text": '```json\n[{"name":"fixed"}]'},
            {"type": "text", "text": "```"},
        ]
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_response)

        with patch(
            "app.cspm_plugin.nodes.validation.fix_policy_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": '[{"name":"broken"}]',
                "validation_error": "Invalid filter",
                "retrieved_schema": "Schema data",
                "retry_count": 1,
            }

            # Act
            from app.cspm_plugin.nodes.validation import fix_policy_node
            result = await fix_policy_node(state)

        # Assert - リスト型contentがextract_and_format_policy_jsonに渡され、
        # JSON抽出に必要な内容が保持されていること（実装の結合方式に依存しない）
        mock_extract.assert_called_once()
        raw_text_arg = mock_extract.call_args[0][0]
        # JSON抽出に必要な内容が連結結果に含まれること
        assert '[{"name":"fixed"}]' in raw_text_arg, "JSONペイロードが連結結果に含まれていません"
        assert "```json" in raw_text_arg, "JSONコードブロック開始タグが含まれていません"
        assert "```" in raw_text_arg, "コードブロック終了タグが含まれていません"
        assert isinstance(result["current_policy_content"], str)
        assert len(result["current_policy_content"]) > 0, "修正ポリシーが空文字列です"
        parsed = json.loads(result["current_policy_content"])
        assert isinstance(parsed, list), "ポリシーはリスト形式であるべき"
        assert result["retry_count"] == 2
        assert result["validation_error"] is None
```

### 2.7 handle_failure_node テスト

```python
class TestHandleFailureNode:
    """検証失敗時の最終処理ノードテスト"""

    @pytest.mark.legacy
    def test_normal_failure_legacy(self):
        """CSPM-ND-016: 通常の検証失敗時のlegacy互換性テスト

        [legacy] 現実装の不正キー名 `final_policy_yaml` での動作を確認する。
        実装が正規キー名に修正されたら、このテストを削除すること。
        CI除外: `pytest -m "not legacy"` で本線から除外される。
        """
        # Arrange
        state = {
            "validation_error": "Invalid filter type",
            "retry_count": 5,
            "current_policy_yaml": None,
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import handle_failure_node
        result = handle_failure_node(state)

        # Assert - legacy: 不正キー名での動作確認
        assert "final_policy_yaml" in result
        assert result["final_policy_yaml"] is None
        assert "failed after 5 attempts" in result["final_error"]
        assert result["final_determined_status"] == "generation_failed"
```

### 2.8 final_review_node テスト

```python
class TestFinalReviewNode:
    """最終レビューノードのテスト"""

    @pytest.fixture
    def review_state(self):
        """レビュー用State"""
        return {
            "current_policy_content": json.dumps([{
                "name": "test-policy",
                "resource": "aws.s3",
                "filters": [{"type": "value", "key": "BucketEncryption", "value": "absent"}],
            }]),
            "input_recommendation": {
                "uuid": "test-uuid",
                "recommendationId": "REC-001",
                "title": "Enable S3 Encryption",
                "description": "Ensure encryption",
                "audit": "Check settings",
                "rationale": "Data protection",
                "remediation": "Enable encryption",
            },
            "cloud_provider": "aws",
            "review_retry_count": 0,
            "remaining_steps": float("inf"),
        }

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.review.retrieve_reference")
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_approved(self, mock_init_llm, mock_rag, review_state):
        """CSPM-ND-017: レビューが承認された場合にstatus="active"が設定されること"""
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_rag.ainvoke = AsyncMock(return_value="Reference context")

        # 構造化出力のモック
        review_result = {
            "is_approved": True,
            "review_status": "approved",
            "issues_found": [],
            "recommendations": [],
            "review_summary": "ポリシーは適切です",
        }
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=review_result)

        with patch(
            "app.cspm_plugin.nodes.review.review_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            mock_prompt_chain = make_chainable_mock()
            type(mock_prompt).__or__ = MagicMock(return_value=mock_prompt_chain)
            type(mock_prompt_chain).__or__ = MagicMock(return_value=mock_chain)

            # Act
            from app.cspm_plugin.nodes.review import final_review_node
            result = await final_review_node(review_state)

        # Assert
        assert result["final_determined_status"] == "active"
        assert result["final_policy_content"] is not None
        assert result["final_error"] is None

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_policy_with_actions(self, mock_init_llm, review_state):
        """CSPM-ND-018: アクション含有ポリシーがrequires_manual_reviewになること

        nodes/review.py:106-114 の分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        # アクションを含むポリシー
        review_state["current_policy_content"] = json.dumps([{
            "name": "test-policy",
            "resource": "aws.s3",
            "filters": [],
            "actions": [{"type": "delete"}],
        }])

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(review_state)

        # Assert
        assert result["final_determined_status"] == "requires_manual_review"
        assert "actions" in result["final_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_policies_dict_format(self, mock_init):
        """CSPM-ND-025: {"policies":[...]}形式のポリシーが正常にパースされること

        nodes/review.py:77-83 の {"policies":[...]} 分岐をカバーする。
        パース構造テスト: アクション付きポリシーで早期リターンさせ、
        パース処理の到達を確認する。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        policies_dict = yaml.dump({
            "policies": [{
                "name": "test-policy",
                "resource": "aws.s3",
                "filters": [{"type": "value"}],
                "actions": [{"type": "delete"}],  # アクション付きで早期リターン
            }]
        })
        state = {
            "current_policy_content": policies_dict,
            "input_recommendation": {"title": "Test"},
            "cloud_provider": "aws",
        }

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(state)

        # Assert - アクション含有により手動レビュー
        assert result["final_determined_status"] == "requires_manual_review"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_single_object_format(self, mock_init):
        """CSPM-ND-026: {"name":"test",...}形式のポリシーが正常にパースされること

        nodes/review.py:91-93 の単一オブジェクト分岐をカバーする。
        パース構造テスト: アクション付きポリシーで早期リターンさせ、
        パース処理の到達を確認する。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        single_policy = yaml.dump({
            "name": "test-policy",
            "resource": "aws.s3",
            "filters": [{"type": "value"}],
            "actions": [{"type": "stop"}],  # アクション付きで早期リターン
        })
        state = {
            "current_policy_content": single_policy,
            "input_recommendation": {"title": "Test"},
            "cloud_provider": "aws",
        }

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(state)

        # Assert - アクション含有により手動レビュー
        assert result["final_determined_status"] == "requires_manual_review"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.review.retrieve_reference")
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_rag_error_response(self, mock_init_llm, mock_rag, review_state):
        """CSPM-ND-028: RAGツールがエラーを返した場合でもレビューが継続されること

        nodes/review.py:164-168 の retrieved_text.startswith("error:") 分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init_llm.return_value = mock_llm
        mock_rag.ainvoke = AsyncMock(return_value="Error: OpenSearch connection refused")

        review_result = {
            "is_approved": True,
            "review_status": "approved",
            "issues_found": [],
            "recommendations": [],
            "review_summary": "ポリシーは適切です",
        }
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=review_result)

        with patch(
            "app.cspm_plugin.nodes.review.review_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            mock_prompt_chain = make_chainable_mock()
            type(mock_prompt).__or__ = MagicMock(return_value=mock_prompt_chain)
            type(mock_prompt_chain).__or__ = MagicMock(return_value=mock_chain)

            # Act
            from app.cspm_plugin.nodes.review import final_review_node
            result = await final_review_node(review_state)

        # Assert - RAGエラーでもレビューが継続し成功すること
        assert result["final_determined_status"] == "active"
        assert isinstance(result["final_policy_content"], str)
        assert len(result["final_policy_content"]) > 0, "最終ポリシーが空文字列です"
        assert result["final_error"] is None
```

### 2.9 check_validation_node 境界値テスト

```python
class TestCheckValidationNodeBoundary:
    """検証条件ノードの境界値テスト"""

    def test_retry_count_just_below_max(self):
        """CSPM-ND-029: リトライ上限直前（retry_count=4）で"search_schema"を返すこと

        validation.py:101 の retry_count < MAX_VALIDATION_RETRIES（=5）の
        境界値をカバーする。retry_count=4 のとき 4 < 5 で True → "search_schema"。
        """
        # Arrange
        state = {
            "validation_error": "Invalid filter",
            "retry_count": 4,
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import check_validation_node
        result = check_validation_node(state)

        # Assert
        assert result == "search_schema"
```

---
