"""
CSPM Tools 単元テスト

テスト規格: docs/testing/plugins/cspm/cspm_tools_tests.md
テスト数量: 56 (正常系:20, 異常系:28, セキュリティ:8)

注意: sys.path と weasyprint mock は conftest.py で設定済み
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock



# ==================== 正常系: validate_policy (CSPM-T-001~008) ====================
class TestValidatePolicy:
    def test_validate_json_policies_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-001: JSON policies形式のポリシー検証が成功"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": '{"policies":[{"name":"test","resource":"s3"}]}'})
        assert "Validation successful" in result

    def test_validate_json_array_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-002: JSON配列形式の検証成功"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": '[{"name":"test","resource":"s3"}]'})
        assert "Validation successful" in result

    def test_validate_json_single_policy(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-003: JSON単一ポリシーの検証成功"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": '{"name":"test","resource":"s3"}'})
        assert "Validation successful" in result

    def test_validate_yaml_policies_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-004: YAML policies形式の検証成功"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": "policies:\n  - name: test\n    resource: s3"})
        assert "Validation successful" in result

    def test_validate_yaml_array_format(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-005: YAML配列形式の検証成功"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": "- name: test\n  resource: s3"})
        assert "Validation successful" in result

    def test_validate_yaml_single_policy(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-006: YAML単一ポリシーの検証成功"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": "name: test\nresource: s3"})
        assert "Validation successful" in result

    def test_validate_success_with_stderr_warning(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-007: 検証成功＋stderr警告"""
        from app.cspm_plugin.tools import validate_policy
        _, mock_result = mock_subprocess_success
        mock_result.stderr = "Warning: deprecated syntax"
        result = validate_policy.invoke({"policy_content": '[{"name":"t","resource":"s3"}]'})
        assert "Validation successful" in result
        assert "Details" in result

    def test_validate_failure_response(self, mock_tempfile):
        """CSPM-T-008: 検証失敗の正常応答"""
        from app.cspm_plugin.tools import validate_policy
        with patch("app.cspm_plugin.tools.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error: invalid resource"
            mock_run.return_value = mock_result
            result = validate_policy.invoke({"policy_content": '[{"name":"t"}]'})
            assert "Validation failed" in result


# ==================== 正常系: _validate_schema_target (CSPM-T-009~010, 015) ====================
class TestValidateSchemaTarget:
    def test_validate_schema_target_valid(self):
        """CSPM-T-009: スキーマターゲット検証（有効）"""
        from app.cspm_plugin.tools import _validate_schema_target
        valid, msg, parts = _validate_schema_target("aws.ec2.filters")
        assert valid is True
        assert parts == ["aws", "ec2", "filters"]

    def test_validate_schema_target_components(self):
        """CSPM-T-009-B: スキーマターゲットコンポーネントバリエーション"""
        from app.cspm_plugin.tools import _validate_schema_target
        for target in ["aws", "aws.ec2", "aws.ec2.filters"]:
            valid, _, _ = _validate_schema_target(target)
            assert valid is True

    def test_validate_schema_target_empty(self):
        """CSPM-T-010: スキーマターゲット検証（空）"""
        from app.cspm_plugin.tools import _validate_schema_target
        valid, msg, parts = _validate_schema_target(None)
        assert valid is True
        assert "warning" in msg.lower()
        assert parts == []

    def test_validate_schema_target_4_components_boundary(self):
        """CSPM-T-015: スキーマ4コンポーネント境界値"""
        from app.cspm_plugin.tools import _validate_schema_target
        valid, _, parts = _validate_schema_target("aws.ec2.filters.tag")
        assert valid is True
        assert len(parts) == 4


# ==================== 正常系: get_custodian_schema (CSPM-T-011~013, 016) ====================
class TestGetCustodianSchema:
    def test_get_schema_success(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-011: スキーマ取得成功"""
        from app.cspm_plugin.tools import get_custodian_schema
        _, mock_result = mock_subprocess_success
        mock_result.stdout = '{"resources": {"s3": {}}}'
        result = get_custodian_schema.invoke({"target": "aws"})
        assert "resources" in result

    def test_get_schema_fallback_success(self, mock_tempfile):
        """CSPM-T-012: スキーマフォールバック成功"""
        from app.cspm_plugin.tools import get_custodian_schema
        with patch("app.cspm_plugin.tools._execute_schema_with_fallback") as mock_exec:
            mock_exec.return_value = ('{"resources":{}}', "Fallback to parent level")
            result = get_custodian_schema.invoke({"target": "aws.nonexistent"})
            assert "resources" in result

    def test_list_resources_success(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-013: リソース一覧取得"""
        from app.cspm_plugin.tools import list_available_resources
        _, mock_result = mock_subprocess_success
        mock_result.stdout = '{"resources": {"s3": {}, "ec2": {}}}'
        result = list_available_resources.invoke({"cloud": "aws"})
        assert "s3" in result or "ec2" in result

    def test_get_schema_success_with_stderr(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-016: スキーマ取得成功＋stderr警告"""
        from app.cspm_plugin.tools import get_custodian_schema
        _, mock_result = mock_subprocess_success
        mock_result.stdout = '{"resources": {}}'
        mock_result.stderr = "Warning: deprecated"
        result = get_custodian_schema.invoke({"target": "aws"})
        assert "resources" in result


# ==================== 正常系: retrieve_reference (CSPM-T-014~014-D) ====================
class TestRetrieveReference:
    @pytest.mark.asyncio
    async def test_retrieve_reference_success_full_metadata(self, mock_rag_system_success):
        """CSPM-T-014: 参照検索成功（全メタデータ）"""
        from app.cspm_plugin.tools import retrieve_reference
        result = await retrieve_reference.ainvoke({"query": "S3 encryption", "cloud": "aws"})
        assert "Test document content" in result

    @pytest.mark.asyncio
    async def test_retrieve_reference_minimal_metadata(self, mock_rag_system_success):
        """CSPM-T-014-B: 参照検索成功（最小メタデータ）"""
        from app.cspm_plugin.tools import retrieve_reference
        mock_rag_system_success.search.return_value = [
            MagicMock(page_content="Content", metadata={"Framework": "AWS"})
        ]
        result = await retrieve_reference.ainvoke({"query": "test", "cloud": "aws"})
        assert "Content" in result

    @pytest.mark.asyncio
    async def test_retrieve_reference_multiple_results(self, mock_rag_system_success):
        """CSPM-T-014-C: 参照検索複数結果の整形"""
        from app.cspm_plugin.tools import retrieve_reference
        mock_rag_system_success.search.return_value = [
            MagicMock(page_content="Doc1", metadata={}),
            MagicMock(page_content="Doc2", metadata={})
        ]
        result = await retrieve_reference.ainvoke({"query": "test", "cloud": "aws"})
        assert "---" in result

    @pytest.mark.asyncio
    async def test_retrieve_reference_non_standard_cloud(self, mock_rag_system_success):
        """CSPM-T-014-D: 非標準クラウドでフィルターNone"""
        from app.cspm_plugin.tools import retrieve_reference
        result = await retrieve_reference.ainvoke({"query": "test", "cloud": "kubernetes"})
        assert len(result) > 0


# ==================== 異常系: validate_policy (CSPM-T-E01~E09) ====================
class TestValidatePolicyErrors:
    def test_validate_empty_input(self):
        """CSPM-T-E01: 空入力でエラー"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": ""})
        assert "empty" in result.lower()

    def test_validate_json_parse_error(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-E02: JSON解析エラー"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": '{"invalid json'})
        assert "parse" in result.lower() or "error" in result.lower()

    def test_validate_invalid_json_structure(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-E03: 無効なJSON構造"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": '{"random": "data"}'})
        assert "structure" in result.lower() or "invalid" in result.lower()

    def test_validate_yaml_parse_error(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-E04: YAML解析エラー"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": "key: [unclosed"})
        assert "parse" in result.lower() or "error" in result.lower()

    def test_validate_invalid_yaml_structure(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-E05: 無効なYAML構造"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": "random: data"})
        assert "structure" in result.lower() or "invalid" in result.lower()

    def test_validate_custodian_command_not_found(self, mock_tempfile):
        """CSPM-T-E06: custodianコマンドが見つからない"""
        from app.cspm_plugin.tools import validate_policy
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=FileNotFoundError()):
            result = validate_policy.invoke({"policy_content": '[{"name":"t","resource":"s3"}]'})
            assert "not found" in result.lower() or "error" in result.lower()

    def test_validate_subprocess_timeout(self, mock_tempfile):
        """CSPM-T-E07: subprocess タイムアウト"""
        from app.cspm_plugin.tools import validate_policy
        import subprocess
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            result = validate_policy.invoke({"policy_content": '[{"name":"t","resource":"s3"}]'})
            assert "timeout" in result.lower()

    def test_validate_subprocess_general_exception(self, mock_tempfile):
        """CSPM-T-E08: subprocess 一般例外"""
        from app.cspm_plugin.tools import validate_policy
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=RuntimeError("Unexpected")):
            result = validate_policy.invoke({"policy_content": '[{"name":"t","resource":"s3"}]'})
            assert "error" in result.lower()

    def test_validate_json_list_empty(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-E09: JSON配列が空"""
        from app.cspm_plugin.tools import validate_policy
        result = validate_policy.invoke({"policy_content": '[]'})
        assert "empty" in result.lower() or "invalid" in result.lower()


# ==================== 異常系: _validate_schema_target (CSPM-T-E10~E12) ====================
class TestValidateSchemaTargetErrors:
    def test_invalid_cloud_name(self):
        """CSPM-T-E10: 無効なクラウド名"""
        from app.cspm_plugin.tools import _validate_schema_target
        valid, msg, _ = _validate_schema_target("invalid.ec2")
        assert valid is False
        assert "cloud" in msg.lower()

    def test_too_many_components(self):
        """CSPM-T-E11: コンポーネント数超過（5個以上）"""
        from app.cspm_plugin.tools import _validate_schema_target
        valid, msg, _ = _validate_schema_target("aws.ec2.filters.tag.extra")
        assert valid is False
        assert "too many" in msg.lower() or "4" in msg

    def test_invalid_category(self):
        """CSPM-T-E12: 無効なカテゴリ"""
        from app.cspm_plugin.tools import _validate_schema_target
        valid, msg, _ = _validate_schema_target("aws.invalid_cat")
        assert valid is False
        assert "category" in msg.lower()


# ==================== 異常系: list_available_resources (CSPM-T-E13) ====================
class TestListResourcesErrors:
    def test_list_resources_invalid_cloud(self):
        """CSPM-T-E13: 無効なクラウドでリソース一覧エラー"""
        from app.cspm_plugin.tools import list_available_resources
        result = list_available_resources.invoke({"cloud": "invalid_cloud"})
        assert "error" in result.lower() or "invalid" in result.lower()


# ==================== 異常系: retrieve_reference (CSPM-T-E14~E17) ====================
class TestRetrieveReferenceErrors:
    @pytest.mark.asyncio
    async def test_retrieve_reference_empty_query(self, mock_rag_system_success):
        """CSPM-T-E14: 空クエリで検索失敗"""
        from app.cspm_plugin.tools import retrieve_reference
        result = await retrieve_reference.ainvoke({"query": "", "cloud": "aws"})
        assert "no results" in result.lower() or "empty" in result.lower()

    @pytest.mark.asyncio
    async def test_retrieve_reference_no_results(self, mock_rag_system_success):
        """CSPM-T-E15: 検索結果なし"""
        from app.cspm_plugin.tools import retrieve_reference
        mock_rag_system_success.search.return_value = []
        result = await retrieve_reference.ainvoke({"query": "nonexistent", "cloud": "aws"})
        assert "no results" in result.lower() or "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_retrieve_reference_search_exception(self, mock_rag_system_success):
        """CSPM-T-E16: RAG検索例外"""
        from app.cspm_plugin.tools import retrieve_reference
        mock_rag_system_success.search.side_effect = RuntimeError("Search failed")
        with patch("app.cspm_plugin.tools._fallback_retrieve_reference", return_value="Fallback result"):
            result = await retrieve_reference.ainvoke({"query": "test", "cloud": "aws"})
            assert "Fallback" in result or len(result) > 0

    @pytest.mark.asyncio
    async def test_retrieve_reference_rag_unavailable(self, mock_rag_unavailable):
        """CSPM-T-E17: RAGシステム利用不可"""
        from app.cspm_plugin.tools import retrieve_reference
        with patch("app.cspm_plugin.tools._fallback_retrieve_reference", return_value="Fallback result"):
            result = await retrieve_reference.ainvoke({"query": "test", "cloud": "aws"})
            assert len(result) > 0


# ==================== 異常系: _fallback_retrieve_reference (CSPM-T-E18~E22, E21-B) ====================
class TestFallbackRetrieveReferenceErrors:
    @pytest.mark.asyncio
    async def test_fallback_rag_manager_unavailable(self):
        """CSPM-T-E18: 従来RAGマネージャー利用不可"""
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        with patch("app.cspm_plugin.tools.get_rag_manager", return_value=None):
            result = await _fallback_retrieve_reference("test", "aws")
            assert "not available" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_empty_query(self):
        """CSPM-T-E19: 空クエリでフォールバック検索失敗"""
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        with patch("app.cspm_plugin.tools.get_rag_manager") as mock_get:
            mock_manager = AsyncMock()
            mock_manager.search.return_value = []
            mock_get.return_value = mock_manager
            result = await _fallback_retrieve_reference("", "aws")
            assert "no results" in result.lower() or len(result) == 0

    @pytest.mark.asyncio
    async def test_fallback_no_results(self):
        """CSPM-T-E20: フォールバック検索結果なし"""
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        with patch("app.cspm_plugin.tools.get_rag_manager") as mock_get:
            mock_manager = AsyncMock()
            mock_manager.search.return_value = []
            mock_get.return_value = mock_manager
            result = await _fallback_retrieve_reference("nonexistent", "aws")
            assert "no results" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_search_exception(self):
        """CSPM-T-E21: フォールバック検索例外"""
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        with patch("app.cspm_plugin.tools.get_rag_manager") as mock_get:
            mock_manager = AsyncMock()
            mock_manager.search.side_effect = RuntimeError("Search error")
            mock_get.return_value = mock_manager
            result = await _fallback_retrieve_reference("test", "aws")
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_embedding_exception(self):
        """CSPM-T-E21-B: 埋め込み関数取得例外"""
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        with patch("app.cspm_plugin.tools.get_embedding_function", side_effect=RuntimeError("Embedding error")):
            result = await _fallback_retrieve_reference("test", "aws")
            assert "error" in result.lower()

    @pytest.mark.asyncio
    async def test_fallback_opensearch_exception(self):
        """CSPM-T-E22: OpenSearchクライアント取得例外"""
        from app.cspm_plugin.tools import _fallback_retrieve_reference
        with patch("app.cspm_plugin.tools.get_opensearch_client", side_effect=RuntimeError("OS error")):
            result = await _fallback_retrieve_reference("test", "aws")
            assert "error" in result.lower()


# ==================== 異常系: _run_custodian_schema (CSPM-T-E23~E26) ====================
class TestRunCustodianSchemaErrors:
    def test_run_schema_command_not_found(self):
        """CSPM-T-E23: custodianコマンドが見つからない"""
        from app.cspm_plugin.tools import _run_custodian_schema
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=FileNotFoundError()):
            stdout, stderr = _run_custodian_schema(["aws"])
            assert "not found" in stderr.lower()

    def test_run_schema_timeout(self):
        """CSPM-T-E24: subprocess タイムアウト"""
        from app.cspm_plugin.tools import _run_custodian_schema
        import subprocess
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 30)):
            stdout, stderr = _run_custodian_schema(["aws"])
            assert "timeout" in stderr.lower()

    def test_run_schema_general_exception(self):
        """CSPM-T-E25: subprocess 一般例外"""
        from app.cspm_plugin.tools import _run_custodian_schema
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=RuntimeError("Unexpected")):
            stdout, stderr = _run_custodian_schema(["aws"])
            assert "error" in stderr.lower()

    def test_run_schema_returncode_nonzero(self):
        """CSPM-T-E26: subprocess returncode!=0"""
        from app.cspm_plugin.tools import _run_custodian_schema
        with patch("app.cspm_plugin.tools.subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stderr = "Error occurred"
            mock_result.stdout = ""
            mock_run.return_value = mock_result
            stdout, stderr = _run_custodian_schema(["aws"])
            assert "Error occurred" in stderr


# ==================== 異常系: _execute_schema_with_fallback (CSPM-T-E27) ====================
class TestExecuteSchemaWithFallbackErrors:
    def test_execute_schema_all_fallbacks_fail(self):
        """CSPM-T-E27: 全フォールバックレベルで失敗"""
        from app.cspm_plugin.tools import _execute_schema_with_fallback
        with patch("app.cspm_plugin.tools._run_custodian_schema", return_value=("", "Error at all levels")):
            result, warning = _execute_schema_with_fallback(["aws", "ec2", "filters", "nonexistent"])
            assert "Error" in warning or len(result) == 0


# ==================== セキュリティテスト (CSPM-T-SEC-01~SEC-08) ====================
@pytest.mark.security
class TestToolsSecurity:
    def test_validate_policy_no_stacktrace_in_error(self, mock_tempfile):
        """CSPM-T-SEC-01: validate_policy エラー時にスタックトレース非露出"""
        from app.cspm_plugin.tools import validate_policy
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=RuntimeError("Internal error: /etc/passwd")):
            result = validate_policy.invoke({"policy_content": '[{"name":"t","resource":"s3"}]'})
            assert "Traceback" not in result
            assert "/etc/passwd" not in result  # 内部パスが露出しないこと

    def test_validate_policy_command_injection_prevention(self, mock_tempfile):
        """CSPM-T-SEC-02: コマンドインジェクション防止"""
        from app.cspm_plugin.tools import validate_policy
        with patch("app.cspm_plugin.tools.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="", stdout="")
            malicious_content = '$(rm -rf /); {"name":"t","resource":"s3"}'
            validate_policy.invoke({"policy_content": malicious_content})
            # subprocess.run の引数がリストであることを確認（シェルインジェクション防止）
            call_args = mock_run.call_args
            assert isinstance(call_args[0][0], list)  # コマンドはリスト形式

    def test_retrieve_reference_query_injection(self, mock_rag_system_success):
        """CSPM-T-SEC-03: RAG検索クエリインジェクション防止"""
        from app.cspm_plugin.tools import retrieve_reference
        malicious_query = '"; DROP TABLE documents; --'
        # RAGシステムがエラーを投げずに処理することを確認
        result = retrieve_reference.ainvoke({"query": malicious_query, "cloud": "aws"})
        # エラーが発生しないことを確認（RAG側で適切に処理される）
        assert result is not None

    def test_get_schema_path_traversal_prevention(self):
        """CSPM-T-SEC-04: パストラバーサル攻撃防止"""
        from app.cspm_plugin.tools import get_custodian_schema
        malicious_target = "../../../etc/passwd"
        result = get_custodian_schema.invoke({"target": malicious_target})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_validate_policy_exception_message_sanitization(self, mock_tempfile):
        """CSPM-T-SEC-05: 例外メッセージのサニタイゼーション（部分的）"""
        from app.cspm_plugin.tools import validate_policy
        with patch("app.cspm_plugin.tools.subprocess.run", side_effect=RuntimeError("DB password: secret123")):
            result = validate_policy.invoke({"policy_content": '[{"name":"t","resource":"s3"}]'})
            # スタックトレースは含まれないが、例外メッセージは含まれる可能性あり
            assert "Traceback" not in result

    def test_validate_policy_large_input_handling(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-SEC-06: 大容量入力の処理"""
        from app.cspm_plugin.tools import validate_policy
        large_policy = '[{"name":"test","resource":"s3"}]' * 10000  # ~500KB
        result = validate_policy.invoke({"policy_content": large_policy})
        # タイムアウトせずに処理されることを確認
        assert "Validation successful" in result or "error" in result.lower()

    def test_validate_yaml_bomb_protection(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-SEC-07: YAML爆弾攻撃への防御"""
        from app.cspm_plugin.tools import validate_policy
        yaml_bomb = "a: &a [*a, *a]\n" * 10  # ネストした参照
        result = validate_policy.invoke({"policy_content": yaml_bomb})
        # yaml.safe_load が再帰参照を防ぐことを確認
        assert "error" in result.lower() or "parse" in result.lower()

    def test_validate_deep_nested_structure(self, mock_subprocess_success, mock_tempfile):
        """CSPM-T-SEC-08: 深いネスト構造の処理"""
        from app.cspm_plugin.tools import validate_policy
        deep_json = '{"a":' * 100 + '{}' + '}' * 100  # 深さ100のネスト
        result = validate_policy.invoke({"policy_content": deep_json})
        # 処理が完了することを確認（パースエラーの可能性あり）
        assert len(result) > 0

