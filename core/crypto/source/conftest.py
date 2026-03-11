# -*- coding: utf-8 -*-
"""
pytest fixtures for crypto module tests.
crypto 模块测试的 pytest fixtures。

This module provides shared fixtures for testing the crypto module,
including environment setup, mock objects, and test data.
本模块提供用于测试 crypto 模块的共享 fixtures，
包括环境设置、模拟对象和测试数据。
"""

import os
import sys
import base64
import json
import hashlib
import pytest
from unittest.mock import patch
from typing import Generator

# Add the project root to Python path for imports
# 将项目根目录添加到 Python 路径以便导入
PROJECT_ROOT = r"C:\pythonProject\python_ai_cspm\platform_python_backend-testing"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# =============================================================================
# Shared Secret Fixtures | 共享密钥相关 Fixtures
# =============================================================================

@pytest.fixture
def test_shared_secret() -> bytes:
    """
    Provide a test shared secret key.
    提供测试用的共享秘密密钥。
    """
    return b"test_shared_secret_for_hmac"


@pytest.fixture
def test_shared_secret_32() -> bytes:
    """
    Provide a 32-byte test shared secret key for AES operations.
    提供用于 AES 操作的 32 字节测试共享秘密密钥。
    """
    return b"test_shared_secret_key_123456789"


@pytest.fixture
def mock_env_shared_secret():
    """
    Mock environment variable SHARED_SECRET.
    模拟环境变量 SHARED_SECRET。
    """
    with patch.dict(os.environ, {"SHARED_SECRET": "env_secret_key"}):
        yield "env_secret_key"


@pytest.fixture
def mock_secret_file(tmp_path):
    """
    Create a mock secret file.
    创建模拟的秘密密钥文件。
    """
    secret_file = tmp_path / "shared_secret"
    secret_file.write_bytes(b"file_secret_key_12345")
    return str(secret_file)


# =============================================================================
# Encrypted Payload Fixtures | 加密载荷相关 Fixtures
# =============================================================================

@pytest.fixture
def encrypted_payload(test_shared_secret_32):
    """
    Provide a test encrypted payload with IV.
    提供带 IV 的测试加密载荷。
    """
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend

    # Test plaintext JSON | 测试用明文 JSON
    plaintext = '{"session_id": "test_123", "prompt": "テストメッセージ"}'

    # Generate key | 生成密钥
    key = hashlib.sha256(test_shared_secret_32).digest()

    # Generate IV | 生成 IV
    iv = os.urandom(16)

    # Add padding | 添加填充
    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode('utf-8')) + padder.finalize()

    # Encrypt | 加密
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    return {
        "encrypted_data": base64.b64encode(ciphertext).decode(),
        "iv": base64.b64encode(iv).decode(),
        "expected": json.loads(plaintext)
    }


# =============================================================================
# Report Configuration | 报告配置
# =============================================================================

@pytest.fixture(scope="session")
def report_dir() -> str:
    """
    Provide the report output directory path.
    提供报告输出目录路径。
    """
    report_path = r"C:\pythonProject\python_ai_cspm\TestReport\crypto\reports"
    os.makedirs(report_path, exist_ok=True)
    return report_path


# =============================================================================
# Test Report Generation | 测试报告生成
# =============================================================================

