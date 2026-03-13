# AI-CSPM テストプロジェクト

## 概要

このディレクトリは、AI-CSPM プラットフォームの包括的なテストスイートです。pytest フレームワークを使用して、プラットフォームのすべての主要コンポーネント（コア機能、モデル、プラグイン）の単体テスト、統合テスト、セキュリティテストを実行します。

## プロジェクト構成

```
TestReport/
├── core/                    # コアモジュールのテスト
│   ├── auth_utils/         # 認証ユーティリティ
│   ├── categories/         # カテゴリ管理
│   ├── checkpointer/       # チェックポイント機能
│   ├── clients/            # クライアント接続
│   ├── config/             # 設定管理
│   ├── crypto/             # 暗号化機能
│   ├── encryption_middleware/  # 暗号化ミドルウェア
│   ├── error_handlers/     # エラーハンドラー
│   ├── health_checker/     # ヘルスチェック
│   ├── llm_factory/        # LLM ファクトリー
│   ├── permission_checker/ # 権限チェック
│   ├── rag_manager/        # RAG マネージャー
│   └── role_based_client/  # ロールベースクライアント
│
├── models/                  # データモデルのテスト
│   ├── api/                # API モデル
│   └── mcp_models/         # MCP モデル
│
├── plugins/                 # プラグインのテスト
│   ├── auth/               # 認証プラグイン
│   ├── aws/                # AWS プラグイン
│   ├── chat_dashboard/     # チャットダッシュボード
│   ├── cspm/               # CSPM プラグイン
│   ├── custodian_scan/     # Custodian スキャン
│   ├── doc_reader/         # ドキュメントリーダー
│   ├── jobs/               # ジョブ管理
│   ├── mcp/                # MCP プラグイン
│   ├── rag/                # RAG プラグイン
│   └── report/             # レポート生成
│
├── testing_md_requirements/ # テスト要件ドキュメント
├── temp/                    # 一時ファイル
├── .env                     # 環境変数設定
├── conftest.py             # pytest ルート設定
├── env_loader.py           # 環境変数ローダー
├── pytest.ini              # pytest 設定ファイル
    # テスト統計更新スクリプト
```

## 環境設定

### 前提条件

- Python 3.9 以上
- pytest 7.0 以上
- pytest-asyncio
- その他の依存関係については `platform_python_backend-testing/pyproject.toml` を参照

### .env ファイルの設定

プロジェクトルート（TestReport/）に `.env` ファイルを作成し、以下の変数を設定してください：

```bash
# ソースコードのルートパス（必須）
SourceCodeRoot="C:/pythonProject/python_ai_cspm/platform_python_backend-testing"

# OpenSearch 設定（オプション - 統合テスト用）
OPENSEARCH_URL="https://localhost:9200"
OPENSEARCH_USER="admin"
OPENSEARCH_PASSWORD="your-password"
OPENSEARCH_CA_CERTS_PATH="/path/to/ca-cert.pem"

# その他の環境変数
# 各テストモジュールの要件に応じて追加
```

### 環境変数の動作原理

1. **自動検出**: `conftest.py` がプロジェクトルートの `.env` ファイルを自動的に読み込みます
2. **sys.path への追加**: `SourceCodeRoot` が Python のモジュール検索パスに追加されます
3. **os.environ への設定**: すべての環境変数が `os.environ` に設定され、テストコードから参照可能になります

## テストの実行

### 基本的な実行方法

```powershell
# すべてのテストを実行
cd C:\pythonProject\python_ai_cspm\TestReport
pytest

# 特定のディレクトリのテストを実行
pytest core/                 # コアモジュールのテスト
pytest models/               # モデルのテスト
pytest plugins/              # プラグインのテスト

# 特定のモジュールのテストを実行
pytest core/config/          # 設定モジュールのテスト
pytest plugins/cspm/         # CSPM プラグインのテスト

# 特定のテストファイルを実行
pytest plugins/cspm/cspm_tools/source/test_cspm_tools.py

# 特定のテストクラスまたは関数を実行
pytest plugins/auth/source/test_auth.py::TestAuthEndpoints
pytest plugins/auth/source/test_auth.py::TestAuthEndpoints::test_login_success
```

