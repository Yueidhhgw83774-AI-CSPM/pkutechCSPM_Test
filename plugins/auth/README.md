# auth 测试项目

## 概述

本项目为认证模块的单元测试，覆盖以下文件：

| 文件 | 说明 |
|------|------|
| `app/core/auth.py` | 认证核心逻辑（JWT生成、密码验证、RBAC） |
| `app/auth/router.py` | 认证API端点 |
| `app/models/auth.py` | 认证数据模型 |

## 测试规格

- **测试要件**: `docs/testing/plugins/auth_tests.md`
- **覆盖率目标**: 90%+
- **测试框架**: pytest + pytest-asyncio

## 测试统计

| 类别 | 数量 | ID范围 |
|------|------|--------|
| 正常系 | 12 | AUTH-001 ~ AUTH-012 |
| 异常系 | 18 | AUTH-E01 ~ AUTH-E18 |
| 安全测试 | 8 | AUTH-SEC-01 ~ AUTH-SEC-08 |
| **合计** | **38** | - |

## 快速开始

### 运行测试

```powershell
# 进入测试目录
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\auth\source

# 运行所有测试
pytest test_auth.py -v

# 只运行正常系测试
pytest test_auth.py -k "not Error and not Security" -v

# 只运行安全测试
pytest test_auth.py -m security -v
```

### 生成覆盖率报告

```powershell
pytest test_auth.py --cov=app.core.auth --cov=app.auth.router --cov-report=html -v
```

### 查看报告

- **Markdown**: `reports/TestReport_auth.md`
- **JSON**: `reports/TestReport_auth.json`

## 测试类别

### 正常系测试

| 类名 | 测试ID | 说明 |
|------|--------|------|
| `TestAuthEndpoints` | AUTH-001~003 | 认证端点测试 |
| `TestAuthCoreLogic` | AUTH-004~008 | 核心逻辑测试 |
| `TestTokenCreation` | AUTH-009~012 | Token生成测试 |

### 异常系测试

| 类名 | 测试ID | 说明 |
|------|--------|------|
| `TestAuthEndpointErrors` | AUTH-E01~E07 | 端点错误测试 |
| `TestAuthCoreLogicErrors` | AUTH-E08~E13 | 核心逻辑错误测试 |
| `TestGetCurrentUserWithRolesErrors` | AUTH-E15~E18 | 角色获取错误测试 |
| `TestRBACErrors` | AUTH-E14 | RBAC错误测试 |

### 安全测试

| 类名 | 测试ID | 说明 |
|------|--------|------|
| `TestAuthSecurity` | AUTH-SEC-01~08 | 认证安全测试 |

## 主要测试内容

### 1. 密码安全 (AUTH-004, AUTH-005, AUTH-SEC-01)
- bcrypt哈希验证
- 密码哈希化
- 密码不泄露检查

### 2. JWT Token (AUTH-009~012, AUTH-SEC-02~07)
- Token生成（有/无有效期指定）
- 角色Token生成
- 过期Token拒绝
- 篡改Token检测
- alg=none攻击防御

### 3. 用户认证 (AUTH-001~003, AUTH-E01~E06)
- 登录成功/失败
- 用户信息获取
- 禁用用户处理

### 4. RBAC (AUTH-E07, AUTH-E14, AUTH-SEC-08)
- 角色权限检查
- 权限不足处理
- 角色提权防止

## 已知问题

### ⚠️ 安全漏洞: 角色提权

**位置**: `app/core/auth.py:163`

**问题**: 当前实现会合并JWT中的roles和DB中的roles:
```python
combined_roles = list(set(token_data.roles + user.roles))
```

这允许攻击者在JWT中注入任意角色。

**修复建议**: 只使用DB中的roles:
```python
return UserWithRoles(..., roles=user.roles)
```

## 依赖项

```
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.0.0
httpx>=0.27.0
python-jose>=3.3.0
passlib>=1.7.4
bcrypt>=4.0.0
python-dotenv>=1.0.0
pycryptodome>=3.19.0  # jose需要的加密库
python-multipart>=0.0.6  # FastAPI表单数据处理
```

**安装命令**:
```bash
pip install pytest pytest-asyncio pytest-cov httpx python-jose passlib bcrypt python-dotenv pycryptodome python-multipart
```

## 环境变量

测试使用 `TestReport/.env` 中的配置：

| 变量 | 说明 |
|------|------|
| `JWT_SECRET_KEY` | JWT签名密钥（测试中验证默认值行为） |
| `OPENSEARCH_URL` | OpenSearch地址 |

## 注意事项

1. ✅ 测试执行后自动生成报告到 `reports/` 目录
2. ✅ 所有测试包含详细的中文注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ⚠️ AUTH-SEC-08 测试标记为 xfail（预期失败），用于暴露安全漏洞
5. ℹ️ 需要 FastAPI 应用的 `app.main:app` 可导入

## 目录结构

```
C:\pythonProject\python_ai_cspm\TestReport\plugins\auth\
├── README.md                    # 本文件
├── 测试完成总结.md               # 测试完成后的总结
├── source\
│   ├── conftest.py             # pytest配置和夹具
│   └── test_auth.py            # 测试源代码 (38个测试)
└── reports\
    ├── TestReport_auth.md      # Markdown测试报告
    └── TestReport_auth.json    # JSON测试报告
```
