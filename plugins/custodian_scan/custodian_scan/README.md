# Custodian Scan テストスイート

Cloud Custodianスキャン機能の包括的なテストスイート

## 📋 概要

このテストスイートは、Cloud Custodian スキャン機能の品質を保証するために設計されています。AWS/Azureのクラウドリソースをポリシーベースでスキャンし、セキュリティ違反を検出する重要機能をカバーします。

### 主要機能

| 機能 | エンドポイント | 説明 |
|------|---------------|------|
| スキャン開始（旧） | POST /api/custodian/start_custodian_scan_async | 従来形式のスキャン実行 |
| コマンドプレビュー | POST /api/custodian/preview_custodian_command | 実行コマンドの事前確認 |
| ジョブステータス | GET /api/custodian/jobs/{job_id}/status | ジョブ状態取得 |
| ジョブ結果 | GET /api/custodian/jobs/{job_id}/result | スキャン結果取得 |
| 新スキャン開始 | POST /api/jobs/new_start_custodian_scan_async | 新形式のマルチリージョンスキャン |

## 📊 テスト統計

| カテゴリ | テスト数 | ID範囲 | 説明 |
|---------|---------|--------|------|
| **正常系** | 7 | SCAN-001 ~ SCAN-007 | 基本機能の正常動作 |
| **異常系** | 10 | SCAN-E01 ~ SCAN-E10 | エラーハンドリング |
| **バリデーション** | 10 | SCAN-VAL-001 ~ SCAN-VAL-010 | 入力検証ロジック |
| **タスク実行** | 10 | SCAN-TASK-001 ~ SCAN-TASK-010 | バックグラウンド処理 |
| **新スキャン** | 7 | NSCAN-001 ~ NSCAN-007 | 新アーキテクチャ |
| **セキュリティ** | 14 | SCAN-SEC-001 ~ SCAN-SEC-008 | セキュリティ対策 |
| **合計** | **58** | - | - |

### カバレッジ目標

- **ターゲット**: 80%以上
- **理由**: セキュリティ重要機能を含むため高い目標を設定

## 🚀 クイックスタート

### 前提条件

```bash
# Python 3.9以上
python --version

# 必要なパッケージ
pip install pytest pytest-asyncio httpx fastapi python-dotenv
```

### 環境設定

`.env` ファイルを `TestReport/` ディレクトリに作成：

```env
soure_root=C:\pythonProject\python_ai_cspm\platform_python_backend-testing\
```

### テスト実行

```bash
# カレントディレクトリを移動
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\custodian_scan\custodian_scan

# 全テスト実行
pytest source/test_custodian_scan.py -v

# カテゴリ別実行
pytest source/test_custodian_scan.py::TestCustodianScanNormalCases -v
pytest source/test_custodian_scan.py::TestCustodianScanErrorCases -v
pytest source/test_custodian_scan.py::TestCustodianScanSecurity -v

# 詳細出力
pytest source/test_custodian_scan.py -vv -s

# カバレッジレポート付き
pytest source/test_custodian_scan.py --cov=app.custodian_scan --cov-report=html
```

## 📁 ディレクトリ構造

```
TestReport/plugins/custodian_scan/custodian_scan/
├── source/
│   ├── conftest.py              # フィクスチャとモック設定
│   └── test_custodian_scan.py   # メインテストスイート
├── reports/                      # テストレポート出力先
│   ├── test_report_*.md
│   └── test_report_*.json
├── pytest.ini                    # pytest設定
├── README.md                     # このファイル
└── 測試完成総結.md               # 完成報告
```

## 🔧 テストアーキテクチャ

### モック戦略

このテストスイートは **Jobs Router の成功パターン** を適用しています：

1. **ルーターモジュールの強制リロード**
   - `sys.modules` からルーターを削除
   - 各テスト実行前に新しくインポート

2. **直接ネームスペース代入**
   - モジュールの関数参照に直接モックを代入
   - `patch()` デコレータではなく直接代入で確実に適用

