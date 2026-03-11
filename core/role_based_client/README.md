# role_based_client 测试项目

## 概述

本项目为 `app/core/role_based_client.py` 的单元测试，全面测试基于角色的 OpenSearch 客户端管理功能。

## 测试规格

- **测试对象**: `app/core/role_based_client.py`
- **测试要件**: `docs/testing/core/role_based_client_tests.md`
- **覆盖率目标**: 75%
- **测试框架**: pytest
- **异步测试**: pytest-asyncio

## 测试统计

| 类别 | 数量 | 说明 |
|------|------|------|
| 正常系 | 18 | 验证正常功能路径 |
| 异常系 | 13 | 验证错误处理逻辑 |
| 安全测试 | 6 | 验证安全性和敏感信息保护 |
| **合计** | **37** | - |

## 快速开始

### 前置条件

确保已安装以下依赖：

```bash
pip install pytest pytest-asyncio pytest-mock pytest-cov
```

### 运行测试

```powershell
# 进入测试目录
cd C:\pythonProject\python_ai_cspm\TestReport\role_based_client\source

# 运行所有测试
pytest test_role_based_client.py -v

# 运行特定类别的测试
pytest test_role_based_client.py::TestOpenSearchRoles -v
pytest test_role_based_client.py::TestRoleBasedOpenSearchClient -v
pytest test_role_based_client.py::TestGlobalFunctions -v
pytest test_role_based_client.py::TestRoleBasedClientErrors -v
pytest test_role_based_client.py::TestRoleBasedClientSecurity -v

# 只运行安全测试
pytest test_role_based_client.py -m security -v

# 运行带覆盖率报告
pytest test_role_based_client.py --cov=app.core.role_based_client --cov-report=html --cov-report=term-missing -v
```

### 查看报告

测试完成后，报告会自动生成在 `reports` 目录：

- **Markdown 报告**: `reports/TestReport_role_based_client.md`
- **JSON 报告**: `reports/TestReport_role_based_client.json`
- **HTML 覆盖率报告**: `htmlcov/index.html` (如果使用了 --cov-report=html)

## 测试类别详解

### 正常系测试 (Normal Case Tests)

测试ID: RBC-001 ~ RBC-018

**主要测试内容:**
- ✅ 角色常量定义验证
- ✅ 角色环境变量映射完整性
- ✅ 客户端获取和缓存机制
- ✅ AWS/标准 OpenSearch 端口配置
- ✅ SSL 证书配置（AWS、自定义CA、开发环境）
- ✅ 重试机制
- ✅ 可用角色列表获取
- ✅ 健康检查功能
- ✅ 单例模式实现
- ✅ 便利函数功能
- ✅ 主机名验证配置

### 异常系测试 (Error Case Tests)

测试ID: RBC-E01 ~ RBC-E13

**主要测试内容:**
- ❌ 未知角色处理
- ❌ 认证信息缺失（用户名/密码）
- ❌ OpenSearch URL 配置错误
- ❌ 连接失败和重试耗尽
- ❌ 初始化错误跳过机制
- ❌ 健康检查各种错误状态

### 安全测试 (Security Tests)

测试ID: RBC-SEC-01 ~ RBC-SEC-06

**主要测试内容:**
- 🔒 密码不泄露到日志
- 🔒 SSL 始终启用
- 🔒 错误消息只包含环境变量名
- 🔒 健康检查错误不泄露密码 ⚠️ (预期失败)
- 🔒 Traceback 输出不包含认证信息
- 🔒 各角色认证信息隔离

## 测试特性

### 模块隔离机制

本测试使用特殊的模块重置机制确保测试间独立性：

```python
@pytest.fixture(autouse=True)
def reset_role_based_client_module():
    """每个测试后重置模块全局变量"""
    yield
    modules_to_remove = [key for key in sys.modules if key.startswith("app.core")]
    for mod in modules_to_remove:
        del sys.modules[mod]
```

这是因为 `role_based_client.py` 使用模块级单例模式，需要在测试间清除缓存。

### 外部依赖模拟

所有测试都使用模拟对象防止实际的 OpenSearch 连接：

```python
@pytest.fixture
def mock_async_opensearch():
    """模拟 AsyncOpenSearch 防止外部连接"""
    with patch("app.core.role_based_client.AsyncOpenSearch") as mock_cls:
        mock_instance = AsyncMock()
        mock_instance.ping = AsyncMock(return_value=True)
        mock_cls.return_value = mock_instance
        yield mock_cls, mock_instance
```

### 环境变量管理

测试使用完整的环境变量集合，包括所有5个角色的认证信息：

```python
MOCK_SETTINGS_ENV = {
    "OPENSEARCH_USER": "admin-user",
    "OPENSEARCH_PASSWORD": "admin-password-do-not-use",
    "CSPM_DASHBOARD_READ_USER": "cspm-read-user",
    "CSPM_DASHBOARD_READ_PASSWORD": "cspm-read-pass-do-not-use",
    # ... 其他角色 ...
}
```

## 自动报告生成

