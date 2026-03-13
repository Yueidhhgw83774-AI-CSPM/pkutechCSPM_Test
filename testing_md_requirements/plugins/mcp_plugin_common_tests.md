# mcp_plugin/common テストケース

## 1. 概要

共通モジュール（`common/`）のテストケースを定義します。Deep Agentsと階層型エージェントの両方から使用される共通機能を包括的にテストします。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `generate_tool_summary` | ツール結果の要約生成 |
| `validate_documentation_url` | ドキュメントURLの検証 |
| `todo_manager` | TODOリスト管理 |
| `evidence_extractor` | evidence抽出 |
| `result_structurer` | 結果構造化 |
| `progress_persister` | 進捗永続化 |
| `policy_detector` | ポリシー検出 |
| `unified_sse_emitter` | 統一SSEイベント発行 |

### 1.2 モジュール構成

| ファイル | 説明 |
|---------|------|
| `summarizer/` | ツール結果要約（tool_summarizer.py, response_utils.py, session_generator.py） |
| `url_validator.py` | URL検証 |
| `todo_manager.py` | TODOリスト管理 |
| `evidence_extractor.py` | evidence抽出 |
| `result_structurer.py` | 結果構造化 |
| `progress_persister.py` | 進捗永続化 |
| `policy_detector.py` | ポリシー検出 |
| `unified_sse_emitter.py` | 統一SSEイベント発行 |
| `background_tasks.py` | バックグラウンドタスク |

### 1.3 カバレッジ目標: 85%

> **注記**: ユーティリティモジュールのため高カバレッジが期待できる

### 1.4 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/mcp_plugin/common/` |
| テストコード | `test/unit/mcp_plugin/common/test_*.py` |
| conftest | `test/unit/mcp_plugin/common/conftest.py` |

### 1.5 補足情報

**モジュール依存ルール:**
- このモジュールは `app/core/` のみに依存可能
- `hierarchical/`, `deep_agents/`, `sessions/` からのインポートは禁止（循環参照防止）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPCO-001 | ツール要約生成成功 | tool results | summary text |
| MCPCO-002 | URL検証成功（有効なURL） | valid doc URL | True |
| MCPCO-003 | URL検証失敗（無効なURL） | invalid URL | False |
| MCPCO-004 | TODOリスト追加 | todo item | item added |
| MCPCO-005 | TODOリスト更新 | todo item update | item updated |
| MCPCO-006 | evidence抽出成功 | text with evidence | extracted evidence |
| MCPCO-007 | 結果構造化成功 | raw results | structured results |
| MCPCO-008 | 進捗永続化成功 | progress data | data saved |
| MCPCO-009 | ポリシー検出成功 | text with policy | detected policy |
| MCPCO-010 | SSEイベント発行成功 | event data | SSE formatted |

### 2.1 要約生成テスト

```python
# test/unit/mcp_plugin/common/test_summarizer.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestToolSummarizer:
    """ツール要約生成のテスト"""

    @pytest.mark.asyncio
    async def test_generate_tool_summary_success(self, mock_llm):
        """MCPCO-001: ツール要約生成成功"""
        # Arrange
        from app.mcp_plugin.common import generate_tool_summary

        mock_llm.ainvoke.return_value = MagicMock(content="要約されたツール結果")

        tool_results = [
            {"tool": "search", "result": "検索結果1"},
            {"tool": "get_details", "result": "詳細情報"}
        ]

        # Act
        with patch("app.mcp_plugin.common.summarizer.tool_summarizer.get_summary_llm", return_value=mock_llm):
            summary = await generate_tool_summary(tool_results)

        # Assert
        assert summary is not None
        assert len(summary) > 0
```

### 2.2 URL検証テスト