3. **明示的な依存関係**
   - フィクスチャの依存関係を明確に定義
   - `autouse=True` を避ける

4. **完全な隔離とクリーンアップ**
   - 各テスト後に状態をリセット
   - テスト間の影響を排除

### フィクスチャ一覧

#### 認証関連
- `mock_jwt_auth`: JWT認証モック
- `mock_crypto`: 暗号化関数モック
- `authenticated_client`: 認証済みHTTPクライアント

#### タスク関連
- `mock_status_manager`: ジョブステータス管理モック
- `mock_custodian_tasks`: Custodianタスクモック
- `mock_opensearch`: OpenSearchクライアントモック

#### テストデータ
- `valid_policy_yaml`: 有効なポリシーYAML
- `valid_aws_credentials`: AWS認証情報
- `valid_azure_credentials`: Azure認証情報
- `assume_role_credentials`: AssumeRole認証情報
- その他多数のテストデータフィクスチャ

## 📝 テストケース詳細

### 正常系テスト (7 tests)

| ID | テスト名 | 検証内容 |
|----|---------|---------|
| SCAN-001 | スキャン開始成功 | POST /api/custodian/start_custodian_scan_async |
| SCAN-002 | コマンドプレビュー成功 | preview_custodian_command の動作 |
| SCAN-003 | ジョブステータス取得 | GET /api/custodian/jobs/{id}/status |
| SCAN-004 | 新スキャン開始成功 | NewCredentials形式でのスキャン |
| SCAN-005 | マルチリージョンスキャン | 複数リージョンの同時スキャン |
| SCAN-006 | 違反のOpenSearch保存 | 違反データの永続化 |
| SCAN-007 | 違反なし時の正常完了 | no_violations_detected: true |

### 異常系テスト (10 tests)

| ID | テスト名 | 期待エラー |
|----|---------|-----------|
| SCAN-E01 | 空のポリシーYAML | ValidationError |
| SCAN-E02 | 無効なYAML形式 | ValidationError |
| SCAN-E03 | 認証情報なし | ValidationError |
| SCAN-E04 | 無効なクラウドプロバイダー | ValidationError |
| SCAN-E05 | 無効なAWSアクセスキー形式 | ValidationError |
| SCAN-E06 | 無効なAzure GUID形式 | ValidationError |
| SCAN-E07 | 危険なキーワード | ValidationError |
| SCAN-E08 | ポリシーサイズ超過 | ValidationError |
| SCAN-E09 | 無効なリージョン形式 | ValidationError |
| SCAN-E10 | Custodian実行タイムアウト | ProcessingError |

### バリデーションテスト (10 tests)

入力検証ロジックの単体テスト：

- YAML構文検証
- policiesキー存在確認
- 必須フィールド検証
- 危険キーワード検出
- AWS/Azure認証情報形式検証
- リージョン形式検証

### タスク実行テスト (10 tests)

バックグラウンドタスクの動作検証：

- タスク初期化
- 環境変数設定
- Custodianコマンド実行
- 違反カウント
- OpenSearch保存
- 履歴インデックス更新
- 暗号化認証情報復号化
- タイムアウト処理

### 新スキャンタスクテスト (7 tests)

新アーキテクチャのコンポーネントテスト：

- CredentialProcessor
- ScanCoordinator
- ResultProcessor
- ErrorHistoryHandler
- AssumeRole認証
- アクセスキー認証
- プリセット情報保存

### セキュリティテスト (14 tests)

セキュリティ対策の検証：

- **SCAN-SEC-001**: パストラバーサル防止
- **SCAN-SEC-002**: 環境変数サニタイズ、コマンドインジェクション防止
- **SCAN-SEC-003**: コマンドパス検証
- **SCAN-SEC-004**: 認証情報マスキング、内部IPマスキング
- **SCAN-SEC-005**: YAMLインジェクション防止
- **SCAN-SEC-006**: ReDoS攻撃防止（入力/出力長制限）
- **SCAN-SEC-007**: 大容量ファイルDoS防止、パストラバーサル防止
- **SCAN-SEC-008**: セキュリティ検証トグル

