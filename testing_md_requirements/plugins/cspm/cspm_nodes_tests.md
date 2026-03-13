# cspm_plugin ノード群 テストケース

## 1. 概要

CSPMプラグインのLangGraphワークフローノード群（`nodes/policy_generation.py`、`nodes/validation.py`、`nodes/review.py`）のテストケースを定義します。
ポリシー生成・検証・修正・レビューのワークフローコアロジックを検証します。

> **ステータス**: 本仕様書は**テスト設計文書（実装予定）** です。テストクラス構成・テストIDは実装時にこの仕様書に準拠して作成してください。
> 現時点で `test/unit/cspm_nodes/` に存在するのは一部のテスト（`test_early_termination.py`）のみであり、本仕様書の全テストケースの実装は未完了です。

> **注記**: cspm_plugin は大規模プラグイン（22ファイル・4,237行）のため、テスト仕様書を機能別に分割しています。
> - [cspm_plugin_tests.md](./cspm_plugin_tests.md): router.py（メインAPIエンドポイント）
> - [cspm_tools_router_tests.md](./cspm_tools_router_tests.md): tools_router.py（MCPツールエンドポイント）
> - [cspm_tools_tests.md](./cspm_tools_tests.md): tools.py（ツール関数）
> - [cspm_utils_tests.md](./cspm_utils_tests.md): ユーティリティ（policy_utils / resource_identification / yaml_converter）
> - [cspm_infra_tests.md](./cspm_infra_tests.md): 基盤コンポーネント（llm_manager / internal_tools）
> - **本ファイル**: ノード群（policy_generation / validation / review）

### 1.1 主要機能

| 機能 | ファイル | 説明 |
|------|---------|------|
| `format_field()` | `nodes/policy_generation.py` | リスト/辞書/その他の型を文字列に変換するヘルパー |
| `generate_policy_node()` | `nodes/policy_generation.py` | 推奨事項からポリシーJSON案を生成（非同期） |
| `enhanced_generate_policy_node()` | `nodes/policy_generation.py` | 強化版ポリシー生成ノード（非同期） |
| `check_generation_success()` | `nodes/policy_generation.py` | 生成成功/失敗の条件分岐ノード |
| `handle_generation_failure_node()` | `nodes/policy_generation.py` | 生成失敗時の処理ノード |
| `validate_policy_node()` | `nodes/validation.py` | Cloud Custodianでポリシーを検証 |
| `check_validation_node()` | `nodes/validation.py` | 検証結果の条件分岐ノード |
| `search_schema_node()` | `nodes/validation.py` | 検証エラーからスキーマ検索（非同期） |
| `fix_policy_node()` | `nodes/validation.py` | LLMでポリシーを修正（非同期） |
| `handle_failure_node()` | `nodes/validation.py` | 検証失敗時の最終処理ノード |
| `final_review_node()` | `nodes/review.py` | 検証済みポリシーの論理的レビュー（非同期） |
| `check_final_review_node()` | `nodes/review.py` | レビュー結果の条件分岐ノード |

### 1.2 カバレッジ目標: 85%

> **注記**: LangGraphノードはLLM呼び出しを含むため、モック設計が複雑。
> 主要分岐の網羅を優先し、LLMレスポンスのバリエーションテストは基盤テスト（仕様書B/C）に委譲する。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象1 | `app/cspm_plugin/nodes/policy_generation.py` |
| テスト対象2 | `app/cspm_plugin/nodes/validation.py` |
| テスト対象3 | `app/cspm_plugin/nodes/review.py` |
| 依存（状態モデル） | `app/models/cspm.py` (PolicyGenerationState) |
| 依存（LLM管理） | `app/cspm_plugin/llm_manager.py` |
| 依存（ユーティリティ） | `app/cspm_plugin/policy_utils.py` |
| 依存（プロンプト） | `app/cspm_plugin/prompts/policy_generation.py` |
| 依存（構造化出力） | `app/cspm_plugin/models/structured_outputs.py` |
| テストコード | `test/unit/cspm_nodes/` |

### 1.4 補足情報

