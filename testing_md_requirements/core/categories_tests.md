# categories テストケース

## 1. 概要

セキュリティカテゴリ定義をJSONファイルから読み込み、LLMプロンプト用の文字列を生成するモジュールのテストケースを定義します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `load_categories(filepath)` | JSONファイルからカテゴリデータを読み込みグローバル変数にキャッシュ |
| `get_available_categories_for_prompt()` | LLMプロンプト用のカテゴリ文字列を取得（未ロード時は自動ロード） |

### 1.2 カバレッジ目標: 60%

> **注記**: 低優先度のシンプルなモジュールであり、主にファイルI/OとJSONパースを行います。
> グローバル変数を使用したキャッシュ機構を持つため、テスト間の独立性確保が重要です。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/core/categories.py` |
| テストコード | `test/unit/core/test_categories.py` |
| カテゴリデータ | `app/categories.json` |

### 1.4 補足情報

**グローバル変数:**

| 変数名 | 型 | 説明 |
|--------|------|------|
| `_categories_data` | `List[Dict[str, str]]` | 読み込んだカテゴリデータのキャッシュ |
| `_categories_for_prompt_str` | `str` | プロンプト用に整形された文字列キャッシュ |
| `DEFAULT_CATEGORIES_FILE_PATH` | `str` | デフォルトのJSONファイルパス（app/categories.json） |

**主要分岐:**

| 行番号 | 条件 | 分岐内容 |
|--------|------|----------|
| 21-38 | ファイル読み込み成功 | カテゴリデータをパースしプロンプト文字列を生成 |
| 32 | `if name:` | nameが存在するカテゴリのみ処理 |
| 37-38 | `if not _categories_data:` | 空のカテゴリリスト時のフォールバック文字列 |
| 43-48 | `except FileNotFoundError` | ファイル未発見時のエラー処理 |
| 49-52 | `except json.JSONDecodeError` | JSON構文エラー時のエラー処理 |
| 53-56 | `except Exception` | その他予期せぬエラー時のエラー処理 |
| 61-62 | `if not _categories_for_prompt_str:` | 未ロード時の自動ロード |

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CAT-001 | モジュールインポート成功 | モジュールインポート | 例外なし、関数が存在 |
| CAT-002 | 有効なJSONファイルからカテゴリ読み込み | 有効なJSONファイルパス | カテゴリデータが読み込まれる |
| CAT-003 | プロンプト文字列の正しいフォーマット | 有効なカテゴリデータ | 番号付きリスト形式 |
| CAT-004 | 未ロード時の自動ロード | 初期状態で`get_available_categories_for_prompt()`呼び出し | 自動的にロードされる |
| CAT-005 | キャッシュされたデータの返却 | 2回目の呼び出し | 同一文字列を返却 |
| CAT-006 | 空のカテゴリリスト読み込み | 空のJSON配列 | フォールバック文字列 |
| CAT-007 | descriptionなしカテゴリの処理 | descriptionフィールドなし | 空の説明で処理 |
| CAT-008 | nameなしカテゴリのスキップ | nameフィールドなし | そのカテゴリをスキップ |

### 2.1 モジュールインポートテスト

```python
# test/unit/core/test_categories.py
import pytest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock


class TestCategoriesImport:
    """カテゴリモジュールインポートテスト"""

    def test_import_categories_module(self):
        """CAT-001: モジュールのインポート成功"""
        # Arrange & Act
        from app.core import categories

        # Assert
        # 関数が存在することを確認
        assert hasattr(categories, "load_categories")
        assert hasattr(categories, "get_available_categories_for_prompt")
        # グローバル変数が存在することを確認
        assert hasattr(categories, "_categories_data")
        assert hasattr(categories, "_categories_for_prompt_str")
        assert hasattr(categories, "DEFAULT_CATEGORIES_FILE_PATH")
