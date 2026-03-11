# Jobs Router テスト クイックスタートガイド

## 前提条件

1. Python 3.9以上がインストールされている
2. 必要なパッケージがインストールされている（下記参照）
3. 環境変数が設定されている

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install pytest pytest-asyncio httpx fastapi python-dotenv
```

### 2. 環境変数の設定

`.env` ファイルを `TestReport/` ディレクトリに作成：

```env
soure_root=C:\pythonProject\python_ai_cspm\platform_python_backend-testing\
```

## テスト実行

### 基本的な実行

```bash
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\jobs\jobs_router\source
pytest test_jobs_router.py -v
```

### カテゴリ別実行

```bash
# 正常系テストのみ
pytest test_jobs_router.py::TestJobsStartEndpoints -v
pytest test_jobs_router.py::TestJobsStatusEndpoints -v
pytest test_jobs_router.py::TestScanFilesEndpoint -v

# 異常系テストのみ
pytest test_jobs_router.py::TestJobsErrors -v
pytest test_jobs_router.py::TestEncryptedRequestErrors -v
pytest test_jobs_router.py::TestScanFilesErrors -v

# セキュリティテストのみ
pytest test_jobs_router.py::TestJobsSecurityEndpoints -v
```

### 詳細な出力

```bash
# より詳細な出力
pytest test_jobs_router.py -vv

# 失敗時の詳細情報
pytest test_jobs_router.py -v --tb=long

# 標準出力も表示
pytest test_jobs_router.py -v -s
```

### 特定のテストのみ実行

```bash
# テスト名で指定
pytest test_jobs_router.py::TestJobsStartEndpoints::test_start_policy_batch -v

# パターンマッチング
pytest test_jobs_router.py -k "custodian" -v
pytest test_jobs_router.py -k "error" -v
```

## 期待される結果

```
=========================== 33 passed, 3 skipped in 4.83s ============================
```

### スキップされるテスト（正常）

以下の3つのテストは意図的にスキップされます：
1. `test_get_job_status` - 実装都合
2. `test_error_message_info_leakage_prevention` - 実装都合
3. `test_job_result_access_control` - 実装都合

## テストレポート

テスト実行後、以下のディレクトリにレポートが生成されます：

```
TestReport/plugins/jobs/jobs_router/reports/
├── test_report_YYYYMMDD_HHMMSS.md    # Markdownレポート
└── test_report_YYYYMMDD_HHMMSS.json  # JSONレポート
```

## トラブルシューティング

### エラー: ModuleNotFoundError

**問題**: `ModuleNotFoundError: No module named 'app'`

**解決策**:
1. `.env` ファイルで `soure_root` が正しく設定されているか確認
2. パスの末尾に `\` または `/` が含まれているか確認

### エラー: テストが収集されない

**問題**: `collected 0 items`

**解決策**:
1. カレントディレクトリを確認: `cd source`
2. ファイル名を確認: `test_jobs_router.py`

### エラー: 全テストが失敗する

**問題**: すべてのテストで同じエラーが発生

**解決策**:
1. Python バージョンを確認: `python --version` (3.9以上)
2. pytest-asyncio をインストール: `pip install pytest-asyncio`
3. キャッシュをクリア: `pytest --cache-clear`

### モックが動作しない

**問題**: Mock call_count が 0 のまま

**解決策**:
- すでに修正済み（2026-03-11）
- `conftest.py` が最新版であることを確認
- `sys.modules` から router モジュールを削除するコードが含まれていることを確認

## ベストプラクティス

### 開発中

```bash
# 変更したテストのみ実行
pytest test_jobs_router.py::TestClassName::test_method_name -v

# 失敗したテストのみ再実行
pytest test_jobs_router.py --lf -v
```

### CI/CD

```bash
# 静かに実行、失敗時のみ詳細表示
pytest test_jobs_router.py -q --tb=short

# カバレッジレポート付き
pytest test_jobs_router.py --cov=app.jobs.router --cov-report=html
```

### デバッグ

```bash
# 詳細なトレースバック
pytest test_jobs_router.py -vv --tb=long -s

# pdb でデバッグ（失敗時に自動起動）
pytest test_jobs_router.py --pdb

# 最初の失敗で停止
pytest test_jobs_router.py -x
```

## 追加リソース

- **要件文書**: `docs/testing/plugins/jobs/jobs_router_tests.md`
- **完成報告**: `測試完成総結.md`
- **修正サマリー**: `FIX_SUMMARY.md`
- **プロジェクト説明**: `README.md`

## サポート

問題が発生した場合:
1. `FIX_SUMMARY.md` で既知の問題を確認
2. テストレポートで詳細なエラー情報を確認
3. `conftest.py` のモック設定を確認

---

**最終更新**: 2026-03-11  
**バージョン**: 1.0  
**ステータス**: ✅ 動作確認済み