测试完成后，`conftest.py` 中的 pytest 钩子会自动生成详细报告：

### Markdown 报告格式

```markdown
# role_based_client.py 测试报告

## 测试概要
- 测试对象: app/core/role_based_client.py
- 执行时间: YYYY-MM-DD HH:MM:SS
- 覆盖率目标: 75%

## 测试结果统计
| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|---------|
| 正常系 | 18 | ... | ... | ... |
| 异常系 | 13 | ... | ... | ... |
| 安全测试 | 6 | ... | ... | ... |

## 测试通过率
- 实际通过率: XX.X%
- 有效通过率: XX.X%
```

### JSON 报告格式

```json
{
  "metadata": {
    "test_target": "app/core/role_based_client.py",
    "test_spec": "docs/testing/core/role_based_client_tests.md",
    "execution_time": "2026-02-03T...",
    "coverage_target": "75%"
  },
  "summary": {
    "total": 37,
    "passed": 36,
    "failed": 0,
    "xfailed": 1,
    "pass_rate": 97.3,
    "effective_pass_rate": 100.0
  },
  "results": {
    "normal": [...],
    "error": [...],
    "security": [...]
  }
}
```

## 预期失败测试

以下测试标记为预期失败（xfail），表示已知的实现问题：

| 测试ID | 问题描述 | 代码位置 | 建议修复 |
|--------|---------|---------|---------|
| RBC-SEC-04 | 健康检查错误消息可能泄露密码 | role_based_client.py:268 | 实现错误消息过滤/清理机制 |

这些测试在计算有效通过率时会被排除。

## 依赖项

### 必需依赖

```txt
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.0.0
pytest-cov>=4.0.0
```

### 测试环境

- Python 3.10+
- Windows PowerShell (测试脚本针对 Windows 优化)
- 项目根目录: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing`

## 注意事项

### 1. 异步测试配置

确保 `pytest.ini` 中包含异步测试配置：

```ini
[pytest]
asyncio_mode = auto
```

### 2. 模块导入路径

测试文件会自动添加项目根目录到 Python 路径：

```python
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
sys.path.insert(0, PROJECT_ROOT)
```

### 3. 环境变量优先级

- 测试使用 `patch.dict()` 设置临时环境变量
- 不会影响系统环境变量
- 每个测试后自动清理

### 4. 重试机制测试

涉及重试的测试会模拟 `asyncio.sleep` 以加快测试速度：

```python
with patch("asyncio.sleep", new_callable=AsyncMock):
    # 测试代码
```

### 5. 日志捕获

使用 `caplog` fixture 捕获日志输出进行验证：

```python
def test_example(self, caplog):
    with caplog.at_level(logging.DEBUG):
        # 测试代码
    assert "expected" in caplog.text
```

## 故障排查

### 测试失败：模块导入错误

**问题**: `ModuleNotFoundError: No module named 'app'`

**解决方案**: 
- 确认项目根目录路径正确
- 检查 `sys.path` 设置
- 确认测试从 `source` 目录运行

### 测试失败：环境变量相关

**问题**: 认证信息未设置错误

**解决方案**:
- 检查 `conftest.py` 中的 `MOCK_SETTINGS_ENV`
- 确认所有5个角色的认证信息都已配置
- 验证 `mock_settings_env` fixture 正在使用

### 测试超时

**问题**: 异步测试长时间无响应

**解决方案**:
- 确认 `asyncio.sleep` 已被模拟
- 检查是否有未模拟的外部调用
- 增加 pytest 超时设置: `pytest --timeout=300`

### 报告未生成

**问题**: 测试完成但报告文件不存在

**解决方案**:
- 确认 `reports` 目录存在
- 检查 `pytest_sessionfinish` 钩子是否被调用
- 查看测试输出中的错误消息

## 贡献指南

### 添加新测试

1. 在适当的测试类中添加测试方法
2. 使用描述性的测试名称（例如：`test_feature_name`）
3. 遵循 Arrange-Act-Assert 模式
4. 添加详细的中文注释
5. 在 `conftest.py` 的 `test_name_map` 中添加映射

### 测试命名规范

```python
def test_{功能描述}(self, fixtures):
    """
    {测试ID}: {测试名称}
    {测试描述}
    
    覆盖代码行: {源文件}:{行号}
    
    测试目的:
      - 验证点1
      - 验证点2
    """
    # Arrange - 准备测试数据
    
    # Act - 执行被测试函数
    
    # Assert - 验证结果
```

## 相关文档

- **源代码**: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing\app\core\role_based_client.py`
- **测试规格**: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing\docs\testing\core\role_based_client_tests.md`
- **pytest 配置**: `C:\pythonProject\python_ai_cspm\TestReport\pytest.ini`
- **环境变量**: `C:\pythonProject\python_ai_cspm\TestReport\.env`

## 联系方式

如有问题或建议，请联系开发团队。

---

**测试项目创建时间**: 2026-02-03  
**最后更新**: 2026-02-03  
**测试框架版本**: pytest 8.0+
