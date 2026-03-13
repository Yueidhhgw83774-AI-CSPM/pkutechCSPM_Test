# Plugins テスト仕様書の状況

## 概要

`app/` ディレクトリ内のプラグインモジュールに対するテスト仕様書の作成状況を管理します。

---

## 1. ディレクトリ構造

```
docs/testing/plugins/
├── auth/
│   └── auth_tests.md
├── aws/
│   └── aws_plugin_tests.md
├── chat_dashboard/
│   └── chat_dashboard_tests.md
├── cspm/
│   ├── cspm_plugin_tests.md (router.py)
│   ├── cspm_tools_router_tests.md (tools_router.py)
│   └── cspm_tools_tests.md (tools.py)
├── custodian_scan/
│   └── custodian_scan_tests.md
├── doc_reader/
│   ├── doc_reader_ai_pretreatment_tests.md
│   ├── doc_reader_chat_logic_tests.md
│   ├── doc_reader_output_models_tests.md
│   ├── doc_reader_pdf_utils_tests.md
│   ├── doc_reader_post_gemini_tests.md
│   ├── doc_reader_router_tests.md
│   └── doc_reader_structuring_tests.md
├── jobs/
│   ├── jobs_router_tests.md (router.py, status_manager.py)
│   ├── common/
│   │   └── jobs_common_tests.md
│   └── tasks/
│       ├── jobs_tasks_base_tests.md
│       ├── jobs_custodian_scan_tests.md
│       ├── jobs_file_processing_tests.md
│       ├── jobs_policy_generation_tests.md
│       └── new_custodian_scan/
│           ├── jobs_ncs_validators_tests.md
│           ├── jobs_ncs_auth_tests.md
│           ├── jobs_ncs_command_builder_tests.md
│           ├── jobs_ncs_command_preview_tests.md
│           ├── jobs_ncs_backward_compat_tests.md
│           ├── jobs_ncs_return_code_analyzer_tests.md
│           ├── jobs_ncs_file_processor_tests.md
│           ├── jobs_ncs_error_history_handler_tests.md
│           └── jobs_ncs_error_analyzer_tests.md
├── mcp/
│   ├── mcp_plugin_chat_agent_tests.md
│   ├── mcp_plugin_client_tests.md
│   ├── mcp_plugin_common_tests.md
│   ├── mcp_plugin_deep_agents_tests.md
│   ├── mcp_plugin_hierarchical_tests.md
│   ├── mcp_plugin_router_tests.md
│   └── mcp_plugin_sessions_tests.md
├── rag/
│   └── rag_plugin_tests.md
└── report/
    └── report_plugin_tests.md
```

---

## 2. テスト仕様書の状況一覧

### 2.1 完成済み