**PolicyGenerationState の主要フィールド:**

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `input_recommendation` | `Dict[str, Any]` | 推奨事項データ |
| `cloud_provider` | `Optional[str]` | クラウドプロバイダー（aws/azure/gcp） |
| `messages` | `List[BaseMessage]` | 会話履歴 |
| `identified_resource` | `Optional[str]` | 特定されたリソースタイプ |
| `current_policy_content` | `Optional[str]` | 現在のポリシーJSON |
| `validation_error` | `Optional[str]` | 検証エラーメッセージ |
| `retrieved_schema` | `Optional[str]` | スキーマ/参照情報 |
| `retry_count` | `int` | 検証リトライ回数 |
| `final_policy_content` | `Optional[str]` | 最終ポリシー |
| `final_error` | `Optional[str]` | 最終エラー |
| `final_determined_status` | `Optional[str]` | 最終ステータス |
| `review_feedback` | `Optional[str]` | レビューフィードバック |
| `review_retry_count` | `int` | レビューリトライ回数 |
| `remaining_steps` | `RemainingSteps` | 残りステップ数（早期終了用） |

**定数:**

| 定数名 | 値 | ファイル | 説明 |
|--------|-----|---------|------|
| `MAX_VALIDATION_RETRIES` | 5 | `validation.py` | バリデーション再試行上限 |
| `EARLY_TERMINATION_THRESHOLD` | 5 | `validation.py`, `review.py` | 早期終了の残りステップ閾値 |
| `MAX_REVIEW_RETRIES` | 4 | `review.py` | レビュー再試行上限 |

> **⚠ 既知の実装不一致（キー名） — テスト戦略:**
>
> `PolicyGenerationState` の正規フィールド名は `current_policy_content` / `final_policy_content`（cspm.py L35, L40）であるが、
> 実装の一部が不正なキー名を使用している:
>
> | ノード関数 | 不正キー（実装の現状） | 正規キー（State定義） |
> |-----------|----------------------|---------------------|
> | `handle_failure_node` (validation.py L345) | `state.get("current_policy_yaml")` | `current_policy_content` |
> | `handle_generation_failure_node` (policy_generation.py L575) | `final_policy_yaml` | `final_policy_content` |
> | `handle_failure_node` (validation.py L371,378) | `final_policy_yaml` | `final_policy_content` |
>
> **テスト戦略（仕様準拠テスト本線 + legacy互換性テスト隔離）:**
>
> 仕様優先の方針に基づき、**仕様準拠テストを本線CI**に置き、
> **互換性テスト（誤実装の動作確認）は `@pytest.mark.legacy` で隔離**する。
>
> - **仕様準拠テスト（本線）**: 正規キー名を期待するテスト。現状の実装では**失敗する**（=契約違反としてCIで検知）。
>   実装修正後にグリーンになる。CI実行: `pytest -m "not legacy"`
> - **legacy互換性テスト**: 現状の不正キー名での動作確認。`@pytest.mark.legacy` でマーク。
>   実装修正時に壊れる → 削除して整理。CI実行: `pytest -m legacy`（別途実行）
> - 関連テスト:
>   - 仕様準拠テスト（本線）: CSPM-ND-E08a-spec, E20-spec, E21-spec
>   - legacy互換性テスト: CSPM-ND-016, E08a, E20, E21
>   - NOTE: E08b は通常異常系テスト（`state={}` でのデフォルト値検証）。キー名不一致の互換性テストではない。
>
> **セキュリティの既知脆弱性テストも同様の方針:**
> - **仕様準拠テスト（本線）**: SEC-07b（漏洩防止）、SEC-10b（不正文字拒否）→ 現状失敗（=修正を強制）
> - **legacy現状記録テスト**: SEC-07（漏洩記録）、SEC-10（インジェクション記録）→ `@pytest.mark.legacy` で隔離

