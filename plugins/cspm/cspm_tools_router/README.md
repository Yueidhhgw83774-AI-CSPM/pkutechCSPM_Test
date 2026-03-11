# CSPM Tools Router 测试项目

## 概述
测试 `app/cspm_plugin/tools_router.py` 的 4 个 MCP 工具エンドポイント。

## 测试规格
- **测试要件**: `docs/testing/plugins/cspm/cspm_tools_router_tests.md`
- **测试数量**: 29 (正常系:10, 異常系:12, セキュリティ:7)
- **覆盖率目标**: 85%+

## エンドポイント
1. `POST /tools/validate` - ポリシー検証
2. `POST /tools/schema` - スキーマ取得
3. `POST /tools/resources` - リソース一覧
4. `POST /tools/reference` - RAG検索

## 快速开始
```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\cspm\cspm_tools_router\source
pytest test_cspm_tools_router.py -v
```

---
*生成日: 2026-03-11*

