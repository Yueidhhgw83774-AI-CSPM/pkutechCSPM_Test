# cspm_plugin ノード群 テストケース — 異常系

> 本ファイルは [cspm_nodes_tests.md](cspm_nodes_tests.md) のセクション3を分割したものです。
> 概要・フィクスチャ・実行例・サマリー・制限事項については本体を参照してください。

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CSPM-ND-E01 | 生成: LLM未初期化 | llm=None | validation_error="LLM is not available." |
| CSPM-ND-E02 | 生成: 推奨事項なし | recommendation=None | validation_error="Input recommendation missing." |
| CSPM-ND-E03 | 生成: リソース識別失敗 | identify→エラー | validation_error=識別エラー |
| CSPM-ND-E04 | 生成: JSON抽出失敗 | extract→エラー | validation_error="JSON extraction failed" |
| CSPM-ND-E05 | 生成: LLM例外 | chain.ainvoke→例外 | validation_error="LLM invocation failed..." |
| CSPM-ND-E06 | 強化版生成: LLM未初期化 | enhanced llm=None | validation_error="Enhanced LLM is not available." |
| CSPM-ND-E07 | 強化版生成: 推奨事項なし | recommendation=None | validation_error含む |
| CSPM-ND-E08 | check_generation: ポリシーなし | policy=None | "handle_generation_failure" |
| CSPM-ND-E08a | 生成失敗ノード: デフォルトメッセージ（legacy） | validation_error有り | [legacy] **`final_policy_yaml`** =None |
| CSPM-ND-E08a-spec | 生成失敗ノード: 仕様準拠キー名（本線） | 同上 | **`final_policy_content`** =None（現状fail→実装修正で解消） |
| CSPM-ND-E08b | 生成失敗ノード: フォールバック | state={} | デフォルトエラーメッセージ |
| CSPM-ND-E09 | 検証: ポリシーなし | current_policy_content=None | validation_error有り |
| CSPM-ND-E10 | 検証: ツール利用不可 | TOOLS_AVAILABLE=False | validation_error有り |
| CSPM-ND-E11 | 検証: ツール例外 | validate_policy→例外 | validation_error有り |
| CSPM-ND-E12 | check_validation: リトライ上限 | retry=5 | "handle_failure" |
| CSPM-ND-E13 | check_validation: 早期終了 | remaining_steps=3 | "handle_failure" |
| CSPM-ND-E14 | search_schema: エラーなし | validation_error=None | retrieved_schema=None |
| CSPM-ND-E15 | search_schema: リトライ上限 | retry_count≥2 | スキップメッセージ |
| CSPM-ND-E16 | search_schema: ツール不可 | TOOLS_AVAILABLE=False | ツール不可メッセージ |
| CSPM-ND-E16a | search_schema: リソース解析不能 | リソースパターンなしエラー + ツール有り | "Could not parse" フォールバック |
| CSPM-ND-E17 | fix: LLM未初期化 | llm=None | validation_error有り |
| CSPM-ND-E17a | fix: validation_errorなし | validation_error=None | retry_count+1, エラーメッセージ |
| CSPM-ND-E18 | fix: ポリシーなし | current_policy=None | retry_count+1 |
| CSPM-ND-E19 | fix: リトライ上限 | retry_count≥5 | retry_count+1, 上限メッセージ |
| CSPM-ND-E19a | fix: LLM例外 | chain.ainvoke→例外 | "Fix attempt failed with exception..." |
| CSPM-ND-E20 | handle_failure: 早期終了（legacy） | remaining_steps≤5 | [legacy] **`final_policy_yaml`** キー存在検証 + "terminated early" |
| CSPM-ND-E20-spec | handle_failure: 早期終了（本線仕様準拠） | 同上 | **`final_policy_content`** キー（現状fail→実装修正で解消） |
| CSPM-ND-E21 | handle_failure: 検証成功含み（legacy） | "Validation successful." 含む | [legacy] **`final_policy_yaml`** キー存在検証 + requires_manual_review |
| CSPM-ND-E21-spec | handle_failure: 検証成功含み（本線仕様準拠） | 同上 | **`final_policy_content`** キー（現状fail→実装修正で解消） |
| CSPM-ND-E22 | レビュー: ポリシーなし | validated_policy=None | status="error" |
| CSPM-ND-E23 | レビュー: 推奨事項なし | recommendation=None | status="error" |
| CSPM-ND-E24 | レビュー: LLMなし | llm=None | status="error" |
| CSPM-ND-E25 | レビュー: YAMLパースエラー | 不正なYAML | requires_manual_review |
| CSPM-ND-E26 | レビュー: 不承認→再生成 | is_approved=False, retry<MAX | needs_regeneration |
| CSPM-ND-E27 | レビュー: 不承認→上限到達 | retry≥MAX_REVIEW_RETRIES | requires_manual_review |
| CSPM-ND-E28 | レビュー: パーサー例外 | OutputParserException | requires_manual_review |
| CSPM-ND-E29 | レビュー: LLM例外 | chain.ainvoke→例外 | status="error" |
| CSPM-ND-E30 | check_final_review: 早期終了 | remaining_steps≤5 | "END" |