| プラグイン | ディレクトリ | テスト仕様書 | テスト数 | 状態 |
|-----------|------------|------------|---------|------|
| auth | `auth/` | [auth_tests.md](./auth/auth_tests.md) | - | ✅ 完成 |
| aws_plugin | `aws/` | [aws_plugin_tests.md](./aws/aws_plugin_tests.md) | 66件 | ✅ 完成 |
| chat_dashboard | `chat_dashboard/` | [chat_dashboard_tests.md](./chat_dashboard/chat_dashboard_tests.md) | 37件 | ✅ 完成 |
| cspm_plugin | `cspm/` | [cspm_plugin_tests.md](./cspm/cspm_plugin_tests.md) | - | ✅ 完成 |
| cspm_plugin | `cspm/` | [cspm_tools_router_tests.md](./cspm/cspm_tools_router_tests.md) | - | ✅ 完成 |
| cspm_plugin | `cspm/` | [cspm_tools_tests.md](./cspm/cspm_tools_tests.md) | - | ✅ 完成 |
| custodian_scan | `custodian_scan/` | [custodian_scan_tests.md](./custodian_scan/custodian_scan_tests.md) | - | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_pdf_utils_tests.md](./doc_reader/doc_reader_pdf_utils_tests.md) | 24件 | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_ai_pretreatment_tests.md](./doc_reader/doc_reader_ai_pretreatment_tests.md) | 46件 | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_router_tests.md](./doc_reader/doc_reader_router_tests.md) | 32件 | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_chat_logic_tests.md](./doc_reader/doc_reader_chat_logic_tests.md) | 28件 | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_structuring_tests.md](./doc_reader/doc_reader_structuring_tests.md) | 38件 | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_post_gemini_tests.md](./doc_reader/doc_reader_post_gemini_tests.md) | 30件 | ✅ 完成 |
| doc_reader_plugin | `doc_reader/` | [doc_reader_output_models_tests.md](./doc_reader/doc_reader_output_models_tests.md) | 46件 | ✅ 完成 |
| jobs | `jobs/` | [jobs_router_tests.md](./jobs/jobs_router_tests.md) | 36件 | ✅ 完成 |
| mcp_plugin | `mcp/` | [mcp_plugin_router_tests.md](./mcp/mcp_plugin_router_tests.md) | 仕様43件 / 実装**0件** | ⚠️ 仕様完成・実装未着手 |
| mcp_plugin | `mcp/` | [mcp_plugin_client_tests.md](./mcp/mcp_plugin_client_tests.md) | 仕様35件 / 実装**0件** | ⚠️ 仕様完成・実装未着手 |
| mcp_plugin | `mcp/` | [mcp_plugin_chat_agent_tests.md](./mcp/mcp_plugin_chat_agent_tests.md) | 仕様18件 / 実装**0件** | ⚠️ 仕様完成・実装未着手 |
| mcp_plugin | `mcp/` | [mcp_plugin_deep_agents_tests.md](./mcp/mcp_plugin_deep_agents_tests.md) | 仕様38件 / 実装24件 | ⚠️ 仕様完成・実装不足14件 |
| mcp_plugin | `mcp/` | [mcp_plugin_hierarchical_tests.md](./mcp/mcp_plugin_hierarchical_tests.md) | 仕様45件 / 実装105件 | ✅ 実装超過 |
| mcp_plugin | `mcp/` | [mcp_plugin_sessions_tests.md](./mcp/mcp_plugin_sessions_tests.md) | 仕様74件 / 実装52件 | ⚠️ 仕様完成・実装不足22件 |
| mcp_plugin | `mcp/` | [mcp_plugin_common_tests.md](./mcp/mcp_plugin_common_tests.md) | 仕様112件 / 実装189件 | ✅ 実装超過 |
| rag | `rag/` | [rag_plugin_tests.md](./rag/rag_plugin_tests.md) | 87件 | ✅ 完成 |
| report_plugin | `report/` | [report_plugin_tests.md](./report/report_plugin_tests.md) | 36件 | ✅ 完成 |

### 2.2 テスト実装の不足・未作成

| プラグイン | ディレクトリ | 対象 | 仕様件数 | 実装件数 | 不足 | 状態 |
|-----------|------------|------|---------|---------|------|------|
| mcp_plugin | `mcp/` | router.py | 43 | 0 | **43** | ⚠️ テスト未実装 |
| mcp_plugin | `mcp/` | client.py | 35 | 0 | **35** | ⚠️ テスト未実装 |
| mcp_plugin | `mcp/` | chat_agent.py | 18 | 0 | **18** | ⚠️ テスト未実装 |
| mcp_plugin | `mcp/` | sessions/ | 74 | 52 | **22** | ⚠️ 部分実装 |
| mcp_plugin | `mcp/` | deep_agents/ | 38 | 24 | **14** | ⚠️ 部分実装 |
| mcp_plugin | `mcp/` | integration/ (仕様書なし) | - | 100 | - | 📝 仕様書未作成 |
| mcp_plugin | `mcp/` | 直下その他 (仕様書なし) | - | 45 | - | 📝 仕様書未作成 |
| | | **mcp_plugin 小計** | **208** | **76** | **132** | |
| jobs | `jobs/` | common/ | - | - | - | ❌ 仕様書未作成 |
| jobs | `jobs/` | tasks/ | - | - | - | ❌ 仕様書未作成 |
| jobs | `jobs/` | tasks/new_custodian_scan/ | - | - | - | ❌ 仕様書未作成 |
| jobs | `jobs/` | utils/ | - | - | - | ❌ 仕様書未作成 |
| cspm_plugin | `cspm/` | 詳細モジュール (14ファイル) | - | - | - | ❌ 仕様書未作成 |
| litellm_key_management | - | status.py | - | - | - | ❌ 仕様書未作成 |

