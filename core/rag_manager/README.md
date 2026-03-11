# rag_manager 测试项目

## 概述

本项目为 `app/core/rag_manager.py` 的单元测试。

RAGクライアントのグローバル管理システムをテストします。シングルトンパターンとdouble-checked lockingの実装を検証します。

## 测试规格

- **测试要件**: `docs/testing/core/rag_manager_tests.md`
- **覆盖率目标**: 75%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 14 |
| 异常系 | 7 |
| 安全测试 | 3 |
| **合计** | **24** |

## 主要功能覆盖

| 功能 | 测试用例数 | 说明 |
|------|-----------|------|
| `RAGManager.get_instance()` | 2 | シングルトンインスタンス取得 |
| `RAGManager.initialize()` | 3 | RAGシステム初期化（double-checked locking含む） |
| `RAGManager.get_enhanced_rag_search()` | 2 | 強化版RAG検索システム取得 |
| `RAGManager.is_initialized()` | 2 | 初期化状態確認 |
| `RAGManager.health_check()` | 4 | ヘルスチェック（正常系＋異常系） |
| グローバル関数 | 4 | グローバルマネージャー操作 |
| セキュリティ | 3 | 情報漏洩防止とスレッドセーフ性 |

## 快速开始

### 前提条件

```powershell
# 必要なパッケージをインストール
pip install pytest pytest-asyncio pytest-cov
```

### 运行测试

```powershell
# rag_managerディレクトリに移動
cd C:\pythonProject\python_ai_cspm\TestReport\rag_manager\source

# 全テストを実行
pytest test_rag_manager.py -v

# 特定のテストクラスを実行
pytest test_rag_manager.py::TestRAGManagerInitialize -v

# セキュリティテストのみ実行
pytest test_rag_manager.py -m security -v
```

### 生成覆盖率报告

```powershell
# HTMLカバレッジレポートを生成
pytest test_rag_manager.py --cov=app.core.rag_manager --cov-report=html --cov-report=term

# レポートを開く
start htmlcov\index.html
```

### 查看报告

テスト実行後、自動的に以下のレポートが生成されます：

- **Markdown**: `reports/TestReport_rag_manager.md`
- **JSON**: `reports/TestReport_rag_manager.json`

## 测试类别

### 正常系测试 (`TestRAGManager*`)

RAGマネージャーの正常な動作を検証します：

- ✅ **モジュールインポート**: 必要なクラス・関数の存在確認
- ✅ **シングルトン取得**: インスタンス取得と一貫性
- ✅ **初期化**: 正常な初期化とdouble-checked locking
- ✅ **RAG検索システム取得**: 初期化済み状態と自動初期化
- ✅ **初期化状態確認**: is_initialized()の動作
- ✅ **ヘルスチェック**: RAGシステムのヘルス情報取得
- ✅ **グローバル関数**: グローバルマネージャー操作

### 异常系测试 (`TestRAGManager*Errors`)

エラーハンドリングとエッジケースを検証します：

- ⚠️ **初期化失敗**: EnhancedRAGSearchの初期化エラー処理
- ⚠️ **初期化例外**: 例外発生時のエラーハンドリング
- ⚠️ **自動初期化失敗**: RuntimeError発生確認
- ⚠️ **未初期化ヘルスチェック**: 適切なエラーメッセージ
- ⚠️ **RAG無しヘルスチェック**: enhanced_rag_search=Noneの処理
- ⚠️ **ヘルスチェック例外**: 接続エラー等の例外処理
- ⚠️ **グローバル初期化例外**: グローバル関数の例外処理

### 安全测试 (`TestRAGManagerSecurity`)

セキュリティとスレッドセーフ性を検証します：

- 🔒 **機密情報漏洩防止**: ログに認証情報が含まれないこと（⚠️ 実装側要修正）
- 🔒 **エラー詳細漏洩防止**: スタックトレースが外部に漏れないこと
- 🔒 **スレッドセーフ性**: 並行アクセス時の競合状態防止

## 依赖项

```
pytest>=8.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
```

## 注意事项

### 重要なポイント

1. ✅ **モジュールリセット**: テスト間でシングルトン状態をリセット（`reset_rag_manager_module` fixture）
2. ✅ **非同期テスト**: `@pytest.mark.asyncio` デコレータ使用
3. ✅ **モックパス**: EnhancedRAGSearchは `app.rag.enhanced_rag_search.EnhancedRAGSearch` でpatch
4. ⚠️ **xfailテスト**: RAG-SEC-01は実装側の修正が必要

### テスト実行時の注意

- **並列実行は推奨しません**: シングルトンパターンのため、テストは順次実行してください
- **モジュールキャッシュ**: `reset_rag_manager_module` fixtureが自動的にクリアします
- **ログレベル**: エラーログテストでは `caplog.set_level(logging.ERROR)` を使用

### 既知の問題

| テストID | 問題 | 対応策 |
|---------|------|--------|
| RAG-SEC-01 | ログに機密情報が漏洩する | `@pytest.mark.xfail` でマーク済み。実装側でサニタイズ処理追加が必要 |

## 推奨される改善

### 実装側の改善提案

```python
# rag_manager.py:69 の改善案
except Exception as e:
    # 機密情報をマスクする
    safe_error = sanitize_error_message(str(e))
    logger.error(f"RAG管理システム初期化エラー: {safe_error}")
    return False

def sanitize_error_message(message: str) -> str:
    """エラーメッセージから機密情報を削除"""
    import re
    # APIキー、パスワード等をマスク
    message = re.sub(r'(api_key|password|token|secret)=[^\s,)]+', r'\1=***', message, flags=re.IGNORECASE)
    return message
```

## プロジェクト構成

```
C:\pythonProject\python_ai_cspm\TestReport\rag_manager\
├── README.md                          # 本ファイル
├── 测试完成总结.md                     # テスト完了サマリー
├── source\
│   ├── conftest.py                    # pytest設定とフック
│   └── test_rag_manager.py            # テストソースコード（24テスト）
└── reports\
    ├── TestReport_rag_manager.md      # Markdownレポート
    └── TestReport_rag_manager.json    # JSONレポート
```

## トラブルシューティング

### テストが失敗する場合

1. **モジュールが見つからない**:
   ```powershell
   # プロジェクトルートが正しいか確認
   echo $env:PYTHONPATH
   ```

2. **非同期エラー**:
   ```powershell
   # pytest-asyncioがインストールされているか確認
   pip show pytest-asyncio
   ```

3. **モック失敗**:
   ```python
   # patchパスが正しいか確認
   # ❌ "app.core.rag_manager.EnhancedRAGSearch"
   # ✅ "app.rag.enhanced_rag_search.EnhancedRAGSearch"
   ```

### よくある質問

**Q: なぜカバレッジ目標が75%なのですか？**  
A: RAGマネージャーは外部依存（EnhancedRAGSearch）が多く、モック中心のテストとなるため、実際の接続動作は統合テストで補完します。

**Q: RAG-SEC-01が失敗するのは正常ですか？**  
A: はい。`@pytest.mark.xfail`でマークされており、実装側の改善が必要であることを示しています。

**Q: 並列実行できますか？**  
A: シングルトンパターンを使用しているため、並列実行は推奨しません。`pytest -n auto`は使用しないでください。

## 関連リンク

- [pytest ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio ドキュメント](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock ドキュメント](https://docs.python.org/3/library/unittest.mock.html)

---

**最終更新**: 2026-02-03  
**作成者**: AI Testing Agent
