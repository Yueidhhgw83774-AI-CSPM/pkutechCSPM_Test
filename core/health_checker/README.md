# health_checker 测试项目

## 概述

本项目为 `app/core/health_checker.py` 的单元测试。

## 测试规格

- **测试要件**: `docs/testing/core/health_checker_tests.md`
- **覆盖率目标**: 90%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 20 |
| 异常系 | 20 |
| 安全测试 | 5 |
| **合计** | **45** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\health_checker\source
pytest test_health_checker.py -v
```

### 生成覆盖率报告

```powershell
pytest test_health_checker.py --cov=app.core.health_checker --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_health_checker.md`
- **JSON**: `reports/TestReport_health_checker.json`

## 测试类别

### 正常系测试
- `TestHealthCheckerInit`: HealthChecker类初始化测试
- `TestCheckHealth`: 包括健康检查执行测试
- `TestCheckDependencies`: 依赖关系检查测试
- `TestCheckAWSSDK`: AWS SDK检查测试
- `TestCheckAzureSDK`: Azure SDK检查测试
- `TestCheckCustodian`: Cloud Custodian检查测试
- `TestCheckOpenSearch`: OpenSearch检查测试
- `TestGetMemoryUsage`: 内存使用量获取测试
- `TestGetActiveJobs`: 活跃作业数获取测试
- `TestDetermineOverallStatus`: 整体状态判定测试

### 异常系测试
- `TestCheckHealthErrors`: check_health异常处理测试
- `TestCheckDependenciesErrors`: 依赖检查异常处理测试
- `TestCheckAWSSDKErrors`: AWS SDK检查异常处理测试
- `TestCheckAzureSDKErrors`: Azure SDK检查异常处理测试
- `TestCheckCustodianErrors`: Custodian检查异常处理测试
- `TestCheckOpenSearchErrors`: OpenSearch检查异常处理测试
- `TestGetMemoryUsageErrors`: 内存获取异常处理测试
- `TestGetActiveJobsErrors`: 活跃作业数获取异常处理测试

### 安全测试
- `TestHealthCheckerSecurity`: 安全性验证测试
  - 敏感信息不泄露
  - 错误消息安全性
  - 超时限制
  - 并发安全性

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.0.0
pytest-asyncio>=0.21.0
psutil>=5.9.0
```

## 环境变量

测试需要以下环境变量(在 `.env` 文件中配置):

```env
OPENSEARCH_URL=https://172.19.75.181:9200/
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
AWS_REGION=us-east-1
```

## 注意事项

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ✅ 使用async/await模式进行异步测试
5. ⚠️ 需要正确配置OpenSearch连接信息
6. ⚠️ 某些测试需要mock subprocess调用

## 已知限制

- Azure SDK和Custodian检查依赖于外部venv环境(`/opt/venv-c7n`)
- OpenSearch连接测试需要实际的OpenSearch实例运行
- 内存和活跃作业数测试依赖于系统状态

## 测试覆盖的功能

### HealthChecker类
- ✅ 初始化和start_time设置
- ✅ check_health() - 包括健康检查
- ✅ _check_dependencies() - 依赖关系检查
- ✅ _check_aws_sdk() - AWS SDK可用性检查
- ✅ _check_azure_sdk() - Azure SDK可用性检查
- ✅ _check_custodian() - Cloud Custodian可用性检查
- ✅ _check_opensearch() - OpenSearch连接检查
- ✅ _get_memory_usage() - 内存使用量获取
- ✅ _get_active_jobs() - 活跃作业数获取
- ✅ _determine_overall_status() - 整体状态判定

### 健康状态模型
- ✅ HealthStatus枚举(HEALTHY, DEGRADED, UNHEALTHY)
- ✅ DependencyStatus枚举(AVAILABLE, UNAVAILABLE)
- ✅ HealthResponse数据模型
- ✅ HealthErrorResponse数据模型

## 报告格式

### Markdown报告示例
```markdown
# health_checker.py 测试报告

## 测试概要
- 测试对象: app/core/health_checker.py
- 执行时间: 2026-02-02 17:30:00
- 总测试数: 45

## 测试结果
- ✅ 正常系: 20/20 通过
- ✅ 异常系: 20/20 通过
- ✅ 安全测试: 5/5 通过
```

### JSON报告结构
```json
{
  "summary": {
    "total": 45,
    "passed": 45,
    "failed": 0,
    "pass_rate": "100.0%"
  },
  "categories": {
    "normal": {...},
    "error": {...},
    "security": {...}
  }
}
```

## 维护指南

### 添加新测试
1. 在相应的测试类中添加测试方法
2. 遵循命名约定: `test_<功能>_<场景>`
3. 添加详细的docstring说明
4. 更新conftest.py中的name_map

### 更新测试
1. 检查源代码变更
2. 更新相关测试用例
3. 运行全部测试验证
4. 更新文档

### 调试测试
```powershell
# 运行单个测试
pytest test_health_checker.py::TestCheckHealth::test_check_health_all_healthy -v

# 显示详细输出
pytest test_health_checker.py -v -s

# 仅运行失败的测试
pytest test_health_checker.py --lf
```

## 联系方式

如有问题或建议,请联系开发团队。
