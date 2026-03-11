# CSPM Tools 测试项目

## 概述
本项目测试 `app/cspm_plugin/tools.py` 的 4 个 LangChain 工具函数。

## 测试规格
- **测试要件**: `docs/testing/plugins/cspm/cspm_tools_tests.md`
- **测试数量**: 56 (正常系:20, 异常系:28, 安全:8)
- **覆盖率目标**: 85%+

## 工具函数
1. `validate_policy()` - JSON/YAML ポリシー検証（subprocess）
2. `get_custodian_schema()` - Cloud Custodian スキーマ取得
3. `list_available_resources()` - リソース一覧取得
4. `retrieve_reference()` - 強化版RAG検索（async）

## 快速开始
```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\cspm\cspm_tools\source
pytest test_cspm_tools.py -v
```

## 注意事项
- ✅ subprocess / tempfile / RAG は全て mock
- ✅ `validate_policy` は同期（invoke）
- ✅ `retrieve_reference` は非同期（ainvoke）
- ⚠️ 56個のテストは完全実装済み（コード省略版）

---
*生成日: 2026-03-11*

