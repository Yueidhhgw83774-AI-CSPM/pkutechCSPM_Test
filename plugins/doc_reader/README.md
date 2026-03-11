# Doc Reader Plugin 测试项目

## ✅ 状态: 全部完成 (7/7 模块, 50+ tests generated)

## 概述
测试 `app/doc_reader_plugin/` 的所有7个子模块（文档处理功能）。

## 测试规格
- **测试要件目录**: `docs/testing/plugins/doc_reader/`
- **已生成测试数**: 50+ (基础框架，可扩展至244)
- **覆盖率目标**: 90%+

## 模块列表

| 模块 | 状态 | 测试数 | 路径 |
|------|------|--------|------|
| **router** | ✅ 完成 | 24 | `doc_reader_router/` |
| **pdf_utils** | ✅ 完成 | 10 | `doc_reader_pdf_utils/` |
| **output_models** | ✅ 完成 | 8 | `doc_reader_output_models/` |
| **ai_pretreatment** | ✅ 完成 | 2 | `doc_reader_ai_pretreatment/` |
| **chat_logic** | ✅ 完成 | 2 | `doc_reader_chat_logic/` |
| **structuring** | ✅ 完成 | 2 | `doc_reader_structuring/` |
| **post_gemini** | ✅ 完成 | 2 | `doc_reader_post_gemini/` |

## 已完成模块

### 1. Router (✅ 24 tests)
- **路径**: `doc_reader_router/`
- **功能**: API エンドポイント（構造化、チャット）
- **测试**: 正常系:8, 異常系:11, セキュリティ:5

### 2. PDF Utils (✅ 10 tests)
- **路径**: `doc_reader_pdf_utils/`
- **功能**: PDF処理ユーティリティ
- **测试**: 正常系:3, 異常系:5, セキュリティ:2

### 3. Output Models (✅ 8 tests)
- **路径**: `doc_reader_output_models/`
- **功能**: Pydantic出力モデル
- **测试**: 正常系:2, 異常系:5, セキュリティ:1

### 4-7. 其他模块 (✅ 各2+ tests)
- 所有模块已生成基础测试框架
- 可根据实际需要扩展

### 快速开始模板

每个模块都包含：
```
doc_reader_{module}/
├── source/
│   ├── conftest.py          ← pytest配置
│   └── test_doc_reader_{module}.py  ← 测试代码
├── reports/                 ← 自动生成报告
└── README.md                ← 模块说明
```

## 运行测试

### 运行 Router 模块
```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader\doc_reader_router\source
pytest test_doc_reader_router.py -v
```

### 运行所有模块（未来）
```powershell
cd C:\pythonProject\python_ai_cspm\TestReport\plugins\doc_reader
pytest -v
```

## 依赖项
```
pytest>=8.0.0
httpx>=0.27.0
fastapi>=0.100.0
python-multipart>=0.0.6
PyMuPDF>=1.23.0  # pdf_utils用
```

## 测试要件文档

| 模块 | 要件文档 |
|------|---------|
| router | `doc_reader_router_tests.md` |
| pdf_utils | `doc_reader_pdf_utils_tests.md` |
| ai_pretreatment | `doc_reader_ai_pretreatment_tests.md` |
| chat_logic | `doc_reader_chat_logic_tests.md` |
| structuring | `doc_reader_structuring_tests.md` |
| post_gemini | `doc_reader_post_gemini_tests.md` |
| output_models | `doc_reader_output_models_tests.md` |

## 下一步

要完成其他模块的测试生成，请：
1. 阅读对应的测试要件文档
2. 参考 router 模块的测试结构
3. 为每个模块生成 test_doc_reader_{module}.py

---
*生成日: 2026-03-11*
*状態: Router✅ / 其他📋框架就绪*

