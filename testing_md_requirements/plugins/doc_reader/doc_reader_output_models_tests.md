# doc_reader_plugin/output_models テストケース

## 1. 概要

`output_models.py`は、ドキュメントリーダープラグインで使用されるPydanticモデル定義モジュールです。PDF文書から抽出されたコンプライアンス情報を構造化するためのスキーマを提供します。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `ImageDiscription` | 画像の詳細説明を保持するモデル |
| `Compliance` | コンプライアンス項目の基本構造（ID、タイトル、説明、ページ） |
| `Severity` | 重要度を表すEnum（Critical/High/Medium/Low/Informational） |
| `ComplianceDetails` | コンプライアンス詳細出力モデル（推奨事項、根拠、影響度、監査手順等） |

### 1.2 カバレッジ目標: 90%

> **注記**: Pydanticモデル定義のため、バリデーション機能のテストが中心。Enumとモデルのインスタンス化、フィールドバリデーション、デフォルト値検証に焦点を当てる。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/doc_reader_plugin/output_models.py` |
| テストコード | `test/unit/doc_reader_plugin/test_output_models.py` |

### 1.4 補足情報

#### モデル定義

1. **ImageDiscription** (output_models.py:5-6)
   - `discription`: str（必須）- 画像の詳細説明

2. **Compliance** (output_models.py:8-16)
   - `id`: str（必須）- ユニークID
   - `title`: str（必須）- タイトル
   - `discription`: str（必須）- 短い説明
   - `page`: str（必須）- PDFのページ番号（例：1-3,6,9）

3. **Severity** (output_models.py:17-25)
   - `CRITICAL = "Critical"`
   - `HIGH = "High"`
   - `MEDIUM = "Medium"`
   - `LOW = "Low"`
   - `INFORMATION = "Informational"`

4. **ComplianceDetails** (output_models.py:27-44)
   - 必須フィールド: recommendationId, title, description, rationale, impact, severity, severity_reason
   - オプションフィールド（デフォルト値あり）: audit=[], remediation=[], defaultValue=None, references=[], additionalInformation=[], category=[]

#### 注意点
- フィールド名に typo あり: `discription`（正しくは `description`）が複数箇所で使用されている
- `Severity` Enum は文字列ベース（`str, Enum`）

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OUTM-001 | ImageDiscription: 正常インスタンス化 | discription="画像の説明" | 正常生成 |
| OUTM-001b | ImageDiscription: フィールドメタデータ確認 | model_fields | description="画像の詳細説明"（注: フィールド名はdiscription） |
| OUTM-002 | Compliance: 全フィールド指定 | id, title, discription, page | 正常生成 |
| OUTM-003 | Compliance: ページ範囲形式（連続） | page="1-5" | 正常生成 |
| OUTM-004 | Compliance: ページ範囲形式（複数） | page="1-3,6,9" | 正常生成 |
| OUTM-005 | Severity: CRITICAL値 | Severity.CRITICAL | "Critical" |
| OUTM-006 | Severity: HIGH値 | Severity.HIGH | "High" |
| OUTM-007 | Severity: MEDIUM値 | Severity.MEDIUM | "Medium" |
| OUTM-008 | Severity: LOW値 | Severity.LOW | "Low" |
| OUTM-009 | Severity: INFORMATION値 | Severity.INFORMATION | "Informational" |
| OUTM-010 | Severity: 文字列からEnum変換 | "High" | Severity.HIGH |
| OUTM-010b | Severity: 全値存在確認 | list(Severity) | 5つの値すべて存在 |
| OUTM-011 | ComplianceDetails: 必須フィールドのみ | 必須フィールドのみ | 正常生成、オプションはデフォルト値 |
| OUTM-012 | ComplianceDetails: 全フィールド指定 | 全フィールド | 正常生成 |
| OUTM-013 | ComplianceDetails: audit空リスト | audit=[] | 正常生成 |
| OUTM-014 | ComplianceDetails: audit複数項目 | audit=["Step1", "Step2"] | 正常生成 |
| OUTM-015 | ComplianceDetails: remediation空リスト | remediation=[] | 正常生成 |
| OUTM-016 | ComplianceDetails: remediation複数項目 | remediation=["Fix1", "Fix2"] | 正常生成 |
| OUTM-017 | ComplianceDetails: defaultValue指定 | defaultValue="デフォルト値" | 正常生成 |
| OUTM-018 | ComplianceDetails: defaultValueなし | defaultValue省略 | None |
| OUTM-019 | ComplianceDetails: category複数 | category=["Security", "Network"] | 正常生成 |
| OUTM-020 | ComplianceDetails: model_dump()でdict変換 | インスタンス | 辞書形式（severityはSeverity.HIGH） |
| OUTM-021 | ComplianceDetails: model_json_schema()でスキーマ取得 | クラス | JSONスキーマ取得 |
| OUTM-022 | ComplianceDetails: model_dump(mode='json')で文字列化 | インスタンス | severityが文字列"High"に変換 |

### 2.1 ImageDiscription テスト

```python
# test/unit/doc_reader_plugin/test_output_models.py
import pytest
from pydantic import ValidationError


