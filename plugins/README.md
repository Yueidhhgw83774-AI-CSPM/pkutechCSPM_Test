# Plugins 模块测试

**目录**: `TestReport/plugins/`  
**模块数**: 1

---

## 📦 已完成的测试模块

1. **auth** - `plugins/auth/`

---

## 📂 目录结构

```
plugins/
├── auth/
│   ├── source/
│   │   ├── conftest.py
│   │   └── test_auth.py
│   ├── reports/
│   │   ├── TestReport_auth.md
│   │   └── TestReport_auth.json
│   └── README.md
```

---

## 🚀 运行测试

### 运行所有模块测试
```bash
cd C:\pythonProject\python_ai_cspm\TestReport\plugins
pytest */source/test_*.py -v
```

### 运行单个模块测试
```bash
cd plugins/[module_name]/source
pytest test_[module_name].py -v
```

---

## 📊 测试统计

| 模块 | 测试数 | 覆盖率 | 状态 |
|------|--------|--------|------|
| auth | - | >90% | ✅ |

---

**创建日期**: 2026-03-10  
**总模块数**: 1  
**完成状态**: ✅ 全部完成
