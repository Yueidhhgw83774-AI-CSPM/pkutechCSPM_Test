# テスト仕様書概要

## 1. 目的

本ドキュメントは、python-fastapiプロジェクトのテスト仕様書です。以下の目的を達成するために作成されました：

- テスト品質の標準化と一貫性の確保
- チームメンバー間でのテスト方針の共有
- テストカバレッジ目標の明確化
- CI/CD パイプラインとの統合方針の定義

## 2. 対象範囲

### 2.1 対象プロジェクト

| 項目 | 値 |
|------|-----|
| プロジェクト名 | python-fastapi |
| パス | `/usr/share/osd/python-fastapi` |
| フレームワーク | FastAPI |
| テストフレームワーク | pytest |

### 2.2 対象プラグイン

| プラグイン | 優先度 | 説明 | エンドポイント |
|-----------|--------|------|---------------|
| cspm_plugin | 高 | CSPMポリシー生成・修正 | `/cspm`, `/cspm-tools` |
| auth | 高 | JWT認証 | `/auth` |
| jobs | 高 | バックグラウンドジョブ管理 | `/jobs` |
| chat_dashboard | 中 | シンプルチャット | `/chat/cspm_dashboard` |
| mcp_plugin | 中 | 外部ツール統合（MCP） | `/mcp` |
| report_plugin | 中 | レポート生成 | `/report` |
| rag | 低 | 意味的検索 | `/rag` |
| doc_reader_plugin | 低 | ドキュメント読み込み | `/docreader` |
| custodian_scan | 低 | Cloud Custodian実行 | `/custodian` |
| logchecker | 低 | ログ解析 | - |
| aws_plugin | 低 | AWS操作 | - |

### 2.3 対象コアサービス

| サービス | 優先度 | 説明 |
|----------|--------|------|
| auth (core) | 高 | 認証コアサービス |
| config | 高 | 設定管理 |
| llm_factory | 高 | LLMインスタンス生成 |
| permission_checker | 中 | 権限チェック |
| checkpointer | 中 | チェックポイント管理 |
| clients | 中 | 外部サービスクライアント |

## 3. 技術スタック

### 3.1 アプリケーション

| 分類 | 技術 | バージョン |
|------|------|-----------|
| フレームワーク | FastAPI | 最新 |
| LLM統合 | LangChain | 1.x |
| グラフ実行 | LangGraph | 1.x |
| データベース | OpenSearch | 非同期クライアント |
| 認証 | JWT | python-jose |

### 3.2 テスト

| 分類 | 技術 | 用途 |
|------|------|------|
| テストフレームワーク | pytest | ユニット・統合テスト |
| カバレッジ | pytest-cov | コードカバレッジ測定 |
| 非同期テスト | pytest-asyncio | 非同期関数テスト |
| HTTPクライアント | httpx | FastAPIテストクライアント |
| モック | unittest.mock / pytest-mock | 外部依存モック |

## 4. ドキュメント構成

```
docs/testing/
├── 00_test_specification_overview.md  # 本ドキュメント
├── 01_test_strategy.md                # テスト戦略
├── 02_test_categories.md              # テストカテゴリ分類
├── 03_test_environment.md             # テスト環境設定
├── 04_conftest_design.md              # conftest.py設計
├── 05_fixture_design.md               # フィクスチャ設計
├── 06_mock_strategy.md                # モック戦略
├── 07_coverage_targets.md             # カバレッジ目標
├── plugins/                           # プラグイン別テストケース
│   ├── cspm_plugin_tests.md
│   ├── chat_dashboard_tests.md
│   ├── mcp_plugin_tests.md
│   ├── doc_reader_plugin_tests.md
│   ├── report_plugin_tests.md
│   ├── auth_tests.md
│   ├── rag_tests.md
│   ├── custodian_scan_tests.md
│   ├── logchecker_tests.md
│   ├── aws_plugin_tests.md
│   └── jobs_tests.md
├── core/                              # コアサービステストケース
│   ├── config_tests.md
│   ├── clients_tests.md
│   ├── auth_tests.md
│   ├── llm_factory_tests.md
│   ├── permission_checker_tests.md
│   └── checkpointer_tests.md
└── recommended/                       # 推奨ドキュメント（将来対応）
    └── ci_cd_integration.md           # CI/CD統合（推奨）
```

## 5. 用語定義

| 用語 | 定義 |
|------|------|
| ユニットテスト | 単一の関数やクラスを単独でテストする |
| 統合テスト | 複数のコンポーネント間の連携をテストする |
| E2Eテスト | エンドツーエンドでシステム全体をテストする |
| フィクスチャ | テストで使用する事前準備されたデータやオブジェクト |
| モック | 外部依存を置き換えるテスト用のダミーオブジェクト |
| カバレッジ | テストがコードのどの程度をカバーしているかの指標 |

## 6. 参照ドキュメント

| ドキュメント | パス | 説明 |
|--------------|------|------|
| プロジェクトREADME | `/usr/share/osd/python-fastapi/README.md` | プロジェクト概要 |
| CLAUDE.md | `/usr/share/osd/python-fastapi/CLAUDE.md` | 開発ガイドライン |
| 既存テストケース | `docs/cspm-plugin-test-cases.md` | CSPMプラグインテストケース（参考） |
| pyproject.toml | `/usr/share/osd/python-fastapi/pyproject.toml` | プロジェクト設定 |

## 7. 更新履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-01-26 | 1.0.0 | 初版作成 |