# Global test results storage
_test_results = []

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test results.
    捕获测试结果的钩子。
    """
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        # Check if test is marked as xfail
        is_xfail = hasattr(rep, "wasxfail") or (hasattr(item, '_evalxfail') and item._evalxfail.wasvalid())

        result = {
            "nodeid": item.nodeid,
            "outcome": rep.outcome,
            "duration": rep.duration,
            "longrepr": str(rep.longrepr) if rep.longrepr else "",
            "is_xfail": is_xfail
        }
        _test_results.append(result)


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook to generate detailed reports after all tests complete.
    在所有测试完成后生成详细报告的 pytest 钩子。
    """
    import json
    from datetime import datetime

    report_dir = r"C:\pythonProject\python_ai_cspm\TestReport\crypto\reports"
    os.makedirs(report_dir, exist_ok=True)

    # Parse test results
    # 解析测试结果
    normal_tests = []
    error_tests = []
    security_tests = []

    passed = 0
    failed = 0
    xfailed = 0

    for result in _test_results:
        nodeid = result["nodeid"]
        outcome = result["outcome"]
        duration = result["duration"]
        is_xfail = result.get("is_xfail", False)

        # Override outcome for xfail tests
        if is_xfail:
            outcome = "xfailed"

        # Extract test ID and name
        if "test_crypto_" in nodeid:
            # Parse test ID
            if "test_crypto_sec_" in nodeid:
                # Security test
                test_type = "security"
                if "sec_01" in nodeid:
                    test_id = "CRYPTO-SEC-01"
                    test_name = "HMAC时序攻击防护"
                elif "sec_02" in nodeid:
                    test_id = "CRYPTO-SEC-02"
                    test_name = "时间戳篡改检测"
                elif "sec_03" in nodeid:
                    test_id = "CRYPTO-SEC-03"
                    test_name = "填充预言攻击防护"
                elif "sec_04" in nodeid:
                    test_id = "CRYPTO-SEC-04"
                    test_name = "默认密钥警告输出"
                elif "sec_05" in nodeid:
                    test_id = "CRYPTO-SEC-05"
                    test_name = "HMAC单比特差异检测"
                elif "sec_06" in nodeid:
                    test_id = "CRYPTO-SEC-06"
                    test_name = "错误消息不泄露内部详情"
                else:
                    continue
                security_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            elif "test_crypto_e" in nodeid:
                # Error test
                test_type = "error"
                if "_e01_" in nodeid:
                    test_id, test_name = "CRYPTO-E01", "空密钥文件错误"
                elif "_e02_" in nodeid:
                    test_id, test_name = "CRYPTO-E02", "无效HMAC格式"
                elif "_e03_" in nodeid:
                    test_id, test_name = "CRYPTO-E03", "时间戳过期"
                elif "_e04_" in nodeid:
                    test_id, test_name = "CRYPTO-E04", "篡改的哈希值"
                elif "_e05_" in nodeid:
                    test_id, test_name = "CRYPTO-E05", "无效IV大小"
                elif "_e06_" in nodeid:
                    test_id, test_name = "CRYPTO-E06", "无效PKCS7填充"
                elif "_e07_" in nodeid:
                    test_id, test_name = "CRYPTO-E07", "空加密输入"
                elif "_e08_" in nodeid:
                    test_id, test_name = "CRYPTO-E08", "非UTF-8数据"
                elif "_e09_" in nodeid:
                    test_id, test_name = "CRYPTO-E09", "无效JSON"
                elif "_e10_" in nodeid:
                    test_id, test_name = "CRYPTO-E10", "无效Base64数据"
                elif "_e11_" in nodeid:
                    test_id, test_name = "CRYPTO-E11", "None认证头"
                elif "_e12_" in nodeid:
                    test_id, test_name = "CRYPTO-E12", "数据短于填充长度"
                elif "_e13_" in nodeid:
                    test_id, test_name = "CRYPTO-E13", "填充字节不一致"
                else:
                    continue
                error_tests.append({
                    "id": test_id,
                    "name": test_name,
                    "status": outcome,
                    "duration": duration
                })
            elif "_001_" in nodeid:
                normal_tests.append({"id": "CRYPTO-001", "name": "环境变量获取共享密钥", "status": outcome, "duration": duration})
            elif "_002_" in nodeid:
                normal_tests.append({"id": "CRYPTO-002", "name": "文件获取共享密钥", "status": outcome, "duration": duration})
            elif "_003_" in nodeid:
                normal_tests.append({"id": "CRYPTO-003", "name": "默认密钥回退", "status": outcome, "duration": duration})
            elif "_004_" in nodeid:
                normal_tests.append({"id": "CRYPTO-004", "name": "保留空白字符", "status": outcome, "duration": duration})
            elif "_005_" in nodeid:
                normal_tests.append({"id": "CRYPTO-005", "name": "有效HMAC认证哈希验证", "status": outcome, "duration": duration})
            elif "_006_" in nodeid:
                normal_tests.append({"id": "CRYPTO-006", "name": "有效载荷AES-CBC解密", "status": outcome, "duration": duration})
            elif "_007_" in nodeid:
                normal_tests.append({"id": "CRYPTO-007", "name": "解密后JSON解析", "status": outcome, "duration": duration})
            elif "_008_" in nodeid:
                normal_tests.append({"id": "CRYPTO-008", "name": "Base64解密认证信息", "status": outcome, "duration": duration})
            elif "_009_" in nodeid:
                normal_tests.append({"id": "CRYPTO-009", "name": "已知数据解密测试", "status": outcome, "duration": duration})
            elif "_010_" in nodeid:
                normal_tests.append({"id": "CRYPTO-010", "name": "时间漂移容忍验证", "status": outcome, "duration": duration})

        # Count outcomes
        if outcome == "passed":
            passed += 1
        elif outcome == "failed":
            failed += 1
        elif outcome == "xfailed":
            xfailed += 1

    total = len(_test_results)

    # Generate detailed Markdown report
    # 生成详细的Markdown报告
    report_md = f"""# crypto.py 测试报告

## 测试概要

| 项目 | 值 |
|------|-----|
| 测试对象 | `app/core/crypto.py` |
| 测试规格 | `crypto_tests.md` |
| 执行时间 | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} |
| 覆盖率目标 | 90% |

## 测试结果统计

| 类别 | 总数 | 通过 | 失败 | 预期失败 |
|------|------|------|------|---------|
| 正常系 | {len(normal_tests)} | {sum(1 for t in normal_tests if t['status']=='passed')} | {sum(1 for t in normal_tests if t['status']=='failed')} | {sum(1 for t in normal_tests if t['status']=='xfailed')} |
| 异常系 | {len(error_tests)} | {sum(1 for t in error_tests if t['status']=='passed')} | {sum(1 for t in error_tests if t['status']=='failed')} | {sum(1 for t in error_tests if t['status']=='xfailed')} |
| 安全测试 | {len(security_tests)} | {sum(1 for t in security_tests if t['status']=='passed')} | {sum(1 for t in security_tests if t['status']=='failed')} | {sum(1 for t in security_tests if t['status']=='xfailed')} |
| **合计** | **{total}** | **{passed}** | **{failed}** | **{xfailed}** |

## 测试通过率

- **实际通过率**: {(passed/total*100) if total>0 else 0:.1f}%
- **有效通过率** (排除预期失败): {(passed/(total-xfailed)*100) if (total-xfailed)>0 else 0:.1f}%

---

## 正常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in normal_tests:
        status_icon = "✅ 通过" if t['status'] == "passed" else "❌ 失败"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 异常系测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in error_tests:
        status_icon = "✅ 通过" if t['status'] == "passed" else "❌ 失败"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 安全测试详情

| ID | 测试名称 | 结果 | 执行时间 |
|----|---------|------|---------|
"""

    for t in security_tests:
        if t['status'] == "passed":
            status_icon = "✅ 通过"
        elif t['status'] == "xfailed":
            status_icon = "⚠️ 预期失败"
        else:
            status_icon = "❌ 失败"
        report_md += f"| {t['id']} | {t['name']} | {status_icon} | {t['duration']*1000:.2f}ms |\n"

    report_md += """
---

## 预期失败测试说明

| ID | 问题描述 | 代码位置 | 建议修复 |
|----|---------|---------|---------|
| CRYPTO-SEC-01 | 使用==比较，存在时序攻击风险 | crypto.py:98 | 使用hmac.compare_digest() |
| CRYPTO-SEC-03 | 错误消息泄露填充详情 | crypto.py:165 | 返回统一错误消息 |
| CRYPTO-SEC-06 | 不同错误返回不同消息 | crypto.py:165 | 统一所有解密错误消息 |

---

## 结论

"""

    if failed == 0:
        report_md += "✅ **所有非预期失败的测试均已通过。**\n\n"
    else:
        report_md += f"❌ **有 {failed} 个测试未通过。**\n\n"

    if xfailed > 0:
        report_md += f"⚠️ **有 {xfailed} 个预期失败的测试（已知安全问题）。**\n"

    report_md += f"""
---

*报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

    # Write Markdown report
    md_path = os.path.join(report_dir, "TestReport_crypto.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Generate JSON report
    json_report = {
        "metadata": {
            "test_target": "app/core/crypto.py",
            "test_spec": "crypto_tests.md",
            "execution_time": datetime.now().isoformat(),
            "coverage_target": "90%"
        },
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "xfailed": xfailed,
            "pass_rate": (passed/total*100) if total>0 else 0
        },
        "results": {
            "normal": normal_tests,
            "error": error_tests,
            "security": security_tests
        }
    }

    json_path = os.path.join(report_dir, "TestReport_crypto.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 测试报告已生成:")
    print(f"  - {md_path}")
    print(f"  - {json_path}")

