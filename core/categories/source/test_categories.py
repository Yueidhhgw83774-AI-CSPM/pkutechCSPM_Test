# -*- coding: utf-8 -*-
"""
categories.py のテスト。
テスト対象: app/core/categories.py
テスト仕様: categories_tests.md
カバレッジ目標: 60%
このテストファイルは categories_tests.md 仕様書に従って記述されており、
正常系テスト、異常系テスト、セキュリティテストの3カテゴリを含む。
テストカテゴリ:
  - 正常系: 8テスト (CAT-001 ~ CAT-008)
  - 異常系: 4テスト (CAT-E01 ~ CAT-E04)
  - セキュリティテスト: 3テスト (CAT-SEC-01 ~ CAT-SEC-03)
"""
import os
import re
import sys
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# ─── SourceCodeRoot を .env から読み込む ────────────────────────────────
def _load_source_root() -> str:
    """プロジェクトルートの .env から SourceCodeRoot を読み込む。"""
    # 優先度1: ルート conftest.py が os.environ に設定済みの場合
    from_env = os.environ.get("SourceCodeRoot", "").strip().strip("'\"")
    if from_env:
        return from_env
    # 優先度2: ディレクトリツリーを遡って .env ファイルを検索する
    current = Path(__file__).resolve()
    for directory in [current, *current.parents]:
        env_file = (directory if directory.is_dir() else directory.parent) / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^\s*SourceCodeRoot\s*=\s*['\"]?(.+?)['\"]?\s*$", line)
                if m:
                    return m.group(1).strip()
    return ""

PROJECT_ROOT = _load_source_root()
if PROJECT_ROOT and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# =============================================================================
# 正常系テスト (CAT-001 ~ CAT-008)
# =============================================================================
class TestCategoriesImport:
    """カテゴリモジュールのインポートテスト。"""
    def test_import_categories_module(self):
        """CAT-001: モジュールのインポート成功。
        
        categories モジュールが正常にインポートでき、必要な関数とグローバル変数を含むことを検証する。
        """
        # Arrange & Act: テストデータを準備し実行する
        from app.core import categories
        # Assert: 期待値と比較する
        # 関数の存在性を検証
        assert hasattr(categories, "load_categories"), "load_categories 関数が見つかりません"
        assert hasattr(categories, "get_available_categories_for_prompt"), "get_available_categories_for_prompt 関数が見つかりません"
        # グローバル変数の存在性を検証
        assert hasattr(categories, "_categories_data"), "_categories_data グローバル変数が見つかりません"
        assert hasattr(categories, "_categories_for_prompt_str"), "_categories_for_prompt_str グローバル変数が見つかりません"
        assert hasattr(categories, "DEFAULT_CATEGORIES_FILE_PATH"), "DEFAULT_CATEGORIES_FILE_PATH 定数が見つかりません"