class TestImageDiscription:
    """ImageDiscriptionモデルのテスト"""

    def test_valid_instance_creation(self):
        """OUTM-001: 正常インスタンス化"""
        # Arrange
        from app.doc_reader_plugin.output_models import ImageDiscription

        # Act
        image_desc = ImageDiscription(discription="この画像はセキュリティ設定の一覧を示しています")

        # Assert
        assert image_desc.discription == "この画像はセキュリティ設定の一覧を示しています"

    def test_field_description_metadata(self):
        """OUTM-001b: フィールドのdescriptionメタデータ確認"""
        # Arrange
        from app.doc_reader_plugin.output_models import ImageDiscription

        # Act
        # Pydantic v2ではmodel_fieldsを使用
        field_info = ImageDiscription.model_fields["discription"]

        # Assert
        assert field_info.description == "画像の詳細説明"


class TestCompliance:
    """Complianceモデルのテスト"""

    def test_valid_instance_with_all_fields(self):
        """OUTM-002: 全フィールド指定"""
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        # Act
        compliance = Compliance(
            id="SEC-001",
            title="アクセス制御設定",
            discription="IAMポリシーの適切な設定を確認",
            page="1-5"
        )

        # Assert
        assert compliance.id == "SEC-001"
        assert compliance.title == "アクセス制御設定"
        assert compliance.discription == "IAMポリシーの適切な設定を確認"
        assert compliance.page == "1-5"

    def test_page_continuous_range(self):
        """OUTM-003: ページ範囲形式（連続）"""
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        # Act
        compliance = Compliance(
            id="SEC-002",
            title="暗号化設定",
            discription="データ暗号化の確認",
            page="1-5"
        )

        # Assert
        assert compliance.page == "1-5"

    def test_page_multiple_ranges(self):
        """OUTM-004: ページ範囲形式（複数）"""
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        # Act
        compliance = Compliance(
            id="SEC-003",
            title="監査ログ設定",
            discription="監査ログの有効化確認",
            page="1-3,6,9"
        )

        # Assert
        assert compliance.page == "1-3,6,9"