**nodes/policy_generation.py の主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `format_field` | L46-57 | list/dict/その他の型判定 |
| `generate_policy_node` | L86-114 | LLM/推奨事項の有無チェック |
| `generate_policy_node` | L134 | リソース識別エラー |
| `generate_policy_node` | L155 | RAG検索の条件 |
| `generate_policy_node` | L247-258 | LLMレスポンスのcontent型判定 |
| `generate_policy_node` | L265 | JSON抽出エラー |
| `enhanced_generate_policy_node` | L328-356 | LLM/推奨事項の有無チェック |
| `check_generation_success` | L555-563 | ポリシー有無・エラー有無 |
| `handle_generation_failure_node` | L572 | エラーメッセージ取得 |

**nodes/validation.py の主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `validate_policy_node` | L44 | ポリシーJSONの有無 |
| `validate_policy_node` | L50 | ツール利用可能か |
| `validate_policy_node` | L61 | "Validation successful." を含むか |
| `check_validation_node` | L94 | 残りステップ数 ≤ 閾値（早期終了） |
| `check_validation_node` | L98-106 | エラーなし/リトライ可/上限超過 |
| `search_schema_node` | L117-128 | エラーなし/リトライ上限/ツール不可 |
| `search_schema_node` | L140-177 | リソースタイプ/フィルタ/アクションの解析 |
| `search_schema_node` | L188-213 | list_resources/get_schema/不明のツール選択 |
| `fix_policy_node` | L239-270 | LLM/ポリシー/エラー/リトライ上限チェック |
| `fix_policy_node` | L288-302 | LLMレスポンスcontent型判定 |
| `handle_failure_node` | L350 | 早期終了 vs 通常失敗 |
| `handle_failure_node` | L368 | バリデーション成功含みか |

**nodes/review.py の主要分岐:**

| 関数 | 行番号 | 分岐条件 |
|------|--------|---------|
| `final_review_node` | L47-67 | ポリシー/推奨事項/LLMの有無チェック |
| `final_review_node` | L77-99 | YAMLパース構造判定（3形式） |
| `final_review_node` | L106-114 | アクション有無チェック |
| `final_review_node` | L220-244 | レビュー結果の判定（承認/問題あり/リトライ） |
| `final_review_node` | L246-252 | OutputParserExceptionフォールバック |
| `check_final_review_node` | L281 | 残りステップ数 ≤ 閾値（早期終了） |
| `check_final_review_node` | L286-293 | needs_regeneration/active/その他 |

---

## 2. 正常系テストケース

→ [cspm_nodes_tests_normal.md](cspm_nodes_tests_normal.md) を参照

---

## 3. 異常系テストケース

→ [cspm_nodes_tests_error.md](cspm_nodes_tests_error.md) を参照

---

## 4. セキュリティテストケース

→ [cspm_nodes_tests_security.md](cspm_nodes_tests_security.md) を参照

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse | 定義場所 |
|--------------|------|---------|---------|---------|
| `set_required_env_vars` | テスト用環境変数を設定 | function | Yes | `test/unit/cspm_nodes/conftest.py`（新規作成） |
| `reset_nodes_module` | テスト間のモジュール状態リセット | function | Yes | `test/unit/cspm_nodes/conftest.py`（新規作成） |
| `required_env_vars` | REQUIRED_ENV_VARS 辞書を返す | function | No | `test/unit/cspm_nodes/conftest.py`（新規作成） |
| `base_state` | 基本的なPolicyGenerationState辞書 | function | No | クラス内定義（TestGeneratePolicyNode等） |
| `review_state` | レビュー用State辞書 | function | No | クラス内定義（TestFinalReviewNode） |

### 共通フィクスチャ定義

