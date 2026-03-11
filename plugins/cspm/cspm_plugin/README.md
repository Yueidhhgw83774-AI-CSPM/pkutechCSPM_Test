# CSPM Plugin Router 测试项目

## 概述

本项目为 `app/cspm_plugin/router.py` 的单元测试。

## 测试规格

- **测试要件**: `docs/testing/plugins/cspm/cspm_plugin_tests.md`
- **覆盖率目标**: 90%+
- **测试框架**: pytest + pytest-asyncio

## 测试统计

| 类别 | 数量 |
|------|------|
| 正常系 | 11 |
| 异常系 | 11 |
| 安全测试 | 4 |
| **合计** | **26** |

## 快速开始

### 运行测试

```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\cspm\cspm_plugin\source
pytest test_cspm_plugin_router.py -v
```

### 生成覆盖率报告

```powershell
pytest test_cspm_plugin_router.py --cov=app.cspm_plugin.router --cov-report=html
```

### 查看报告

- **Markdown**: `reports/TestReport_cspm_plugin_router.md`
- **JSON**: `reports/TestReport_cspm_plugin_router.json`

## 测试类别

### 正常系测试 (TestRefineEndpoint, TestAgentEndpoint, TestValidateEndpoint)
- **CSPM-001 ~ CSPM-011**: 验证三个端点的正常工作流程
- `/cspm/chat/refine`: ポリシー修正チャット
- `/cspm/chat/agent`: ポリシー生成エージェント（LangGraph）
- `/cspm/validate_policy_with_tool`: ポリシー検証

### 異常系テスト (TestRefineEndpointErrors, TestAgentEndpointErrors, TestValidateEndpointErrors)
- **CSPM-E01 ~ CSPM-E11**: 验证错误处理逻辑
- バリデーションエラー（422）
- HTTPException 伝播
- 予期しない例外（500 + Error ID）

### セキュリティテスト (TestCSPMRouterSecurity)
- **CSPM-SEC-01 ~ CSPM-SEC-04**: 验证安全性
- Error ID でスタックトレース非露出
- インジェクション防止
- 大容量データ処理

## エンドポイント一覧

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/cspm/chat/refine` | POST | ポリシー修正チャット |
| `/cspm/chat/agent` | POST | ポリシー生成エージェント（AWS/Azure/GCP） |
| `/cspm/validate_policy_with_tool` | POST | ポリシー検証（レガシー） |

## 依赖项

```
pytest>=8.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
httpx>=0.24.0
python-dotenv>=1.0.0
```

## 注意事项

1. ✅ 测试执行后自动生成报告
2. ✅ 所有测试包含详细的中文/日文注释
3. ✅ Mock 掉所有外部依赖（LLM、LangGraph、subprocess）
4. ⚠️ **CSPM-SEC-02 は xfail**: `router.py:105` で `str(e)` が直接レスポンスに含まれる既知の脆弱性

## 既知の問題

| テストID | 問題 | 修正方針 |
|---------|-----|---------|
| CSPM-SEC-02 | `policy_agent_endpoint` のエラーレスポンスに `str(e)` が含まれ、内部情報が露出 | Error ID のみを返すように実装修正 |

## 環境設定

テストは `.env` ファイルから `soure_root` を読み取ります：

```dotenv
soure_root="C:\pythonProject\python_ai_cspm\platform_python_backend-testing\"
```

## セキュリティ推奨事項

1. **リクエストサイズ制限**: nginx 等で 1MB 程度に制限
2. **レート制限**: リバースプロキシで設定
3. **エラーメッセージ**: Error ID のみを返し、内部詳細を露出しない
4. **YAML インジェクション**: Cloud Custodian パーサーのバリデーション強化

---

*テスト生成日: 2026-03-11*
*テスト規格: cspm_plugin_tests.md*

