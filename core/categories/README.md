# categories.py 测试项目

## 概述

本项目为 `app/core/categories.py` 的单元测试，该模块负责从 JSON 文件加载安全类别定义并生成 LLM 提示字符串。

## 测试规格

- **测试对象**: `app/core/categories.py`
- **测试要件**: `docs/testing/core/categories_tests.md`
- **覆盖率目标**: 60%
- **测试框架**: pytest

## 功能说明

### 主要函数

| 函数 | 说明 |
|------|------|
| `load_categories(filepath)` | 从 JSON 文件读取类别数据并缓存到全局变量 |
| `get_available_categories_for_prompt()` | 获取 LLM 提示用的类别字符串（未加载时自动加载） |

### 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `_categories_data` | `List[Dict[str, str]]` | 缓存的类别数据 |
| `_categories_for_prompt_str` | `str` | 格式化的提示字符串缓存 |
| `DEFAULT_CATEGORIES_FILE_PATH` | `str` | 默认 JSON 文件路径 |

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 8 |
| 异常系 | 4 |
| 安全测试 | 3 |
| **合计** | **15** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\categories\source
$env:PYTHONPATH = "C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
pytest test_categories.py -v
```

### 按类别运行

```powershell
# 仅运行正常系测试
pytest test_categories.py::TestLoadCategories -v
pytest test_categories.py::TestGetAvailableCategoriesForPrompt -v

# 仅运行异常系测试
pytest test_categories.py::TestLoadCategoriesErrors -v

# 仅运行安全测试
pytest test_categories.py -m security -v
```

### 生成覆盖率报告

```powershell
pytest test_categories.py --cov=app.core.categories --cov-report=term-missing --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_categories.md`
- **JSON**: `reports/TestReport_categories.json`

## 测试类别

### 正常系测试 (CAT-001 ~ CAT-008)

| ID | 测试内容 |
|----|---------|
| CAT-001 | 模块导入成功 |
| CAT-002 | 有效JSON文件读取 |
| CAT-003 | 提示字符串格式验证 |
| CAT-004 | 未加载时自动加载 |
| CAT-005 | 缓存数据返回 |
| CAT-006 | 空列表回退处理 |
| CAT-007 | 无描述字段处理 |
| CAT-008 | 无名称字段跳过 |

### 异常系测试 (CAT-E01 ~ CAT-E04)

| ID | 测试内容 |
|----|---------|
| CAT-E01 | 文件不存在错误处理 |
| CAT-E02 | 无效JSON语法处理 |
| CAT-E03 | 预期外异常处理 |
| CAT-E04 | 权限错误处理 |

### 安全测试 (CAT-SEC-01 ~ CAT-SEC-03)

| ID | 测试内容 |
|----|---------|
| CAT-SEC-01 | 路径遍历攻击防护 |
| CAT-SEC-02 | 大量数据DoS防护 |
| CAT-SEC-03 | 恶意JSON内容处理 |

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
```

## 注意事项

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ✅ 使用 `autouse` fixture 自动重置模块状态
5. ⚠️ 该模块使用全局变量缓存，测试间需要隔离

## 已知限制

| # | 限制事项 | 影响 | 对策 |
|---|---------|------|------|
| 1 | 全局变量缓存 | 测试间可能相互影响 | 使用 autouse fixture 重置 |
| 2 | print 输出日志 | 非结构化日志 | 未来建议使用 logging 模块 |
| 3 | 无输入验证 | LLM 提示注入风险 | 建议添加类别名称清理 |

## 安全建议

根据测试发现，建议在生产环境中：

1. **输入验证**: 对类别名称进行清理，防止 LLM 提示注入
2. **大小限制**: 限制可加载的类别数量，防止 DoS
3. **路径验证**: 验证文件路径，防止路径遍历攻击

## 测试覆盖

- ✅ 正常流程完全覆盖
- ✅ 所有异常分支覆盖
- ✅ 安全边界测试
- ✅ 缓存机制验证

## 维护指南

### 添加新测试

1. 在适当的测试类中添加新方法
2. 使用 CAT-XXX 命名规则
3. 更新 conftest.py 中的测试识别逻辑
4. 更新本 README 文档

### 修改测试

1. 修改测试代码
2. 运行测试验证
3. 更新文档（如需要）

## 联系方式

如有问题，请联系项目负责人。