> **NOTE**: CSPM-ND-E30 のテストコードは [cspm_nodes_tests_normal.md](cspm_nodes_tests_normal.md) の `TestCheckFinalReviewNode` クラスに含まれています。

### 3.1 generate_policy_node 異常系

```python
class TestGeneratePolicyNodeErrors:
    """ポリシー生成ノードのエラーテスト"""

    @pytest.fixture
    def base_state(self):
        return {
            "input_recommendation": {
                "recommendationId": "REC-001",
                "uuid": "test-uuid",
                "title": "Test",
            },
            "cloud_provider": "aws",
            "messages": [],
            "retrieved_schema": None,
            "review_feedback": None,
        }

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm", return_value=None)
    async def test_llm_not_initialized(self, mock_init, base_state):
        """CSPM-ND-E01: LLM未初期化時のエラー

        nodes/policy_generation.py:86-100 の分岐をカバーする。
        """
        # Act
        from app.cspm_plugin.nodes.policy_generation import generate_policy_node
        result = await generate_policy_node(base_state)

        # Assert
        assert result["validation_error"] == "LLM is not available."
        assert result["current_policy_content"] is None

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    async def test_recommendation_missing(self, mock_init):
        """CSPM-ND-E02: 推奨事項なしのエラー

        nodes/policy_generation.py:101-114 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "input_recommendation": None,
            "cloud_provider": "aws",
            "messages": [],
            "retrieved_schema": None,
            "review_feedback": None,
        }

        # Act
        from app.cspm_plugin.nodes.policy_generation import generate_policy_node
        result = await generate_policy_node(state)

        # Assert
        assert result["validation_error"] == "Input recommendation missing."

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    async def test_resource_identification_failure(self, mock_init, mock_identify, base_state):
        """CSPM-ND-E03: リソース識別失敗時のエラー

        nodes/policy_generation.py:134-148 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        mock_identify.return_value = (None, "Tool returned error")

        # Act
        from app.cspm_plugin.nodes.policy_generation import generate_policy_node
        result = await generate_policy_node(base_state)

        # Assert
        assert "Tool returned error" in result["validation_error"]
        assert result["identified_resource"] is None

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.extract_and_format_policy_json")
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    async def test_json_extraction_failure(self, mock_init, mock_identify, mock_extract, base_state):
        """CSPM-ND-E04: JSON抽出失敗時のエラー

        nodes/policy_generation.py:265-278 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        mock_identify.return_value = ("aws.s3", None)
        mock_extract.return_value = (None, "No JSON block found.")

        mock_response = MagicMock()
        mock_response.content = "no json here"
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

        # Assert
        assert "JSON extraction failed" in result["validation_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.identify_resource_type_for_recommendation")
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_policy_llm")
    async def test_llm_invocation_exception(self, mock_init, mock_identify, base_state):
        """CSPM-ND-E05: LLM呼び出し中に例外が発生した場合

        nodes/policy_generation.py:297-311 の例外処理をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        mock_identify.return_value = ("aws.s3", None)

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("Connection timeout"))

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

        # Assert
        assert "LLM invocation failed" in result["validation_error"]
        assert result["current_policy_content"] is None

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_enhanced_llm", return_value=None)
    async def test_enhanced_llm_not_initialized(self, mock_init):
        """CSPM-ND-E06: 強化版LLM未初期化時のエラー

        nodes/policy_generation.py:328-340 の分岐をカバーする。
        """
        # Arrange
        state = {
            "input_recommendation": {"title": "Test"},
            "cloud_provider": "aws",
            "messages": [],
            "retrieved_schema": None,
            "review_feedback": None,
        }

        # Act
        from app.cspm_plugin.nodes.policy_generation import enhanced_generate_policy_node
        result = await enhanced_generate_policy_node(state)

        # Assert
        assert "LLM" in result["validation_error"] or "not available" in result["validation_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.policy_generation.initialize_enhanced_llm")
    async def test_enhanced_recommendation_missing(self, mock_init):
        """CSPM-ND-E07: 強化版生成で推奨事項なし時のエラー

        nodes/policy_generation.py:341-356 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "input_recommendation": None,
            "cloud_provider": "aws",
            "messages": [],
            "retrieved_schema": None,
            "review_feedback": None,
        }

        # Act
        from app.cspm_plugin.nodes.policy_generation import enhanced_generate_policy_node
        result = await enhanced_generate_policy_node(state)

        # Assert
        assert result["validation_error"] is not None

    def test_check_generation_no_policy(self):
        """CSPM-ND-E08: ポリシーなしで"handle_generation_failure"を返すこと

        nodes/policy_generation.py:555-557 の分岐をカバーする。
        """
        # Arrange
        state = {"current_policy_content": None, "validation_error": "Some error"}

        # Act
        from app.cspm_plugin.nodes.policy_generation import check_generation_success
        result = check_generation_success(state)

        # Assert
        assert result == "handle_generation_failure"


class TestHandleGenerationFailureNode:
    """生成失敗時の処理ノードテスト"""

    @pytest.mark.legacy
    def test_default_error_message_legacy(self):
        """CSPM-ND-E08a: 生成失敗ノードのlegacy互換性テスト

        [legacy] 現実装の不正キー名 `final_policy_yaml` での動作を確認する。
        実装が正規キー名に修正されたら、このテストを削除すること。
        CI除外: `pytest -m "not legacy"` で本線から除外される。
        """
        # Arrange
        state = {"validation_error": "LLM is not available."}

        # Act
        from app.cspm_plugin.nodes.policy_generation import handle_generation_failure_node
        result = handle_generation_failure_node(state)

        # Assert - legacy: 不正キー名での動作確認
        assert result["final_policy_yaml"] is None
        assert "Policy generation failed" in result["final_error"]
        assert "LLM is not available." in result["final_error"]
        assert result["final_determined_status"] == "generation_failed"

    def test_default_error_message_spec_compliant(self):
        """CSPM-ND-E08a-spec: 生成失敗ノードが正規キー名で返却すること（仕様準拠テスト）

        PolicyGenerationState の正規フィールド `final_policy_content` で返却されるべき。
        NOTE: 現状の実装はこのテストに失敗する（契約違反）。
        CI本線に含めることで実装修正を強制する。
        """
        # Arrange
        state = {"validation_error": "LLM is not available."}

        # Act
        from app.cspm_plugin.nodes.policy_generation import handle_generation_failure_node
        result = handle_generation_failure_node(state)

        # Assert - 正規キー名で返却されること
        assert "final_policy_content" in result, "正規キー final_policy_content が存在しません"
        assert result["final_policy_content"] is None
        assert result["final_determined_status"] == "generation_failed"

    def test_fallback_error_message(self):
        """CSPM-ND-E08b: validation_errorがない場合にデフォルトメッセージが使用されること

        nodes/policy_generation.py:572 の state.get デフォルト値をカバーする。
        NOTE: このテストはキー名互換性テストではなく、
        state={} 時のデフォルト値検証テストです。
        """
        # Arrange
        state = {}

        # Act
        from app.cspm_plugin.nodes.policy_generation import handle_generation_failure_node
        result = handle_generation_failure_node(state)

        # Assert
        assert "Policy generation failed" in result["final_error"]
        assert result["final_determined_status"] == "generation_failed"
```