class TestSeverity:
    """Severity Enumのテスト"""

    def test_critical_value(self):
        """OUTM-005: CRITICAL値"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        assert Severity.CRITICAL.value == "Critical"
        assert Severity.CRITICAL == "Critical"  # str継承のため

    def test_high_value(self):
        """OUTM-006: HIGH値"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        assert Severity.HIGH.value == "High"
        assert Severity.HIGH == "High"

    def test_medium_value(self):
        """OUTM-007: MEDIUM値"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        assert Severity.MEDIUM.value == "Medium"
        assert Severity.MEDIUM == "Medium"

    def test_low_value(self):
        """OUTM-008: LOW値"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        assert Severity.LOW.value == "Low"
        assert Severity.LOW == "Low"

    def test_information_value(self):
        """OUTM-009: INFORMATION値"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        assert Severity.INFORMATION.value == "Informational"
        assert Severity.INFORMATION == "Informational"

    def test_string_to_enum_conversion(self):
        """OUTM-010: 文字列からEnum変換"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act
        severity = Severity("High")

        # Assert
        assert severity == Severity.HIGH
        assert severity.value == "High"

    def test_all_severity_values_exist(self):
        """OUTM-010b: 全Severity値の存在確認"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act
        all_values = [s.value for s in Severity]

        # Assert
        expected = ["Critical", "High", "Medium", "Low", "Informational"]
        assert all_values == expected
```

### 2.2 ComplianceDetails テスト

```python
# test/unit/doc_reader_plugin/test_output_models.py（続き）


class TestComplianceDetails:
    """ComplianceDetailsモデルのテスト

    注: フィクスチャ`required_compliance_fields`はconftest.pyで定義。
    テストクラス内でのローカル定義は行わない（重複防止）。
    """

    def test_required_fields_only(self, required_compliance_fields):
        """OUTM-011: 必須フィールドのみ"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act
        details = ComplianceDetails(**required_compliance_fields)

        # Assert
        assert details.recommendationId == "REC-001"
        assert details.title == "S3バケットの暗号化"
        assert details.description == "S3バケットでサーバー側暗号化を有効にする"
        assert details.rationale == "保存データの機密性を確保するため"
        assert details.impact == "暗号化されていない場合、データ漏洩時に情報が平文で流出"
        assert details.severity.value == "High"
        assert details.severity_reason == "機密データを扱うため高リスク"
        # デフォルト値の確認
        assert details.audit == []
        assert details.remediation == []
        assert details.defaultValue is None
        assert details.references == []
        assert details.additionalInformation == []
        assert details.category == []

    def test_all_fields_specified(self, required_compliance_fields):
        """OUTM-012: 全フィールド指定"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        full_data = {
            **required_compliance_fields,
            "audit": ["AWSコンソールでS3バケット一覧を確認", "暗号化設定をチェック"],
            "remediation": ["aws s3api put-bucket-encryption コマンドで暗号化を有効化"],
            "defaultValue": "暗号化なし",
            "references": ["https://docs.aws.amazon.com/s3/"],
            "additionalInformation": ["KMSキーの管理も推奨"],
            "category": ["Security", "Data Protection"]
        }

        # Act
        details = ComplianceDetails(**full_data)

        # Assert
        assert len(details.audit) == 2
        assert len(details.remediation) == 1
        assert details.defaultValue == "暗号化なし"
        assert len(details.references) == 1
        assert len(details.additionalInformation) == 1
        assert len(details.category) == 2

    def test_audit_empty_list(self, required_compliance_fields):
        """OUTM-013: audit空リスト"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act
        details = ComplianceDetails(**required_compliance_fields, audit=[])

        # Assert
        assert details.audit == []

    def test_audit_multiple_items(self, required_compliance_fields):
        """OUTM-014: audit複数項目"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        audit_steps = [
            "Step 1: ログイン",
            "Step 2: 設定確認",
            "Step 3: レポート出力"
        ]

        # Act
        details = ComplianceDetails(**required_compliance_fields, audit=audit_steps)

        # Assert
        assert details.audit == audit_steps
        assert len(details.audit) == 3

    def test_remediation_empty_list(self, required_compliance_fields):
        """OUTM-015: remediation空リスト"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act
        details = ComplianceDetails(**required_compliance_fields, remediation=[])

        # Assert
        assert details.remediation == []

    def test_remediation_multiple_items(self, required_compliance_fields):
        """OUTM-016: remediation複数項目"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        remediation_steps = [
            "Fix 1: 設定変更",
            "Fix 2: 再起動"
        ]

        # Act
        details = ComplianceDetails(**required_compliance_fields, remediation=remediation_steps)

        # Assert
        assert details.remediation == remediation_steps
        assert len(details.remediation) == 2

    def test_default_value_specified(self, required_compliance_fields):
        """OUTM-017: defaultValue指定"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act
        details = ComplianceDetails(**required_compliance_fields, defaultValue="無効")

        # Assert
        assert details.defaultValue == "無効"

    def test_default_value_none_by_default(self, required_compliance_fields):
        """OUTM-018: defaultValueなし（デフォルトでNone）"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act
        details = ComplianceDetails(**required_compliance_fields)

        # Assert
        assert details.defaultValue is None

    def test_category_multiple(self, required_compliance_fields):
        """OUTM-019: category複数"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        categories = ["Security", "Network", "Compliance"]

        # Act
        details = ComplianceDetails(**required_compliance_fields, category=categories)

        # Assert
        assert details.category == categories
        assert len(details.category) == 3

    def test_model_dump_to_dict(self, required_compliance_fields):
        """OUTM-020: model_dump()でdict変換

        注: model_dump()のデフォルトではEnumはEnumオブジェクトのまま。
        文字列が必要な場合はmode='json'を使用する。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        details = ComplianceDetails(**required_compliance_fields)

        # Act
        result = details.model_dump()

        # Assert
        assert isinstance(result, dict)
        assert result["recommendationId"] == "REC-001"
        # デフォルトではEnumはそのまま（Severity型）
        assert result["severity"] == Severity.HIGH

    def test_model_json_schema(self):
        """OUTM-021: model_json_schema()でスキーマ取得"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act
        schema = ComplianceDetails.model_json_schema()

        # Assert
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "recommendationId" in schema["properties"]
        assert "severity" in schema["properties"]

    def test_model_dump_json_mode(self, required_compliance_fields):
        """OUTM-022: model_dump(mode='json')で文字列化

        mode='json'を指定するとEnumが文字列に変換される。
        API出力時はこのモードを使用することを推奨。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        details = ComplianceDetails(**required_compliance_fields)

        # Act
        result = details.model_dump(mode='json')

        # Assert
        assert isinstance(result, dict)
        assert result["recommendationId"] == "REC-001"
        # mode='json'ではEnumは文字列に変換
        assert result["severity"] == "High"
        assert isinstance(result["severity"], str)
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OUTM-E01 | ImageDiscription: discription欠落 | {} | ValidationError |
| OUTM-E02 | ImageDiscription: discription型強制 | discription=123 | 型強制で通る（"123"に変換） |
| OUTM-E03 | Compliance: 必須フィールド欠落 | idのみ | ValidationError |
| OUTM-E04 | Compliance: page型強制 | page=123 | 型強制で通る（"123"に変換） |
| OUTM-E05 | Severity: 無効な値 | "Invalid" | ValueError |
| OUTM-E05b | Severity: 大文字小文字区別 | "high" | ValueError |
| OUTM-E06 | ComplianceDetails: 必須フィールド欠落 | recommendationIdのみ | ValidationError |
| OUTM-E07 | ComplianceDetails: severity無効値 | severity="Invalid" | ValidationError |
| OUTM-E08 | ComplianceDetails: audit型エラー | audit="string" | ValidationError |
| OUTM-E09 | ComplianceDetails: remediation型エラー | remediation="string" | ValidationError |
| OUTM-E10 | ComplianceDetails: category型エラー | category="Security" | ValidationError |
| OUTM-E11 | ComplianceDetails: title空文字列 | title="" | 正常生成（空文字列許可）※ビジネスロジックで要検証 |

### 3.1 バリデーションエラー テスト

```python
# test/unit/doc_reader_plugin/test_output_models.py（続き）


class TestImageDiscriptionErrors:
    """ImageDiscriptionモデルのエラーテスト"""

    def test_missing_discription(self):
        """OUTM-E01: discription欠落"""
        # Arrange
        from app.doc_reader_plugin.output_models import ImageDiscription

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ImageDiscription()

        # 必須フィールドの欠落を確認
        assert "discription" in str(exc_info.value)

    def test_discription_type_coercion(self):
        """OUTM-E02: discription型強制（整数入力）

        Pydanticは型強制を行うため、整数は文字列に変換される。
        注: これはValidationErrorではなく、正常に変換される挙動。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ImageDiscription

        # Act
        # Pydanticの型強制により、123は"123"に変換される
        image_desc = ImageDiscription(discription=123)

        # Assert
        assert image_desc.discription == "123"


