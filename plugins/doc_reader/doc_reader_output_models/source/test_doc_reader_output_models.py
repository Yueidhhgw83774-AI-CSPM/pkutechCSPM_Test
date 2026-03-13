"""
Doc Reader Output Models 完整テスト (44 tests)
要件: doc_reader_output_models_tests.md

正常系:22, 異常系:12, セキュリティ:10
"""
import pytest
from pydantic import ValidationError

# ==================== 正常系 (OUTM-001~022) ====================
class TestImageDiscription:
    """ImageDiscription モデル正常系 (2 tests)"""

    def test_valid_instance_creation(self):
        """OUTM-001: ImageDiscription 正常インスタンス化"""
        from app.doc_reader_plugin.output_models import ImageDiscription

        instance = ImageDiscription(discription="画像の説明")
        assert instance.discription == "画像の説明"

    def test_field_metadata(self):
        """OUTM-001b: ImageDiscription フィールドメタデータ確認"""
        from app.doc_reader_plugin.output_models import ImageDiscription

        fields = ImageDiscription.model_fields
        assert "discription" in fields
        # フィールド名はdiscription（typo）


class TestCompliance:
    """Compliance モデル正常系 (3 tests)"""

    def test_all_fields_specified(self):
        """OUTM-002: Compliance 全フィールド指定"""
        from app.doc_reader_plugin.output_models import Compliance

        instance = Compliance(
            id="COMP-001",
            title="タイトル",
            discription="説明",
            page="1"
        )

        assert instance.id == "COMP-001"
        assert instance.title == "タイトル"
        assert instance.discription == "説明"
        assert instance.page == "1"

    def test_page_range_continuous(self):
        """OUTM-003: Compliance ページ範囲形式（連続）"""
        from app.doc_reader_plugin.output_models import Compliance

        instance = Compliance(
            id="COMP-002",
            title="タイトル",
            discription="説明",
            page="1-5"
        )

        assert instance.page == "1-5"

    def test_page_range_multiple(self):
        """OUTM-004: Compliance ページ範囲形式（複数）"""
        from app.doc_reader_plugin.output_models import Compliance

        instance = Compliance(
            id="COMP-003",
            title="タイトル",
            discription="説明",
            page="1-3,6,9"
        )

        assert instance.page == "1-3,6,9"


class TestSeverity:
    """Severity Enum 通常系 (6 tests)"""

    def test_critical_value(self):
        """OUTM-005: シverity CRITICAL値"""
        from app.doc_reader_plugin.output_models import Severity

        assert Severity.CRITICAL == "Critical"
        assert Severity.CRITICAL.value == "Critical"

    def test_high_value(self):
        """OUTM-006: シェビリティ HIGH値"""
        from app.doc_reader_plugin.output_models import Severity

        assert Severity.HIGH == "High"
        assert Severity.HIGH.value == "High"

    def test_medium_value(self):
        """OUTM-007: 脅威度 MEDIUM値"""
        from app.doc_reader_plugin.output_models import Severity

        assert Severity.MEDIUM == "Medium"
        assert Severity.MEDIUM.value == "Medium"

    def test_low_value(self):
        """OUTM-008: シェビリティ LOW値"""
        from app.doc_reader_plugin.output_models import Severity

        assert Severity.LOW == "Low"
        assert Severity.LOW.value == "Low"

    def test_information_value(self):
        """OUTM-009: 警告度 INFORMATION値"""
        from app.doc_reader_plugin.output_models import Severity

        assert Severity.INFORMATION == "Informational"
        assert Severity.INFORMATION.value == "Informational"

    def test_string_to_enum_conversion(self):
        """OUTM-010: Severity 文字列からEnum変換"""
        from app.doc_reader_plugin.output_models import Severity

        severity = Severity("High")
        assert severity == Severity.HIGH

    def test_all_values_exist(self):
        """OUTM-010b: Severity すべての値が存在することを確認する"""
        from app.doc_reader_plugin.output_models import Severity

        all_values = list(Severity)
        assert len(all_values) == 5
        assert Severity.CRITICAL in all_values
        assert Severity.HIGH in all_values
        assert Severity.MEDIUM in all_values
        assert Severity.LOW in all_values
        assert Severity.INFORMATION in all_values