> **mcp_plugin 注記**: 仕様書7本（合計365件）は全て完成済みだが、テスト実装は5カテゴリ（common/hierarchical/deep_agents/sessions/その他）の515件のみ。router・client・chat_agent の3モジュール（計96件）は完全未実装、sessions・deep_agents は部分実装（計36件不足）。一方で仕様書のないテスト（integration/ 100件、直下45件）が存在する。

### 2.3 対象外

| プラグイン | 理由 |
|-----------|------|
| logchecker | 内部モジュール、単体テスト対象外 |

---

## 3. 詳細モジュールの未実装・未作成一覧

### 3.0 mcp_plugin/ テスト実装ギャップ

仕様書は7本（合計365件）全て完成済み。テスト実装（合計515件）との対応は以下のとおり。

#### 仕様書あり・テスト未実装（96件）

| 仕様書 | 対象ファイル | 仕様件数 | テストファイル | 実装件数 |
|--------|-----------|---------|-------------|---------|
| `mcp_plugin_router_tests.md` | `router.py` | 43 | 未作成 | 0 |
| `mcp_plugin_client_tests.md` | `client.py` | 35 | 未作成 | 0 |
| `mcp_plugin_chat_agent_tests.md` | `chat_agent.py` | 18 | 未作成 | 0 |

#### 仕様書あり・テスト部分実装（36件不足）

| 仕様書 | 仕様件数 | 実装件数 | 不足 | テスト配置 |
|--------|---------|---------|------|----------|
| `mcp_plugin_sessions_tests.md` | 74 | 52 | 22 | `app/mcp_plugin/sessions/tests/` ※配置が `test/unit/` 外 |
| `mcp_plugin_deep_agents_tests.md` | 38 | 24 | 14 | `test/unit/mcp_plugin/deep_agents/` |

#### 仕様書あり・テスト超過実装

| 仕様書 | 仕様件数 | 実装件数 | 超過 | テスト配置 |
|--------|---------|---------|------|----------|
| `mcp_plugin_common_tests.md` | 112 | 189 | +77 | `test/unit/mcp_plugin/common/` (8ファイル) |
| `mcp_plugin_hierarchical_tests.md` | 45 | 105 | +60 | `test/unit/mcp_plugin/hierarchical/` (7ファイル) |

#### 仕様書なし・テスト実装あり（145件）

| テスト配置 | ファイル数 | 実装件数 | 備考 |
|-----------|----------|---------|------|
| `test/unit/mcp_plugin/integration/` | 6 | 100 | API後方互換性、E2E、SSEイベント等 |
| `test/unit/mcp_plugin/test_error_analyzer.py` | 1 | 20 | deep_agents関連 |
| `test/unit/mcp_plugin/test_subagents.py` | 1 | 10 | deep_agents関連 |
| `test/unit/mcp_plugin/test_url_validator.py` | 1 | 15 | common/url_validator関連 |

#### mcp_plugin 実装テスト数サマリー

| カテゴリ | テストファイル数 | テスト関数数 |
|---------|--------------|------------|
| common/ | 8 | 189 |
| deep_agents/ | 2 | 24 |
| hierarchical/ | 7 | 105 |
| integration/ | 6 | 100 |
| sessions/ (`app/`配下) | 4 | 52 |
| 直下 | 3 | 45 |
| **合計** | **30** | **515** |

### 3.1 jobs/ 詳細モジュール（63ファイル）

現在 `jobs_router_tests.md` は `router.py` と `status_manager.py` のみカバー。

#### common/ (3ファイル)
| ファイル | 説明 | 優先度 |
|---------|------|--------|
| `error_handling.py` | エラー処理共通関数 | 高 |
| `logging.py` | ロギング共通関数 | 中 |
| `status_tracking.py` | ステータス追跡 | 高 |

