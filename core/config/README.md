# config 测试项目

## 概述

本项目为 `app/core/config.py` 的单元测试。

## 测试规格

- **测试要件**: `docs/testing/core/config_tests.md`
- **覆盖率目标**: 85%+
- **测试框架**: pytest

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 6 |
| 异常系 | 5 |
| 安全测试 | 0 |
| **合计** | **11** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\config\source
pytest test_config.py -v
```

### 生成覆盖率报告

```powershell
pytest test_config.py --cov=app.core.config --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_config.md`
- **JSON**: `reports/TestReport_config.json`

## 测试类别

### 正常系测试 (`TestSettings`)
- 验证Settings类的正常工作流程
- 覆盖配置加载和默认值应用
- 测试辅助函数is_aws_opensearch_service

**测试用例:**
- CFG-001: 环境变量から設定読み込み
- CFG-002: デフォルト値の適用
- CFG-003: OpenSearch URL生成
- CFG-004: AWS OpenSearch判定
- CFG-005: MIN_INTERVAL_SECONDS計算
- CFG-006: 設定インスタンス存在確認

### 异常系测试 (`TestSettingsErrors`)
- 验证错误处理逻辑
- 测试无效输入和边界条件

**测试用例:**
- CFG-E01: 必須設定の欠落
- CFG-E02: 無効な型 - RPM_LIMIT
- CFG-E03: 無効なOpenSearch URL形式
- CFG-E04: 無効なURL形式の処理
- CFG-E05: None URL の処理

### 集成测试 (`TestConfigIntegration`)
- 验证settings与辅助函数协同工作
- 验证配置项之间的关系

## 测试模块说明

### `config.py` 主要功能

| 功能 | 说明 |
|------|------|
| `Settings` 类 | Pydanticベースの設定管理クラス |
| 环境变量读取 | .envファイルからの自動読み込み |
| 必須設定検証 | Pydanticによる自動バリデーション |
| `is_aws_opensearch_service()` | AWS OpenSearch判定ヘルパー関数 |
| `MIN_INTERVAL_SECONDS` | RPM制限に基づく間隔計算 |

### 配置项分类

#### 必須設定
- GPT5系API キー (5種類)
- Claude 4.5系API キー (2種類)
- Gemini API キー
- DOCKER_BASE_URL
- EMBEDDING API キー
- OPENSEARCH_URL

#### オプション設定 (デフォルト値あり)
- MODEL_NAME (デフォルト: "gpt-5.1-chat")
- MINI_MODEL_NAME (デフォルト: "gpt-5-mini")
- RPM_LIMIT (デフォルト: 5)
- JWT設定
- LangGraph Storage設定

## 依赖项

```
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.14.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
```

## 注意事项

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文注释
3. ✅ 遵循 Arrange-Act-Assert 模式
4. ⚠️ 部分测试需要完整的环境变量配置(已标记为skip)
5. ⚠️ 测试会使用实际的.env文件,请确保配置正确

## 测试覆盖范围

### 已覆盖功能
- ✅ Settings类实例化
- ✅ 环境变量读取
- ✅ デフォルト値適用
- ✅ is_aws_opensearch_service函数
- ✅ MIN_INTERVAL_SECONDS計算
- ✅ 必須フィールド検証
- ✅ 型検証

### 未覆盖功能
- ⚠️ 完整的环境变量加载测试(需要完整配置)
- ⚠️ CA证书路径验证
- ⚠️ JWT设定的詳細なテスト

## 问题排查

### 常见错误

**错误1: ValidationError - 缺少必须字段**
```
原因: .env文件中缺少必须的API密钥
解决: 检查TestReport/.env文件,确保所有必须字段已配置
```

**错误2: 模块导入失败**
```
原因: 项目根目录路径不正确
解决: 确认platform_python_backend-testing目录位置正确
```

**错误3: 测试被跳过**
```
原因: 某些测试需要完整环境变量配置
解决: 这是正常的,跳过的测试已标记@pytest.mark.skip
```

## 测试报告示例

测试完成后会生成两种格式的报告:

1. **Markdown报告** (`reports/TestReport_config.md`)
   - 人类可读的格式化报告
   - 包含详细的统计和测试结果

2. **JSON报告** (`reports/TestReport_config.json`)
   - 机器可读的结构化数据
   - 便于自动化处理和集成

## 持续改进

### 待改进项
1. 增加更多的边界条件测试
2. 添加性能测试(配置加载时间)
3. 添加安全测试(敏感信息不泄露)
4. 增加配置验证规则的测试

### 已知限制
1. 某些测试依赖于实际的.env文件
2. 环境变量隔离在某些测试中较难实现
3. Pydantic的验证行为可能在版本间有差异

---

**项目创建时间**: 2026-02-02
**维护者**: AI Agent
**最后更新**: 2026-02-02
