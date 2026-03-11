# MCP Plugin - Deep Agents テストスイート

## 概要

このディレクトリには、MCP Plugin の Deep Agents サブモジュールに対する完全なテストスイートが含まれています。

## テスト対象

- **ソースコードパス**: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing\app\mcp_plugin\deep_agents\`
- **テスト要件**: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing\docs\testing\plugins\mcp\mcp_plugin_deep_agents_tests.md`

## テスト構成

### 📁 ディレクトリ構造

```
mcp_plugin_deep_agents/
├── README.md                    # このファイル
└── source/
    ├── conftest.py             # 共通フィクスチャ定義
    └── test_deep_agents.py     # 完全テストスイート (38 tests)
```

## テストカテゴリ

### ✅ 正常系テスト (16 tests)

| テストID | テスト名 | 説明 |
|---------|---------|------|
| MCPDA-001 | コンポーネント初期化成功 | MCPチャットコンポーネントの初期化 |
| MCPDA-002 | チャット実行成功 | Deep Agentsチャット実行 |
| MCPDA-003 | ストリーミング実行成功 | SSEストリーミングチャット |
| MCPDA-004 | セッションキャッシュクリア | Responses APIキャッシュクリア |
| MCPDA-005 | 進捗情報構築（dict形式） | 進捗情報の構築（辞書形式） |
| MCPDA-006 | MCPツール作成 | call_mcp_toolツール作成 |
| MCPDA-007 | ツールイベント（write_todos） | write_todosツール呼び出しイベント |
| MCPDA-008 | cloud_credentials付きツール実行 | クレデンシャルコンテキスト渡し |
| MCPDA-009 | 進捗情報構築（object形式） | model_dump使用の進捗構築 |
| MCPDA-010 | 進捗情報構築（server_nameなし） | server_nameなしでの進捗構築 |
| MCPDA-011 | サブエージェント作成 | 5つのカスタムサブエージェント |
| MCPDA-012 | ツールイベント（call_mcp_tool） | MCPツール呼び出しイベント |
| MCPDA-013 | ツールイベント（task） | サブエージェント呼び出しイベント |
| MCPDA-014 | MCPツール一覧取得 | list_mcp_tools実行 |
| MCPDA-015 | MCPサーバー一覧取得 | list_mcp_servers実行 |
| MCPDA-016 | ポリシー検証統合成功 | ポリシー検証ミドルウェア統合 |

### ❌ 異常系テスト (10 tests)

| テストID | テスト名 | 説明 |
|---------|---------|------|
| MCPDA-E01 | 初期化エラー | LLM取得失敗時のエラー処理 |
| MCPDA-E02 | チャット実行エラー | エージェント実行時のエラー処理 |
| MCPDA-E03 | ストリーミングエラー | ストリーム中のエラー処理 |
| MCPDA-E04 | ツール作成エラー | MCPクライアントエラー処理 |
| MCPDA-E05 | 存在しないセッションクリア | 冪等性の確認 |
| MCPDA-E06 | ストリーム初期化失敗 | エージェント未初期化時のエラー |
| MCPDA-E07 | クライアント切断 | CancelledErrorの処理 |
| MCPDA-E08 | APIパースエラー | ValidationError相当の処理 |
| MCPDA-E09 | ポリシー検証エラー | 不正なポリシーの処理 |
| MCPDA-E10 | ツール実行タイムアウト | タイムアウトの検証 |

### 🔒 セキュリティテスト (12 tests)

| テストID | テスト名 | 説明 |
|---------|---------|------|
| MCPDA-SEC-01 | システムプロンプトのセキュリティ | 危険な指示が含まれないことを確認 |
| MCPDA-SEC-02 | ツール結果のサニタイズ | 出力の切り詰めとサニタイズ |
| MCPDA-SEC-03 | セッション分離 | セッション間の独立性 |
| MCPDA-SEC-04 | プロンプトインジェクション対策 | 悪意のあるプロンプトの処理 |
| MCPDA-SEC-05 | クレデンシャル漏洩防止（出力） | 出力へのクレデンシャル非含有 |
| MCPDA-SEC-06 | セッションハイジャック防止 | セッションIDの分離 |
| MCPDA-SEC-07 | DoS対策（過大入力） | 大量入力の処理 |
| MCPDA-SEC-08 | ツール認可検証 | 未承認ツールアクセスの拒否 |
| MCPDA-SEC-09 | ログへの機密情報漏洩防止 | ログへのクレデンシャル非出力 |
| MCPDA-SEC-10 | 入力バリデーション | 不正なセッションID形式の処理 |
| MCPDA-SEC-11 | ツールパラメータ改ざん防止 | 不正なパラメータの処理 |
| MCPDA-SEC-12 | ストリーミングレスポンスID検証 | レスポンスIDの分離 |

