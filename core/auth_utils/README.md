# auth_utils.py 测试说明

## 1. 测试目的

本测试套件针对 `app/core/auth_utils.py` 模块进行全面的单元测试，确保认证相关工具函数的正确性、安全性和稳定性。

### 1.1 为什么需要这些测试？

`auth_utils.py` 是 AI-CSPM 系统的核心认证工具模块，负责：

- **Basic认证令牌提取** - 从HTTP头中安全提取认证令牌
- **认证要求验证** - 验证并规范化认证信息
- **调试日志输出** - 安全地记录认证相关信息（不泄露敏感数据）

任何认证模块的缺陷都可能导致：
- 未授权访问
- 敏感信息泄露
- 安全日志被绕过

### 1.2 测试意义

| 测试类型 | 意义 |
|---------|------|
| 正常系测试 | 验证功能在预期输入下正确运行 |
| 异常系测试 | 验证错误处理机制的健壮性 |
| 安全测试 | 防止敏感信息泄露到日志中 |

---

## 2. 测试范围

### 2.1 正常系测试 (AUTIL-INIT, AUTIL-001 ~ AUTIL-011)

| ID | 测试内容 |
|----|---------|
| AUTIL-INIT | 模块导入成功 |
| AUTIL-001 | Basic认证令牌提取（有空格） |
| AUTIL-002 | Basic认证令牌提取（无空格） |
| AUTIL-003 | SHARED-HMAC认证头接受 |
| AUTIL-004 | 从Request对象获取头（小写） |
| AUTIL-005 | 从Request对象获取头（大写） |
| AUTIL-006 | 认证要求验证（有OpenSearch） |
| AUTIL-007 | 认证要求验证（无OpenSearch） |
| AUTIL-007-B | opensearch_auth参数默认值 |
| AUTIL-008 | 调试日志输出（两种认证都有） |
| AUTIL-009 | 调试日志输出（头过滤） |
| AUTIL-010 | 调试日志输出（无认证） |
| AUTIL-010-B | 无请求头的日志输出 |
| AUTIL-011 | DEBUG级别禁用时的日志 |

### 2.2 异常系测试 (AUTIL-E01 ~ AUTIL-E07)

| ID | 测试内容 |
|----|---------|
| AUTIL-E01 | 无认证头抛出HTTPException |
| AUTIL-E02 | 无效认证格式抛出HTTPException |
| AUTIL-E03 | 空字符串认证头抛出HTTPException |
| AUTIL-E04 | 无endpoint认证抛出HTTPException |
| AUTIL-E05 | 空endpoint认证抛出HTTPException |
| AUTIL-E06 | Request也获取失败抛出HTTPException |
| AUTIL-E07 | 小写basic前缀抛出HTTPException |

### 2.3 安全测试 (AUTIL-SEC-01 ~ AUTIL-SEC-05)

| ID | 测试内容 |
|----|---------|
| AUTIL-SEC-01 | 认证头不完全输出到日志 |
| AUTIL-SEC-02 | 错误消息不包含认证信息 |
| AUTIL-SEC-03 | x-auth-hash头被掩码 |
| AUTIL-SEC-04 | 空头值过滤安全性 |
| AUTIL-SEC-05 | 短认证头值过滤 |

---

## 3. 如何运行测试

### 3.1 环境准备

```bash
# 安装依赖
pip install pytest pytest-mock pytest-asyncio pytest-cov fastapi

# 确保 auth_utils.py 可被导入
set PYTHONPATH=C:\pythonProject\python_ai_cspm\platform_python_backend-testing
```

### 3.2 运行所有测试

```bash
cd C:\pythonProject\python_ai_cspm\TestReport\auth_utils\source
pytest test_auth_utils.py -v
```

### 3.3 运行特定类型测试

```bash
# 仅运行正常系测试
pytest test_auth_utils.py -k "not Error and not Security" -v

# 仅运行异常系测试
pytest test_auth_utils.py -k "Error" -v

# 仅运行安全测试
pytest test_auth_utils.py -m security -v
```

### 3.4 生成覆盖率报告

```bash
pytest test_auth_utils.py --cov=app.core.auth_utils --cov-report=term-missing --cov-report=html
```

### 3.5 生成测试报告

测试完成后，报告将自动生成在 `reports/` 目录：

- `TestReport_auth_utils.md` - Markdown 格式报告
- `TestReport_auth_utils.json` - JSON 格式报告（机器可读）

---

## 4. 目录结构

```
auth_utils/
├── README.md              # 本说明文件
├── source/
│   ├── conftest.py        # pytest fixtures
│   └── test_auth_utils.py # 测试源代码
└── reports/
    ├── TestReport_auth_utils.md    # Markdown 报告（测试后生成）
    └── TestReport_auth_utils.json  # JSON 报告（测试后生成）
```

---

## 5. 覆盖率目标

| 指标 | 目标 |
|------|------|
| 行覆盖率 | ≥ 90% |
| 分支覆盖率 | ≥ 85% |

---

## 6. 主要测试点

### 6.1 extract_basic_auth_token 函数

- ✅ Basic认证头提取（有/无空格）
- ✅ SHARED-HMAC认证头支持
- ✅ 从Request对象回退获取
- ✅ 无效格式错误处理
- ✅ 大小写敏感性验证

### 6.2 validate_auth_requirements 函数

- ✅ 认证令牌存在性验证
- ✅ OpenSearch认证可选性
- ✅ 缺失认证错误处理

### 6.3 log_auth_debug_info 函数

- ✅ 认证状态日志记录
- ✅ 敏感头信息掩码
- ✅ 日志级别控制
- ✅ 空值安全处理

---

## 7. 安全注意事项

### 7.1 日志掩码机制

认证头在日志中会被自动掩码：
- `authorization` 头：只显示前10个字符 + "..."
- `x-auth-hash` 头：只显示前10个字符 + "..."

### 7.2 错误消息安全

HTTPException 的错误消息**不包含**用户提交的认证信息，防止信息泄露。

---

## 8. 联系方式

如有问题，请联系项目负责人。
