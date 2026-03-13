# {モジュール名} テストケース

## 1. 概要

{モジュールの役割と主要機能の説明（1-2文）}

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `{関数/クラス名}` | {機能の説明} |
| `{関数/クラス名}` | {機能の説明} |

### 1.2 カバレッジ目標: {80-95}%

> **注記**: {カバレッジ目標の根拠や、実装の特記事項があれば記載}

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/{module_path}.py` |
| テストコード | `test/unit/{module_path}/test_{module}.py` |

### 1.4 補足情報（任意）

{グローバル変数一覧、主要分岐の説明など、テスト設計に影響する実装詳細を記載}

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| {PREFIX}-001 | {テスト概要} | {入力条件} | {期待される結果} |
| {PREFIX}-002 | {テスト概要} | {入力条件} | {期待される結果} |

### 2.1 {テストグループ名} テスト

```python
# test/unit/{module_path}/test_{module}.py
import pytest
import os
from unittest.mock import patch, MagicMock


class Test{テストグループ名}:
    """{テストグループの説明}"""

    def test_{テスト内容}(self):
        """{PREFIX}-001: {テスト概要}"""
        # Arrange
        # {テストの前提条件を準備}

        # Act
        # {テスト対象の操作を実行}

        # Assert
        # {結果を検証}
        assert result == expected
```

### 2.2 {テストグループ名} テスト

```python
class Test{テストグループ名}:
    """{テストグループの説明}"""

    # 必要に応じてフィクスチャを定義
    @pytest.fixture
    def {フィクスチャ名}(self):
        """{フィクスチャの説明}"""
        # セットアップ処理
        return test_data

    def test_{テスト内容}(self, {フィクスチャ名}):
        """{PREFIX}-002: {テスト概要}"""
        # Arrange
        # Act
        # Assert
        pass
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| {PREFIX}-E01 | {異常テスト概要} | {異常入力} | {期待される例外/エラー} |
| {PREFIX}-E02 | {異常テスト概要} | {異常入力} | {期待される例外/エラー} |

### 3.1 {テストグループ名} 異常系

```python
class Test{テストグループ名}Errors:
    """{テストグループ}エラーテスト"""

    def test_{異常テスト内容}(self):
        """{PREFIX}-E01: {異常テスト概要}"""
        # Arrange
        # {異常な前提条件を準備}

        # Act & Assert
        with pytest.raises({ExpectedException}, match="{エラーメッセージパターン}"):
            # {テスト対象の操作を実行}
            pass

    def test_{異常テスト内容}(self):
        """{PREFIX}-E02: {異常テスト概要}

        {実装コード上のどの分岐をカバーするか記載}
        例: module.py:XX の条件分岐をカバーする。
        """
        # Arrange
        # Act
        # Assert
        pass
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| {PREFIX}-SEC-01 | {セキュリティテスト概要} | {入力条件} | {期待結果} |
| {PREFIX}-SEC-02 | {セキュリティテスト概要} | {入力条件} | {期待結果} |

```python
@pytest.mark.security
class Test{モジュール名}Security:
    """{モジュール名}セキュリティテスト"""

    def test_{セキュリティテスト内容}(self):
        """{PREFIX}-SEC-01: {セキュリティテスト概要}

        {セキュリティ上の懸念と検証目的を記載}
        """
        # Arrange
        # Act
        # Assert
        pass

    def test_{セキュリティテスト内容}(self):
        """{PREFIX}-SEC-02: {セキュリティテスト概要}

        {現在の実装で失敗する場合は以下の形式で明示}
        【実装失敗予定】{ファイル名}:{行番号} で {問題の説明}
        """
        # Arrange
        # Act
        # Assert
        pass
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_{module}_module` | テスト間のモジュール状態リセット | function | Yes |
| `{フィクスチャ名}` | {用途} | function | No |

### 共通フィクスチャ定義

```python
# test/unit/{module_path}/conftest.py に追加
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# テスト用定数（config.pyバリデーション通過に必要な最小環境変数セット）
REQUIRED_ENV_VARS = {
    "GPT5_1_CHAT_API_KEY": "test-key",
    "GPT5_1_CODEX_API_KEY": "test-key",
    "GPT5_2_API_KEY": "test-key",
    "GPT5_MINI_API_KEY": "test-key",
    "GPT5_NANO_API_KEY": "test-key",
    "CLAUDE_HAIKU_4_5_KEY": "test-key",
    "CLAUDE_SONNET_4_5_KEY": "test-key",
    "GEMINI_API": "test-key",
    "DOCKER_BASE_URL": "http://localhost:11434",
    "EMBEDDING_3_LARGE_API_KEY": "test-embedding-key",
    "OPENSEARCH_URL": "https://localhost:9200",
}