### 詳細オプション

```powershell
# 詳細な出力を表示
pytest -v

# 非常に詳細な出力を表示
pytest -vv

# 失敗したテストのみ再実行
pytest --lf

# キーワードでテストをフィルタリング
pytest -k "test_login"
pytest -k "Security"

# マーカーでテストをフィルタリング
pytest -m security          # セキュリティテストのみ
pytest -m "not slow"        # 遅いテストを除外

# カバレッジレポートを生成
pytest --cov=app --cov-report=html

# 並列実行（pytest-xdist が必要）
pytest -n auto              # CPU コア数に応じて自動調整
pytest -n 4                 # 4 プロセスで実行

# 特定のエラーで停止
pytest -x                   # 最初の失敗で停止
pytest --maxfail=3          # 3 回失敗したら停止

# テストの詳細なトレースバック
pytest --tb=short           # 短いトレースバック
pytest --tb=long            # 長いトレースバック
pytest --tb=no              # トレースバックなし
```

### 非同期テストの実行

このプロジェクトでは多くの非同期テストが含まれています。pytest-asyncio が自動的に処理しますが、`pytest.ini` で設定されています：

```ini
asyncio_mode = auto
```

## テストの記述ガイドライン

### ファイル命名規則

- テストファイル: `test_*.py`
- テストクラス: `Test*`
- テスト関数: `test_*`

### テストの構造例

```python
# -*- coding: utf-8 -*-
"""
モジュールの説明
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock


@pytest.fixture
def sample_fixture():
    """フィクスチャの説明"""
    return {"key": "value"}


class TestModuleName:
    """モジュール名のテストクラス"""
    
    def test_basic_functionality(self, sample_fixture):
        """基本機能のテスト"""
        assert sample_fixture["key"] == "value"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """非同期機能のテスト"""
        result = await some_async_function()
        assert result is not None
    
    @pytest.mark.security
    def test_security_feature(self):
        """セキュリティ機能のテスト"""
        # セキュリティ関連のテスト
        pass


class TestModuleNameErrors:
    """エラーケースのテストクラス"""
    
    def test_error_handling(self):
        """エラーハンドリングのテスト"""
        with pytest.raises(ValueError):
            some_function_that_raises()
```

### 共通のフィクスチャ

各テストディレクトリの `conftest.py` には共通のフィクスチャが定義されています：

- `mock_opensearch_client`: OpenSearch クライアントのモック
- `mock_settings`: 設定のモック
- `mock_subprocess_success`: subprocess の成功モック
- `mock_rag_system_success`: RAG システムのモック
- その他、モジュール固有のフィクスチャ

## テストカテゴリ

### 1. 単体テスト (Unit Tests)
個々の関数やメソッドの動作を検証します。

### 2. 統合テスト (Integration Tests)
複数のコンポーネントの連携を検証します。

### 3. セキュリティテスト (Security Tests)
`@pytest.mark.security` マーカーが付いたテストで、以下を検証します：
- 認証・認可
- SQL/コマンドインジェクション防止
- XSS 防止
- データサニタイゼーション
- パストラバーサル防止

### 4. エラーハンドリングテスト
異常系の動作を検証します：
- 無効な入力
- タイムアウト
- ネットワークエラー
- リソース不足

## レポート生成

各テストディレクトリには独自のレポート生成機能があります。テスト実行後、以下の場所にレポートが生成されます：

```
TestReport/
├── core/[module]/reports/
│   ├── TestReport_[module].md
│   └── TestReport_[module].json
├── models/[module]/reports/
│   ├── TestReport_[module].md
│   └── TestReport_[module].json
└── plugins/[plugin]/reports/
    ├── TestReport_[plugin].md
    └── TestReport_[plugin].json
```