## 🔍 トラブルシューティング

### エラー: ModuleNotFoundError

**問題**: `ModuleNotFoundError: No module named 'app'`

**解決策**:
1. `.env` ファイルで `soure_root` が正しく設定されているか確認
2. パスの末尾に `\` が含まれているか確認
3. Python パスを確認: `echo $PYTHONPATH`

### エラー: テストがスキップされる

**問題**: 多くのテストが `SKIPPED` になる

**理由**: 一部のテストは統合テスト用に設計されているため、ユニットテストではスキップされます

**対応**: これは正常な動作です。スキップされたテストは統合テスト環境で実行されます

### エラー: モックが動作しない

**問題**: Mock call_count が 0 のまま

**解決策**:
- `conftest.py` が最新版であることを確認
- `sys.modules` から router モジュールを削除するコードが含まれていることを確認
- Jobs Router の成功パターンが適用されていることを確認

## 📈 期待される結果

```bash
======================== test session starts ========================
collected 58 items

test_custodian_scan.py::TestCustodianScanNormalCases::test_scan_001_start_scan_success PASSED [  1%]
test_custodian_scan.py::TestCustodianScanNormalCases::test_scan_002_command_preview_success PASSED [  3%]
...
test_custodian_scan.py::TestCustodianScanSecurity::test_scan_sec_008_security_validation_toggle_disabled PASSED [100%]

=================== 43 passed, 15 skipped in 5.23s ===================
```

**スキップされるテスト**: 約15テスト（統合テストで実施するため）
**実行されるテスト**: 約43テスト

## 🎯 ベストプラクティス

### テスト作成時

1. **明確なテスト名**: `test_scan_001_start_scan_success` のように番号と説明を含める
2. **AAA パターン**: Arrange, Act, Assert を明確に分離
3. **モックの検証**: モックが実際に呼ばれたか確認
4. **エラーケース**: 正常系だけでなく異常系も必ずテスト

### テスト実行時

```bash
# 開発中: 変更したテストのみ
pytest source/test_custodian_scan.py::TestClassName::test_method_name -v

# 失敗したテストのみ再実行
pytest source/test_custodian_scan.py --lf -v

# デバッグモード
pytest source/test_custodian_scan.py -vv --tb=long -s --pdb
```

### CI/CD統合

```yaml
# .github/workflows/test.yml
name: Custodian Scan Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install pytest pytest-asyncio httpx fastapi python-dotenv
      - name: Run tests
        run: |
          cd TestReport/plugins/custodian_scan/custodian_scan
          pytest source/test_custodian_scan.py -v --junitxml=reports/junit.xml
      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: TestReport/plugins/custodian_scan/custodian_scan/reports/
```

## 📚 関連ドキュメント

- **要件文書**: `docs/testing/plugins/custodian_scan/custodian_scan_tests.md`
- **完成報告**: `測試完成総結.md`
- **ソースコード**: 
  - `app/custodian_scan/router.py`
  - `app/jobs/tasks/custodian_scan.py`
  - `app/jobs/tasks/new_custodian_scan/`

## 🤝 貢献

新しいテストケースを追加する場合：

1. 要件文書に新しいテストケースIDを追加
2. `test_custodian_scan.py` に実装
3. 必要に応じて `conftest.py` にフィクスチャを追加
4. README.md を更新

## 📞 サポート

問題が発生した場合：
1. `conftest.py` のモック設定を確認
2. テストレポートで詳細なエラー情報を確認
3. Jobs Router の成功パターンが適用されているか確認

---

**最終更新**: 2026-03-11  
**バージョン**: 1.0  
**ステータス**: ✅ 完成・テスト準備完了  
**基づく成功パターン**: Jobs Router テストスイート

