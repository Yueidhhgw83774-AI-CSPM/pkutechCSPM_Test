# llm_factory 测试项目

## 概述

本项目为 `app/core/llm_factory.py` 的单元测试。

## 测试规格

- **测试要件**: `docs/testing/core/llm_factory_tests.md`
- **覆盖率目标**: 90%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 43 |
| 异常系 | 12 |
| 安全测试 | 6 |
| **合计** | **61** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\llm_factory\source
pytest test_llm_factory.py -v
```

### 生成覆盖率报告

```powershell
pytest test_llm_factory.py --cov=app.core.llm_factory --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_llm_factory.md`
- **JSON**: `reports/TestReport_llm_factory.json`

## 测试类别

### 正常系测试
- **TestLLMFactoryCreateLLM**: 测试 `create_llm()` 函数的各种参数组合
- **TestLLMFactoryModelInfo**: 测试模型信息查询功能
- **TestLLMFactoryAddModelConfig**: 测试动态添加模型配置
- **TestConvenienceFunctions**: 测试便捷函数 (get_llm, get_policy_llm等)

### 异常系测试
- **TestLLMFactoryErrors**: 测试错误处理逻辑
  - 未知模型名称
  - 缺失 API Key
  - 无效参数值

### 安全测试
- **TestLLMFactorySecurity**: 测试安全相关功能
  - API Key 不在错误消息中泄露
  - 所有别名指向有效模型
  - 默认配置安全性

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
langchain-openai
langchain-aws
```

## 注意事项

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ⚠️ 需要在 `.env` 文件中配置 API Keys
5. ⚠️ 测试使用 mock 对象,不会实际调用 LLM API

## 环境变量配置

测试需要以下环境变量(从 `C:\pythonProject\python_ai_cspm\TestReport\.env` 加载):

- `GPT5_1_CHAT_API_KEY`
- `GPT5_1_CODEX_API_KEY`
- `GPT5_2_API_KEY`
- `GPT5_MINI_API_KEY`
- `GPT5_NANO_API_KEY`
- `CLAUDE_HAIKU_4_5_KEY`
- `CLAUDE_SONNET_4_5_KEY`
- `GEMINI_API`
- `DOCKER_BASE_URL`
- `EMBEDDING_3_LARGE_API_KEY`

## 测试覆盖的功能

| 函数/类 | 测试用例数 | 状态 |
|---------|----------|------|
| `LLMFactory.create_llm()` | 29个 | ✅ |
| `LLMFactory.get_model_info()` | 2个 | ✅ |
| `LLMFactory.list_available_models()` | 1个 | ✅ |
| `LLMFactory.list_models_by_category()` | 3个 | ✅ |
| `LLMFactory.get_all_categories()` | 1个 | ✅ |
| `LLMFactory.add_model_config()` | 3个 | ✅ |
| 便捷函数 (`get_llm` 等) | 7个 | ✅ |
| 错误处理 | 12个 | ✅ |
| 安全测试 | 6个 | ✅ |

## 已知问题

无

## 更新日志

- **2026-02-03**: 初始版本创建
  - 61个测试用例
  - 覆盖所有公开函数
  - 包含正常系、异常系、安全测试
