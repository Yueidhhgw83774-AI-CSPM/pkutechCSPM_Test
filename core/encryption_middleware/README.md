# encryption_middleware 测试项目

## 概述

本项目为 `app/core/encryption_middleware.py` 的单元测试。

该模块提供ASGI中间件功能,用于拦截和解密加密的HTTP请求体,然后将解密后的数据传递给应用程序。

## 测试规格

- **测试要件**: `docs/testing/core/encryption_middleware_tests.md`
- **覆盖率目标**: 85%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 15 |
| 异常系 | 8 |
| 安全测试 | 5 |
| **合计** | **28** |

## 功能概述

### DecryptionMiddleware 类

ASGIミドルウェアとして動作し、以下の機能を提供します:

- **暗号化リクエストの検出**: `encrypted: true` フラグを持つJSONボディを検出
- **復号処理**: AES-256-CBCを使用してリクエストボディを復号
- **認証ハッシュ検証**: X-Auth-Hash ヘッダーによるHMAC認証(オプション)
- **パススルー**: 非暗号化リクエストはそのまま転送
- **エラーハンドリング**: 復号失敗時は400エラーレスポンスを返却

### 主要関数

| 関数 | 説明 |
|------|------|
| `__init__(app, paths_to_decrypt)` | ミドルウェアの初期化 |
| `__call__(scope, receive, send)` | ASGIエントリーポイント |
| `_decrypt_request(encrypted_request, auth_header)` | 暗号化データの復号 |
| `create_decryption_middleware(paths)` | ファクトリ関数 |

## 快速开始

### 运行所有测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\encryption_middleware\source
pytest test_encryption_middleware.py -v
```

### 运行特定类别的测试

```powershell
# 只运行正常系测试
pytest test_encryption_middleware.py -v -k "not Errors and not Security"

# 只运行异常系测试
pytest test_encryption_middleware.py -v -k "Errors"

# 只运行安全测试
pytest test_encryption_middleware.py -v -m security
```

### 生成覆盖率报告

```powershell
pytest test_encryption_middleware.py --cov=app.core.encryption_middleware --cov-report=html --cov-report=term
```

覆盖率报告将生成在 `htmlcov/` 目录中。

### 查看测试报告

测试完成后,会自动生成以下报告:

- **Markdown报告**: `reports/TestReport_encryption_middleware.md`
- **JSON报告**: `reports/TestReport_encryption_middleware.json`

## 测试类别说明

### 正常系测试 (`Test*` 类)

验证模块的正常工作流程:

- ✅ 初期化処理の成功
- ✅ 非暗号化リクエストのパススルー
- ✅ 暗号化リクエストの復号成功
- ✅ 認証ハッシュ検証
- ✅ ヘッダー更新処理

**测试类:**
- `TestDecryptionMiddlewareInit`: 初期化テスト
- `TestDecryptionMiddlewarePassthrough`: パススルーテスト
- `TestDecryptionMiddlewareDecrypt`: 復号成功テスト
- `TestCreateDecryptionMiddleware`: ファクトリ関数テスト

### 异常系测试 (`Test*Errors` 类)

验证错误处理逻辑:

- ❌ 初期化時のエラー処理
- ❌ 不正な暗号化データの処理
- ❌ 認証ハッシュ検証失敗
- ❌ IV欠落エラー
- ❌ 復号処理の例外ハンドリング

**测试类:**
- `TestDecryptionMiddlewareInitErrors`: 初期化エラー
- `TestDecryptionMiddlewareDecryptErrors`: 復号エラー

### 安全测试 (`Test*Security` 类)

验证安全相关功能:

- 🔒 秘密鍵のログ出力防止
- 🔒 復号データのログ出力防止
- 🔒 認証ハッシュの保護
- 🔒 エラーメッセージの安全性
- 🔒 タイミング攻撃への耐性

**测试类:**
- `TestEncryptionMiddlewareSecurity`: セキュリティテスト

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
pytest-asyncio>=0.23.0
cryptography>=41.0.0
```

## 测试用固定装置 (Fixtures)

### `reset_encryption_middleware_module`

- **スコープ**: 各テスト関数
- **用途**: テスト間でモジュールキャッシュをクリアし、独立性を保証

### `test_shared_secret`

- **用途**: テスト用の共有秘密鍵を提供

### `encrypted_request_data`

- **用途**: 有効な暗号化リクエストデータを生成

### `middleware_and_mocks`

- **用途**: テスト用ミドルウェアインスタンスとモックアプリを提供

## 注意事項

### 1. モジュールキャッシュのクリア

`encryption_middleware.py` は初期化時に復号テストを実行するため、テスト間で `autouse=True` の fixture を使用してモジュールキャッシュをクリアしています。

### 2. 非同期テスト

ASGIミドルウェアの性質上、ほとんどのテストは `@pytest.mark.asyncio` でマークされています。

### 3. 暗号化データの生成

テストでは `cryptography` ライブラリを使用して実際の暗号化データを生成しています。

### 4. モックの使用

- `AsyncMock`: 非同期関数のモック
- `patch`: 外部依存関係のモック(crypto.py の関数など)

## トラブルシューティング

### テストが失敗する場合

1. **依存関係の確認**
   ```powershell
   pip install -r requirements.txt
   ```

2. **環境変数の確認**
   `.env` ファイルが正しく設定されているか確認

3. **詳細なエラー情報を表示**
   ```powershell
   pytest test_encryption_middleware.py -v --tb=long
   ```

### カバレッジが低い場合

1. **カバレッジレポートを生成**
   ```powershell
   pytest test_encryption_middleware.py --cov=app.core.encryption_middleware --cov-report=html
   ```

2. **未カバー行を確認**
   `htmlcov/index.html` をブラウザで開き、赤色でハイライトされた行を確認

## 参考資料

- [pytest 公式ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio ドキュメント](https://pytest-asyncio.readthedocs.io/)
- [ASGI 仕様](https://asgi.readthedocs.io/)
- [Cryptography ライブラリ](https://cryptography.io/)

---

**最終更新**: 2026-02-02  
**作成者**: AI Agent