class TestComplianceErrors:
    """Complianceモデルのエラーテスト"""

    def test_missing_required_fields(self):
        """OUTM-E03: 必須フィールド欠落"""
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Compliance(id="SEC-001")  # 他の必須フィールドが欠落

        error_str = str(exc_info.value)
        assert "title" in error_str or "discription" in error_str or "page" in error_str

    def test_page_type_coercion(self):
        """OUTM-E04: page型強制（整数入力）

        Pydanticは型強制を行うため、整数は文字列に変換される。
        注: これはValidationErrorではなく、正常に変換される挙動。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        # Act
        compliance = Compliance(
            id="SEC-001",
            title="テスト",
            discription="説明",
            page=123
        )

        # Assert
        # 整数は文字列に変換される
        assert compliance.page == "123"


class TestSeverityErrors:
    """Severity Enumのエラーテスト"""

    def test_invalid_severity_value(self):
        """OUTM-E05: 無効なSeverity値"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        with pytest.raises(ValueError):
            Severity("Invalid")

    def test_case_sensitive(self):
        """OUTM-E05b: Severity値は大文字小文字を区別"""
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act & Assert
        # "high"（小文字）は無効
        with pytest.raises(ValueError):
            Severity("high")


class TestComplianceDetailsErrors:
    """ComplianceDetailsモデルのエラーテスト"""

    def test_missing_required_fields(self):
        """OUTM-E06: 必須フィールド欠落"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComplianceDetails(recommendationId="REC-001")

        # 他の必須フィールドが欠落していることを確認
        error_str = str(exc_info.value)
        assert "title" in error_str or "description" in error_str

    def test_invalid_severity(self):
        """OUTM-E07: severity無効値"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComplianceDetails(
                recommendationId="REC-001",
                title="テスト",
                description="説明",
                rationale="理由",
                impact="影響",
                severity="Invalid",  # 無効なSeverity値
                severity_reason="理由"
            )

        assert "severity" in str(exc_info.value).lower()

    def test_audit_type_error(self):
        """OUTM-E08: audit型エラー（文字列入力）"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComplianceDetails(
                recommendationId="REC-001",
                title="テスト",
                description="説明",
                rationale="理由",
                impact="影響",
                severity=Severity.HIGH,
                severity_reason="理由",
                audit="これはリストではない"  # 文字列はlist[str]に変換できない
            )

        assert "audit" in str(exc_info.value)

    def test_remediation_type_error(self):
        """OUTM-E09: remediation型エラー（文字列入力）"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComplianceDetails(
                recommendationId="REC-001",
                title="テスト",
                description="説明",
                rationale="理由",
                impact="影響",
                severity=Severity.HIGH,
                severity_reason="理由",
                remediation="これはリストではない"
            )

        assert "remediation" in str(exc_info.value)

    def test_category_type_error(self):
        """OUTM-E10: category型エラー（文字列入力）"""
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ComplianceDetails(
                recommendationId="REC-001",
                title="テスト",
                description="説明",
                rationale="理由",
                impact="影響",
                severity=Severity.HIGH,
                severity_reason="理由",
                category="Security"  # リストではなく文字列
            )

        assert "category" in str(exc_info.value)

    def test_empty_title_allowed(self):
        """OUTM-E11: title空文字列

        空文字列はPydanticバリデーションを通過する。
        ビジネスロジックレベルでの検証が必要な場合は別途対応。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails, Severity

        # Act
        details = ComplianceDetails(
            recommendationId="REC-001",
            title="",  # 空文字列
            description="説明",
            rationale="理由",
            impact="影響",
            severity=Severity.HIGH,
            severity_reason="理由"
        )

        # Assert
        assert details.title == ""
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| OUTM-SEC-01 | XSSペイロード耐性 | HTML/JSインジェクション文字列 | 文字列としてそのまま保存（エスケープなし） |
| OUTM-SEC-02 | SQLインジェクション耐性 | SQL文字列 | 文字列としてそのまま保存 |
| OUTM-SEC-03 | 長大文字列DoS耐性 | 1MB文字列 | 正常生成（メモリ枯渇なし） |
| OUTM-SEC-04 | Unicode制御文字耐性 | 制御文字を含む文字列 | 正常生成 |
| OUTM-SEC-05 | NULLバイトインジェクション耐性 | NULLバイト含む文字列 | 正常生成 |
| OUTM-SEC-06 | 機密情報フィールドの存在確認 | モデル構造 | 機密フィールドなし（APIキー等を保持しない） |
| OUTM-SEC-07 | 型強制バイパス防止 | dict型注入（page={"$ne": 1}） | 型強制で文字列化される（NoSQLインジェクション無効化） |
| OUTM-SEC-08 | pageフィールドReDoS耐性 | 大量カンマ区切りページ（約6000文字） | 3秒以内に処理完了（@slow） |
| OUTM-SEC-09 | パストラバーサルペイロード保存 | page="../../../etc/passwd" | 文字列として保存（バリデーションなし） |
| OUTM-SEC-10 | Severityエラーメッセージの安全性 | 無効なSeverity値 | スタックトレースに機密情報なし |

### OWASP Top 10 カバレッジ

| OWASP Category | テストID | カバー内容 |
|----------------|----------|-----------|
| A03:2021 – Injection | OUTM-SEC-01, OUTM-SEC-02, OUTM-SEC-07, OUTM-SEC-09 | XSS/SQL/NoSQL/パストラバーサル |
| A04:2021 – Insecure Design | OUTM-SEC-09 | ページフィールドのバリデーション欠如を文書化 |
| A05:2021 – Security Misconfiguration | OUTM-SEC-06, OUTM-SEC-10 | 機密情報フィールドの不在、エラーメッセージの安全性 |
| A08:2021 – Software/Data Integrity | OUTM-SEC-04, OUTM-SEC-05 | 特殊文字のハンドリング |
| DoS耐性 | OUTM-SEC-03, OUTM-SEC-08 | 長大文字列、ReDoS攻撃 |

```python
# test/unit/doc_reader_plugin/test_output_models_security.py
import pytest


@pytest.mark.security
class TestOutputModelsSecurity:
    """output_modelsセキュリティテスト

    注: このテストファイルは独立して実行可能にするため、
    フィクスチャをローカル定義しています。conftest.pyの
    フィクスチャと同名ですが、テストファイル単位での
    上書きはpytestで許可されています。
    """

    @pytest.fixture
    def required_compliance_fields(self):
        """ComplianceDetails必須フィールド（セキュリティテスト用）"""
        from app.doc_reader_plugin.output_models import Severity
        return {
            "recommendationId": "SEC-001",
            "title": "テスト",
            "description": "説明",
            "rationale": "理由",
            "impact": "影響",
            "severity": Severity.MEDIUM,
            "severity_reason": "理由"
        }

    def test_xss_payload_in_string_fields(self, required_compliance_fields):
        """OUTM-SEC-01: XSSペイロード耐性

        HTML/JavaScriptインジェクション文字列がモデルに保存されても、
        Pydanticモデル自体はエスケープを行わない（出力時の責任）。
        データの整合性が保たれることを確認。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        xss_payload = '<script>alert("XSS")</script>'

        # Act
        details = ComplianceDetails(
            **required_compliance_fields,
            additionalInformation=[xss_payload]
        )

        # Assert
        # XSSペイロードはそのまま保存される（モデルの責任ではない）
        assert details.additionalInformation[0] == xss_payload
        # 出力時にはフロントエンドでエスケープが必要

    def test_sql_injection_in_string_fields(self, required_compliance_fields):
        """OUTM-SEC-02: SQLインジェクション耐性

        SQL文字列がモデルに保存されても、データの整合性が保たれることを確認。
        実際のSQLクエリ実行はモデルの責任外。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        sql_injection = "'; DROP TABLE users;--"

        # Act
        details = ComplianceDetails(
            **{**required_compliance_fields, "title": sql_injection}
        )

        # Assert
        # SQL文字列はそのまま保存される
        assert details.title == sql_injection

    def test_large_string_dos_resistance(self, required_compliance_fields):
        """OUTM-SEC-03: 長大文字列DoS耐性

        1MB相当の文字列を各フィールドに設定してもメモリ枯渇せずに
        インスタンス化できることを確認。
        注: CI環境では`pytest -m slow`で10MB以上のテストを分離実行することを推奨。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        # 1MB文字列（テスト時間考慮）
        large_string = "A" * (1024 * 1024)

        # Act
        details = ComplianceDetails(
            **{**required_compliance_fields, "description": large_string}
        )

        # Assert
        assert len(details.description) == 1024 * 1024

    def test_unicode_control_characters(self, required_compliance_fields):
        """OUTM-SEC-04: Unicode制御文字耐性

        制御文字（改行、タブ、NULL等）を含む文字列が正常に処理されることを確認。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        control_chars_string = "テスト\n\t\r\x00\x1f制御文字"

        # Act
        details = ComplianceDetails(
            **{**required_compliance_fields, "description": control_chars_string}
        )

        # Assert
        assert "\n" in details.description
        assert "\t" in details.description
        assert "\x00" in details.description

    def test_null_byte_injection(self, required_compliance_fields):
        """OUTM-SEC-05: NULLバイトインジェクション耐性

        NULLバイト（\x00）を含む文字列が正常に処理されることを確認。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import ComplianceDetails

        null_byte_string = "テスト\x00後の文字列"

        # Act
        details = ComplianceDetails(
            **{**required_compliance_fields, "title": null_byte_string}
        )

        # Assert
        assert details.title == null_byte_string
        assert "\x00" in details.title

    def test_no_sensitive_fields_in_model(self):
        """OUTM-SEC-06: 機密情報フィールドの不在確認

        モデルにAPIキーやパスワード等の機密情報フィールドが
        定義されていないことを確認。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import (
            ImageDiscription, Compliance, ComplianceDetails
        )

        sensitive_field_patterns = [
            "api_key", "apikey", "password", "secret",
            "token", "credential", "auth", "private_key"
        ]

        # Act
        all_fields = set()
        for model in [ImageDiscription, Compliance, ComplianceDetails]:
            all_fields.update(model.model_fields.keys())

        # Assert
        for pattern in sensitive_field_patterns:
            for field in all_fields:
                assert pattern not in field.lower(), \
                    f"機密情報フィールド '{field}' がモデルに存在します"

    def test_type_coercion_dict_to_string(self, required_compliance_fields):
        """OUTM-SEC-07: 型強制バイパス防止（dict型注入）

        dict型をpageフィールドに注入しても、Pydanticの型強制により
        文字列に変換される。NoSQLインジェクションパターン（{"$ne": 1}等）は
        文字列化されるため無効化される。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        nosql_injection = {"$ne": 1}

        # Act
        compliance = Compliance(
            id="SEC-001",
            title="テスト",
            discription="説明",
            page=nosql_injection  # dict型注入
        )

        # Assert
        # dictは文字列に変換される（NoSQLインジェクション無効化）
        assert isinstance(compliance.page, str)
        assert compliance.page == str(nosql_injection)

    @pytest.mark.slow
    def test_page_field_redos_resistance(self, required_compliance_fields):
        """OUTM-SEC-08: pageフィールドReDoS耐性

        大量のカンマ区切りページ指定でも処理時間が妥当な範囲内であることを確認。
        将来バリデータが追加された場合のReDoS攻撃耐性を検証。

        注: CI環境の負荷によりフレークする可能性があるため、
        閾値を3秒に設定し、@pytest.mark.slowマーカーを付与。
        通常のテスト実行では`pytest -m "not slow"`で除外可能。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance
        import time

        # ReDoSペイロード：約6000文字のカンマ区切りページ指定（range(1000)で生成）
        redos_payload = ",".join([f"{i}-{i+1}" for i in range(1000)])

        # Act
        start = time.time()
        compliance = Compliance(
            id="SEC-001",
            title="テスト",
            discription="説明",
            page=redos_payload
        )
        elapsed = time.time() - start

        # Assert
        # CI負荷を考慮して閾値を3秒に設定（ローカルでは通常0.1秒未満）
        assert elapsed < 3.0, f"ReDoS検出: 処理時間{elapsed}秒"
        assert compliance.page == redos_payload

    def test_path_traversal_payload_stored(self, required_compliance_fields):
        """OUTM-SEC-09: パストラバーサルペイロード保存

        pageフィールドにパストラバーサルペイロードが入力されても、
        現在の実装ではバリデーションがないため文字列として保存される。
        これは制限事項#2として文書化済み。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import Compliance

        path_traversal = "../../../etc/passwd"

        # Act
        compliance = Compliance(
            id="SEC-001",
            title="テスト",
            discription="説明",
            page=path_traversal
        )

        # Assert
        # パストラバーサルペイロードはそのまま保存される
        assert compliance.page == path_traversal

    def test_severity_error_message_safety(self):
        """OUTM-SEC-10: Severityエラーメッセージの安全性

        無効なSeverity値のエラーメッセージにスタックトレースや
        内部パス情報が含まれないことを確認。
        """
        # Arrange
        from app.doc_reader_plugin.output_models import Severity

        # Act
        try:
            Severity("InvalidSeverity")
            assert False, "ValueErrorが発生するはず"
        except ValueError as e:
            error_message = str(e)

        # Assert
        # 内部パスやスタックトレースが含まれないこと
        sensitive_patterns = [
            "/usr/", "/home/", "site-packages",
            "Traceback", "File \"", ".py\""
        ]
        for pattern in sensitive_patterns:
            assert pattern not in error_message, \
                f"エラーメッセージに機密情報パターン'{pattern}'が含まれています"
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `reset_output_models_module` | モジュール状態リセット（必要時のみ） | function | No |
| `required_compliance_fields` | ComplianceDetails必須フィールドセット | function | No |

