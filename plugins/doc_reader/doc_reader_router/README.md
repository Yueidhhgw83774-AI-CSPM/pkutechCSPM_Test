# Doc Reader Router 测试项目

## ✅ 状态: 完成 (24 tests)

## 概述
测试 `app/doc_reader_plugin/router.py` 的 API 路由端点。

## 测试规格
- **测试要件**: `docs/testing/plugins/doc_reader/doc_reader_router_tests.md`
- **测试数量**: 24 (正常系:8, 異常系:11, セキュリティ:5)
- **覆盖率目标**: 90%+

## 主要功能
1. **/docreader/chat/structure** - テキスト構造化エンドポイント
2. **/docreader/chat** - チャット応答生成エンドポイント

## 测试统计

| 类别 | 数量 | ID範囲 |
|------|------|--------|
| 正常系 | 8 | DOCR-001 ~ DOCR-008 |
| 異常系 | 11 | DOCR-E01 ~ DOCR-E11 |
| セキュリティ | 5 | DOCR-SEC-01 ~ DOCR-SEC-05 |
| **合計** | **24** | |

## 快速开始

### 运行测试
```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader\doc_reader_router\source
pytest test_doc_reader_router.py -v
```

### 查看报告
- **Markdown**: `../reports/TestReport_doc_reader_router.md`
- **JSON**: `../reports/TestReport_doc_reader_router.json`

## 测试类别

### 正常系 (8 tests)
- 構造化成功/失敗
- 日本語テキスト
- 空白処理
- チャット正常応答
- ドキュメント/クラウドコンテキスト指定

### 異常系 (11 tests)
- 空プロンプト
- 欠落パラメータ
- HTTPException再スロー
- 予期せぬ例外処理

### セキュリティ (5 tests)
- SQLインジェクション防止
- XSS防止
- session_id検証
- 大きなペイロード処理

## 依赖项
```
pytest>=8.0.0
httpx>=0.27.0
fastapi>=0.100.0
```

---
*生成日: 2026-03-11*
*状態: ✅ 生産就緒*