```

### 2.2 load_categories テスト

```python
class TestLoadCategories:
    """カテゴリ読み込みテスト"""

    @pytest.fixture
    def valid_categories_json(self, tmp_path):
        """有効なカテゴリJSONファイルを作成"""
        categories = [
            {
                "name": "Identity and Access Management",
                "description": "IAM related controls"
            },
            {
                "name": "Data Security",
                "description": "Data protection controls"
            },
            {
                "name": "Network Security",
                "description": "Network related controls"
            }
        ]
        json_file = tmp_path / "categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        return str(json_file)

    def test_load_valid_categories(self, valid_categories_json):
        """CAT-002: 有効なJSONファイルからカテゴリ読み込み成功"""
        # Arrange
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(valid_categories_json)

        # Assert
        assert len(cat_module._categories_data) == 3
        assert cat_module._categories_data[0]["name"] == "Identity and Access Management"
        assert cat_module._categories_for_prompt_str != ""

    def test_prompt_string_format(self, valid_categories_json):
        """CAT-003: プロンプト文字列が番号付きリスト形式で生成される"""
        # Arrange
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(valid_categories_json)

        # Assert
        prompt_str = cat_module._categories_for_prompt_str
        # 番号付きリスト形式の検証
        assert "1. Identity and Access Management" in prompt_str
        assert "2. Data Security" in prompt_str
        assert "3. Network Security" in prompt_str
        # 説明が含まれていることを検証
        assert "(Description:" in prompt_str

    def test_empty_categories_list(self, tmp_path):
        """CAT-006: 空のカテゴリリスト読み込み時のフォールバック

        categories.py:37-38 の分岐をカバーする。
        """
        # Arrange
        json_file = tmp_path / "empty_categories.json"
        json_file.write_text("[]", encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(str(json_file))

        # Assert
        assert cat_module._categories_data == []
        assert "No predefined categories are available" in cat_module._categories_for_prompt_str

    def test_category_without_description(self, tmp_path):
        """CAT-007: descriptionなしカテゴリが空の説明で処理される

        categories.py:31 の `get("description", "")` をカバーする。
        """
        # Arrange
        categories = [{"name": "Test Category"}]  # descriptionなし
        json_file = tmp_path / "no_desc_categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(str(json_file))

        # Assert
        assert len(cat_module._categories_data) == 1
        # 空の説明で処理されていることを確認
        assert "1. Test Category (Description: )" in cat_module._categories_for_prompt_str

    def test_category_without_name_skipped(self, tmp_path):
        """CAT-008: nameなしカテゴリがスキップされる

        categories.py:32 の `if name:` 分岐をカバーする。
        """
        # Arrange
        categories = [
            {"name": "Valid Category", "description": "Has name"},
            {"description": "No name field"},  # nameなし
            {"name": "", "description": "Empty name"},  # 空のname
            {"name": "Another Valid", "description": "Also has name"}
        ]
        json_file = tmp_path / "mixed_categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(str(json_file))

        # Assert
        # プロンプト文字列には有効なカテゴリのみが含まれる
        # 注意: enumerateはリスト全体をカウントするため、nameなしの要素も
        # インデックスに含まれる（ただしプロンプト文字列には出力されない）
        prompt_str = cat_module._categories_for_prompt_str
        assert "1. Valid Category" in prompt_str
        # インデックス2, 3はnameなし/空nameのためスキップされ、
        # "Another Valid"はインデックス4（=5番目の要素は4番目）として出力される
        assert "4. Another Valid" in prompt_str
        # nameなし・空のカテゴリは含まれない
        assert "No name field" not in prompt_str
        assert "Empty name" not in prompt_str
        # プロンプト文字列には2行のみ存在（有効なカテゴリは2つ）
        lines = [line for line in prompt_str.split('\n') if line.strip()]
        assert len(lines) == 2, f"Expected 2 valid categories, got {len(lines)}"
```

### 2.3 get_available_categories_for_prompt テスト

```python
class TestGetAvailableCategoriesForPrompt:
    """プロンプト用カテゴリ取得テスト"""

    def test_auto_load_when_not_loaded(self, tmp_path, monkeypatch):
        """CAT-004: 未ロード時に自動的にロードされる

        categories.py:61-62 の `if not _categories_for_prompt_str:` 分岐をカバーする。
        """
        # Arrange
        # テスト用のcategories.jsonを作成
        categories = [{"name": "Auto Loaded", "description": "Auto load test"}]
        json_file = tmp_path / "categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")

        import app.core.categories as cat_module
        # グローバル変数をリセット
        cat_module._categories_data = []
        cat_module._categories_for_prompt_str = ""

        # DEFAULT_CATEGORIES_FILE_PATHをモック
        monkeypatch.setattr(cat_module, "DEFAULT_CATEGORIES_FILE_PATH", str(json_file))

        # Act
        result = cat_module.get_available_categories_for_prompt()

        # Assert
        assert "Auto Loaded" in result

    def test_cached_data_returned(self, tmp_path):
        """CAT-005: キャッシュされたデータが返却される"""
        # Arrange
        categories = [{"name": "Cached Category", "description": "Cache test"}]
        json_file = tmp_path / "categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")

        from app.core.categories import load_categories, get_available_categories_for_prompt

        # 最初にロード
        load_categories(str(json_file))
        first_result = get_available_categories_for_prompt()

        # Act
        second_result = get_available_categories_for_prompt()

        # Assert
        # 同一の文字列が返却される
        assert first_result == second_result
        assert "Cached Category" in second_result
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CAT-E01 | 存在しないファイルパス | 無効なファイルパス | FileNotFoundError処理、フォールバック文字列 |
| CAT-E02 | 無効なJSON構文 | 不正なJSONファイル | JSONDecodeError処理、フォールバック文字列 |
| CAT-E03 | 予期せぬ例外 | ファイル読み込み中の例外 | Exception処理、フォールバック文字列 |
| CAT-E04 | 権限エラー | 読み取り権限なしファイル | Exception処理、フォールバック文字列 |

