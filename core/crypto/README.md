# crypto.py 测试说明

## 1. 测试目的

本测试套件针对 `app/core/crypto.py` 模块进行全面的单元测试，确保加密解密功能的正确性、安全性和稳定性。

### 1.1 为什么需要这些测试？

`crypto.py` 是 AI-CSPM 系统的核心安全模块，负责：

- **环境变量加密密钥管理** - 保护敏感配置信息
- **密码哈希验证** - 用户认证的基础
- **数据加密/解密** - 保护传输和存储中的敏感数据

任何加密模块的缺陷都可能导致：
- 敏感数据泄露
- 认证绕过
- 时序攻击等安全漏洞

### 1.2 测试意义

| 测试类型 | 意义 |
|---------|------|
| 正常系测试 | 验证功能在预期输入下正确运行 |
| 异常系测试 | 验证错误处理机制的健壮性 |
| 安全测试 | 发现潜在的安全漏洞 |

---

## 2. 测试范围

### 2.1 正常系测试 (CRYPTO-001 ~ CRYPTO-010)

| ID | 测试内容 |
|----|---------|
| CRYPTO-001 | 环境变量密钥加载 |
| CRYPTO-002 | 默认密钥回退机制 |
| CRYPTO-003 | 密码哈希生成 |
| CRYPTO-004 | 哈希验证成功 |
| CRYPTO-005 | 密钥长度填充（短密钥 → 32字节） |
| CRYPTO-006 | 密钥长度截断（长密钥 → 32字节） |
| CRYPTO-007 | 文本加密 |
| CRYPTO-008 | 文本解密 |
| CRYPTO-009 | 加密-解密往返测试 |
| CRYPTO-010 | 二进制数据加密解密 |

### 2.2 异常系测试 (CRYPTO-E01 ~ CRYPTO-E13)

| ID | 测试内容 |
|----|---------|
| CRYPTO-E01 | 空密钥处理 |
| CRYPTO-E02 | 无效密钥类型 |
| CRYPTO-E03 | 空数据加密 |
| CRYPTO-E04 | None数据处理 |
| CRYPTO-E05 | 无效密文解密 |
| CRYPTO-E06 | 无效Base64解密 |
| CRYPTO-E07 | 错误密钥解密 |
| CRYPTO-E08 | 损坏的IV解密 |
| CRYPTO-E09 | 损坏的密文解密 |
| CRYPTO-E10 | 空密码哈希验证 |
| CRYPTO-E11 | 无效哈希格式 |
| CRYPTO-E12 | 极长数据处理 |
| CRYPTO-E13 | 特殊字符处理 |

### 2.3 安全测试 (CRYPTO-SEC-01 ~ CRYPTO-SEC-06)

| ID | 测试内容 | 预期结果 |
|----|---------|---------|
| CRYPTO-SEC-01 | 时序攻击防护 | ⚠️ 预期失败（当前使用 `==` 比较） |
| CRYPTO-SEC-02 | IV唯一性验证 | 应通过 |
| CRYPTO-SEC-03 | 错误信息不泄露敏感数据 | ⚠️ 预期失败（`str(e)` 泄露详情） |
| CRYPTO-SEC-04 | 密钥内存清理 | 应通过 |
| CRYPTO-SEC-05 | 加密输出随机性 | 应通过 |
| CRYPTO-SEC-06 | 解密错误信息一致性 | ⚠️ 预期失败（错误详情泄露） |

---

## 3. 如何运行测试

### 3.1 环境准备

```bash
# 安装依赖
pip install pytest pytest-mock pytest-asyncio pytest-cov

# 确保 crypto.py 可被导入
# 如果需要，设置 PYTHONPATH
set PYTHONPATH=C:\pythonProject\python_ai_cspm\platform_python_backend-testing
```

### 3.2 运行所有测试

```bash
cd C:\pythonProject\python_ai_cspm\TestReport\crypto\source
pytest test_crypto.py -v
```

### 3.3 运行特定类型测试

```bash
# 仅运行正常系测试
pytest test_crypto.py -v -m normal

# 仅运行异常系测试
pytest test_crypto.py -v -m error

# 仅运行安全测试
pytest test_crypto.py -v -m security
```

### 3.4 生成覆盖率报告

```bash
pytest test_crypto.py --cov=app.core.crypto --cov-report=term-missing --cov-report=html
```

### 3.5 生成测试报告

测试完成后，报告将自动生成在 `reports/` 目录：

- `TestReport_crypto.md` - Markdown 格式报告
- `TestReport_crypto.json` - JSON 格式报告（机器可读）

---

## 4. 目录结构

```
crypto/
├── README.md              # 本说明文件
├── source/
│   ├── conftest.py        # pytest fixtures
│   └── test_crypto.py     # 测试源代码
└── reports/
    ├── TestReport_crypto.md    # Markdown 报告（测试后生成）
    └── TestReport_crypto.json  # JSON 报告（测试后生成）
```

---

## 5. 预期失败的测试说明

以下测试被标记为 `xfail`（预期失败），这是因为当前 `crypto.py` 实现存在已知的安全问题：

### CRYPTO-SEC-01: 时序攻击风险
- **问题位置**: `crypto.py:98` 的 `verify_auth_hash` 函数
- **问题描述**: 使用 `==` 进行字符串比较，比较时间与字符串匹配长度相关
- **建议修复**: 使用 `hmac.compare_digest()` 进行常数时间比较

### CRYPTO-SEC-03 & CRYPTO-SEC-06: 错误信息泄露
- **问题位置**: `crypto.py:165` 的异常处理
- **问题描述**: `str(e)` 可能泄露内部实现细节（如 padding 长度）
- **建议修复**: 返回统一的通用错误信息

---

## 6. 覆盖率目标

| 指标 | 目标 |
|------|------|
| 行覆盖率 | ≥ 90% |
| 分支覆盖率 | ≥ 85% |

---

## 7. 联系方式

如有问题，请联系项目负责人。
