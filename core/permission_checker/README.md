# permission_checker 测试项目

## 概述

本项目为 `app/core/permission_checker.py` 的单元测试。

permission_checker 模块提供 OpenSearch 动态权限检查功能，支持用户角色查询、权限验证和索引访问控制。

## 测试规格

- **测试要件**: `docs/testing/core/permission_checker_tests.md`
- **覆盖率目标**: 85%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 22 |
| 异常系 | 12 |
| 安全测试 | 6 |
| **合计** | **40** |

## 快速开始

### 前置条件

确保已安装以下依赖：

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock
```

### 运行测试

#### 运行所有测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\permission_checker\source
pytest test_permission_checker.py -v
```

#### 运行特定类别的测试

```powershell
# 运行正常系测试
pytest test_permission_checker.py -k "not Error and not Security" -v

# 运行异常系测试
pytest test_permission_checker.py -k "Error" -v

# 运行安全测试
pytest test_permission_checker.py -m security -v
```

#### 运行特定测试类

```powershell
# 初始化测试
pytest test_permission_checker.py::TestOpenSearchPermissionCheckerInit -v

# 用户信息获取测试
pytest test_permission_checker.py::TestGetUserInfo -v

# 权限检查测试
pytest test_permission_checker.py::TestCheckIndexAccessPermission -v

# 动作展开测试
pytest test_permission_checker.py::TestExpandGenericAction -v

# 安全测试
pytest test_permission_checker.py::TestPermissionSecurity -v
```

### 生成覆盖率报告

```powershell
# 生成终端报告
pytest test_permission_checker.py --cov=app.core.permission_checker --cov-report=term-missing -v

# 生成 HTML 报告
pytest test_permission_checker.py --cov=app.core.permission_checker --cov-report=html -v
```

HTML 报告将生成在 `htmlcov/index.html`。

### 查看报告

测试完成后，自动生成的报告位于：

- **Markdown 报告**: `reports/TestReport_permission_checker.md`
- **JSON 报告**: `reports/TestReport_permission_checker.json`

## 测试类别

### 正常系测试 (22个)

验证 permission_checker 模块的正常功能：

| 测试ID | 测试内容 |
|--------|---------|
| PERM-INIT | 管理员客户端初始化 |
| PERM-001 | 用户信息获取成功 |
| PERM-002 | 用户角色获取成功 |
| PERM-003 | 角色权限获取成功 |
| PERM-004 | 索引访问权限许可 |
| PERM-005 | 索引访问权限拒绝 |
| PERM-006 | 通用动作展开（read） |
| PERM-007 | 通用动作展开（write） |
| PERM-008 | 通用动作展开（通配符） |
| PERM-009 | 多索引一次检查 |
| PERM-010 | 可访问索引获取 |
| PERM-011 | 便利函数检查 |
| PERM-012 | 角色统合（去重） |
| PERM-013 | 通配符索引模式匹配 |
| PERM-014 | 多动作许可（crud） |
| PERM-006-B | 通用动作展开（manage） |
| PERM-006-C | 通用动作展开（index） |
| PERM-006-D | 通用动作展开（delete） |
| PERM-006-E | 通用动作展开（indices_all） |
| PERM-006-F | 通用动作展开（create_index） |
| PERM-006-G | fnmatch通配符模式匹配 |
| PERM-006-H | 不匹配动作 |

### 异常系测试 (12个)

验证错误处理和异常情况：

| 测试ID | 测试内容 |
|--------|---------|
| PERM-E01 | 不存在用户信息获取返回None |
| PERM-E02 | 用户信息获取API错误 |
| PERM-E03 | 不存在用户的角色获取 |
| PERM-E04 | 不存在角色的权限获取 |
| PERM-E05 | 角色权限获取API错误 |
| PERM-E06 | 角色检查错误时跳过继续 |
| PERM-E07 | 全角色检查失败 |
| PERM-E08 | 批量检查中部分角色错误 |
| PERM-E08-B | 批量检查中用户获取失败 |
| PERM-E09 | 用户角色获取失败 |
| PERM-E10 | 可访问索引获取用户错误 |
| PERM-E10-B | 部分角色错误时跳过继续 |

### 安全测试 (6个)

验证安全性和权限控制：

| 测试ID | 测试内容 |
|--------|---------|
| PERM-SEC-01 | 无权限用户访问拒绝 |
| PERM-SEC-02 | 通配符模式安全性 |
| PERM-SEC-03 | 角色提升攻击防止 |
| PERM-SEC-04 | 注入攻击耐性 |
| PERM-SEC-05 | 最小权限原则验证 |
| PERM-SEC-06 | 时间攻击耐性 |

## 测试覆盖的功能

### 核心类和异常

- `PermissionError`: 权限检查相关的自定义异常
- `OpenSearchPermissionChecker`: OpenSearch 权限检查器主类

### 主要方法