### 共通フィクスチャ定義

```python
# test/unit/doc_reader_plugin/conftest.py（追加）
import sys
import pytest


@pytest.fixture
def reset_output_models_module():
    """モジュールのグローバル状態をリセット（必要時のみ使用）

    注: Pydanticモデル定義は静的なため、通常このフィクスチャは不要です。
    モジュールレベルの状態変更（例：動的なConfig変更）をテストする場合のみ使用してください。
    autouse=Falseに設定しているため、必要なテストで明示的に引数として受け取ってください。

    使用例:
        def test_with_reset(self, reset_output_models_module):
            # このテストではモジュールがリセットされる
            ...
    """
    yield

    # テスト後にクリーンアップ
    modules_to_remove = [
        key for key in sys.modules
        if key.startswith("app.doc_reader_plugin.output_models")
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def required_compliance_fields():
    """ComplianceDetails必須フィールドのセット"""
    from app.doc_reader_plugin.output_models import Severity
    return {
        "recommendationId": "REC-001",
        "title": "S3バケットの暗号化",
        "description": "S3バケットでサーバー側暗号化を有効にする",
        "rationale": "保存データの機密性を確保するため",
        "impact": "暗号化されていない場合、データ漏洩時に情報が平文で流出",
        "severity": Severity.HIGH,
        "severity_reason": "機密データを扱うため高リスク"
    }
```

