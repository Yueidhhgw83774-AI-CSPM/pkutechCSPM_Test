# テスト仕様書 全体サマリー

## 概要

本ドキュメントは、python-fastapi プロジェクトのテスト仕様書作成状況を集約したダッシュボードです。

---

## 1. 全体統計

| 領域 | 対象ファイル数 | カバー済み | 未カバー | カバー率 | テスト仕様書数 |
|------|-------------|----------|---------|---------|--------------|
| Core | 14 | 14 | 0 | 100% | 14 |
| Models | 9 | 0 | 9 | 0% | 0 |
| Plugins | 171 | 91 | 78 | 53% | 24 |
| **合計** | **194** | **105** | **87** | **54%** | **38** |

---

## 2. ディレクトリ構造

```
docs/testing/
├── 00-07_*.md             # 共通ドキュメント（戦略、環境、フィクスチャ等）
├── TEMPLATE_test_spec.md  # テスト仕様書テンプレート
├── test_status_summary.md # 本ファイル
│
├── core/                  # Core モジュール（14仕様書）
│   ├── *_tests.md
│   └── core_tests_status.md
│
├── models/                # 共通モデル（未作成）
│   └── (作成予定)
│
└── plugins/               # プラグイン（24仕様書）
    ├── auth/
    ├── aws/
    ├── chat_dashboard/
    ├── cspm/
    ├── custodian_scan/
    ├── doc_reader/
    ├── jobs/
    ├── mcp/
    ├── rag/
    ├── report/
    └── plugins_tests_status.md
```

---

## 3. 領域別状況

### 3.1 Core モジュール ✅ 完全カバー

| 対象ファイル | テスト仕様書 | 状態 |
|------------|------------|------|
| `config.py` | [config_tests.md](./core/config_tests.md) | ✅ 完成 |
| `llm_factory.py` | [llm_factory_tests.md](./core/llm_factory_tests.md) | ✅ 完成 |
| `clients.py` | [clients_tests.md](./core/clients_tests.md) | ✅ 完成 |
| `crypto.py` | [crypto_tests.md](./core/crypto_tests.md) | ✅ 完成 |
| `auth.py` | [auth_tests.md](./plugins/auth/auth_tests.md) | ✅ 完成（plugins側） |
| `auth_utils.py` | [auth_utils_tests.md](./core/auth_utils_tests.md) | ✅ 完成 |
| `permission_checker.py` | [permission_checker_tests.md](./core/permission_checker_tests.md) | ✅ 完成 |
| `checkpointer.py` | [checkpointer_tests.md](./core/checkpointer_tests.md) | ✅ 完成 |
| `encryption_middleware.py` | [encryption_middleware_tests.md](./core/encryption_middleware_tests.md) | ✅ 完成 |
| `error_handlers.py` | [error_handlers_tests.md](./core/error_handlers_tests.md) | ✅ 完成 |
| `rag_manager.py` | [rag_manager_tests.md](./core/rag_manager_tests.md) | ✅ 完成 |
| `role_based_client.py` | [role_based_client_tests.md](./core/role_based_client_tests.md) | ✅ 完成 |
| `health_checker.py` | [health_checker_tests.md](./core/health_checker_tests.md) | ✅ 完成 |
| `categories.py` | [categories_tests.md](./core/categories_tests.md) | ✅ 完成 |

### 3.2 Models ❌ 未作成

| 対象ファイル | 説明 | 優先度 |
|------------|------|--------|
| `api.py` | API共通モデル | 高 |
| `auth.py` | 認証モデル | 高 |
| `chat.py` | チャットモデル | 中 |
| `compliance.py` | コンプライアンスモデル | 中 |
| `cspm.py` | CSPMモデル | 中 |
| `cspm_tools.py` | CSPMツールモデル | 低 |
| `health.py` | ヘルスチェックモデル | 低 |
| `jobs.py` | ジョブモデル | 中 |
| `mcp.py` | MCPモデル | 低 |

### 3.3 Plugins

