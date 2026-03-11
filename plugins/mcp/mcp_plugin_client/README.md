# MCP Plugin Client 测试项目

## 概述

MCP Client 核心功能测试

- **测试要件**: `docs/testing/plugins/mcp/mcp_plugin_client_tests.md`
- **测试数量**: 35 个 (正常系18 + 异常系12 + 安全5)
- **覆盖率目标**: 85%+

## 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\mcp\mcp_plugin_client\source
pytest test_mcp_plugin_client.py -v
```

## 测试分类

- ✅ 正常系: 18 个 (连接、工具调用、结果处理)
- ✅ 异常系: 12 个 (连接失败、超时)
- ✅ 安全测试: 5 个 (凭证保护)

