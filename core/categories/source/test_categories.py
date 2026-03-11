# -*- coding: utf-8 -*-
"""
categories.py 单元测试
测试对象: app/core/categories.py
测试规格: categories_tests.md
覆盖率目标: 60%
本测试文件严格按照 categories_tests.md 测试规格文档编写，
包含正常系测试、异常系测试和安全测试三大类。
测试类别:
  - 正常系: 8 个测试 (CAT-001 ~ CAT-008)
  - 异常系: 4 个测试 (CAT-E01 ~ CAT-E04)
  - 安全测试: 3 个测试 (CAT-SEC-01 ~ CAT-SEC-03)
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
# Add project root to path
# 添加项目根目录到路径
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# =============================================================================
# 正常系测试 (CAT-001 ~ CAT-008)
# =============================================================================
class TestCategoriesImport:
    """カテゴリモジュールインポートテスト"""
    def test_import_categories_module(self):
        """CAT-001: モジュールのインポート成功
        验证 categories 模块可以正常导入，并且包含所需的函数和全局变量。
        """
        # Arrange & Act - 准备并执行
        from app.core import categories
        # Assert - 验证结果
        # 函数存在性验证
        assert hasattr(categories, "load_categories"), "缺少 load_categories 函数"
        assert hasattr(categories, "get_available_categories_for_prompt"), "缺少 get_available_categories_for_prompt 函数"
        # 全局变量存在性验证
        assert hasattr(categories, "_categories_data"), "缺少 _categories_data 全局变量"
        assert hasattr(categories, "_categories_for_prompt_str"), "缺少 _categories_for_prompt_str 全局变量"
        assert hasattr(categories, "DEFAULT_CATEGORIES_FILE_PATH"), "缺少 DEFAULT_CATEGORIES_FILE_PATH 常量"
class TestLoadCategories:
    """カテゴリ読み込みテスト"""
    def test_load_valid_categories(self, valid_categories_json):
        """CAT-002: 有効なJSONファイルからカテゴリ読み込み成功
        覆盖代码行: categories.py:21-38
        验证从有效的 JSON 文件中正确读取类别数据。
        """
        # Arrange - 准备测试数据
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数
        load_categories(valid_categories_json)
        # Assert - 验证结果
        assert len(cat_module._categories_data) == 3, f"期望加载3个类别，实际: {len(cat_module._categories_data)}"
        assert cat_module._categories_data[0]["name"] == "Identity and Access Management"
        assert cat_module._categories_for_prompt_str != "", "提示字符串不应为空"
    def test_prompt_string_format(self, valid_categories_json):
        """CAT-003: プロンプト文字列が番号付きリスト形式で生成される
        覆盖代码行: categories.py:28-35
        验证生成的提示字符串使用正确的编号列表格式。
        """
        # Arrange - 准备测试数据
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数
        load_categories(valid_categories_json)
        # Assert - 验证结果
        prompt_str = cat_module._categories_for_prompt_str
        # 验证编号列表格式
        assert "1. Identity and Access Management" in prompt_str, "缺少第1项"
        assert "2. Data Security" in prompt_str, "缺少第2项"
        assert "3. Network Security" in prompt_str, "缺少第3项"
        # 验证描述包含在内
        assert "(Description:" in prompt_str, "描述格式不正确"
    def test_empty_categories_list(self, tmp_path):
        """CAT-006: 空のカテゴリリスト読み込み時のフォールバック
        覆盖代码行: categories.py:37-38
        验证空的类别列表时返回回退字符串。
        """
        # Arrange - 准备测试数据（空的 JSON 数组）
        json_file = tmp_path / "empty_categories.json"
        json_file.write_text("[]", encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数
        load_categories(str(json_file))
        # Assert - 验证结果
        assert cat_module._categories_data == [], "数据应为空列表"
        assert "No predefined categories are available" in cat_module._categories_for_prompt_str, "回退字符串不正确"
    def test_category_without_description(self, tmp_path):
        """CAT-007: descriptionなしカテゴリが空の説明で処理される
        覆盖代码行: categories.py:31
        验证没有 description 字段的类别使用空字符串处理。
        """
        # Arrange - 准备测试数据（无 description 字段）
        categories = [{"name": "Test Category"}]
        json_file = tmp_path / "no_desc_categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数
        load_categories(str(json_file))
        # Assert - 验证结果
        assert len(cat_module._categories_data) == 1, "应加载1个类别"
        # 验证空描述的处理
        assert "1. Test Category (Description: )" in cat_module._categories_for_prompt_str, "空描述格式不正确"
    def test_category_without_name_skipped(self, tmp_path):
        """CAT-008: nameなしカテゴリがスキップされる
        覆盖代码行: categories.py:32
        验证没有 name 或 name 为空的类别被跳过。
        """
        # Arrange - 准备测试数据（混合有效和无效的类别）
        categories = [
            {"name": "Valid Category", "description": "Has name"},
            {"description": "No name field"},  # 无 name 字段
            {"name": "", "description": "Empty name"},  # 空 name
            {"name": "Another Valid", "description": "Also has name"}
        ]
        json_file = tmp_path / "mixed_categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数
        load_categories(str(json_file))
        # Assert - 验证结果
        prompt_str = cat_module._categories_for_prompt_str
        # 验证有效类别被包含
        assert "1. Valid Category" in prompt_str, "有效类别1应被包含"
        assert "4. Another Valid" in prompt_str, "有效类别2应被包含（索引为4）"
        # 验证无效类别被排除
        assert "No name field" not in prompt_str, "无name字段的类别应被排除"
        assert "Empty name" not in prompt_str, "空name的类别应被排除"
        # 验证只有2行有效类别
        lines = [line for line in prompt_str.split('\n') if line.strip()]
        assert len(lines) == 2, f"期望2个有效类别，实际: {len(lines)}"
class TestGetAvailableCategoriesForPrompt:
    """プロンプト用カテゴリ取得テスト"""
    def test_auto_load_when_not_loaded(self, tmp_path):
        """CAT-004: 未ロード時に自動的にロードされる
        覆盖代码行: categories.py:61-62
        验证未加载时自动调用 load_categories()。
        """
        # Arrange - 准备测试数据
        import app.core.categories as cat_module

        # 重置全局变量
        cat_module._categories_data = []
        cat_module._categories_for_prompt_str = ""

        # Act - 调用函数(应该自动调用 load_categories 并加载真实数据)
        result = cat_module.get_available_categories_for_prompt()

        # Assert - 验证返回了加载的数据(真实的分类列表)
        # 验证返回值不为空
        assert result is not None, "自动加载失败,返回None"
        assert len(result) > 0, "自动加载失败,返回空字符串"

        # 验证包含分类内容(检查是否包含典型分类名称)
        # 实际实现会加载真实的分类数据,而不是"Auto Loaded"字符串
        assert "Identity and Access Management" in result or "IAM" in result, \
            f"自动加载失败,未包含预期分类内容。实际返回: {result[:200]}..."

        # 验证包含序号格式(验证已格式化)
        assert "1." in result or "2." in result, \
            "返回的字符串应该包含格式化的序号"

        # 验证全局变量已更新
        assert cat_module._categories_for_prompt_str == result, \
            "全局缓存变量未正确更新"
        assert len(cat_module._categories_data) > 0, \
            "全局分类数据未正确加载"

    def test_cached_data_returned(self, tmp_path):
        """CAT-005: キャッシュされたデータが返却される
        验证第二次调用返回缓存的数据。
        """
        # Arrange - 准备测试数据
        categories = [{"name": "Cached Category", "description": "Cache test"}]
        json_file = tmp_path / "categories.json"
        json_file.write_text(json.dumps(categories), encoding="utf-8")
        from app.core.categories import load_categories, get_available_categories_for_prompt
        # 首次加载
        load_categories(str(json_file))
        first_result = get_available_categories_for_prompt()
        # Act - 第二次调用
        second_result = get_available_categories_for_prompt()
        # Assert - 验证结果
        assert first_result == second_result, "两次调用应返回相同字符串"
        assert "Cached Category" in second_result, "缓存数据应包含正确内容"
# =============================================================================
# 异常系测试 (CAT-E01 ~ CAT-E04)
# =============================================================================
class TestLoadCategoriesErrors:
    """カテゴリ読み込みエラーテスト"""
    def test_file_not_found(self, tmp_path, capsys):
        """CAT-E01: 存在しないファイルパスでフォールバック文字列が設定される
        覆盖代码行: categories.py:43-48
        验证文件不存在时正确处理 FileNotFoundError。
        """
        # Arrange - 准备测试数据（不存在的文件路径）
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        nonexistent_path = str(tmp_path / "nonexistent" / "categories.json")
        # Act - 执行被测试函数
        load_categories(nonexistent_path)
        # Assert - 验证结果
        assert cat_module._categories_data == [], "数据应为空列表"
        assert cat_module._categories_for_prompt_str == "Predefined category list not found.", "回退字符串不正确"
        # 验证错误消息被输出
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: Category file not found" in output, "错误消息未输出"
    def test_invalid_json_syntax(self, tmp_path, capsys):
        """CAT-E02: 無効なJSON構文でフォールバック文字列が設定される
        覆盖代码行: categories.py:49-52
        验证无效 JSON 语法时正确处理 JSONDecodeError。
        """
        # Arrange - 准备测试数据（无效的 JSON）
        invalid_json_file = tmp_path / "invalid.json"
        invalid_json_file.write_text("{invalid json syntax", encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数
        load_categories(str(invalid_json_file))
        # Assert - 验证结果
        assert cat_module._categories_data == [], "数据应为空列表"
        assert cat_module._categories_for_prompt_str == "Error loading predefined categories.", "回退字符串不正确"
        # 验证错误消息被输出
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: Could not decode JSON" in output, "错误消息未输出"
    def test_unexpected_exception(self, tmp_path, capsys):
        """CAT-E03: 予期せぬ例外でフォールバック文字列が設定される
        覆盖代码行: categories.py:53-56
        验证预期外异常时正确处理。
        """
        # Arrange - 准备测试数据
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # 模拟 json.load 抛出 MemoryError
        with patch("app.core.categories.json.load", side_effect=MemoryError("Out of memory")):
            valid_json_file = tmp_path / "valid.json"
            valid_json_file.write_text('[{"name": "Test"}]', encoding="utf-8")
            # Act - 执行被测试函数
            load_categories(str(valid_json_file))
        # Assert - 验证结果
        assert cat_module._categories_data == [], "数据应为空列表"
        assert cat_module._categories_for_prompt_str == "Unexpected error loading predefined categories.", "回退字符串不正确"
        # 验证错误消息被输出
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: An unexpected error occurred" in output, "错误消息未输出"
    def test_permission_error(self, tmp_path, capsys):
        """CAT-E04: 読み取り権限エラーでフォールバック文字列が設定される
        覆盖代码行: categories.py:53-56
        验证权限错误时正确处理（PermissionError 是 Exception 的子类）。
        """
        # Arrange - 准备测试数据
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # 模拟 open 抛出 PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Act - 执行被测试函数
            load_categories("/some/protected/file.json")
        # Assert - 验证结果
        assert cat_module._categories_data == [], "数据应为空列表"
        assert cat_module._categories_for_prompt_str == "Unexpected error loading predefined categories.", "回退字符串不正确"
        # 验证错误消息被输出
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR: An unexpected error occurred" in output, "错误消息未输出"
# =============================================================================
# 安全测试 (CAT-SEC-01 ~ CAT-SEC-03)
# =============================================================================
@pytest.mark.security
class TestCategoriesSecurity:
    """カテゴリセキュリティテスト"""
    def test_path_traversal_handling(self, tmp_path, capsys):
        """CAT-SEC-01: パストラバーサル攻撃パスが安全に処理される
        验证包含 ".." 的路径遍历攻击路径被安全处理。
        """
        # Arrange - 准备测试数据（路径遍历攻击）
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        malicious_path = str(tmp_path / ".." / ".." / ".." / "nonexistent" / "categories.json")
        # Act - 执行被测试函数
        load_categories(malicious_path)
        # Assert - 验证结果
        assert cat_module._categories_data == [], "数据应为空列表（安全处理）"
        assert cat_module._categories_for_prompt_str != "", "回退字符串应被设置"
        # 验证错误被安全处理
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert "ERROR" in output or "not found" in output.lower(), "错误应被记录"
    def test_large_categories_list_dos_resistance(self, tmp_path):
        """CAT-SEC-02: 大量カテゴリリストによるDoS攻撃への耐性
        验证大量类别列表不会导致内存溢出或超时。
        """
        # Arrange - 准备测试数据（10000个类别）
        large_categories = [
            {"name": f"Category {i}", "description": f"Description for category {i}"}
            for i in range(10000)
        ]
        json_file = tmp_path / "large_categories.json"
        json_file.write_text(json.dumps(large_categories), encoding="utf-8")
        from app.core.categories import load_categories
        import app.core.categories as cat_module
        # Act - 执行被测试函数并测量时间
        start_time = time.time()
        load_categories(str(json_file))
        elapsed_time = time.time() - start_time
        # Assert - 验证结果
        assert elapsed_time < 10.0, f"处理时间过长: {elapsed_time}秒"
        assert len(cat_module._categories_data) == 10000, "所有类别应被加载"
        assert cat_module._categories_for_prompt_str != "", "提示字符串应被生成"
    def test_malicious_json_content_handling(self, tmp_path):
        """CAT-SEC-03: 悪意のあるJSONコンテンツが安全に処理される
        验证包含特殊字符、HTML标签等恶意内容的类别名被安全处理。
        """
        # Arrange - 准备测试数据（包含各种恶意内容）
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
        # Act - 执行被测试函数
        load_categories(str(json_file))
        # Assert - 验证结果
        assert len(cat_module._categories_data) == 4, "所有类别应被加载（不过滤）"
        # 验证恶意内容作为字符串被包含（未被执行）
        prompt_str = cat_module._categories_for_prompt_str
        assert "<script>" in prompt_str, "HTML标签应作为字符串存在"
        assert "DROP TABLE" in prompt_str, "SQL注入尝试应作为字符串存在"
# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
