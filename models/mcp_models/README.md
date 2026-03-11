# models/mcp_models 测试项目

## 概述

本项目为 `app/models/mcp.py` 的单元测试。

## 测试规格

- **测试要件**: `docs/testing/models/mcp_models_tests.md`
- **覆盖率目标**: 90%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 18 |
| 异常系 | 5 |
| **合计** | **23** |

## 测试对象

### 主要模型

#### 认证相关
- **CloudCredentialsContext** - 云认证信息（AWS/Azure/GCP）

#### 枚举类型
- **MCPToolType** - MCP 工具类型
- **SSEEventType** - SSE 事件类型

#### 工具定义
- **MCPTool** - MCP 工具定义
- **MCPToolParameter** - 工具参数
- **MCPServer** - MCP 服务器配置

#### 聊天相关
- **MCPChatMessage** - 聊天消息
- **MCPChatRequest** - 聊天请求
- **MCPChatStreamRequest** - 流式聊天请求
- **MCPChatResponse** - 聊天响应

#### 任务管理
- **SubTaskResult** - 子任务结果
- **TodoItem** - TODO 项目
- **ThinkingLog** - 思考日志
- **ValidationResult** - 验证结果
- **MCPProgress** - 处理进度

#### 会话管理
- **SessionInfo** - 会话信息
- **SessionListResponse** - 会话列表
- **SessionUpdateRequest** - 会话更新

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\models\mcp_models\source
pytest test_mcp_models.py -v
```

### 运行特定分类

```powershell
# 正常系测试
pytest test_mcp_models.py -v -k "Normal"

# 异常系测试
pytest test_mcp_models.py -v -k "Errors"
```

### 生成覆盖率报告

```powershell
pytest test_mcp_models.py --cov=app.models.mcp --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_mcp_models.md`
- **JSON**: `reports/TestReport_mcp_models.json`

## 测试类别

### 正常系测试

#### TestCloudCredentialsContextNormal (4个)
- AWS 认证配置
- Azure 认证配置
- GCP 认证配置
- 最小配置

#### TestEnumsNormal (2个)
- MCPToolType 枚举
- SSEEventType 枚举（包含新增的流式事件）

#### TestMCPToolNormal (3个)
- MCPToolParameter 定义
- MCPTool 基本配置
- 带参数的 MCPTool

#### TestMCPServerNormal (2个)
- MCPServer 基本配置
- MCPServer 完整配置

#### TestMCPChatModelsNormal (3个)
- 基本聊天消息
- 带工具调用的消息
- 子任务结果

#### TestTaskManagementModelsNormal (3个)
- TodoItem (pending/completed)
- ThinkingLog

#### TestMCPRequestResponseNormal (3个)
- MCPChatRequest
- MCPChatStreamRequest（流式请求）
- MCPChatResponse（完整响应）

#### TestSessionModelsNormal (2个)
- SessionInfo
- SessionListResponse

### 异常系测试

#### TestCloudCredentialsContextErrors (1个)
- 无效的云提供商

#### TestMCPChatRequestErrors (2个)
- 缺少必填字段
- 无效的类型

#### TestValidationResultErrors (2个)
- 缺少必填字段
- 名称长度超限

### 模型操作测试

#### TestModelOperations (1个)
- Pydantic v2 API（model_dump/model_validate）

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pydantic>=2.0.0
```

## 注意事项

1. ✅ 使用 Pydantic v2 API
2. ✅ 所有测试包含详细的中文注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ✅ 覆盖了 MCP 模型的主要功能

## 测试覆盖的代码行

- `app/models/mcp.py:9-50` - CloudCredentialsContext
- `app/models/mcp.py:53-76` - Enum 定义
- `app/models/mcp.py:79-103` - MCPTool 和 MCPServer
- `app/models/mcp.py:106-125` - 聊天相关模型
- `app/models/mcp.py:128-177` - 任务管理模型
- `app/models/mcp.py:180-289` - 请求/响应模型
- `app/models/mcp.py:292-362` - 会话管理模型

## 模型特点

### CloudCredentialsContext
- 支持 AWS、Azure、GCP 三种云平台
- 可选的认证字段，适应不同场景

### SSEEventType
- 包含传统事件类型（ORCHESTRATOR, RESPONSE 等）
- 新增流式事件（RESPONSE_CHUNK, LLM_START 等）
- 支持 Deep Agents 工具调用事件

### MCPChatResponse
- 向后兼容的 API 设计
- 新增字段全部为 Optional
- 支持 todos、thinking_logs、validation_result

### 会话管理
- SessionInfo 用于显示会话列表
- 支持分页（limit/offset）
- 支持会话名称自定义

## Pydantic v2 迁移说明

本项目使用 Pydantic v2 API：
- `model_dump()` 代替 v1 的 `dict()`
- `model_validate()` 代替 v1 的 `parse_obj()`
- 使用 `Field()` 进行字段定义和验证