## テスト実行方法

### 前提条件

```bash
# 必要なパッケージのインストール
pip install pytest pytest-asyncio pytest-cov
```

### 基本的な実行

```bash
# すべてのテストを実行
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\mcp\mcp_plugin_deep_agents\source
pytest test_deep_agents.py -v

# カバレッジ付きで実行
pytest test_deep_agents.py --cov=app.mcp_plugin.deep_agents --cov-report=term-missing -v

# 特定のカテゴリのみ実行
pytest test_deep_agents.py -k "TestDeepAgentsInitialization" -v

# セキュリティテストのみ実行
pytest test_deep_agents.py -m "security" -v
```

### 環境変数設定

テストを実行する前に、`.env` ファイルで以下を設定してください：

```env
# TestReport/.env
source_root="C:\pythonProject\python_ai_cspm\platform_python_backend-testing\"
```

### pytest.ini 設定

プロジェクトルートに `pytest.ini` を追加：

```ini
[pytest]
markers =
    security: セキュリティ関連のテスト
asyncio_mode = auto
```

## 主要フィクスチャ

### conftest.py に定義されたフィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_deep_agents_module` | グローバル状態リセット | function | Yes |
| `mock_llm` | LLMモック | function | No |
| `mock_agent_graph` | エージェントグラフモック | function | No |
| `mock_mcp_client` | MCPクライアントモック | function | No |
| `mock_existing_message_ids` | メッセージID取得モック | function | No |
| `mock_result_storage` | ResultStorageモック | function | No |

## カバレッジ目標

- **目標カバレッジ**: 80%
- **現状**: LangGraph状態管理とLLM呼び出しの複雑さから、主要パスと重要なエラーハンドリングをカバー

## 既知の制限事項

1. **LangGraph状態管理**: 内部状態遷移の完全テストは困難
2. **astream_eventsのモック**: ストリーミングテストが限定的
3. **実LLM呼び出し**: モデル応答品質の検証は統合テストで実施
4. **Checkpointer依存**: `_get_existing_message_ids` をモックで回避

## 予想される失敗テスト

以下のテストは、現在の実装では失敗が予想されます（セキュリティ改善のトリガー）：

- **MCPDA-SEC-07**: DoS対策（入力サイズ制限が未実装の可能性）
- **MCPDA-SEC-10**: 入力バリデーション（セッションIDバリデーションが未実装の可能性）

これらのテスト失敗は、将来のセキュリティ改善の指標として機能します。

## テスト統計

```
総テスト数: 38
├── 正常系: 16 tests
├── 異常系: 10 tests
└── セキュリティ: 12 tests

実装済み: 38/38 (100%)
```

## 関連ドキュメント

- [テスト要件書](C:\pythonProject\python_ai_cspm\platform_python_backend-testing\docs\testing\plugins\mcp\mcp_plugin_deep_agents_tests.md)
- [ソースコード](C:\pythonProject\python_ai_cspm\platform_python_backend-testing\app\mcp_plugin\deep_agents\)

## トラブルシューティング

### モジュールインポートエラー

```bash
# PYTHONPATH を設定
set PYTHONPATH=C:\pythonProject\python_ai_cspm\platform_python_backend-testing
```

### 非同期テストエラー

```bash
# pytest-asyncio をインストール
pip install pytest-asyncio
```

### カバレッジレポートが生成されない

```bash
# coverage パッケージをインストール
pip install pytest-cov coverage
```

## 更新履歴

- **2026-03-11**: 初回実装 - 38テスト完全実装
  - 正常系: 16 tests
  - 異常系: 10 tests
  - セキュリティ: 12 tests

