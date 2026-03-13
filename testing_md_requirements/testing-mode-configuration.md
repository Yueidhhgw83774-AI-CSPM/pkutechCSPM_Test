# テストモード設定ガイド（TESTING_MODE）

## 1. 概要

本ドキュメントでは、`TESTING_MODE`環境変数によるAPIキーバリデーションスキップ機能について説明します。

### 1.1 背景と目的

FastAPIバックエンドは多数のAPIキー（LLM、OpenSearch等）を必須としているため、APIキーが未設定の環境では`app/core/config.py`のインポート時点で`SystemExit`が発生し、単体テストの実行が困難でした。

この問題を解決するため、`TESTING_MODE`環境変数を導入し、テスト実行時にAPIキーバリデーションをスキップできるようにしました。

### 1.2 必須フィールド一覧（本番モードで必須）

| カテゴリ | フィールド名 | 用途 |
|---------|-------------|------|
| LLM APIキー | `GPT5_1_CHAT_API_KEY` | GPT-5.1 Chat用 |
| | `GPT5_1_CODEX_API_KEY` | GPT-5.1 Codex用 |
| | `GPT5_2_API_KEY` | GPT-5.2用 |
| | `GPT5_MINI_API_KEY` | GPT-5 Mini用 |
| | `GPT5_NANO_API_KEY` | GPT-5 Nano用 |
| | `CLAUDE_HAIKU_4_5_KEY` | Claude 4.5 Haiku用 |
| | `CLAUDE_SONNET_4_5_KEY` | Claude 4.5 Sonnet用 |
| | `GEMINI_API_KEY` | Google Gemini用 |
| インフラ | `DOCKER_BASE_URL` | LLMプロキシURL |
| | `EMBEDDING_API_KEY` | Embedding API用 |
| | `OPENSEARCH_URL` | OpenSearch接続URL |

## 2. 動作仕様

### 2.1 環境別動作

| 環境 | TESTING_MODE | 動作 |
|-----|-------------|------|
| **本番** | `false`（未設定） | 必須フィールド未設定時にエラー終了 |
| **テスト** | `true` | 必須フィールドのバリデーションをスキップ |

### 2.2 バリデーションフロー

```
Settings()インスタンス化
    ↓
@model_validator(mode='after')実行
    ↓
TESTING_MODE判定
    ├── true → バリデーションスキップ、正常終了
    └── false → 必須フィールドチェック
                    ├── 全て設定済み → 正常終了
                    └── 未設定あり → ValueError発生 → SystemExit
```

## 3. 使用方法

### 3.1 pytestでのテスト実行（推奨）

`test/conftest.py`が自動的に`TESTING_MODE=true`を設定するため、特別な設定なしでテスト実行可能です。

```bash
# 全テスト実行
pytest test/

# ユニットテストのみ
pytest test/unit/

# 特定のテストファイル
pytest test/unit/test_checkpointer.py -v
```

### 3.2 手動での設定

pytestを使わずにテストスクリプトを実行する場合は、環境変数を明示的に設定します。

```bash
# シェルで設定
export TESTING_MODE=true
python -c "from app.core.config import settings; print(settings.TESTING_MODE)"
# → True

# ワンライナー
TESTING_MODE=true python your_test_script.py
```

### 3.3 Pythonコード内での設定

```python
import os

# app.core.configをインポートする前に設定
os.environ['TESTING_MODE'] = 'true'

# これでエラーなくインポート可能
from app.core.config import settings

print(settings.TESTING_MODE)  # True
print(settings.GPT5_1_CHAT_API_KEY)  # '' (空文字、エラーにならない)
```

## 4. 実装詳細

### 4.1 `app/core/config.py`の変更点

```python
from pydantic import Field, model_validator

class Settings(BaseSettings):
    # テストモードフラグ
    TESTING_MODE: bool = Field(False, validation_alias='TESTING_MODE')

    # 必須フィールド → デフォルト空文字に変更
    GPT5_1_CHAT_API_KEY: str = Field(default="", validation_alias='GPT5_1_CHAT_API_KEY')
    # ... 他の必須フィールドも同様

    @model_validator(mode='after')
    def validate_required_fields_in_production(self) -> 'Settings':
        """本番モード時に必須フィールドが設定されているか検証"""
        if self.TESTING_MODE:
            return self  # テストモードではスキップ

        required_fields = {...}
        missing = [name for name, value in required_fields.items() if not value]
        if missing:
            raise ValueError(f"本番モードで必須の環境変数が未設定です: {missing}")
        return self
```

### 4.2 `test/conftest.py`

```python
import os

# インポート前に環境変数を設定
os.environ.setdefault('TESTING_MODE', 'true')

import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """テスト環境の共通セットアップ"""
    os.environ['TESTING_MODE'] = 'true'
    yield
```

## 5. 注意事項

### 5.1 テストコードでの考慮事項

`TESTING_MODE=true`の状態では、APIキーが空文字になります。LLM呼び出しを行うテストでは、適切にモックを使用してください。

```python
from unittest.mock import patch, MagicMock

def test_with_llm_mock():
    """LLM呼び出しをモックしたテスト"""
    with patch('app.core.llm_factory.get_llm') as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = "mocked response"
        mock_get_llm.return_value = mock_llm

        # テスト実行
        result = some_function_using_llm()
        assert result == "expected"
```

### 5.2 本番環境での確認

本番環境では`TESTING_MODE`を設定しないでください。設定した場合、APIキーバリデーションがスキップされ、実行時にエラーが発生する可能性があります。

```bash
# 本番環境確認（TESTING_MODE未設定で実行）
python -c "from app.core.config import settings"
# APIキー未設定の場合 → ValueError: 本番モードで必須の環境変数が未設定です...
```

### 5.3 CI/CD環境での設定

GitHub ActionsなどのCI/CD環境でテストを実行する場合は、環境変数として`TESTING_MODE=true`を設定してください。

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      TESTING_MODE: 'true'
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest test/ -v
```

## 6. トラブルシューティング

### 6.1 よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| `SystemExit: Configuration error` | TESTING_MODEが設定されていない | `export TESTING_MODE=true`を実行 |
| テストでLLM呼び出しが失敗 | APIキーが空文字 | モックを使用するか、テスト用APIキーを設定 |
| conftest.pyが読み込まれない | pytestではなくpythonで直接実行 | 手動で環境変数を設定 |

### 6.2 デバッグ方法

```bash
# 現在の設定を確認
TESTING_MODE=true python -c "
from app.core.config import settings
print('TESTING_MODE:', settings.TESTING_MODE)
print('GPT5_1_CHAT_API_KEY:', repr(settings.GPT5_1_CHAT_API_KEY))
print('OPENSEARCH_URL:', repr(settings.OPENSEARCH_URL))
"
```

## 7. 関連ドキュメント

- [テスト環境設定](./03_test_environment.md) - テスト環境の全般的なセットアップ
- [conftest設計](./04_conftest_design.md) - pytestフィクスチャの設計方針
- [モック戦略](./06_mock_strategy.md) - 外部依存のモック方法
