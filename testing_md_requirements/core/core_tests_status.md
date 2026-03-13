# Core テスト仕様書の状況

## 概要

`app/core/` ディレクトリ内のモジュールに対するテスト仕様書の作成状況を管理します。

---

## 1. テスト仕様書の状況一覧

| ファイル | テスト仕様書 | 状態 | 優先度 |
|---------|------------|------|--------|
| `config.py` | `config_tests.md` | ✅ 完成 | - |
| `llm_factory.py` | `llm_factory_tests.md` | ✅ 完成 | - |
| `clients.py` | `clients_tests.md` | ✅ 完成 | - |
| `auth.py` | `plugins/auth_tests.md` | ✅ 完成（plugins側） | - |
| `permission_checker.py` | `permission_checker_tests.md` | ✅ 完成 | - |
| `checkpointer.py` | `checkpointer_tests.md` | ✅ 完成 | - |
| `crypto.py` | `crypto_tests.md` | ✅ 完成 | - |
| `auth_utils.py` | `auth_utils_tests.md` | ✅ 完成 | - |
| `encryption_middleware.py` | `encryption_middleware_tests.md` | ✅ 完成 | - |
| `categories.py` | `categories_tests.md` | ✅ 完成 | - |
| `rag_manager.py` | `rag_manager_tests.md` | ✅ 完成 | - |
| `role_based_client.py` | `role_based_client_tests.md` | ✅ 完成 | - |
| `health_checker.py` | `health_checker_tests.md` | ✅ 完成 | - |
| `error_handlers.py` | `error_handlers_tests.md` | ✅ 完成 | - |
| `__init__.py` | - | N/A | - |

### 凡例
- ✅ 完成: 詳細なテスト仕様書が存在
- ⚠️ テンプレートのみ: 基本構造のみ、詳細化が必要
- ❌ 未作成: テスト仕様書が存在しない
- N/A: テスト不要（インポートのみ等）

---

## 2. 完全に未作成のテスト仕様書（7ファイル）

### ~~2.1 crypto.py~~ → ✅ 完成（[crypto_tests.md](./crypto_tests.md) 参照）

---

### 2.2 auth_utils.py（優先度: 高）

**機能概要:**
- 認証関連のユーティリティ関数
- トークン処理補助

**推奨カバレッジ:** 85%

---

### 2.3 encryption_middleware.py（優先度: 高）

**機能概要:**
- FastAPIミドルウェアとしての暗号化処理
- リクエスト/レスポンスの暗号化・復号

**推奨カバレッジ:** 85%

---

### ~~2.4 rag_manager.py~~ → ✅ 完成（[rag_manager_tests.md](./rag_manager_tests.md) 参照）

**機能概要:**
- RAG（Retrieval Augmented Generation）検索管理
- ベクトル検索・セマンティック検索

**推奨カバレッジ:** 75%

---

### 2.5 error_handlers.py（優先度: 高）

**機能概要:**
- FastAPIグローバルエラーハンドラー
- 例外からHTTPレスポンスへの変換

**推奨カバレッジ:** 80%

---

### 2.6 role_based_client.py（優先度: 中）

**機能概要:**
- ロールベースのOpenSearchクライアント
- ユーザーロールに応じたアクセス制御

**推奨カバレッジ:** 75%

---

### ~~2.7 health_checker.py~~ → ✅ 完成（[health_checker_tests.md](./health_checker_tests.md) 参照）

**機能概要:**
- サービスヘルスチェック
- OpenSearch/Redis等の接続確認

**推奨カバレッジ:** 90%

---

### ~~2.8 categories.py~~ → ✅ 完成（[categories_tests.md](./categories_tests.md) 参照）

**機能概要:**
- カテゴリ定義・管理
- 推奨事項のカテゴリ分類

**推奨カバレッジ:** 60%

---

## 3. テンプレートから詳細化が必要（4ファイル）

### ~~3.1 clients.py~~ → ✅ 完成（[clients_tests.md](./clients_tests.md) 参照）

---

### ~~3.2 auth.py~~ → ✅ 完成（[plugins/auth_tests.md](../plugins/auth_tests.md) 参照）

> `app/core/auth.py` のテスト仕様は `plugins/auth_tests.md`（AUTH-001〜, AUTH-RBAC-*, AUTH-SEC-*）で包括的にカバー済み。