```python
# test/unit/cspm_nodes/conftest.py に追加（既存のものとマージ）
import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# テスト用定数（config.pyバリデーション通過に必要な最小環境変数セット）
# NOTE: "test-DONOTUSE-" プレフィックスで実際のAPIキーとの混同を防止
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-DONOTUSE-gpt5-chat",
    "GPT5_1_CODEX_API_KEY": "test-DONOTUSE-gpt5-codex",
    "GPT5_2_API_KEY": "test-DONOTUSE-gpt5-2",
    "GPT5_MINI_API_KEY": "test-DONOTUSE-gpt5-mini",
    "GPT5_NANO_API_KEY": "test-DONOTUSE-gpt5-nano",
    "CLAUDE_HAIKU_4_5_KEY": "test-DONOTUSE-claude-haiku",
    "CLAUDE_SONNET_4_5_KEY": "test-DONOTUSE-claude-sonnet",
    "GEMINI_API": "test-DONOTUSE-gemini",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-DONOTUSE-embedding",
    "OPENSEARCH_URL": "https://localhost:9200",
    "OPENSEARCH_USER": "admin",
}


def make_chainable_mock(**kwargs):
    """LangChainチェーン（prompt | llm | parser）をモック化するためのヘルパー

    type(mock).__or__ はMagicMockクラス全体に影響するため、
    使い捨てサブクラスを生成してテスト間の干渉を防ぐ。

    Usage:
        mock_prompt = make_chainable_mock()
        type(mock_prompt).__or__ = MagicMock(return_value=mock_chain)
        # → このサブクラスのインスタンスのみに __or__ が適用される
    """
    class _ChainableMock(MagicMock):
        pass
    return _ChainableMock(**kwargs)


@pytest.fixture(autouse=True)
def set_required_env_vars():
    """テスト用環境変数を設定（config.pyバリデーション通過に必要）"""
    with patch.dict(os.environ, REQUIRED_ENV_VARS):
        yield


@pytest.fixture
def required_env_vars():
    """REQUIRED_ENV_VARS 辞書を返すフィクスチャ

    テストコードから直接 conftest の定数を import するのではなく、
    pytestフィクスチャ経由でアクセスすることで依存関係を安定化する。
    """
    return REQUIRED_ENV_VARS


@pytest.fixture(autouse=True)
def reset_nodes_module():
    """テストごとにノードモジュールのグローバル状態をリセット

    llm_manager.py のキャッシュをクリアし、
    ノードモジュールのTOOLS_AVAILABLEフラグが
    テスト間で干渉しないようにする。
    """
    yield
    # テスト後にクリーンアップ
    target_modules = [
        "app.cspm_plugin.nodes.policy_generation",
        "app.cspm_plugin.nodes.validation",
        "app.cspm_plugin.nodes.review",
        "app.cspm_plugin.llm_manager",
        "app.cspm_plugin.tools",
        "app.core.llm_factory",
    ]
    for mod in target_modules:
        sys.modules.pop(mod, None)
    # LLMキャッシュもリセット
    try:
        import app.cspm_plugin.llm_manager as lm
        lm.CACHED_POLICY_LLM = None
        lm.CACHED_ENHANCED_LLM = None
        lm.CACHED_REVIEW_LLM = None
    except ImportError:
        pass
```

---

## 6. テスト実行例