## トラブルシューティング

### よくある問題

#### 1. ModuleNotFoundError: No module named 'app'

**原因**: `SourceCodeRoot` が正しく設定されていない

**解決方法**:
- `.env` ファイルが TestReport/ ルートに存在するか確認
- `SourceCodeRoot` のパスが正しいか確認
- パスの区切り文字が正しいか確認（Windows: `/` または `\\`）

#### 2. OpenSearch 接続エラー

**原因**: OpenSearch サーバーが起動していない、または設定が間違っている

**解決方法**:
- OpenSearch サーバーが起動しているか確認
- `.env` の OpenSearch 設定を確認
- ネットワーク接続を確認
- 証明書のパスが正しいか確認

#### 3. AsyncIO 関連のエラー

**原因**: 非同期テストの設定が不適切

**解決方法**:
- `pytest.ini` に `asyncio_mode = auto` が設定されているか確認
- テスト関数に `@pytest.mark.asyncio` デコレータが付いているか確認
- pytest-asyncio がインストールされているか確認

#### 4. フィクスチャが見つからない

**原因**: conftest.py が正しく読み込まれていない

**解決方法**:
- テストファイルと同じディレクトリまたは親ディレクトリに conftest.py があるか確認
- pytest を TestReport/ ディレクトリから実行しているか確認

## CI/CD との統合

### GitHub Actions の例

```yaml
name: Tests

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
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Configure environment
        run: |
          echo "SourceCodeRoot=${{ github.workspace }}/platform_python_backend-testing" > TestReport/.env
      
      - name: Run tests
        run: |
          cd TestReport
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## テスト統計

テストプロジェクトの統計を更新するには：

```powershell
python test_stats_update.py
```

このスクリプトは、すべてのテストファイルをスキャンし、統計情報を更新します。

## 開発ガイドライン

### 新しいテストの追加

1. **適切なディレクトリを選択**: core/、models/、または plugins/
2. **テストファイルを作成**: `test_[module_name].py`
3. **conftest.py を更新**: 必要に応じて共通フィクスチャを追加
4. **テストを実装**: 命名規則とガイドラインに従う
5. **ドキュメント更新**: testing_md_requirements/ 内の関連ドキュメントを更新

### コードレビューのチェックリスト

- [ ] テストが明確で理解しやすい
- [ ] エッジケースがカバーされている
- [ ] エラーハンドリングがテストされている
- [ ] 非同期コードに適切な `@pytest.mark.asyncio` が付いている
- [ ] モックが適切に使用されている
- [ ] テストが独立している（他のテストに依存していない）
- [ ] ドキュメントが更新されている

## 参考資料

### 公式ドキュメント

- [pytest 公式ドキュメント](https://docs.pytest.org/)
- [pytest-asyncio ドキュメント](https://pytest-asyncio.readthedocs.io/)

### プロジェクト固有のドキュメント

- `testing_md_requirements/`: 各モジュールの詳細なテスト要件
- `CLAUDE.md`: プロジェクト全体のドキュメント（親ディレクトリ）
- 各モジュールの `README.md`: モジュール固有のドキュメント

## ライセンス

このテストプロジェクトは AI-CSPM プラットフォームの一部です。詳細については親ディレクトリの LICENSE.md を参照してください。

## 貢献

バグ報告、機能リクエスト、プルリクエストを歓迎します。貢献する前に、コーディング規約とテストガイドラインを確認してください。

## サポート

問題が発生した場合：
1. このドキュメントのトラブルシューティングセクションを確認
2. 既存の Issue を検索
3. 新しい Issue を作成（問題の詳細、環境情報、再現手順を含める）

---

**最終更新**: 2026年3月12日
**バージョン**: 1.0.0
**メンテナー**: AI-CSPM Development Team