@pytest.fixture(autouse=True)
def reset_{module}_module():
    """テストごとにモジュールのグローバル状態をリセット

    {モジュール固有のリセット理由を記載}
    """
    yield
    # テスト後にクリーンアップ
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def mock_{依存サービス名}():
    """{依存サービス}モック（外部接続防止）"""
    with patch("app.{module_path}.{DependencyClass}") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance
```

---

## 6. テスト実行例

```bash
# {モジュール}関連テストのみ実行
pytest test/unit/{module_path}/test_{module}.py -v

# 特定のテストクラスのみ実行
pytest test/unit/{module_path}/test_{module}.py::Test{ClassName} -v

# カバレッジ付きで実行
pytest test/unit/{module_path}/test_{module}.py --cov=app.{module_path} --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/{module_path}/test_{module}.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | {N} | {PREFIX}-001 〜 {PREFIX}-{N} |
| 異常系 | {M} | {PREFIX}-E01 〜 {PREFIX}-E{M} |
| セキュリティ | {S} | {PREFIX}-SEC-01 〜 {PREFIX}-SEC-{S} |
| **合計** | **{N+M+S}** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `Test{ClassName}` | {PREFIX}-001〜{PREFIX}-00X | X |
| `Test{ClassName}Errors` | {PREFIX}-E01〜{PREFIX}-E0Y | Y |
| `Test{ClassName}Security` | {PREFIX}-SEC-01〜{PREFIX}-SEC-0Z | Z |

### 実装失敗が予想されるテスト

以下のテストは現在の実装では**意図的に失敗**します。実装側の修正が必要です。

| テストID | 失敗理由 | 修正方針 |
|---------|---------|---------|
| {PREFIX}-{ID} | {失敗する理由}（`{file}:{line}`） | {修正方針} |

> 失敗予定テストがない場合は「現時点で失敗が予想されるテストはありません。」と記載

### 注意事項

- テスト実行に必要な追加パッケージ（例: `pytest-asyncio`）
- `@pytest.mark.security` マーカーの登録要否
- 環境変数パッチのタイミング（`import` 前に適用が必要な場合）

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | {制限事項の説明} | {テストへの影響} | {対応策} |
| 2 | {制限事項の説明} | {テストへの影響} | {対応策} |

---

## テンプレート使用ガイド

### プレースホルダー一覧

| プレースホルダー | 説明 | 例 |
|----------------|------|-----|
| `{モジュール名}` | テスト対象モジュールの表示名 | `crypto`, `config`, `clients` |
| `{module_path}` | Pythonモジュールパス | `core/crypto`, `core/config` |
| `{module}` | ファイル名（拡張子なし） | `crypto`, `config` |
| `{PREFIX}` | テストID接頭辞（大文字3-6文字） | `CRYPTO`, `CFG`, `CLI` |
| `{N}`, `{M}`, `{S}` | 正常系/異常系/セキュリティの件数 | `10`, `13`, `6` |

### テストID命名規則

| カテゴリ | 形式 | 例 |
|---------|------|-----|
| 正常系 | `{PREFIX}-001` 〜 | `CRYPTO-001`, `CFG-001` |
| 異常系 | `{PREFIX}-E01` 〜 | `CRYPTO-E01`, `CFG-E01` |
| セキュリティ | `{PREFIX}-SEC-01` 〜 | `CRYPTO-SEC-01`, `CFG-SEC-01` |

### テストコード記述規則

1. **Arrange/Act/Assert パターン**を必ず使用し、コメントで明示する
2. **docstring** に テストID + テスト概要 を記載する
3. **分岐カバレッジ**の対象行を docstring に記載する（特に異常系・セキュリティ）
4. **実装失敗予定**のテストは docstring に `【実装失敗予定】` を明記する
5. **フィクスチャ** は外部接続を防止し、テスト間の独立性を保証する

### 作成フロー

1. テスト対象の実装ファイルを読み込み、全関数・全分岐を洗い出す
2. 本テンプレートをコピーし、プレースホルダーを埋める
3. 正常系 → 異常系 → セキュリティの順にテストケースを設計する
4. MCPツールで診断チェック（マークダウン構文エラーなし確認）
5. code-reviewer + Codex でレビュー
6. レビュー指摘を反映してコミット