| 方法 | 功能 | 测试数 |
|------|------|--------|
| `__init__()` | 初始化权限检查器 | 1 |
| `get_user_info()` | 获取用户详细信息 | 3 |
| `get_user_roles()` | 获取用户角色列表 | 3 |
| `get_role_permissions()` | 获取角色权限信息 | 3 |
| `check_index_access_permission()` | 检查索引访问权限 | 10 |
| `_expand_generic_action()` | 展开通用动作 | 9 |
| `_check_role_index_access()` | 角色级索引访问检查 | - |
| `_check_role_index_access_sync()` | 同步角色级索引访问检查 | - |
| `check_multiple_index_access()` | 批量检查多个索引 | 3 |
| `get_user_accessible_indices()` | 获取可访问索引模式 | 3 |
| `check_user_index_access()` | 便利函数 | 1 |

## 依赖项

```txt
pytest>=8.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
opensearchpy>=2.0.0
```

## 项目结构

```
C:\pythonProject\python_ai_cspm\TestReport\permission_checker\
├── README.md                          # 本文件
├── 测试完成总结.md                     # 测试完成总结（测试后生成）
├── source\
│   ├── conftest.py                    # pytest配置和钩子
│   └── test_permission_checker.py     # 测试源代码
└── reports\
    ├── TestReport_permission_checker.md    # Markdown测试报告（测试后生成）
    └── TestReport_permission_checker.json  # JSON测试报告（测试后生成）
```

## 测试设计原则

### Arrange-Act-Assert 模式

所有测试遵循 AAA 模式：

```python
def test_example(self, mock_admin_client):
    """测试说明"""
    # Arrange - 准备测试数据
    checker = OpenSearchPermissionChecker(mock_admin_client)
    
    # Act - 执行被测试函数
    result = await checker.some_method()
    
    # Assert - 验证结果
    assert result == expected_value
```

### 路径基于的模拟（Path-based Mocking）

为了避免角色顺序依赖问题，使用路径基于的模拟策略：

```python
async def path_based_side_effect(method, path, **kwargs):
    if "internalusers/test_user" in path:
        return {"test_user": user_info}
    elif "roles/role1" in path:
        return {"role1": role1_permissions}
    elif "roles/role2" in path:
        return {"role2": role2_permissions}
    return {}

mock_admin_client.transport.perform_request = AsyncMock(side_effect=path_based_side_effect)
```

这种方法确保测试不受 `get_user_roles()` 返回角色顺序的影响。

### 异步测试

所有异步方法使用 `@pytest.mark.asyncio` 装饰器：

```python
@pytest.mark.asyncio
async def test_async_method(self):
    result = await async_function()
    assert result is not None
```

### 安全测试标记

安全测试使用 `@pytest.mark.security` 标记，可单独运行：

```python
@pytest.mark.security
class TestPermissionSecurity:
    """安全测试类"""
    pass
```

## 注意事项

### OpenSearch Security API 模拟

1. ✅ 所有测试使用模拟的 AsyncOpenSearch 客户端
2. ✅ 不需要实际的 OpenSearch 实例
3. ✅ API 调用通过 `mock_admin_client.transport.perform_request` 模拟

### 角色顺序问题

- `get_user_roles()` 返回的角色列表顺序是不确定的（使用 `list(set(...))`）
- 测试使用路径基于模拟避免顺序依赖
- 不要使用 `side_effect` 列表假设固定调用顺序

### 通配符模式安全性

- `*` 模式会匹配所有索引（包括系统索引如 `.security`）
- 生产环境应在 OpenSearch 配置中排除系统索引
- 测试 PERM-SEC-02 验证了这一行为

### 最小权限原则

- 测试验证只授予必要的最小权限
- 只有 read 权限的角色不能执行 write 操作
- 角色权限严格按配置执行

## 故障排除

### 测试失败：找不到模块

```powershell
# 确保项目根目录在 Python 路径中
$env:PYTHONPATH="C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
pytest test_permission_checker.py -v
```

### 异步测试错误

确保安装了 pytest-asyncio：

```powershell
pip install pytest-asyncio
```

### 报告未生成

报告通过 `conftest.py` 中的 pytest 钩子自动生成。确保：

1. ✅ `conftest.py` 在同一目录下
2. ✅ 测试正常执行完成
3. ✅ `reports/` 目录存在

## 相关文档

- **源代码**: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing\app\core\permission_checker.py`
- **测试规格**: `C:\pythonProject\python_ai_cspm\platform_python_backend-testing\docs\testing\core\permission_checker_tests.md`
- **pytest 配置**: `C:\pythonProject\python_ai_cspm\TestReport\pytest.ini`

## 联系方式

如有问题或建议，请联系开发团队。

---

**创建日期**: 2026-02-03  
**最后更新**: 2026-02-03  
**测试框架**: pytest 8.0+  
**Python 版本**: 3.9+