### 3.2 validation ノード群 異常系

```python
class TestValidatePolicyNodeErrors:
    """ポリシー検証ノードのエラーテスト"""

    def test_no_policy_content(self):
        """CSPM-ND-E09: ポリシーなし時のエラー

        validation.py:44-48 の分岐をカバーする。
        """
        # Arrange
        state = {"current_policy_content": None}

        # Act
        from app.cspm_plugin.nodes.validation import validate_policy_node
        result = validate_policy_node(state)

        # Assert
        assert "No policy JSON" in result["validation_error"]

    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", False)
    def test_tools_unavailable(self):
        """CSPM-ND-E10: ツール利用不可時のエラー

        validation.py:50-53 の分岐をカバーする。
        """
        # Arrange
        state = {"current_policy_content": '[{"name":"test"}]'}

        # Act
        from app.cspm_plugin.nodes.validation import validate_policy_node
        result = validate_policy_node(state)

        # Assert
        assert "not available" in result["validation_error"]

    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.validate_policy")
    def test_validation_exception(self, mock_validate):
        """CSPM-ND-E11: 検証中に例外が発生した場合

        validation.py:73-77 の例外処理をカバーする。
        """
        # Arrange
        mock_validate.invoke.side_effect = RuntimeError("Connection refused")
        state = {"current_policy_content": '[{"name":"test"}]'}

        # Act
        from app.cspm_plugin.nodes.validation import validate_policy_node
        result = validate_policy_node(state)

        # Assert
        assert "Validation error" in result["validation_error"]


class TestCheckValidationNodeErrors:
    """検証結果条件分岐のエラーテスト"""

    def test_max_retries_reached(self):
        """CSPM-ND-E12: リトライ上限到達時に"handle_failure"を返すこと

        validation.py:104-106 の分岐をカバーする。
        """
        # Arrange
        state = {
            "validation_error": "Still failing",
            "retry_count": 5,
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import check_validation_node
        result = check_validation_node(state)

        # Assert
        assert result == "handle_failure"

    def test_early_termination(self):
        """CSPM-ND-E13: 残りステップ数が閾値以下の場合に"handle_failure"を返すこと

        validation.py:94-96 の早期終了分岐をカバーする。
        """
        # Arrange
        state = {
            "validation_error": None,
            "retry_count": 0,
            "remaining_steps": 3,
        }

        # Act
        from app.cspm_plugin.nodes.validation import check_validation_node
        result = check_validation_node(state)

        # Assert
        assert result == "handle_failure"


class TestSearchSchemaNodeErrors:
    """スキーマ検索ノードのエラーテスト"""

    @pytest.mark.asyncio
    async def test_no_validation_error(self):
        """CSPM-ND-E14: エラーなし時にNoneを返すこと

        validation.py:117-118 の分岐をカバーする。
        """
        # Arrange
        state = {"validation_error": None, "cloud_provider": "aws", "retry_count": 0}

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        assert result["retrieved_schema"] is None

    @pytest.mark.asyncio
    async def test_retry_limit_skip(self):
        """CSPM-ND-E15: リトライ上限でスキーマ検索がスキップされること

        validation.py:121-123 の分岐をカバーする。
        """
        # Arrange
        state = {
            "validation_error": "Some error",
            "cloud_provider": "aws",
            "retry_count": 2,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        assert "skipped" in result["retrieved_schema"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", False)
    async def test_tools_unavailable(self):
        """CSPM-ND-E16: ツール利用不可時のフォールバック

        validation.py:126-128 の分岐をカバーする。
        """
        # Arrange
        state = {
            "validation_error": "Some error",
            "cloud_provider": "aws",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert
        assert "unavailable" in result["retrieved_schema"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.validation.get_custodian_schema")
    @patch("app.cspm_plugin.nodes.validation.list_available_resources")
    async def test_unparseable_error_fallback(self, mock_list, mock_schema):
        """CSPM-ND-E16a: リソースパターンが解析できないエラーの場合にフォールバックすること

        validation.py:174-182 の resource_type も invalid resource も
        マッチしない場合のフォールバックパスをカバーする。
        """
        # Arrange
        state = {
            "validation_error": "Some generic error without resource info",
            "cloud_provider": "aws",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import search_schema_node
        result = await search_schema_node(state)

        # Assert - ツールが呼ばれず、フォールバックメッセージが返ること
        mock_schema.invoke.assert_not_called()
        mock_list.invoke.assert_not_called()
        assert result["retrieved_schema"] is not None
        assert "Could not parse" in result["retrieved_schema"] or "No specific" in result["retrieved_schema"]


class TestFixPolicyNodeErrors:
    """ポリシー修正ノードのエラーテスト"""

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm", return_value=None)
    async def test_llm_not_available(self, mock_init):
        """CSPM-ND-E17: LLM未初期化時のエラー

        validation.py:239-240 の分岐をカバーする。
        """
        # Arrange
        state = {
            "current_policy_content": '[{"name":"test"}]',
            "validation_error": "error",
            "retry_count": 0,
        }

        # Act
        from app.cspm_plugin.nodes.validation import fix_policy_node
        result = await fix_policy_node(state)

        # Assert
        assert "LLM not available" in result["validation_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm")
    async def test_no_validation_error(self, mock_init):
        """CSPM-ND-E17a: validation_errorがNone時のエラー

        validation.py:257-262 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "current_policy_content": '[{"name":"test"}]',
            "validation_error": None,
            "retry_count": 1,
        }

        # Act
        from app.cspm_plugin.nodes.validation import fix_policy_node
        result = await fix_policy_node(state)

        # Assert
        assert result["retry_count"] == 2
        assert "No validation error" in result["validation_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm")
    async def test_no_policy_content(self, mock_init):
        """CSPM-ND-E18: ポリシーなし時のエラー

        validation.py:250-255 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "current_policy_content": None,
            "validation_error": "error",
            "retry_count": 1,
        }

        # Act
        from app.cspm_plugin.nodes.validation import fix_policy_node
        result = await fix_policy_node(state)

        # Assert
        assert result["retry_count"] == 2
        assert "No policy content" in result["validation_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm")
    async def test_max_retry_exceeded(self, mock_init):
        """CSPM-ND-E19: リトライ上限到達時のエラー

        validation.py:265-270 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "current_policy_content": '[{"name":"test"}]',
            "validation_error": "error",
            "retry_count": 5,
        }

        # Act
        from app.cspm_plugin.nodes.validation import fix_policy_node
        result = await fix_policy_node(state)

        # Assert
        assert result["retry_count"] == 6
        assert "Maximum retry" in result["validation_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.validation.initialize_policy_llm")
    async def test_fix_policy_exception(self, mock_init):
        """CSPM-ND-E19a: fix_policy_nodeでLLM呼び出し中に例外が発生した場合

        validation.py:325-331 の例外処理をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init.return_value = mock_llm

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(side_effect=RuntimeError("Connection timeout"))

        with patch(
            "app.cspm_plugin.nodes.validation.fix_policy_prompt",
            new=make_chainable_mock(),
        ) as mock_prompt:
            type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": '[{"name":"test"}]',
                "validation_error": "Invalid filter",
                "retrieved_schema": "Schema data",
                "retry_count": 2,
            }

            # Act
            from app.cspm_plugin.nodes.validation import fix_policy_node
            result = await fix_policy_node(state)

        # Assert
        assert "Fix attempt failed with exception" in result["validation_error"]
        assert result["retry_count"] == 3


class TestHandleFailureNodeErrors:
    """検証失敗処理ノードのエラーテスト"""

    @pytest.mark.legacy
    def test_early_termination_message_legacy(self):
        """CSPM-ND-E20: 早期終了時のlegacy互換性テスト

        [legacy] 現実装の不正キー名 `final_policy_yaml` での動作を確認する。
        実装が正規キー名に修正されたら、このテストを削除すること。
        CI除外: `pytest -m "not legacy"` で本線から除外される。
        """
        # Arrange
        state = {
            "validation_error": "Still failing",
            "retry_count": 2,
            "current_policy_yaml": None,
            "remaining_steps": 3,
        }

        # Act
        from app.cspm_plugin.nodes.validation import handle_failure_node
        result = handle_failure_node(state)

        # Assert - legacy: 不正キー名での動作確認
        assert "final_policy_yaml" in result
        assert "terminated early" in result["final_error"]
        assert "Remaining steps:" in result["final_error"]
        assert result["final_determined_status"] == "generation_failed"

    def test_early_termination_spec_compliant(self):
        """CSPM-ND-E20-spec: 早期終了時に正規キー名で返却すること（仕様準拠テスト）

        PolicyGenerationState の正規フィールド `final_policy_content` で返却されるべき。
        NOTE: 現状の実装はこのテストに失敗する（契約違反）。
        CI本線に含めることで実装修正を強制する。
        """
        # Arrange
        state = {
            "validation_error": "Still failing",
            "retry_count": 2,
            "current_policy_content": None,
            "remaining_steps": 3,
        }

        # Act
        from app.cspm_plugin.nodes.validation import handle_failure_node
        result = handle_failure_node(state)

        # Assert - 正規キー名で返却されること
        assert "final_policy_content" in result, "正規キー final_policy_content が存在しません"
        assert result["final_determined_status"] == "generation_failed"

    @pytest.mark.legacy
    def test_validation_success_in_error_legacy(self):
        """CSPM-ND-E21: 検証成功含みエラーのlegacy互換性テスト

        [legacy] 現実装の不正キー名 `current_policy_yaml`/`final_policy_yaml` での動作を確認する。
        実装が正規キー名に修正されたら、このテストを削除すること。
        CI除外: `pytest -m "not legacy"` で本線から除外される。
        """
        # Arrange
        state = {
            "validation_error": "Validation successful. But step limit",
            "retry_count": 3,
            "current_policy_yaml": "name: test\nresource: aws.s3",
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import handle_failure_node
        result = handle_failure_node(state)

        # Assert - legacy: 不正キー名での動作確認
        assert "final_policy_yaml" in result
        assert result["final_policy_yaml"] is not None
        assert result["final_policy_yaml"] == "name: test\nresource: aws.s3"
        assert result["final_determined_status"] == "requires_manual_review"
        assert "Warning:" in result["final_error"]

    def test_validation_success_spec_compliant(self):
        """CSPM-ND-E21-spec: 正規キー名で state を読み書きすること（仕様準拠テスト）

        PolicyGenerationState の正規フィールド `current_policy_content`（入力）/
        `final_policy_content`（出力）で処理されるべき。
        NOTE: 現状の実装はこのテストに失敗する（契約違反）。
        CI本線に含めることで実装修正を強制する。
        """
        # Arrange - 正規キー名でStateを構築
        state = {
            "validation_error": "Validation successful. But step limit",
            "retry_count": 3,
            "current_policy_content": "name: test\nresource: aws.s3",
            "remaining_steps": float("inf"),
        }

        # Act
        from app.cspm_plugin.nodes.validation import handle_failure_node
        result = handle_failure_node(state)

        # Assert - 正規キー名で返却されること
        assert "final_policy_content" in result, "正規キー final_policy_content が存在しません"
        assert result["final_determined_status"] == "requires_manual_review"
        assert result["final_policy_content"] is not None
```