```python
class TestURLValidator:
    """URL検証のテスト"""

    def test_validate_url_valid(self):
        """MCPCO-002: URL検証成功（有効なURL）"""
        # Arrange
        from app.mcp_plugin.common import validate_documentation_url

        valid_urls = [
            "https://docs.aws.amazon.com/lambda/",
            "https://learn.microsoft.com/azure/",
            "https://cloud.google.com/docs/"
        ]

        # Act & Assert
        for url in valid_urls:
            assert validate_documentation_url(url) is True

    def test_validate_url_invalid(self):
        """MCPCO-003: URL検証失敗（無効なURL）"""
        # Arrange
        from app.mcp_plugin.common import validate_documentation_url

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "https://malicious-site.com/phishing",
            ""
        ]

        # Act & Assert
        for url in invalid_urls:
            assert validate_documentation_url(url) is False
```

### 2.3 TODOマネージャーテスト

```python
class TestTodoManager:
    """TODOマネージャーのテスト"""

    def test_add_todo_item(self):
        """MCPCO-004: TODOリスト追加"""
        # Arrange
        from app.mcp_plugin.common.todo_manager import TodoManager

        manager = TodoManager()
        todo_item = {
            "id": "todo-001",
            "description": "ドキュメント検索",
            "status": "pending"
        }

        # Act
        manager.add_item(todo_item)

        # Assert
        items = manager.get_items()
        assert len(items) == 1
        assert items[0]["id"] == "todo-001"

    def test_update_todo_item(self):
        """MCPCO-005: TODOリスト更新"""
        # Arrange
        from app.mcp_plugin.common.todo_manager import TodoManager

        manager = TodoManager()
        manager.add_item({
            "id": "todo-001",
            "description": "タスク",
            "status": "pending"
        })

        # Act
        manager.update_item("todo-001", {"status": "completed"})

        # Assert
        items = manager.get_items()
        assert items[0]["status"] == "completed"
```

### 2.4 evidence抽出テスト

```python
class TestEvidenceExtractor:
    """evidence抽出のテスト"""

    def test_extract_evidence_success(self):
        """MCPCO-006: evidence抽出成功"""
        # Arrange
        from app.mcp_plugin.common.evidence_extractor import extract_evidence

        text_with_evidence = """
        検索結果:
        - AWS Lambda は最大15分のタイムアウトをサポートしています。
        - メモリは128MB〜10GBの範囲で設定可能です。

        ソース: AWS公式ドキュメント
        """

        # Act
        evidence = extract_evidence(text_with_evidence)

        # Assert
        assert evidence is not None
        assert len(evidence) > 0
```

### 2.5 結果構造化テスト

```python
class TestResultStructurer:
    """結果構造化のテスト"""

    def test_structure_results_success(self):
        """MCPCO-007: 結果構造化成功"""
        # Arrange
        from app.mcp_plugin.common.result_structurer import structure_results

        raw_results = [
            {"source": "search", "content": "検索結果1"},
            {"source": "api", "content": "API結果"}
        ]

        # Act
        structured = structure_results(raw_results)

        # Assert
        assert structured is not None
        assert "results" in structured or isinstance(structured, list)
```

### 2.6 進捗永続化テスト

```python
class TestProgressPersister:
    """進捗永続化のテスト"""

    @pytest.mark.asyncio
    async def test_persist_progress_success(self, mock_opensearch):
        """MCPCO-008: 進捗永続化成功"""
        # Arrange
        from app.mcp_plugin.common.progress_persister import persist_progress

        progress_data = {
            "session_id": "test-session",
            "step": "mcp_search",
            "status": "in_progress",
            "timestamp": "2026-01-30T12:00:00Z"
        }

        mock_opensearch.index.return_value = {"result": "created"}

        # Act
        with patch("app.mcp_plugin.common.progress_persister.get_opensearch_client", return_value=mock_opensearch):
            result = await persist_progress(progress_data)

        # Assert
        assert result is True
```

### 2.7 ポリシー検出テスト

```python
class TestPolicyDetector:
    """ポリシー検出のテスト"""

    def test_detect_policy_success(self):
        """MCPCO-009: ポリシー検出成功"""
        # Arrange
        from app.mcp_plugin.common.policy_detector import detect_policy

        text_with_policy = """
        以下のCloud Custodianポリシーを生成しました:

        ```yaml
        policies:
          - name: ec2-unused-eip
            resource: ec2
            filters:
              - type: value
                key: State.Name
                value: stopped
        ```
        """

        # Act
        detected = detect_policy(text_with_policy)

        # Assert
        assert detected is not None
        assert "policies" in str(detected) or detected.get("found") is True
```

