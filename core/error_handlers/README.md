# error_handlers 测试项目

## 概述

本项目为 `app/core/error_handlers.py` 的单元测试。

error_handlers モジュールはエラーハンドリングに関する共通関数を提供し、標準化されたエラーレスポンス作成、OpenSearch/チャット処理の例外変換、リクエストログ出力を担当します。

## 测试规格

- **测试要件**: `docs/testing/core/error_handlers_tests.md`
- **覆盖率目标**: 90%+
- **测试框架**: pytest

## 测试对象モジュール

| 関数 | 説明 |
|------|------|
| `create_error_response()` | 標準化されたHTTPExceptionを作成（エラーID付き） |
| `handle_opensearch_exceptions()` | OpenSearch関連例外を適切なHTTPExceptionに変換 |
| `handle_chat_exceptions()` | チャット処理例外を適切なHTTPExceptionに変換 |
| `log_request_start()` | リクエスト開始をログ出力 |
| `log_request_end()` | リクエスト終了をログ出力 |

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 23 |
| 異常系 | 7 |
| セキュリティテスト | 9 |
| **合計** | **39** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\error_handlers\source
pytest test_error_handlers.py -v
```

### 生成覆盖率报告

```powershell
pytest test_error_handlers.py --cov=app.core.error_handlers --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_error_handlers.md`
- **JSON**: `reports/TestReport_error_handlers.json`

## 测试类别

### 正常系测试

| テストクラス | 対象関数 | テスト数 |
|------------|---------|---------|
| `TestCreateErrorResponse` | `create_error_response()` | 6 |
| `TestHandleOpenSearchExceptions` | `handle_opensearch_exceptions()` | 5 |
| `TestHandleChatExceptions` | `handle_chat_exceptions()` | 5 |
| `TestLogRequestStart` | `log_request_start()` | 4 |
| `TestLogRequestEnd` | `log_request_end()` | 3 |

### 異常系テスト

| テストクラス | 対象関数 | テスト数 |
|------------|---------|---------|
| `TestCreateErrorResponseErrors` | `create_error_response()` | 2 |
| `TestHandleOpenSearchExceptionsErrors` | `handle_opensearch_exceptions()` | 1 |
| `TestHandleChatExceptionsErrors` | `handle_chat_exceptions()` | 2 |
| `TestLogFunctionsErrors` | ログ関数 | 2 |

### セキュリティテスト

| テストクラス | 対策内容 | テスト数 |
|------------|---------|---------|
| `TestErrorHandlersSecurity` | CWE-209, CWE-330, OWASP A02:2021等 | 9 |

## テストの実行オプション

### 特定のテストクラスのみ実行

```powershell
# 正常系テストのみ
pytest test_error_handlers.py::TestCreateErrorResponse -v
pytest test_error_handlers.py::TestHandleOpenSearchExceptions -v
pytest test_error_handlers.py::TestHandleChatExceptions -v

# 異常系テストのみ
pytest test_error_handlers.py::TestCreateErrorResponseErrors -v
pytest test_error_handlers.py::TestHandleChatExceptionsErrors -v

# セキュリティテストのみ
pytest test_error_handlers.py -m "security" -v
```

### カバレッジ付きで実行

```powershell
pytest test_error_handlers.py --cov=app.core.error_handlers --cov-report=term-missing -v
```

### xfailを含めた詳細表示

```powershell
pytest test_error_handlers.py -v --tb=short
```

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
fastapi>=0.100.0
opensearchpy>=2.0.0
```

## 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | ログに`exc_info=True`で出力 | スタックトレースがログに出力される | 本番環境ではログレベルをWARNING以上に設定 |
| 2 | `str(e)`をそのままログ出力 | 例外メッセージに機密情報が含まれる場合、ログに露出 | 例外メッセージのサニタイズ処理追加を推奨 |
| 3 | 入力バリデーションなし | `status_code`や`message`の不正値をそのまま使用 | FastAPI側でレスポンス検証されるため影響は限定的 |
| 4 | ログレベル判定 | `logger.isEnabledFor(logging.DEBUG)`でDEBUG出力を制御 | テスト時はロガーレベルを適切に設定 |
| 5 | UUID生成の衝突可能性 | 理論上は衝突可能だが実用上は無視できる | 追跡IDとして十分なユニーク性 |
| 6 | ログインジェクション未対策 | 改行を含むエラーメッセージがログにそのまま出力される | `_sanitize_log_message()`関数の追加を推奨 |
| 7 | HTTPException再発生 | `handle_chat_exceptions`でHTTPExceptionを`raise`する | 呼び出し元でtry-exceptが必要 |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します（`@pytest.mark.xfail`）。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| ERH-SEC-08 | `str(e)`をそのままログ出力（`error_handlers.py:75, 108`） | エラーメッセージから制御文字を除去するサニタイズ処理を追加 |

## 注意事项

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文和日本語注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ✅ セキュリティテストには `@pytest.mark.security` マーカーを使用
5. ✅ ログ検証時は `caplog` フィクスチャを使用し、`logger="app.core.error_handlers"` を指定

## プロジェクト構造

```
C:\pythonProject\python_ai_cspm\TestReport\error_handlers\
├── README.md                          # 本ファイル
├── 测试完成总结.md                     # テスト完成総括
├── source\
│   ├── conftest.py                    # pytest設定とレポート生成
│   └── test_error_handlers.py         # テストコード（39個のテスト）
└── reports\
    ├── TestReport_error_handlers.md   # Markdownテストレポート
    └── TestReport_error_handlers.json # JSONテストレポート
```

---

**最終更新**: 2026-02-02
**テスト作成者**: AI Agent