---

### ~~3.3 permission_checker.py~~ → ✅ 完成（[permission_checker_tests.md](./permission_checker_tests.md) 参照）

> 以下のテンプレートは陳腐化しています（`check_permission()`, `has_role()` 等、実装に存在しない関数を参照）。最新のテスト仕様は `permission_checker_tests.md`（PERM-001〜, PERM-E*, PERM-SEC-*）を参照してください。

---

### ~~3.4 checkpointer.py~~ → ✅ 完成（[checkpointer_tests.md](./checkpointer_tests.md) 参照）

> 以下のテンプレートは陳腐化しています（`save_checkpoint()`, `restore_checkpoint()` 等、実装に存在しない関数を参照）。
> 実装は `get_async_checkpointer()` 関数中心で、シングルトンパターンとフォールバック機構を持ちます。
> 最新のテスト仕様は `checkpointer_tests.md`（CKP-001〜, CKP-E*, CKP-SEC-*）を参照してください。

---

## 4. 作成優先順位

### フェーズ1（セキュリティ・基盤）
1. **crypto.py** - セキュリティ最重要
2. **clients.py** - 全プラグインが依存
3. **auth.py** - 認証基盤

### フェーズ2（機能コア）
4. **error_handlers.py** - エラー処理統一
5. **rag_manager.py** - AI機能の中核
6. **encryption_middleware.py** - 通信セキュリティ

### フェーズ3（補助機能）
7. **permission_checker.py** - 権限管理
8. **auth_utils.py** - 認証補助
9. **role_based_client.py** - ロールベースアクセス

### フェーズ4（その他）
10. **checkpointer.py** - 状態管理
11. **health_checker.py** - 監視
12. **categories.py** - 分類機能

---

## 5. 進捗管理

| フェーズ | 対象ファイル | 状態 | 完了日 |
|---------|-------------|------|--------|
| 1 | crypto.py | ✅ 完成 | 2026-01-27 |
| 1 | clients.py | ✅ 完成 | 2026-01-28 |
| 1 | auth.py | ✅ 完成（plugins側） | - |
| 2 | error_handlers.py | ✅ 完成 | 2026-01-30 |
| 2 | rag_manager.py | ✅ 完成 | 2026-01-30 |
| 2 | encryption_middleware.py | ✅ 完成 | 2026-01-30 |
| 3 | permission_checker.py | ✅ 完成 | 2026-01-30 |
| 3 | auth_utils.py | ✅ 完成 | 2026-01-30 |
| 3 | role_based_client.py | ✅ 完成 | 2026-01-30 |
| 4 | checkpointer.py | ✅ 完成 | 2026-01-30 |
| 4 | health_checker.py | ✅ 完成 | 2026-01-30 |
| 4 | categories.py | ✅ 完成 | 2026-01-30 |

---

## 6. 参考: 完成済みテスト仕様書

- [config_tests.md](./config_tests.md) - 設定管理
- [llm_factory_tests.md](./llm_factory_tests.md) - LLMファクトリー
- [crypto_tests.md](./crypto_tests.md) - 暗号化・復号
- [clients_tests.md](./clients_tests.md) - OpenSearch/Embeddingクライアント
- [permission_checker_tests.md](./permission_checker_tests.md) - OpenSearch動的権限チェック
- [plugins/auth_tests.md](../plugins/auth_tests.md) - 認証・認可（plugins側でcore/auth.pyをカバー）
- [checkpointer_tests.md](./checkpointer_tests.md) - LangGraph Checkpointer
- [auth_utils_tests.md](./auth_utils_tests.md) - 認証ユーティリティ
- [encryption_middleware_tests.md](./encryption_middleware_tests.md) - 暗号化ミドルウェア
- [categories_tests.md](./categories_tests.md) - カテゴリ定義・管理
- [rag_manager_tests.md](./rag_manager_tests.md) - RAGクライアント管理
- [role_based_client_tests.md](./role_based_client_tests.md) - ロールベースOpenSearchクライアント
- [health_checker_tests.md](./health_checker_tests.md) - ヘルスチェック
- [error_handlers_tests.md](./error_handlers_tests.md) - エラーハンドリング
- [remaining_core_template.md](./remaining_core_template.md) - 基本テンプレート