class TestComplianceDetails:
    """ComplianceDetails モデル正常系 (11 tests)"""

    def test_required_fields_only(self):
        """OUTM-011: ComplianceDetails 必須フィールドのみ"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-001",
            title="推奨事項タイトル",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.HIGH,
            severity_reason="重要度の理由"
        )

        # オプションフィールドはデフォルト値
        assert instance.audit == []
        assert instance.remediation == []
        assert instance.defaultValue is None
        assert instance.references == []
        assert instance.additionalInformation == []
        assert instance.category == []

    def test_all_fields_specified(self):
        """OUTM-012: ComplianceDetails 全フィールド指定"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-002",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.CRITICAL,
            severity_reason="理由",
            audit=["監査手順1", "監査手順2"],
            remediation=["修復方法1", "修復方法2"],
            defaultValue="デフォルト値",
            references=["参考1", "参考2"],
            additionalInformation=["追加情報1"],
            category=["Security", "Network"]
        )

        assert instance.recommendationId == "REC-002"
        assert len(instance.audit) == 2
        assert len(instance.remediation) == 2
        assert instance.defaultValue == "デフォルト値"
        assert len(instance.category) == 2

    def test_audit_empty_list(self):
        """OUTM-013: ComplianceDetails audit空リスト"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-003",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.MEDIUM,
            severity_reason="理由",
            audit=[]
        )

        assert instance.audit == []

    def test_audit_multiple_items(self):
        """OUTM-014: ComplianceDetails 実行内容 複数項目"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-004",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.LOW,
            severity_reason="理由",
            audit=["Step1", "Step2", "Step3"]
        )

        assert len(instance.audit) == 3
        assert "Step1" in instance.audit

    def test_remediation_empty_list(self):
        """OUTM-015: ComplianceDetails remediation空リスト"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-005",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.INFORMATION,
            severity_reason="理由",
            remediation=[]
        )

        assert instance.remediation == []

    def test_remediation_multiple_items(self):
        """OUTM-016: ComplianceDetails 討正複数項目"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-006",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.HIGH,
            severity_reason="理由",
            remediation=["Fix1", "Fix2"]
        )

        assert len(instance.remediation) == 2

    def test_default_value_specified(self):
        """OUTM-017: ComplianceDetails defaultValue指定"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-007",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.MEDIUM,
            severity_reason="理由",
            defaultValue="デフォルト値"
        )

        assert instance.defaultValue == "デフォルト値"

    def test_default_value_none(self):
        """OUTM-018: ComplianceDetails defaultValueなし"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-008",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.LOW,
            severity_reason="理由"
        )

        assert instance.defaultValue is None

    def test_category_multiple(self):
        """OUTM-019: ComplianceDetails カテゴリ複数"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-009",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.CRITICAL,
            severity_reason="理由",
            category=["Security", "Network", "Compliance"]
        )

        assert len(instance.category) == 3
        assert "Security" in instance.category

    def test_model_dump_to_dict(self):
        """OUTM-020: ComplianceDetails model_dump()でdict変換"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-010",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.HIGH,
            severity_reason="理由"
        )

        data = instance.model_dump()
        assert isinstance(data, dict)
        assert data["recommendationId"] == "REC-010"
        assert data["severity"] == Severity.HIGH or data["severity"] == "High"

    def test_model_json_schema(self):
        """OUTM-021: ComplianceDetails model_json_schema()でスキーマ取得"""
        from app.doc_reader_plugin.output_models import ComplianceDetails

        schema = ComplianceDetails.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "recommendationId" in schema["properties"]

    def test_model_dump_json_mode(self):
        """OUTM-022: ComplianceDetails model_dump(mode='json')で文字列化"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        instance = ComplianceDetails(
            recommendationId="REC-011",
            title="推奨事項",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.HIGH,
            severity_reason="理由"
        )

        data = instance.model_dump(mode='json')
        assert isinstance(data, dict)
        # mode='json'でseverityが文字列"High"に変換
        assert data["severity"] == "High" or isinstance(data["severity"], str)


# ==================== 異常系 (OUTM-E01~E11) ====================
class TestImageDiscriptionErrors:
    """ImageDiscription 異常系 (2 tests)"""

    def test_discription_missing(self):
        """OUTM-E01: ImageDiscription 説明欠落"""
        from app.doc_reader_plugin.output_models import ImageDiscription

        with pytest.raises(ValidationError):
            ImageDiscription()

    def test_discription_type_coercion(self):
        """OUTM-E02: ImageDiscription discription型強制"""
        from app.doc_reader_plugin.output_models import ImageDiscription
        
        # Pydantic v2では型強制しないのでValidationError
        with pytest.raises(ValidationError):
            ImageDiscription(discription=123)

    def test_required_fields_missing(self):
        """OUTM-E03: Compliance 必須フィールド欠落"""
        from app.doc_reader_plugin.output_models import Compliance

        with pytest.raises(ValidationError):
            Compliance(id="COMP-001")

    def test_page_type_coercion(self):
        """OUTM-E04: コンプライアンスページ型強制"""
        from app.doc_reader_plugin.output_models import Compliance
        
        # Pydantic v2では型強制しないのでValidationError
        with pytest.raises(ValidationError):
            Compliance(id="COMP-004", title="タイトル", discription="説明", page=123)

    def test_invalid_value(self):
        """OUTM-E05: Severity 無効な値"""
        from app.doc_reader_plugin.output_models import Severity

        with pytest.raises(ValueError):
            Severity("Invalid")

    def test_case_sensitive(self):
        """OUTM-E05b: Severity 大文字小文字区別"""
        from app.doc_reader_plugin.output_models import Severity

        with pytest.raises(ValueError):
            Severity("high")  # "High"でなければならない


class TestComplianceDetailsErrors:
    """ComplianceDetails 異常系 (6 tests)"""

    def test_required_fields_missing(self):
        """OUTM-E06: ComplianceDetails 必須フィールド欠落"""
        from app.doc_reader_plugin.output_models import ComplianceDetails

        with pytest.raises(ValidationError):
            ComplianceDetails(recommendationId="REC-001")

    def test_severity_invalid_value(self):
        """OUTM-E07: ComplianceDetails severity無効値"""
        from app.doc_reader_plugin.output_models import ComplianceDetails

        with pytest.raises(ValidationError):
            ComplianceDetails(
                recommendationId="REC-012",
                title="推奨事項",
                description="説明",
                rationale="根拠",
                impact="影響",
                severity="Invalid",
                severity_reason="理由"
            )

    def test_audit_type_error(self):
        """OUTM-E08: ComplianceDetails audit型エラー"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        with pytest.raises(ValidationError):
            ComplianceDetails(
                recommendationId="REC-013",
                title="推奨事項",
                description="説明",
                rationale="根拠",
                impact="影響",
                severity=Severity.HIGH,
                severity_reason="理由",
                audit="string"  # リストであるべき
            )

    def test_remediation_type_error(self):
        """OUTM-E09: ComplianceDetails remediation型エラー"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        with pytest.raises(ValidationError):
            ComplianceDetails(
                recommendationId="REC-014",
                title="推奨事項",
                description="説明",
                rationale="根拠",
                impact="影響",
                severity=Severity.MEDIUM,
                severity_reason="理由",
                remediation="string"  # リストであるべき
            )

    def test_category_type_error(self):
        """OUTM-E10: ComplianceDetails category型エラー"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        with pytest.raises(ValidationError):
            ComplianceDetails(
                recommendationId="REC-015",
                title="推奨事項",
                description="説明",
                rationale="根拠",
                impact="影響",
                severity=Severity.LOW,
                severity_reason="理由",
                category="Security"  # リストであるべき
            )

    def test_title_empty_string(self):
        """OUTM-E11: ComplianceDetails title空文字列"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        # 正常生成（空文字列許可）※ビジネスロジックで要検証
        instance = ComplianceDetails(
            recommendationId="REC-016",
            title="",
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.INFORMATION,
            severity_reason="理由"
        )
        assert instance.title == ""


# ==================== セキュリティ (OUTM-SEC-01~10) ====================
@pytest.mark.security
class TestOutputModelsSecurity:
    """Output Models セキュリティテスト (10 tests)"""

    def test_xss_payload_resistance(self):
        """OUTM-SEC-01: XSSペイロード耐性"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        xss_payload = "<script>alert('XSS')</script>"

        instance = ComplianceDetails(
            recommendationId="REC-XSS",
            title=xss_payload,
            description=xss_payload,
            rationale="根拠",
            impact="影響",
            severity=Severity.HIGH,
            severity_reason="理由"
        )

        # 文字列としてそのまま保存（エスケープなし）
        assert instance.title == xss_payload
        assert instance.description == xss_payload

    def test_sql_injection_resistance(self):
        """OUTM-SEC-02: SQLインジェクション耐性"""
        from app.doc_reader_plugin.output_models import Compliance

        sql_payload = "1' OR '1'='1'; DROP TABLE users;--"

        instance = Compliance(
            id="COMP-SQL",
            title=sql_payload,
            discription="説明",
            page="1"
        )

        # 文字列としてそのまま保存
        assert instance.title == sql_payload

    def test_large_string_dos_resistance(self):
        """OUTM-SEC-03: 長大文字列DoS耐性"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        # 1MB文字列
        large_string = "A" * (1024 * 1024)

        instance = ComplianceDetails(
            recommendationId="REC-DOS",
            title="推奨事項",
            description=large_string,
            rationale="根拠",
            impact="影響",
            severity=Severity.MEDIUM,
            severity_reason="理由"
        )

        # 正常生成（メモリ枯渇なし）
        assert len(instance.description) == 1024 * 1024

    def test_unicode_control_characters_resistance(self):
        """OUTM-SEC-04: Unicode制御文字耐性"""
        from app.doc_reader_plugin.output_models import Compliance

        control_chars = "test\x00\x01\x02\x03\x1f"

        instance = Compliance(
            id="COMP-CTRL",
            title=control_chars,
            discription="説明",
            page="1"
        )

        # 正常生成
        assert instance.title == control_chars

    def test_null_byte_injection_resistance(self):
        """OUTM-SEC-05: NULLバイトインジェクション耐性"""
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        null_byte_payload = "test\x00hidden"

        instance = ComplianceDetails(
            recommendationId="REC-NULL",
            title=null_byte_payload,
            description="説明",
            rationale="根拠",
            impact="影響",
            severity=Severity.LOW,
            severity_reason="理由"
        )

        # 正常生成
        assert "\x00" in instance.title

    def test_no_sensitive_fields(self):
        """OUTM-SEC-06: 機密情報フィールドの存在確認"""
        from app.doc_reader_plugin.output_models import ComplianceDetails

        fields = ComplianceDetails.model_fields
        field_names = list(fields.keys())

        # 機密フィールドなし（APIキー等を保持しない）
        assert "api_key" not in field_names
        assert "password" not in field_names
        assert "secret" not in field_names
        assert "token" not in field_names

    def test_type_coercion_bypass_prevention(self):
        """OUTM-SEC-07: 型強制バイパス防止"""
        from app.doc_reader_plugin.output_models import Compliance
        nosql_payload = {"$ne": 1}
        
        # Pydantic v2では型強制しないのでValidationError
        with pytest.raises(ValidationError):
            Compliance(id="COMP-NOSQL", title="タイトル", discription="説明", page=nosql_payload)

    def test_page_field_redos_resistance(self):
        """OUTM-SEC-08: pageフィールドReDoS耐性"""
        import time
        from app.doc_reader_plugin.output_models import Compliance

        # 大量カンマ区切りページ（約6000文字）
        large_page_range = ",".join([str(i) for i in range(1, 1001)])

        start = time.time()
        instance = Compliance(
            id="COMP-REDOS",
            title="タイトル",
            discription="説明",
            page=large_page_range
        )
        elapsed = time.time() - start

        # 3秒以内に処理完了
        assert elapsed < 3.0
        assert len(instance.page) > 3000

    def test_path_traversal_payload_storage(self):
        """OUTM-SEC-09: パストラバーサルペイロード保存"""
        from app.doc_reader_plugin.output_models import Compliance

        path_traversal = "../../../etc/passwd"

        instance = Compliance(
            id="COMP-PATH",
            title="タイトル",
            discription="説明",
            page=path_traversal
        )

        # 文字列として保存（バリデーションなし）
        assert instance.page == path_traversal

    def test_severity_error_message_safety(self):
        """OUTM-SEC-10: Severityエラーメッセージの安全性"""
        from app.doc_reader_plugin.output_models import Severity

        try:
            Severity("InvalidValue")
        except ValueError as e:
            error_message = str(e)
            # スタックトレースに機密情報なし
            assert "password" not in error_message.lower()
            assert "secret" not in error_message.lower()
            assert "api_key" not in error_message.lower()