### 3.1 ファイル読み込みエラーテスト

```python
class TestLoadCategoriesErrors:
    """カテゴリ読み込みエラーテスト"""

    def test_file_not_found(self, tmp_path, capsys):
        """CAT-E01: 存在しないファイルパスでフォールバック文字列が設定される

        categories.py:43-48 の FileNotFoundError 分岐をカバーする。
        """
        # Arrange
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # tmp_path下の存在しないファイルパスを使用（環境非依存）
        nonexistent_path = str(tmp_path / "nonexistent" / "categories.json")

        # Act
        load_categories(nonexistent_path)

        # Assert
        assert cat_module._categories_data == []
        assert cat_module._categories_for_prompt_str == "Predefined category list not found."
        # エラーメッセージが出力されていることを確認（stdout/stderr両方チェック）
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: Category file not found" in output

    def test_invalid_json_syntax(self, tmp_path, capsys):
        """CAT-E02: 無効なJSON構文でフォールバック文字列が設定される

        categories.py:49-52 の JSONDecodeError 分岐をカバーする。
        """
        # Arrange
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("{invalid json syntax", encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(str(invalid_json_file))

        # Assert
        assert cat_module._categories_data == []
        assert cat_module._categories_for_prompt_str == "Error loading predefined categories."
        # エラーメッセージが出力されていることを確認（stdout/stderr両方チェック）
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: Could not decode JSON" in output

    def test_unexpected_exception(self, tmp_path, capsys):
        """CAT-E03: 予期せぬ例外でフォールバック文字列が設定される

        categories.py:53-56 の Exception 分岐をカバーする。
        """
        # Arrange
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # json.loadをモックして予期せぬ例外を発生させる
        with patch("app.core.categories.json.load", side_effect=MemoryError("Out of memory")):
            # 有効なJSONファイルを作成（openは成功させる）
            valid_json_file = tmp_path / "valid.json"
            valid_json_file.write_text('[{"name": "Test"}]', encoding="utf-8")

            # Act
            load_categories(str(valid_json_file))

        # Assert
        assert cat_module._categories_data == []
        assert cat_module._categories_for_prompt_str == "Unexpected error loading predefined categories."
        # エラーメッセージが出力されていることを確認（stdout/stderr両方チェック）
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: An unexpected error occurred" in output

    def test_permission_error(self, tmp_path, capsys):
        """CAT-E04: 読み取り権限エラーでフォールバック文字列が設定される

        categories.py:53-56 の Exception 分岐をカバーする（PermissionErrorはExceptionのサブクラス）。
        """
        # Arrange
        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # openをモックしてPermissionErrorを発生させる
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Act
            load_categories("/some/protected/file.json")

        # Assert
        assert cat_module._categories_data == []
        assert cat_module._categories_for_prompt_str == "Unexpected error loading predefined categories."
        # エラーメッセージが出力されていることを確認（stdout/stderr両方チェック）
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: An unexpected error occurred" in output
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| CAT-SEC-01 | パストラバーサル攻撃への耐性 | 存在しない相対パス | エラーハンドリングが正常に動作 |
| CAT-SEC-02 | 大量カテゴリによるDoS耐性 | 10000個のカテゴリ | タイムアウトなしで処理完了 |
| CAT-SEC-03 | 悪意のあるJSONコンテンツ | 特殊文字・制御文字を含むカテゴリ | 安全に処理される |

```python
@pytest.mark.security
class TestCategoriesSecurity:
    """カテゴリセキュリティテスト"""

    def test_path_traversal_handling(self, tmp_path, capsys):
        """CAT-SEC-01: パストラバーサル攻撃パスが安全に処理される

        「..」を含むパストラバーサル攻撃パスが渡されても、
        安全にエラーハンドリングされることを検証。
        tmp_pathを起点に相対パスでディレクトリを遡り、存在しないパスへアクセスを試みる。
        """
        # Arrange
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # 「..」を含むパストラバーサル攻撃パス（存在しないディレクトリ）
        malicious_path = str(tmp_path / ".." / ".." / ".." / "nonexistent" / "categories.json")

        # Act
        load_categories(malicious_path)

        # Assert
        # FileNotFoundErrorまたはその他のエラーとして安全に処理される
        assert cat_module._categories_data == []
        # フォールバック文字列が設定されている（エラー種別に依存しない検証）
        assert cat_module._categories_for_prompt_str != ""
        # エラーメッセージが出力されていることを確認
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR" in output or "not found" in output.lower()

    def test_large_categories_list_dos_resistance(self, tmp_path):
        """CAT-SEC-02: 大量カテゴリリストによるDoS攻撃への耐性

        大量のカテゴリを含むJSONファイルを処理できることを検証。
        メモリ枯渇やタイムアウトが発生しないことを確認。
        """
        # Arrange
        import time
        large_categories = [
            {"name": f"Category {i}", "description": f"Description for category {i}"}
            for i in range(10000)
        ]
        json_file = tmp_path / "large_categories.json"
        json_file.write_text(json.dumps(large_categories), encoding="utf-8")

        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        start_time = time.time()
        load_categories(str(json_file))
        elapsed_time = time.time() - start_time

        # Assert
        # 10秒以内に処理完了
        assert elapsed_time < 10.0, f"処理時間が長すぎます: {elapsed_time}秒"
        # 全カテゴリが読み込まれている
        assert len(cat_module._categories_data) == 10000
        # プロンプト文字列が生成されている
        assert cat_module._categories_for_prompt_str != ""

    def test_malicious_json_content_handling(self, tmp_path):
        """CAT-SEC-03: 悪意のあるJSONコンテンツが安全に処理される

        特殊文字、制御文字、HTMLタグなどを含むカテゴリ名が
        そのまま文字列として扱われることを検証。
        """
        # Arrange
        malicious_categories = [
            {
                "name": "<script>alert('XSS')</script>",
                "description": "XSS attempt"
            },
            {
                "name": "'; DROP TABLE users; --",
                "description": "SQL injection attempt"
            },
            {
                "name": "Control\x00Char\x1fTest",
                "description": "Control characters"
            },
            {
                "name": "{{template.injection}}",
                "description": "Template injection attempt"
            }
        ]
        json_file = tmp_path / "malicious_categories.json"
        json_file.write_text(json.dumps(malicious_categories), encoding="utf-8")

        from app.core.categories import load_categories
        import app.core.categories as cat_module

        # Act
        load_categories(str(json_file))

        # Assert
        # 全カテゴリが読み込まれている（フィルタリングされていない）
        assert len(cat_module._categories_data) == 4
        # 悪意のあるコンテンツがそのまま文字列として含まれている
        # （実行されていないことの間接的な検証）
        prompt_str = cat_module._categories_for_prompt_str
        assert "<script>" in prompt_str
        assert "DROP TABLE" in prompt_str
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_categories_module` | テスト間のモジュール状態リセット | function | Yes |
| `valid_categories_json` | 有効なテスト用JSONファイル作成 | function | No |

### 共通フィクスチャ定義

```python
# test/unit/core/conftest.py に追加
import sys
import pytest


