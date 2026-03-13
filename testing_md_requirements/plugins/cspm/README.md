# CSPM Plugin テスト仕様書

`app/cspm_plugin/` 配下の全モジュールに対するテスト仕様書です。

## 仕様書一覧

| # | 仕様書 | 対象ファイル | テスト数 | カバレッジ目標 | レビュー状況 |
|---|-------|------------|---------|-------------|------------|
| 1 | [cspm_plugin_tests.md](./cspm_plugin_tests.md) | `router.py` | 26件 | 90% | 完了 |
| 2 | [cspm_tools_tests.md](./cspm_tools_tests.md) | `tools.py` | 56件 | 85% | 完了 |
| 3 | [cspm_tools_router_tests.md](./cspm_tools_router_tests.md) | `tools_router.py` | 29件 | 90% | 完了 |
| 4 | [cspm_utils_tests.md](./cspm_utils_tests.md) | `policy_utils.py`, `resource_identification.py`, `utils/yaml_converter.py` | 44件 | 90% | 完了 |
| 5 | [cspm_infra_tests.md](./cspm_infra_tests.md) | `llm_manager.py`, `internal_tools.py` | 35件 | 90% | 完了 |
| 6 | [cspm_nodes_tests.md](./cspm_nodes_tests.md) | `nodes/policy_generation.py`, `nodes/validation.py`, `nodes/review.py` | 59件 | 85% | **未完了** |

**合計: 249件**（正常系 100 / 異常系 111 / セキュリティ 38）

## テストID体系

| 接頭辞 | 対象 | 仕様書 |
|--------|------|-------|
| `CSPM-` | router.py | cspm_plugin_tests.md |
| `CSPM-T-` | tools.py | cspm_tools_tests.md |
| `CSPM-TR-` | tools_router.py | cspm_tools_router_tests.md |
| `CSPM-UT-` | ユーティリティ群 | cspm_utils_tests.md |
| `CSPM-IF-` | 基盤コンポーネント | cspm_infra_tests.md |
| `CSPM-ND-` | ノード群 | cspm_nodes_tests.md |

## 対象外ファイル

以下のファイルは仕様書の対象外です。

| ファイル | 理由 |
|---------|------|
| `agent_executor.py` | `cspm_plugin_tests.md` で `run_policy_agent()` が間接カバー済み |
| `refinement.py` | `cspm_plugin_tests.md` で `generate_refined_policy()` が間接カバー済み |
| `policy_nodes.py` | 後方互換ラッパー（`nodes/` パッケージの再エクスポートのみ） |
| `models/structured_outputs.py` | Pydantic モデル定義のみ |
| `prompts/policy_generation.py` | テンプレート定数のみ |
| `agent.py` | パッケージラッパー（定数定義のみ） |

## レビューワークフロー

各仕様書は以下のワークフローでレビューを実施します。

1. code-reviewer + security-engineer + Codex の3並列レビュー
2. 指摘修正 → 再レビュー（最大3サイクル）
3. 全レビューアー APPROVED 後、最終統合レビュー
4. MCP 診断エラー 0 件を確認してコミット

## テスト実行

```bash
# 全 CSPM テスト実行
pytest test/unit/cspm_plugin/ -v

# カテゴリ別実行
pytest test/unit/cspm_plugin/ -v -k "Security"      # セキュリティのみ
pytest test/unit/cspm_plugin/ -v -k "not Security"   # セキュリティ以外

# 仕様書別実行
pytest test/unit/cspm_plugin/test_utils.py -v        # ユーティリティ
pytest test/unit/cspm_plugin/test_infra.py -v        # 基盤
pytest test/unit/cspm_plugin/test_nodes.py -v        # ノード群
```

## 前提条件

- `pytest-asyncio>=0.23.0` が必要（`pyproject.toml` の dev 依存に追加）
- `pyproject.toml` に `asyncio_mode = "auto"` の設定を推奨
- `@pytest.mark.security` マーカーの登録が必要