---

## 6. テスト実行例

```bash
# output_models関連テストのみ実行
pytest test/unit/doc_reader_plugin/test_output_models.py -v

# 特定のテストクラスのみ実行
pytest test/unit/doc_reader_plugin/test_output_models.py::TestComplianceDetails -v

# カバレッジ付きで実行
pytest test/unit/doc_reader_plugin/test_output_models.py --cov=app.doc_reader_plugin.output_models --cov-report=term-missing -v

# セキュリティマーカーで実行
pytest test/unit/doc_reader_plugin/test_output_models_security.py -m "security" -v

# エラーハンドリングテストのみ実行
pytest test/unit/doc_reader_plugin/test_output_models.py -k "Error" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 24 | OUTM-001 〜 OUTM-022（001b, 010b含む） |
| 異常系 | 12 | OUTM-E01 〜 OUTM-E11（E05b含む） |
| セキュリティ | 10 | OUTM-SEC-01 〜 OUTM-SEC-10 |
| **合計** | **46** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestImageDiscription` | OUTM-001, OUTM-001b | 2 |
| `TestCompliance` | OUTM-002〜OUTM-004 | 3 |
| `TestSeverity` | OUTM-005〜OUTM-010, OUTM-010b | 7 |
| `TestComplianceDetails` | OUTM-011〜OUTM-022 | 12 |
| `TestImageDiscriptionErrors` | OUTM-E01〜OUTM-E02 | 2 |
| `TestComplianceErrors` | OUTM-E03〜OUTM-E04 | 2 |
| `TestSeverityErrors` | OUTM-E05, OUTM-E05b | 2 |
| `TestComplianceDetailsErrors` | OUTM-E06〜OUTM-E11 | 6 |
| `TestOutputModelsSecurity` | OUTM-SEC-01〜OUTM-SEC-10 | 10 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