```bash
# ノード群関連テストのみ実行
pytest test/unit/cspm_nodes/ -v

# ポリシー生成ノードのみ
pytest test/unit/cspm_nodes/ -k "TestGeneratePolicyNode" -v

# 検証ノードのみ
pytest test/unit/cspm_nodes/ -k "TestValidatePolicyNode" -v

# レビューノードのみ
pytest test/unit/cspm_nodes/ -k "TestFinalReviewNode" -v

# カバレッジ付きで実行
pytest test/unit/cspm_nodes/ --cov=app.cspm_plugin.nodes --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/cspm_nodes/ -m "security" -v

# 本線CI（legacyテストを除外）
pytest test/unit/cspm_nodes/ -m "not legacy" -v

# legacyテストのみ実行（互換性確認用）
pytest test/unit/cspm_nodes/ -m "legacy" -v

# 本線CI + カバレッジ（legacyテスト除外）
pytest test/unit/cspm_nodes/ -m "not legacy" --cov=app.cspm_plugin.nodes --cov-report=term-missing -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 29 | CSPM-ND-001 〜 CSPM-ND-029 |
| 異常系 | 38 | CSPM-ND-E01 〜 CSPM-ND-E30, E08a, E08a-spec, E08b, E16a, E17a, E19a, E20-spec, E21-spec |
| セキュリティ | 14 | CSPM-ND-SEC-01 〜 CSPM-ND-SEC-11, SEC-04b, SEC-07b, SEC-10b |
| **合計** | **81** | - |

### テストクラス構成（実装予定）

> NOTE: 以下は実装時の目標構成です。各テストの docstring に `CSPM-ND-{ID}` を付与し、本表との1対1トレーサビリティを確保してください。

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestFormatField` | CSPM-ND-001〜004 | 4 |
| `TestGeneratePolicyNode` | CSPM-ND-005〜006, 021, 024 | 4 |
| `TestCheckGenerationSuccess` | CSPM-ND-007〜008 | 2 |
| `TestCheckValidationNode` | CSPM-ND-011〜012 | 2 |
| `TestCheckValidationNodeBoundary` | CSPM-ND-029 | 1 |
| `TestValidatePolicyNode` | CSPM-ND-009〜010 | 2 |
| `TestSearchSchemaNode` | CSPM-ND-013〜014, 022〜023 | 4 |
| `TestFixPolicyNode` | CSPM-ND-015, 027 | 2 |
| `TestHandleFailureNode` | CSPM-ND-016 | 1 |
| `TestFinalReviewNode` | CSPM-ND-017〜018, 025〜026, 028 | 5 |
| `TestCheckFinalReviewNode` | CSPM-ND-019〜020, E30 | 3 |
| `TestGeneratePolicyNodeErrors` | CSPM-ND-E01〜E08 | 8 |
| `TestHandleGenerationFailureNode` | CSPM-ND-E08a, E08a-spec, E08b | 3 |
| `TestValidatePolicyNodeErrors` | CSPM-ND-E09〜E11 | 3 |
| `TestCheckValidationNodeErrors` | CSPM-ND-E12〜E13 | 2 |
| `TestSearchSchemaNodeErrors` | CSPM-ND-E14〜E16, E16a | 4 |
| `TestFixPolicyNodeErrors` | CSPM-ND-E17〜E19, E17a, E19a | 5 |
| `TestHandleFailureNodeErrors` | CSPM-ND-E20, E20-spec, E21, E21-spec | 4 |
| `TestFinalReviewNodeErrors` | CSPM-ND-E22〜E29 | 8 |
| `TestCspmNodesSecurity` | CSPM-ND-SEC-01〜SEC-11, SEC-04b, SEC-07b, SEC-10b | 14 |

### 本線CIで失敗が予想されるテスト（仕様準拠 — 実装修正で解消）

| テストID | 理由 | CIでの扱い |
|---------|------|-----------|
| CSPM-ND-E08a-spec | 実装が `final_policy_yaml` を返却（正規は `final_policy_content`） | **本線で失敗** → 実装のキー名修正で解消 |
| CSPM-ND-E20-spec | 同上 | **本線で失敗** → 実装のキー名修正で解消 |
| CSPM-ND-E21-spec | 同上（入力側 `current_policy_yaml` も不正） | **本線で失敗** → 実装のキー名修正で解消 |
| CSPM-ND-SEC-07b | validation_error のサニタイズが未実装 | **本線で失敗** → サニタイズ実装で解消 |
| CSPM-ND-SEC-10b | target のホワイトリスト検証が未実装 | **本線で失敗** → バリデーション追加で解消 |

> **NOTE**: CSPM-ND-005, 006, 015, 017 等は `make_chainable_mock()` ヘルパーで対処済みのため正常passが予定されており、上記テーブルには含めません。

### legacyテスト（本線CIから除外）

| テストID | 目的 | 実装修正後の対応 |
|---------|------|----------------|
| CSPM-ND-016 | handle_failure_node の不正キー名動作確認 | 削除 |
| CSPM-ND-E08a | handle_generation_failure_node の不正キー名動作確認 | 削除 |
| CSPM-ND-E20 | handle_failure_node 早期終了の不正キー名動作確認 | 削除 |
| CSPM-ND-E21 | handle_failure_node 検証成功含みの不正キー名動作確認 | 削除 |
| CSPM-ND-SEC-07 | 情報漏洩の現状動作記録 | 削除 |
| CSPM-ND-SEC-10 | スキーマクエリインジェクションの現状動作記録 | 削除 |