class TestLoadCategories:
    """カテゴリ読み込みテスト。"""
    def test_load_valid_categories(self, valid_categories_json):
        """CAT-002: 有効なJSONファイルからカテゴリを読み込む。
        
        コード行 categories.py:21-38 をカバーする。
        有効な JSON ファイルから正しくカテゴリデータを読み取ることを検証する。
        """
        # Arrange: テストデータを準備する
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行する
        load_categories(valid_categories_json)
        # Assert: 期待値と比較する
        assert len(cat_module._categories_data) == 3, f"3つのカテゴリが読み込まれるべきです。実際: {len(cat_module._categories_data)}"
        assert cat_module._categories_data[0]["name"] == "Identity and Access Management"
        assert cat_module._categories_for_prompt_str != "", "プロンプト文字列は空であってはなりません"
    def test_prompt_string_format(self, valid_categories_json):
        """CAT-003: プロンプト文字列が番号付きリスト形式で生成される。
        
        コード行 categories.py:28-35 をカバーする。
        生成されたプロンプト文字列が正しい番号付きリスト形式であることを検証する。
        """
        # Arrange: テストデータを準備する
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行する
        load_categories(valid_categories_json)
        # Assert: 期待値と比較する
        prompt_str = cat_module._categories_for_prompt_str
        # 番号付きリスト形式を検証
        assert "1. Identity and Access Management" in prompt_str, "1つ目の項目が見つかりません"
        assert "2. Data Security" in prompt_str, "2つ目の項目が見つかりません"
        assert "3. Network Security" in prompt_str, "3つ目の項目が見つかりません"
        # 説明が含まれることを検証
        assert "(Description:" in prompt_str, "説明の形式が正しくありません"
    def test_empty_categories_list(self, tmp_path):
        """CAT-006: 空のカテゴリリストを読み込んだときのフォールバック。
        
        コード行 categories.py:37-38 をカバーする。
        空のカテゴリリストに対してフォールバック文字列が返されることを検証する。
        """
        # Arrange: テストデータを準備する（空のJSON配列）
        json_file = tmp_path / "empty_categories.json"
        json_file.write_text("[]", encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行する
        load_categories(str(json_file))
        # Assert: 期待値と比較する
        assert cat_module._categories_data == [], "データは空のリストであるべきです"
        assert "No predefined categories are available" in cat_module._categories_for_prompt_str, "フォールバック文字列が正しくありません"
    def test_category_without_description(self, tmp_path):
        """CAT-007: descriptionなしのカテゴリが空の説明で処理される。
        
        コード行 categories.py:31 をカバーする。
        description フィールドがないカテゴリが空文字列で処理されることを検証する。
        """
        # Arrange: テストデータを準備する（descriptionフィールドなし）
        categories = [{"name": "Test Category"}]
        json_file = tmp_path / "no_desc_categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行する
        load_categories(str(json_file))
        # Assert: 期待値と比較する
        assert len(cat_module._categories_data) == 1, "1つのカテゴリが読み込まれるべきです"
        # 空の説明が処理されることを検証
        assert "1. Test Category (Description: )" in cat_module._categories_for_prompt_str, "空の説明の形式が正しくありません"
    def test_category_without_name_skipped(self, tmp_path):
        """CAT-008: nameなしまたは空のnameを持つカテゴリがスキップされる。
        
        コード行 categories.py:32 をカバーする。
        name がないか空のカテゴリがスキップされることを検証する。
        """
        # Arrange: テストデータを準備する（有効と無効が混在）
        categories = [
            {"name": "Valid Category", "description": "Has name"},
            {"description": "No name field"},  # nameフィールドなし
            {"name": "", "description": "Empty name"},  # 空のname
            {"name": "Another Valid", "description": "Also has name"}
        ]
        json_file = tmp_path / "mixed_categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行する
        load_categories(str(json_file))
        # Assert: 期待値と比較する
        prompt_str = cat_module._categories_for_prompt_str
        # 有効なカテゴリが含まれることを検証
        assert "1. Valid Category" in prompt_str, "有効なカテゴリ1が含まれるべきです"
        assert "4. Another Valid" in prompt_str, "有効なカテゴリ2が含まれるべきです（インデックス4）"
        # 無効なカテゴリが除外されることを検証
        assert "No name field" not in prompt_str, "nameフィールドがないカテゴリは除外されるべきです"
        assert "Empty name" not in prompt_str, "空のnameを持つカテゴリは除外されるべきです"
        # 2つの有効なカテゴリだけが存在することを検証
        lines = [line for line in prompt_str.split('\n') if line.strip()]
        assert len(lines) == 2, f"2つの有効なカテゴリが期待されます。実際: {len(lines)}"
class TestGetAvailableCategoriesForPrompt:
    """プロンプト用カテゴリ取得テスト。"""
    def test_auto_load_when_not_loaded(self, tmp_path):
        """CAT-004: 未ロード時に自動的にロードされる。
        
        コード行 categories.py:61-62 をカバーする。
        未ロード時に自動的に load_categories() が呼び出されることを検証する。
        """
        # Arrange: テストデータを準備する
        import app.core.categories as cat_module
        # グローバル変数をリセット
        cat_module._categories_data = []
        cat_module._categories_for_prompt_str = ""
        # Act: 関数を呼び出す（自動的に load_categories を呼び出して実際のデータをロードする）
        result = cat_module.get_available_categories_for_prompt()
        # Assert: 期待値と比較する（ロードされたデータが返される）
        # 返り値が空でないことを検証
        assert result is not None, "自動ロードが失敗し、Noneが返されました"
        assert len(result) > 0, "自動ロードが失敗し、空文字列が返されました"
        # カテゴリ内容が含まれることを検証（典型的なカテゴリ名を確認）
        # 実際の実装は実際のカテゴリデータをロードするため、"Auto Loaded"文字列ではない
        assert "Identity and Access Management" in result or "IAM" in result, \
            f"自動ロードが失敗し、期待されるカテゴリ内容が含まれていません。実際の返り値: {result[:200]}..."
        # 番号形式が含まれることを検証（フォーマット済みであることを確認）
        assert "1." in result or "2." in result, \
            "返された文字列はフォーマットされた番号を含むべきです"
        # グローバル変数が更新されたことを検証
        assert cat_module._categories_for_prompt_str == result, \
            "グローバルキャッシュ変数が正しく更新されていません"
        assert len(cat_module._categories_data) > 0, \
            "グローバルカテゴリデータが正しくロードされていません"
    def test_cached_data_returned(self, tmp_path):
        """CAT-005: キャッシュされたデータが返される。
        
        2回目の呼び出しでキャッシュされたデータが返されることを検証する。
        """
        # Arrange: テストデータを準備する
        categories = [{"name": "Cached Category", "description": "Cache test"}]
        json_file = tmp_path / "categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories, get_available_categories_for_prompt
        # 最初のロード
        load_categories(str(json_file))
        first_result = get_available_categories_for_prompt()
        # Act: 2回目の呼び出し
        second_result = get_available_categories_for_prompt()
        # Assert: 期待値と比較する
        assert first_result == second_result, "2回の呼び出しで同じ文字列が返されるべきです"
        assert "Cached Category" in second_result, "キャッシュデータは正しい内容を含むべきです"
# =============================================================================
# 異常系テスト (CAT-E01 ~ CAT-E04)
# =============================================================================
class TestLoadCategoriesErrors:
    """カテゴリ読み込みエラーテスト。"""
    def test_file_not_found(self, tmp_path, capsys):
        """CAT-E01: 存在しないファイルパスでフォールバック文字列が設定される。
        
        コード行 categories.py:43-48 をカバーする。
        ファイルが存在しないときに FileNotFoundError が正しく処理されることを検証する。
        """
        # Arrange: テストデータを準備する（存在しないファイルパス）
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        nonexistent_path = str(tmp_path / "nonexistent" / "categories.json")
        # Act: テスト対象を実行する
        load_categories(nonexistent_path)
        # Assert: 期待値と比較する
        assert cat_module._categories_data == [], "データは空のリストであるべきです"
        assert cat_module._categories_for_prompt_str == "Predefined category list not found.", "フォールバック文字列が正しくありません"
        # エラーメッセージが出力されることを検証
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: Category file not found" in output, "エラーメッセージが出力されていません"
    def test_invalid_json_syntax(self, tmp_path, capsys):
        """CAT-E02: 無効なJSON構文でフォールバック文字列が設定される。
        
        コード行 categories.py:49-52 をカバーする。
        無効な JSON 構文のときに JSONDecodeError が正しく処理されることを検証する。
        """
        # Arrange: テストデータを準備する（無効なJSON）
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("{invalid json syntax", encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行する
        load_categories(str(invalid_json_file))
        # Assert: 期待値と比較する
        assert cat_module._categories_data == [], "データは空のリストであるべきです"
        assert cat_module._categories_for_prompt_str == "Error loading predefined categories.", "フォールバック文字列が正しくありません"
        # エラーメッセージが出力されることを検証
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: Could not decode JSON" in output, "エラーメッセージが出力されていません"
    def test_unexpected_exception(self, tmp_path, capsys):
        """CAT-E03: 予期しない例外でフォールバック文字列が設定される。
        
        コード行 categories.py:53-56 をカバーする。
        予期しない例外が正しく処理されることを検証する。
        """
        # Arrange: テストデータを準備する
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # json.load が MemoryError を発生させるようにモックする
        with patch("app.core.categories.json.load", side_effect=MemoryError("Out of memory")):
            valid_json_file = tmp_path / "valid.json"
            valid_json_file.write_text('[{"name": "Test"}]', encoding="utf-8")
            # Act: テスト対象を実行する
            load_categories(str(valid_json_file))
        # Assert: 期待値と比較する
        assert cat_module._categories_data == [], "データは空のリストであるべきです"
        assert cat_module._categories_for_prompt_str == "Unexpected error loading predefined categories.", "フォールバック文字列が正しくありません"
        # エラーメッセージが出力されることを検証
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: An unexpected error occurred" in output, "エラーメッセージが出力されていません"
    def test_permission_error(self, tmp_path, capsys):
        """CAT-E04: 読み取り権限エラーでフォールバック文字列が設定される。
        
        コード行 categories.py:53-56 をカバーする。
        権限エラーが正しく処理されることを検証する（PermissionError は Exception のサブクラス）。
        """
        # Arrange: テストデータを準備する
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # open が PermissionError を発生させるようにモックする
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Act: テスト対象を実行する
            load_categories("/some/protected/file.json")
        # Assert: 期待値と比較する
        assert cat_module._categories_data == [], "データは空のリストであるべきです"
        assert cat_module._categories_for_prompt_str == "Unexpected error loading predefined categories.", "フォールバック文字列が正しくありません"
        # エラーメッセージが出力されることを検証
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: An unexpected error occurred" in output, "エラーメッセージが出力されていません"
# =============================================================================
# セキュリティテスト (CAT-SEC-01 ~ CAT-SEC-03)
# =============================================================================
@pytest.mark.security
class TestCategoriesSecurity:
    """カテゴリセキュリティテスト。"""
    def test_path_traversal_handling(self, tmp_path, capsys):
        """CAT-SEC-01: パストラバーサル攻撃パスが安全に処理される。
        
        ".." を含むパストラバーサル攻撃パスが安全に処理されることを検証する。
        """
        # Arrange: テストデータを準備する（パストラバーサル攻撃）
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        malicious_path = str(tmp_path / ".." / ".." / ".." / "nonexistent" / "categories.json")
        # Act: テスト対象を実行する
        load_categories(malicious_path)
        # Assert: 期待値と比較する
        assert cat_module._categories_data == [], "データは空のリストであるべきです（安全に処理）"
        assert cat_module._categories_for_prompt_str != "", "フォールバック文字列が設定されるべきです"
        # エラーが安全に処理されることを検証
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR" in output or "not found" in output.lower(), "エラーが記録されるべきです"
    def test_large_categories_list_dos_resistance(self, tmp_path):
        """CAT-SEC-02: 大量カテゴリリストによるDoS攻撃への耐性。
        
        大量のカテゴリリストがメモリオーバーフローやタイムアウトを引き起こさないことを検証する。
        """
        # Arrange: テストデータを準備する（10000個のカテゴリ）
        large_categories = [
            {"name": f"Category {i}", "description": f"Description for category {i}"}
            for i in range(10000)
        ]
        json_file = tmp_path / "large_categories.json"
        json_file.write_text(json.dumps(large_categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act: テスト対象を実行し時間を測定する
        start_time = time.time()
        load_categories(str(json_file))
        elapsed_time = time.time() - start_time
        # Assert: 期待値と比較する
        assert elapsed_time < 10.0, f"処理時間が長すぎます: {elapsed_time}秒"
        assert len(cat_module._categories_data) == 10000, "すべてのカテゴリがロードされるべきです"
        assert cat_module._categories_for_prompt_str != "", "プロンプト文字列が生成されるべきです"
    def test_malicious_json_content_handling(self, tmp_path):
        """CAT-SEC-03: 悪意のあるJSONコンテンツが安全に処理される。
        
        特殊文字、HTMLタグなどの悪意のあるコンテンツを含むカテゴリ名が安全に処理されることを検証する。
        """
        # Arrange: テストデータを準備する（様々な悪意のあるコンテンツを含む）
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
        # Act: テスト対象を実行する
        load_categories(str(json_file))
        # Assert: 期待値と比較する
        assert len(cat_module._categories_data) == 4, "すべてのカテゴリがロードされるべきです（フィルタリングなし）"
        # 悪意のあるコンテンツが文字列として含まれることを検証（実行されない）
        prompt_str = cat_module._categories_for_prompt_str
        assert "<script>" in prompt_str, "HTMLタグは文字列として存在すべきです"
        assert "DROP TABLE" in prompt_str, "SQLインジェクション試行は文字列として存在すべきです"
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