### 2.8 SSEイベント発行テスト

```python
class TestUnifiedSSEEmitter:
    """統一SSEイベント発行のテスト"""

    def test_emit_sse_event(self):
        """MCPCO-010: SSEイベント発行成功"""
        # Arrange
        from app.mcp_plugin.common.unified_sse_emitter import format_sse_event

        event_type = "task_complete"
        event_data = {
            "task_id": "task-001",
            "result": "検索完了"
        }

        # Act
        sse_formatted = format_sse_event(event_type, event_data)

        # Assert
        assert f"event: {event_type}" in sse_formatted
        assert "data:" in sse_formatted
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPCO-E01 | ツール要約生成エラー | LLM error | fallback or error |
| MCPCO-E02 | evidence抽出エラー | malformed text | empty result |
| MCPCO-E03 | 進捗永続化エラー | OpenSearch error | False |
| MCPCO-E04 | ポリシー検出エラー | no policy text | None or empty |
| MCPCO-E05 | TODO項目未発見 | unknown id | error or None |

### 3.1 エラーハンドリングテスト

```python
class TestCommonErrors:
    """共通モジュールエラーのテスト"""

    @pytest.mark.asyncio
    async def test_generate_summary_error(self, mock_llm):
        """MCPCO-E01: ツール要約生成エラー"""
        # Arrange
        from app.mcp_plugin.common import generate_tool_summary

        mock_llm.ainvoke.side_effect = Exception("LLM error")

        # Act
        with patch("app.mcp_plugin.common.summarizer.tool_summarizer.get_summary_llm", return_value=mock_llm):
            result = await generate_tool_summary([{"tool": "test"}])

        # Assert
        # フォールバック動作またはエラー
        assert result is not None or result == ""

    def test_extract_evidence_malformed(self):
        """MCPCO-E02: evidence抽出エラー"""
        # Arrange
        from app.mcp_plugin.common.evidence_extractor import extract_evidence

        malformed_text = None

        # Act
        result = extract_evidence(malformed_text)

        # Assert
        assert result is None or result == []

    @pytest.mark.asyncio
    async def test_persist_progress_error(self, mock_opensearch):
        """MCPCO-E03: 進捗永続化エラー"""
        # Arrange
        from app.mcp_plugin.common.progress_persister import persist_progress

        mock_opensearch.index.side_effect = Exception("OpenSearch error")

        # Act
        with patch("app.mcp_plugin.common.progress_persister.get_opensearch_client", return_value=mock_opensearch):
            result = await persist_progress({"session_id": "test"})

        # Assert
        assert result is False

    def test_detect_policy_no_policy(self):
        """MCPCO-E04: ポリシー検出エラー"""
        # Arrange
        from app.mcp_plugin.common.policy_detector import detect_policy

        text_without_policy = "これはポリシーを含まないテキストです。"

        # Act
        result = detect_policy(text_without_policy)

        # Assert
        assert result is None or result.get("found") is False

    def test_todo_item_not_found(self):
        """MCPCO-E05: TODO項目未発見"""
        # Arrange
        from app.mcp_plugin.common.todo_manager import TodoManager

        manager = TodoManager()

        # Act
        result = manager.get_item("nonexistent-id")

        # Assert
        assert result is None
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| MCPCO-SEC-01 | URL検証でのSSRF対策 | internal URL | 拒否 |
| MCPCO-SEC-02 | ポリシー検出でのインジェクション対策 | malicious YAML | 安全に処理 |
| MCPCO-SEC-03 | SSEイベントのエスケープ | special characters | 正しくエスケープ |