### 3.3 review ノード 異常系

```python
class TestFinalReviewNodeErrors:
    """最終レビューノードのエラーテスト"""

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_no_validated_policy(self, mock_init):
        """CSPM-ND-E22: ポリシーなし時のエラー

        nodes/review.py:47-53 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "current_policy_content": None,
            "input_recommendation": {"title": "test"},
            "cloud_provider": "aws",
        }

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "error"
        assert "missing" in result["final_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_no_recommendation(self, mock_init):
        """CSPM-ND-E23: 推奨事項なし時のエラー

        nodes/review.py:54-60 の分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "current_policy_content": '[{"name":"test"}]',
            "input_recommendation": None,
            "cloud_provider": "aws",
        }

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "error"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm", return_value=None)
    async def test_llm_not_available(self, mock_init):
        """CSPM-ND-E24: LLMなし時のエラー

        nodes/review.py:61-67 の分岐をカバーする。
        """
        # Arrange
        state = {
            "current_policy_content": '[{"name":"test"}]',
            "input_recommendation": {"title": "test"},
            "cloud_provider": "aws",
        }

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "error"
        assert "LLM not available" in result["final_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_yaml_parse_error(self, mock_init):
        """CSPM-ND-E25: YAMLパースエラー時にrequires_manual_reviewになること

        nodes/review.py:116-123 の YAMLError 分岐をカバーする。
        """
        # Arrange
        mock_init.return_value = MagicMock()
        state = {
            "current_policy_content": "{{invalid: yaml: content",
            "input_recommendation": {"title": "test"},
            "cloud_provider": "aws",
        }

        # Act
        from app.cspm_plugin.nodes.review import final_review_node
        result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "requires_manual_review"
        assert result["final_policy_content"] is not None  # パース失敗でもポリシーは返す

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.review.retrieve_reference")
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_rejected_with_retry(self, mock_init, mock_rag):
        """CSPM-ND-E26: レビュー不承認でリトライ可能な場合にneeds_regenerationになること

        nodes/review.py:227-239 の分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init.return_value = mock_llm
        mock_rag.ainvoke = AsyncMock(return_value="Reference")

        review_result = {
            "is_approved": False,
            "review_status": "needs_modification",
            "issues_found": ["Filter condition is incorrect"],
            "recommendations": ["Use correct filter type"],
            "review_summary": "フィルター条件が不適切です",
        }
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=review_result)

        with patch("app.cspm_plugin.nodes.review.review_prompt", new=make_chainable_mock()) as mock_prompt:
            mock_prompt_chain = make_chainable_mock()
            type(mock_prompt).__or__ = MagicMock(return_value=mock_prompt_chain)
            type(mock_prompt_chain).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": json.dumps([{"name": "test", "resource": "aws.s3", "filters": []}]),
                "input_recommendation": {"uuid": "u1", "recommendationId": "R1", "title": "T"},
                "cloud_provider": "aws",
                "review_retry_count": 0,
            }

            # Act
            from app.cspm_plugin.nodes.review import final_review_node
            result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "needs_regeneration"
        assert result["review_feedback"] is not None
        assert result["review_retry_count"] == 1

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.review.retrieve_reference")
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_rejected_max_retries(self, mock_init, mock_rag):
        """CSPM-ND-E27: レビュー不承認でリトライ上限到達時にrequires_manual_reviewになること

        nodes/review.py:240-244 の分岐をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init.return_value = mock_llm
        mock_rag.ainvoke = AsyncMock(return_value="Reference")

        review_result = {
            "is_approved": False,
            "review_status": "critical_issue",
            "issues_found": ["Critical issue"],
            "recommendations": [],
            "review_summary": "重大な問題があります",
        }
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=review_result)

        with patch("app.cspm_plugin.nodes.review.review_prompt", new=make_chainable_mock()) as mock_prompt:
            mock_prompt_chain = make_chainable_mock()
            type(mock_prompt).__or__ = MagicMock(return_value=mock_prompt_chain)
            type(mock_prompt_chain).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": json.dumps([{"name": "test", "resource": "aws.s3", "filters": []}]),
                "input_recommendation": {"uuid": "u1", "recommendationId": "R1", "title": "T"},
                "cloud_provider": "aws",
                "review_retry_count": 4,  # MAX_REVIEW_RETRIES に到達
            }

            # Act
            from app.cspm_plugin.nodes.review import final_review_node
            result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "requires_manual_review"

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.review.retrieve_reference")
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_parser_exception(self, mock_init, mock_rag):
        """CSPM-ND-E28: OutputParserException時にrequires_manual_reviewになること

        nodes/review.py:246-252 の例外処理をカバーする。
        """
        # Arrange
        from langchain_core.exceptions import OutputParserException

        mock_llm = MagicMock()
        mock_init.return_value = mock_llm
        mock_rag.ainvoke = AsyncMock(return_value="Reference")

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(
            side_effect=OutputParserException("Invalid JSON output")
        )

        with patch("app.cspm_plugin.nodes.review.review_prompt", new=make_chainable_mock()) as mock_prompt:
            mock_prompt_chain = make_chainable_mock()
            type(mock_prompt).__or__ = MagicMock(return_value=mock_prompt_chain)
            type(mock_prompt_chain).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": json.dumps([{"name": "test", "resource": "aws.s3", "filters": []}]),
                "input_recommendation": {"uuid": "u1", "recommendationId": "R1", "title": "T"},
                "cloud_provider": "aws",
                "review_retry_count": 0,
            }

            # Act
            from app.cspm_plugin.nodes.review import final_review_node
            result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "requires_manual_review"
        assert "parsing failed" in result["final_error"]

    @pytest.mark.asyncio
    @patch("app.cspm_plugin.nodes.review.TOOLS_AVAILABLE", True)
    @patch("app.cspm_plugin.nodes.review.retrieve_reference")
    @patch("app.cspm_plugin.nodes.review.initialize_review_llm")
    async def test_review_llm_exception(self, mock_init, mock_rag):
        """CSPM-ND-E29: LLM呼び出し中に一般例外が発生した場合

        nodes/review.py:254-259 の例外処理をカバーする。
        """
        # Arrange
        mock_llm = MagicMock()
        mock_init.return_value = mock_llm
        mock_rag.ainvoke = AsyncMock(return_value="Reference")

        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(
            side_effect=RuntimeError("LLM service unavailable")
        )

        with patch("app.cspm_plugin.nodes.review.review_prompt", new=make_chainable_mock()) as mock_prompt:
            mock_prompt_chain = make_chainable_mock()
            type(mock_prompt).__or__ = MagicMock(return_value=mock_prompt_chain)
            type(mock_prompt_chain).__or__ = MagicMock(return_value=mock_chain)

            state = {
                "current_policy_content": json.dumps([{"name": "test", "resource": "aws.s3", "filters": []}]),
                "input_recommendation": {"uuid": "u1", "recommendationId": "R1", "title": "T"},
                "cloud_provider": "aws",
                "review_retry_count": 0,
            }

            # Act
            from app.cspm_plugin.nodes.review import final_review_node
            result = await final_review_node(state)

        # Assert
        assert result["final_determined_status"] == "error"
        assert "Error during final review" in result["final_error"]
```

---