### 注意事項

- `pytest-asyncio` が必要（大半のノード関数が非同期）
- `pyproject.toml` に `asyncio_mode = "auto"` の設定を推奨（明示的な `@pytest.mark.asyncio` が不要になる）
- `@pytest.mark.security` および `@pytest.mark.legacy` マーカーの `pyproject.toml` への登録が必要:
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "security: セキュリティテスト",
      "legacy: 互換性テスト（不正キー名等の現状動作確認。実装修正後に削除）",
  ]
  ```
- LangChainチェーン（`prompt | llm | parser`）のモックは `make_chainable_mock()` + `type(mock).__or__` でパッチ（インスタンスレベルの `__or__` 代入は動作しないため、使い捨てサブクラスを生成して干渉を防止）
- `PolicyGenerationState` は `MessagesState` を継承しているが、テストでは通常の辞書で代用可能
- `remaining_steps` は `RemainingSteps` マネージド型だが、テストでは `float('inf')` や数値で代用
- ノード関数のテストでは、依存モジュール（llm_manager, policy_utils, tools）を全てモック化すること
- **ノードごとの返却キー名の違い**に注意:

| ノード関数 | ポリシー返却キー（現実装） | 正規キー（State定義） | ステータス返却キー |
|-----------|------------------------|---------------------|-------------------|
| `generate_policy_node` | `current_policy_content` | `current_policy_content` ✅ | `validation_error` |
| `enhanced_generate_policy_node` | `current_policy_content` | `current_policy_content` ✅ | `validation_error` |
| `handle_generation_failure_node` | `final_policy_yaml` ⚠ | `final_policy_content` | `final_determined_status` |
| `handle_failure_node` | `final_policy_yaml` ⚠ | `final_policy_content` | `final_determined_status` |
| `final_review_node` | `final_policy_content` | `final_policy_content` ✅ | `final_determined_status` |

> ⚠ 不一致キーには **仕様準拠テスト（本線CI、現状失敗）** と **legacy互換性テスト（`@pytest.mark.legacy` で隔離）** の両方を用意。
> 実装修正時: 仕様準拠テストが pass に変わる → legacy互換性テストを削除。

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | LangChainチェーンのモックが複雑（`prompt | llm | parser` の `__or__` オーバーロード） | テストコードの可読性低下 | `make_chainable_mock()` ヘルパーで使い捨てサブクラスを生成し、テスト間干渉を防止 |
| 2 | `PolicyGenerationState` の `remaining_steps` は `RemainingSteps` マネージド型 | 単体テストではLangGraphランタイムなしで利用不可 | 通常の `float('inf')` や数値で代用 |
| 3 | `generate_policy_node` と `enhanced_generate_policy_node` は構造が類似 | テストの重複が発生 | 共通テストパターンをパラメタライズで共通化可能 |
| 4 | `final_review_node` のRAG検索はツール依存 | ツールモック設定が必須 | `TOOLS_AVAILABLE=False` でRAGスキップパスもテスト |
| 5 | ノード関数は `print()` でログ出力 | テスト出力が冗長 | `capsys` または `capfd` で出力をキャプチャ |
| 6 | conftest.py の REQUIRED_ENV_VARS が複数仕様書で参照される | 更新時に不整合の可能性 | `required_env_vars` pytestフィクスチャ経由でアクセスし、直接importを回避 |
| 7 | legacyテスト（ND-016, E08a, E20, E21, SEC-07, SEC-10）は実装修正後に削除が必要 | 放置すると不要なテストが残り続ける | **移行手順**: 実装のキー名修正後 → (1) `pytest -m legacy` で失敗を確認 → (2) 対応するlegacyテストを削除 → (3) `pytest -m "not legacy"` で仕様準拠テストが pass することを確認。**対応表**: ND-016→削除 / E08a→削除(E08a-specが本線) / E20→削除(E20-specが本線) / E21→削除(E21-specが本線) / SEC-07→削除(SEC-07bが本線) / SEC-10→削除(SEC-10bが本線) |