#### tasks/ 直下 (4ファイル)
| ファイル | 説明 | 優先度 |
|---------|------|--------|
| `base_task.py` | 基底タスククラス | 高 |
| `custodian_scan.py` | 旧Custodianスキャンタスク | 中 |
| `file_processing.py` | ファイル処理タスク | 中 |
| `policy_generation.py` | ポリシー生成タスク | 中 |

#### tasks/new_custodian_scan/ (25ファイル)
| サブディレクトリ | ファイル数 | 説明 | 優先度 |
|----------------|----------|------|--------|
| ルート | 14 | メインタスク、認証、コマンドビルダー等 | 高 |
| executor/ | 5 | 実行、エラー検出、統計分析 | 高 |
| log_analyzer/ | 5 | ログ解析、パターンマッチング | 中 |
| results/ | 10 | 結果処理、インサイト生成、OpenSearch | 中 |

#### utils/ (19ファイル)
| ファイル | 説明 | 優先度 |
|---------|------|--------|
| `account_id_extractor.py` | AWSアカウントID抽出 | 中 |
| `aws_resource_counter.py` | AWSリソースカウント | 低 |
| `custodian_output.py` | Custodian出力処理 | 中 |
| `document_creators.py` | ドキュメント作成 | 低 |
| `document_extractors.py` | ドキュメント抽出 | 低 |
| `error_analysis.py` | エラー分析 | 中 |
| `field_normalizers.py` | フィールド正規化 | 低 |
| `helper_functions.py` | ヘルパー関数 | 低 |
| `metadata_extractor.py` | メタデータ抽出 | 低 |
| `opensearch_v2_indexer.py` | OpenSearchインデクサー | 中 |
| `recommendation_uuid_mapper.py` | UUID マッピング | 低 |
| `resource_id_extractor.py` | リソースID抽出 | 低 |
| `scan_analysis.py` | スキャン分析 | 中 |
| `store_operations.py` | ストア操作 | 低 |
| `summary_generation.py` | サマリー生成 | 低 |
| `v2_format_converter.py` | V2フォーマット変換 | 中 |
| `v2_format_helpers.py` | V2フォーマットヘルパー | 低 |
| `v2_format_legacy_functions.py` | V2レガシー関数 | 低 |
| `v2_hierarchical_helpers.py` | V2階層ヘルパー | 低 |
| `violations_counter.py` | 違反カウント | 低 |

### 3.2 cspm_plugin/ 詳細モジュール（14ファイル）

現在 `cspm/` 内の3仕様書は `router.py`, `tools_router.py`, `tools.py` のみカバー。

| ファイル | 説明 | 優先度 |
|---------|------|--------|
| `agent.py` | CSPMエージェント | 高 |
| `agent_executor.py` | エージェント実行 | 高 |
| `internal_tools.py` | 内部ツール | 中 |
| `llm_manager.py` | LLM管理 | 中 |
| `models/structured_outputs.py` | 構造化出力モデル | 低 |
| `nodes/policy_generation.py` | ポリシー生成ノード | 高 |
| `nodes/review.py` | レビューノード | 中 |
| `nodes/validation.py` | 検証ノード | 高 |
| `policy_nodes.py` | ポリシーノード | 中 |
| `policy_utils.py` | ポリシーユーティリティ | 中 |
| `prompts/policy_generation.py` | ポリシー生成プロンプト | 低 |
| `refinement.py` | 推敲処理 | 中 |
| `resource_identification.py` | リソース識別 | 中 |
| `utils/yaml_converter.py` | YAML変換 | 低 |

### 3.3 litellm_key_management/ (1ファイル)

| ファイル | 説明 | 優先度 |
|---------|------|--------|
| `status.py` | LiteLLMキー管理ステータス | 低 |

---

## 4. カバレッジサマリー

### 4.1 仕様書カバレッジ（実装ファイルに対する仕様書の存在）