### 型強制に関するテストの注意

以下のテストはPydanticの型強制（Type Coercion）挙動を検証します。ValidationErrorは発生せず、正常に変換されます：

| テストID | 入力 | 挙動 |
|---------|------|------|
| OUTM-E02 | discription=123 | 文字列"123"に変換 |
| OUTM-E04 | page=123 | 文字列"123"に変換 |
| OUTM-SEC-07 | page={"$ne": 1} | 文字列に変換（NoSQLインジェクション無効化） |

> **前提条件**: これらのテストは現在の`output_models.py`が**Pydantic strict mode（`model_config = ConfigDict(strict=True)`）を使用していない**ことを前提としています。
>
> **Config変更時の対応**: 将来モデルにstrict設定が追加された場合、上記テストはValidationErrorを期待する形に修正が必要です。その際は以下のように変更してください：
> ```python
> # strict=True設定後の修正例
> with pytest.raises(ValidationError):
>     ImageDiscription(discription=123)
> ```

### 注意事項

- テスト実行には `pydantic` パッケージが必要です（プロジェクトの依存関係に含まれる）
- `@pytest.mark.security` および `@pytest.mark.slow` マーカーを `pyproject.toml` に登録してください：
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "security: セキュリティ関連テスト",
      "slow: 実行時間が長いテスト（CI分離実行推奨）",
  ]
  ```
- CI環境では`pytest -m "not slow"`でslowマーカー付きテストを除外可能
- Pydantic v2 APIを使用（`model_dump()`, `model_fields`, `model_json_schema()`）
- フィールド名の typo（`discription`）は実装をそのままテストします

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 |
|---|---------|------|--------|
| 1 | フィールド名に typo あり（`discription`） | 他システムとの連携時に混乱の可能性 | 互換性を維持しつつリファクタリング検討 |
| 2 | ページ番号フォーマットのバリデーションなし | 不正なページ指定を検出できない | カスタムバリデータの追加検討 |
| 3 | Severityの大文字小文字区別 | "high"と"High"で異なる挙動 | ドキュメント化、または大文字小文字無視バリデータ追加 |
| 4 | XSS/SQLインジェクション対策はモデル責任外 | 出力時に脆弱性が生じる可能性 | フロントエンド/DB層でのエスケープ必須 |
| 5 | 文字列長の上限なし | 極端に長い入力でメモリ消費増大 | 必要に応じて`max_length`バリデータ追加 |
| 6 | リスト項目数の上限なし | audit/remediationに大量項目でメモリ消費 | 必要に応じて項目数制限バリデータ追加 |