| プラグイン | ファイル数 | カバー済み | カバー率 | 状態 |
|-----------|----------|----------|---------|------|
| auth | 1 | 1 | 100% | ✅ 完全 |
| aws_plugin | 3 | 3 | 100% | ✅ 完全 |
| chat_dashboard | 7 | 7 | 100% | ✅ 完全 |
| cspm_plugin | 17 | 3 | 18% | ⚠️ 詳細未カバー |
| custodian_scan | 1 | 1 | 100% | ✅ 完全 |
| doc_reader_plugin | 7 | 7 | 100% | ✅ 完全 |
| jobs | 65 | 2 | 3% | ⚠️ 詳細未カバー |
| litellm_key_management | 1 | 0 | 0% | ❌ 未作成 |
| logchecker | 2 | - | N/A | ➖ 対象外 |
| mcp_plugin | 53 | 53 | 100% | ✅ 完全 |
| rag | 4 | 4 | 100% | ✅ 完全 |
| report_plugin | 10 | 10 | 100% | ✅ 完全 |

---

## 4. 未カバーモジュール一覧

### 4.1 高優先度（78ファイル）

| カテゴリ | ファイル数 | 説明 |
|---------|----------|------|
| **jobs/tasks/new_custodian_scan/** | 25 | セキュリティスキャンの中核 |
| **jobs/common/** | 3 | エラー処理、ステータス追跡 |
| **jobs/tasks/** 直下 | 4 | 基底タスク、各種タスク実装 |
| **cspm_plugin/** 詳細 | 14 | エージェント、ポリシー生成ノード |
| **models/** | 9 | 全プラグインが依存する共通モデル |

### 4.2 中優先度（19ファイル）

| カテゴリ | ファイル数 | 説明 |
|---------|----------|------|
| **jobs/utils/** | 19 | ユーティリティ関数群 |

### 4.3 低優先度（1ファイル）

| カテゴリ | ファイル数 | 説明 |
|---------|----------|------|
| **litellm_key_management/** | 1 | キー管理ステータス |

---

## 5. 作成優先順位

### フェーズ4: jobs 詳細モジュール
1. `jobs/common/` - エラー処理、ステータス追跡
2. `jobs/tasks/new_custodian_scan/` - セキュリティスキャンの中核
3. `jobs/tasks/` 直下 - 基底タスク、各種タスク実装

### フェーズ5: models + cspm_plugin 詳細
4. `models/` - 共通データモデル
5. `cspm_plugin/` 詳細 - エージェント、ポリシーノード

### フェーズ6: その他
6. `jobs/utils/` - ユーティリティ関数群
7. `litellm_key_management/` - キー管理

---

## 6. 凡例

| マーク | 意味 |
|--------|------|
| ✅ 完成 | レビュー済みの詳細なテスト仕様書が存在 |
| ⚠️ 詳細未カバー | ルートレベルはカバー済み、詳細モジュール未作成 |
| ❌ 未作成 | テスト仕様書が存在しない |
| ➖ 対象外 | テスト作成不要（内部モジュール等） |

---

## 7. 詳細リンク

| ドキュメント | 説明 |
|-------------|------|
| [core_tests_status.md](./core/core_tests_status.md) | Core モジュールの詳細状況 |
| [plugins_tests_status.md](./plugins/plugins_tests_status.md) | Plugins の詳細状況 |
| [00_test_specification_overview.md](./00_test_specification_overview.md) | テスト仕様書概要・全体構成 |
| [TEMPLATE_test_spec.md](./TEMPLATE_test_spec.md) | テスト仕様書テンプレート |

---

## 8. 更新履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-01-28 | 初版作成 |
| 2026-02-04 | 全面改訂: ディレクトリ構造を案Aに変更 |
| 2026-02-04 | Core 14/14 完成、Plugins 24仕様書完成を反映 |
| 2026-02-04 | 未カバーモジュール一覧を追加（jobs 63件、cspm 14件、models 9件） |
| 2026-02-04 | 全体カバー率: 54%（105/194ファイル） |
