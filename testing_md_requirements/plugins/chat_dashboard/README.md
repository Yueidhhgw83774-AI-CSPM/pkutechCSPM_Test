# chat_dashboard テスト仕様書一覧

> `app/chat_dashboard/` 配下のチャットダッシュボードプラグインに対するテスト仕様書を管理する。

## 仕様書マップ

| # | グループ名 | 仕様書 | テスト数 | カバレッジ目標 | ステータス |
|---|-----------|--------|---------|--------------|-----------|
| 1 | ルーター・チャットハンドラー・Basic認証 | [chat_dashboard_tests.md](chat_dashboard_tests.md) | 55 | 85% | 完了 |
| 2 | チャットツール（v1） | [chat_tools_tests.md](chat_tools_tests.md) | 81 | 80% | 完了 |
| 3 | チャットツールv2・リソース検索v2 | [chat_tools_v2_resource_search_tests.md](chat_tools_v2_resource_search_tests.md) | 84 | 85% | 完了 |
| | **合計** | | **220** | | |

> `tools.py`（6行、空スタブ）はテスト対象外としてスキップ。

## 依存関係

```
#1 chat_dashboard_tests.md（router.py / simple_chat_handler.py / basic_auth_logic.py）
  │
  └─▶ #2 chat_tools_tests.md（chat_tools.py）
        │   simple_chat_handler.py が chat_tools.py の @tool 関数を利用
        │
        └─▶ #3 chat_tools_v2_resource_search_tests.md（chat_tools_v2.py / resource_search_v2.py）
              chat_tools_v2.py が chat_tools.py の既存機能をインポート
```

## 対象ファイル一覧

| ファイル | 行数 | 関数数 | 対応仕様書 |
|---------|------|--------|-----------|
| `app/chat_dashboard/router.py` | - | - | #1 chat_dashboard_tests.md |
| `app/chat_dashboard/simple_chat_handler.py` | - | - | #1 chat_dashboard_tests.md |
| `app/chat_dashboard/basic_auth_logic.py` | - | - | #1 chat_dashboard_tests.md |
| `app/chat_dashboard/chat_tools.py` | 1,442 | 14 | #2 chat_tools_tests.md |
| `app/chat_dashboard/chat_tools_v2.py` | 297 | 4 | #3 chat_tools_v2_resource_search_tests.md |
| `app/chat_dashboard/resource_search_v2.py` | 483 | 16 | #3 chat_tools_v2_resource_search_tests.md |
| `app/chat_dashboard/tools.py` | 6 | 0 | スキップ（空スタブ） |

## 共有リソース

| リソース | パス | 説明 |
|---------|------|------|
| conftest.py | `test/unit/chat_dashboard/conftest.py` | 共通フィクスチャ（#1 で定義、全仕様書共有） |
| テストコード | `test/unit/chat_dashboard/test_*.py` | 各仕様書に対応するテストファイル |

## ディレクトリ構造

```
docs/testing/plugins/chat_dashboard/
├── README.md                                         ← このファイル
├── chat_dashboard_tests.md                           ← #1 ルーター・ハンドラー・認証（42件）
├── chat_tools_tests.md                               ← #2 チャットツールv1（81件）
└── chat_tools_v2_resource_search_tests.md            ← #3 ツールv2・リソース検索v2（84件）
```
