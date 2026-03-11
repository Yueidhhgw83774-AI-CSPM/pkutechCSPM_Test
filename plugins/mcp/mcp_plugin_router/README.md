# MCP Plugin Router 测试项目

## 概述

本项目为 `app/mcp_plugin/router.py` 的单元测试。

## 测试规格

- **测试要件**: `docs/testing/plugins/mcp/mcp_plugin_router_tests.md`
- **覆盖率目标**: 80%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 13 |
| 异常系 | 22 |
| 安全测试 | 8 |
| **合计** | **43** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\mcp\mcp_plugin_router\source
pytest test_mcp_plugin_router.py -v
```

### 生成覆盖率报告

```powershell
pytest test_mcp_plugin_router.py --cov=app.mcp_plugin.router --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_mcp_plugin_router.md`
- **JSON**: `reports/TestReport_mcp_plugin_router.json`

## 测试类别

### 正常系测试
- チャットエンドポイント (2个)
- サーバー管理 (7个)  
- ヘルスチェック (1个)
- SSE ストリーミング (3个)

### 異常系テスト
- チャットエラー (8个)
- サーバー管理エラー (10个)
- ストリーミングエラー (4个)

### セキュリティテスト
- JWT/HMAC検証 (2个)
- インジェクション防止 (2个)
- その他セキュリティ (4个)

## 依赖项

```
pytest>=8.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
```

## 注意事項

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文注释
3. ✅ 支持异步测试 (pytest-asyncio)
4. ✅ SSE ストリーミングテストあり

