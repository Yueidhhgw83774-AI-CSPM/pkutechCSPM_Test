# MCP Plugin Chat Agent 测试项目

## 概述

MCP Chat Agent 核心功能测试

- **测试要件**: `docs/testing/plugins/mcp/mcp_plugin_chat_agent_tests.md`
- **测试数量**: 18 个 (正常系9 + 异常系3 + 安全6)
- **覆盖率目标**: 90%+

## 测试对象

- `app/mcp_plugin/chat_agent.py` - MCP 聊天代理入口点
- 支持两种模式：
  - 阶层式代理（默认）- 成本削减92%
  - Deep Agents（遗留）- 完整功能模式

## 运行测试

### 基本运行

```bash
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\mcp\mcp_plugin_chat_agent\source
pytest test_mcp_plugin_chat_agent.py -v
```

### 按类别运行

```bash
# 正常系测试
pytest test_mcp_plugin_chat_agent.py -v -k "TestInvoke"

# 异常系测试
pytest test_mcp_plugin_chat_agent.py -v -k "Exception"

# 安全测试
pytest test_mcp_plugin_chat_agent.py -v -m security
```

### 生成覆盖率报告

```bash
pytest test_mcp_plugin_chat_agent.py --cov=app.mcp_plugin.chat_agent --cov-report=html
```

## 测试分类

### 正常系 (9个)

- MCPCA-001: 阶层式模式执行
- MCPCA-002: Deep Agents模式执行
- MCPCA-003: 无服务器指定
- MCPCA-004: 特定服务器指定
- MCPCA-005: 错误响应格式化
- MCPCA-006: Progress 构建
- MCPCA-007: 参数传播（阶层式）
- MCPCA-008: 参数传播（Deep Agents）
- MCPCA-009: 模块导出验证

### 异常系 (3个)

- MCPCA-E01: 阶层式代理异常
- MCPCA-E02: Deep Agents异常
- MCPCA-E03: 空响应处理

### 安全测试 (6个)

- MCPCA-SEC-01: 错误ID唯一性
- MCPCA-SEC-02: 内部错误不暴露
- MCPCA-SEC-03: Session ID日志记录
- MCPCA-SEC-04: 状态错误凭证暴露（xfail）
- MCPCA-SEC-05: 日志注入防护
- MCPCA-SEC-06: Server name安全验证

## 依赖项

```
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
```

**安装命令**:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

## 注意事项

1. ✅ 测试使用 Mock 避免实际调用 MCP 服务器
2. ✅ 异步测试使用 pytest-asyncio
3. ✅ 安全测试标记为 @pytest.mark.security
4. ⚠️ MCPCA-SEC-04 标记为 xfail（已知安全漏洞）

## 查看报告

测试完成后，报告位于：

- **Markdown**: `reports/TestReport_mcp_plugin_chat_agent.md`
- **JSON**: `reports/TestReport_mcp_plugin_chat_agent.json`