@pytest.fixture(autouse=True)
def reset_categories_module():
    """テストごとにcategoriesモジュールのグローバル状態をリセット

    categories.pyはグローバル変数でキャッシュを管理しており、
    テスト間の独立性を保証するためリセットが必要。
    テスト前後両方でクリアすることで、並列実行時の競合を防止する。
    """
    # テスト前にもモジュールキャッシュをクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.categories")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # テスト後にクリーンアップ
    try:
        import app.core.categories as cat_module
        cat_module._categories_data = []
        cat_module._categories_for_prompt_str = ""
    except ImportError:
        pass
    # モジュールキャッシュもクリア
    modules_to_remove = [
        key for key in list(sys.modules.keys())
        if key.startswith("app.core.categories")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

---

## 6. テスト実行例

```bash
# categories関連テストのみ実行
pytest test/unit/core/test_categories.py -v

# 特定のテストクラスのみ実行
pytest test/unit/core/test_categories.py::TestLoadCategories -v
pytest test/unit/core/test_categories.py::TestLoadCategoriesErrors -v
pytest test/unit/core/test_categories.py::TestCategoriesSecurity -v

# カバレッジ付きで実行
pytest test/unit/core/test_categories.py --cov=app.core.categories --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/core/test_categories.py -m "security" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 8 | CAT-001 〜 CAT-008 |
| 異常系 | 4 | CAT-E01 〜 CAT-E04 |
| セキュリティ | 3 | CAT-SEC-01 〜 CAT-SEC-03 |
| **合計** | **15** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestCategoriesImport` | CAT-001 | 1 |
| `TestLoadCategories` | CAT-002〜CAT-003, CAT-006〜CAT-008 | 5 |
| `TestGetAvailableCategoriesForPrompt` | CAT-004〜CAT-005 | 2 |
| `TestLoadCategoriesErrors` | CAT-E01〜CAT-E04 | 4 |
| `TestCategoriesSecurity` | CAT-SEC-01〜CAT-SEC-03 | 3 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> **推奨事項**: CAT-SEC-03 で検証しているように、悪意のあるコンテンツがそのまま
> プロンプト文字列に含まれます。LLMプロンプトインジェクション対策として、
> カテゴリ名のサニタイズ処理の追加を検討してください。

### 注意事項

- `pytest` の標準機能のみ使用（追加パッケージ不要）
- `@pytest.mark.security` マーカーを `pyproject.toml` に登録してください
- `capsys` フィクスチャを使用してprint出力をキャプチャしています
- `tmp_path` フィクスチャを使用して一時ファイルを作成しています

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | グローバル変数によるキャッシュ | 並列テスト実行時に競合の可能性 | autouseフィクスチャでリセット |
| 2 | print文によるログ出力 | 構造化ログではない | 将来的にloggingモジュールへ移行推奨 |
| 3 | カテゴリ名のサニタイズなし | LLMプロンプトインジェクションのリスク | 入力検証の追加を推奨 |