| プラグイン | 総ファイル数 | 仕様書カバー | 未カバー | カバー率 |
|-----------|-----------|------------|---------|---------|
| auth | 1 | 1 | 0 | 100% |
| aws_plugin | 3 | 3 | 0 | 100% |
| chat_dashboard | 7 | 7 | 0 | 100% |
| cspm_plugin | 17 | 3 | 14 | 18% |
| custodian_scan | 1 | 1 | 0 | 100% |
| doc_reader_plugin | 7 | 7 | 0 | 100% |
| jobs | 65 | 2 | 63 | 3% |
| litellm_key_management | 1 | 0 | 1 | 0% |
| logchecker | 2 | 0 | 0 | N/A (対象外) |
| mcp_plugin | 53 | 53 | 0 | 100% |
| rag | 4 | 4 | 0 | 100% |
| report_plugin | 10 | 10 | 0 | 100% |
| **合計** | **171** | **91** | **78** | **53%** |

### 4.2 mcp_plugin テスト実装ギャップ

| 仕様書 | 仕様件数 | 実装件数 | 差分 | 状態 |
|--------|---------|---------|------|------|
| router | 43 | 0 | **-43** | 未実装 |
| client | 35 | 0 | **-35** | 未実装 |
| chat_agent | 18 | 0 | **-18** | 未実装 |
| deep_agents | 38 | 24 | **-14** | 部分実装 |
| sessions | 74 | 52 | **-22** | 部分実装 |
| hierarchical | 45 | 105 | +60 | 超過 |
| common | 112 | 189 | +77 | 超過 |
| (integration: 仕様なし) | - | 100 | - | 仕様書未対応 |
| (直下その他: 仕様なし) | - | 45 | - | 仕様書未対応 |
| **合計** | **365** | **515** | **-132** (仕様ベース) | |

> **注記**: 仕様書ベースでは132件不足だが、実装テスト総数（515件）は仕様書総数（365件）を150件上回る。integration/（100件）や直下テスト（45件）に対応する仕様書が存在しないため、仕様管理上のギャップがある。

---

## 5. 作成優先順位

### フェーズ4: jobs 詳細モジュール（優先度: 高）
1. `jobs/common/` - エラー処理、ステータス追跡
2. `jobs/tasks/new_custodian_scan/` - セキュリティスキャンの中核
3. `jobs/tasks/` 直下 - 基底タスク、各種タスク実装

### フェーズ5: cspm_plugin 詳細モジュール（優先度: 中）
4. `cspm/agent.py`, `cspm/agent_executor.py` - エージェント実装
5. `cspm/nodes/` - ポリシー生成・検証ノード

### フェーズ6: その他（優先度: 低）
6. `jobs/utils/` - ユーティリティ関数群
7. `litellm_key_management/` - キー管理

---

## 6. 凡例

| マーク | 意味 |
|--------|------|
| ✅ 完成 | レビュー済みの詳細なテスト仕様書が存在し、テスト実装も十分 |
| ✅ 実装超過 | 仕様書のテスト件数を超えるテスト実装が存在 |
| ⚠️ 仕様完成・実装未着手 | 仕様書は完成しているがテストコードが未作成 |
| ⚠️ 仕様完成・実装不足 | 仕様書は完成しているがテスト実装が一部不足 |
| 📝 仕様書未作成 | テスト実装はあるが対応する仕様書がない |
| 📝 未レビュー | テスト仕様書が存在するがレビュー未実施 |
| ⚠️ テンプレートのみ | 基本構造のみ、詳細化が必要 |
| ❌ 未作成 | テスト仕様書もテスト実装も存在しない |
| ➖ 対象外 | テスト作成不要（内部モジュール等） |

---

## 7. 更新履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-01-28 | 初版作成 |
| 2026-02-04 | ディレクトリ構造を案Aに変更（プラグイン別サブディレクトリ化） |
| 2026-02-04 | jobs_tests.md を jobs/jobs_router_tests.md にリネーム・移動 |
| 2026-02-04 | 未作成モジュール一覧を追加（jobs 63件、cspm 14件、litellm 1件） |
| 2026-02-04 | カバレッジサマリーを追加（全体53%カバー） |
| 2026-02-18 | mcp_pluginセクションを実態に合わせて更新（仕様365件 vs 実装515件、仕様ベース132件不足を明記） |