```python
@pytest.mark.security
class TestCommonSecurity:
    """共通モジュールセキュリティテスト"""

    def test_url_validation_ssrf_prevention(self):
        """MCPCO-SEC-01: URL検証でのSSRF対策"""
        # Arrange
        from app.mcp_plugin.common import validate_documentation_url

        internal_urls = [
            "http://localhost/admin",
            "http://127.0.0.1:8080/internal",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://[::1]/internal"  # IPv6 localhost
        ]

        # Act & Assert
        for url in internal_urls:
            result = validate_documentation_url(url)
            # 内部URLは拒否される
            assert result is False, f"Internal URL should be rejected: {url}"

    def test_policy_detection_injection(self):
        """MCPCO-SEC-02: ポリシー検出でのインジェクション対策"""
        # Arrange
        from app.mcp_plugin.common.policy_detector import detect_policy

        malicious_yaml = """
        !!python/object/apply:os.system
        args: ['rm -rf /']
        """

        # Act - YAML爆弾や悪意のあるYAMLを検出しようとしても安全
        result = detect_policy(malicious_yaml)

        # Assert
        # 例外が発生せず、安全に処理される
        # 悪意のあるYAMLはポリシーとして検出されない
        assert result is None or result.get("found") is False

    def test_sse_event_escape(self):
        """MCPCO-SEC-03: SSEイベントのエスケープ"""
        # Arrange
        from app.mcp_plugin.common.unified_sse_emitter import format_sse_event

        event_data = {
            "content": "テスト\n\nevent: malicious\ndata: injected",
            "html": "<script>alert('xss')</script>"
        }

        # Act
        sse_formatted = format_sse_event("response", event_data)

        # Assert
        # データはJSON化されているため、改行によるイベント注入は防止
        lines = sse_formatted.split("\n")
        event_lines = [l for l in lines if l.startswith("event:")]
        # 1つのevent行のみ存在
        assert len(event_lines) == 1
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `mock_llm` | LLMモック | function | No |
| `mock_opensearch` | OpenSearchモック | function | No |

### 共通フィクスチャ定義

```python
# test/unit/mcp_plugin/common/conftest.py
import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_llm():
    """LLMモック"""
    mock = MagicMock()
    mock.ainvoke = AsyncMock(return_value=MagicMock(content="モック応答"))
    return mock


@pytest.fixture
def mock_opensearch():
    """OpenSearchモック"""
    mock = MagicMock()
    mock.index = AsyncMock(return_value={"result": "created"})
    mock.search = AsyncMock(return_value={"hits": {"hits": []}})
    return mock
```

---

## 6. テスト実行例

```bash
# common関連テストのみ実行
pytest test/unit/mcp_plugin/common/ -v

# カバレッジ付きで実行
pytest test/unit/mcp_plugin/common/ --cov=app.mcp_plugin.common --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/mcp_plugin/common/ -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 10 | MCPCO-001 〜 MCPCO-010 |
| 異常系 | 5 | MCPCO-E01 〜 MCPCO-E05 |
| セキュリティ | 3 | MCPCO-SEC-01 〜 MCPCO-SEC-03 |
| **合計** | **18** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestToolSummarizer` | MCPCO-001 | 1 |
| `TestURLValidator` | MCPCO-002〜MCPCO-003 | 2 |
| `TestTodoManager` | MCPCO-004〜MCPCO-005 | 2 |
| `TestEvidenceExtractor` | MCPCO-006 | 1 |
| `TestResultStructurer` | MCPCO-007 | 1 |
| `TestProgressPersister` | MCPCO-008 | 1 |
| `TestPolicyDetector` | MCPCO-009 | 1 |
| `TestUnifiedSSEEmitter` | MCPCO-010 | 1 |
| `TestCommonErrors` | MCPCO-E01〜MCPCO-E05 | 5 |
| `TestCommonSecurity` | MCPCO-SEC-01〜MCPCO-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | 各サブモジュールの実装詳細に依存 | テストが実装と乖離する可能性 | 実装に合わせて調整 |
| 2 | LLM依存の要約生成テスト | 品質検証困難 | モック使用、統合テストで別途検証 |
| 3 | YAML解析のセキュリティ | 完全な検証困難 | safe_loadの使用を確認 |

---

## 関連ドキュメント

- [mcp_plugin_deep_agents_tests.md](./mcp_plugin_deep_agents_tests.md) - Deep Agentsのテスト
- [mcp_plugin_hierarchical_tests.md](./mcp_plugin_hierarchical_tests.md) - 階層的エージェントのテスト
