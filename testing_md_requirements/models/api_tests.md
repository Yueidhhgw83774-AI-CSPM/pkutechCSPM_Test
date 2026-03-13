# models/api テストケース

## ⚠️ 重要なセキュリティ警告

### 🚨 これらのモデルはセキュリティ検証を行いません

Pydanticモデルは**型検証のみ**を行います。以下のセキュリティ対策は**必ず上位層で実装**してください：

| 脅威 | 影響度 | 対策レイヤー | 必須対策 |
|-----|--------|------------|---------|
| Command Injection | **Critical** | Router/Service | `subprocess`等でfilename使用厳禁 |
| CRLF Injection | **High** | Router | HTTPヘッダー設定前に`\r\n`除去 |
| Path Traversal | **High** | Service | `os.path.basename()` + allowlist検証 |
| JWT alg=none | **Critical** | Middleware | `jwt.decode(algorithms=['HS256'])` 明示 |
| Large Input DoS | **Medium** | FastAPI/Starlette | リクエストボディサイズ制限（例: カスタムミドルウェアまたはリバースプロキシで制限） |
| XSS | **Medium** | Frontend | Jinja2 autoescapeまたはReact自動エスケープ |

### 絶対にやってはいけないこと

```python
# ❌ NEVER DO THIS - Command Injection
import subprocess
request = Base64TextRequest(...)
subprocess.run(f"process_file {request.filename}", shell=True)  # RCE脆弱性

# ❌ NEVER DO THIS - Path Traversal
import shutil
request = Base64TextRequest(filename="../../../etc/passwd", ...)
shutil.copy(request.filename, "/tmp/upload/")  # 任意ファイル読み取り

# ❌ NEVER DO THIS - CRLF Injection
from fastapi import Response
request = Base64TextRequest(...)
return Response(
    headers={"Content-Disposition": f"attachment; filename={request.filename}"}
)  # HTTPレスポンス分割

# ❌ NEVER DO THIS - JWT without algorithm specification
import jwt
request = Base64TextRequest(...)
jwt.decode(request.session_id, key, verify=True)  # alg=none bypass
```

---

## 1. 概要

API共通のリクエスト/レスポンスモデルを定義するモジュールのテストケースを定義します。`ProcessTextFileResponse`（テキストファイル処理レスポンス）と`Base64TextRequest`（Base64エンコードされたテキストリクエスト）の2つのPydanticモデルを包括的にテストします。

> **Pydantic バージョン要件: v2**
>
> 本仕様書は **Pydantic v2 (`pydantic>=2.0`)** を正式なターゲットとしています。
>
> **必須対応**: `pyproject.toml` に以下を明記してください：
> ```toml
> [project]
> dependencies = [
>     "pydantic>=2.0,<3.0",
> ]
> ```
>
> **v2専用API使用箇所**:
> - `model_dump()` (v1: `dict()`)
> - `model_validate()` (v1: `parse_obj()`)
> - `model_dump_json()` (v1: `json()`)
> - `model_validate_json()` (v1: `parse_raw()`)
> - `model_config = ConfigDict(...)` (v1: `class Config`)
>
> ※ 本プロジェクトはPydantic v2形式（`model_config = ConfigDict(...)`）に移行済みです。

### 1.1 主要機能

| 機能 | 説明 |
|------|------|
| `ProcessTextFileResponse` | 構造化されたコンプライアンスアイテム、メッセージ、ソースファイル名を含むレスポンスモデル |
| `Base64TextRequest` | Base64エンコードされたファイル内容と関連メタデータを含むリクエストモデル |

### 1.2 カバレッジ目標: 90%

> **注記**: シンプルなPydanticモデル定義だが、API境界で使用されるため高いカバレッジを設定。必須フィールドとオプションフィールドの検証が重要。

### 1.3 主要ファイル

| ファイル | パス |
|---------|------|
| テスト対象 | `app/models/api.py` |
| テストコード | `test/unit/models/test_api.py` |
| conftest | `test/unit/models/conftest.py` |
| 依存モジュール | `app/models/compliance.py` |

> **実装上の注記**: `ProcessTextFileResponse`と`Base64TextRequest`は`app/models/api.py`と`app/models/compliance.py`の両方に定義されています。本テスト仕様書は`app/models/api.py`を正式なテスト対象とします。重複解消については実装タスクとして別途対応が必要です。

### 1.4 補足情報

**モデル一覧（2モデル）:**

| カテゴリ | モデル名 | 行番号 | 説明 |
|---------|---------|--------|------|
| レスポンス | `ProcessTextFileResponse` | 5-8 | テキストファイル処理結果のレスポンスモデル |
| リクエスト | `Base64TextRequest` | 10-13 | Base64エンコードされたファイルのリクエストモデル |

**フィールド詳細:**

| モデル | フィールド | 型 | 必須 | デフォルト |
|--------|----------|-----|------|-----------|
| `ProcessTextFileResponse` | `structured_items` | `List[ComplianceItem]` | Yes | - |
| `ProcessTextFileResponse` | `message` | `str` | Yes | - |
| `ProcessTextFileResponse` | `source_filename` | `str` | Yes | - |
| `Base64TextRequest` | `filename` | `str` | Yes | - |
| `Base64TextRequest` | `file_content_base64` | `str` | Yes | - |
| `Base64TextRequest` | `session_id` | `Optional[str]` | No | `None` |

**依存関係:**

- `ComplianceItem`（`app/models/compliance.py`）: 複雑なネストモデル

---

## 2. 正常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| API-001 | ProcessTextFileResponse 最小構成 | 空リスト + 必須フィールド | 正常生成 |
| API-002 | ProcessTextFileResponse 単一ComplianceItem | 1アイテム | 正常生成 |
| API-003 | ProcessTextFileResponse 複数ComplianceItem | 複数アイテム | 正常生成 |
| API-004 | ProcessTextFileResponse 完全構成ComplianceItem | 全フィールド指定 | 正常生成 |
| API-005 | Base64TextRequest 最小構成 | filename + base64 | 正常生成、session_id=None |
| API-006 | Base64TextRequest session_id付き | 全フィールド指定 | 正常生成 |
| API-007 | Base64TextRequest 空session_id | session_id="" | 正常生成 |
| API-008 | model_dump 辞書変換検証 | 両モデル | 正しい辞書形式 |
| API-009 | model_validate 辞書からの生成 | 辞書データ | 正常生成 |
| API-010 | JSON往復変換テスト | model_dump_json→model_validate_json | データ一致 |
| API-011 | Base64TextRequest 大きなBase64コンテンツ | 1MBのBase64文字列 | 正常生成 |
| API-012 | ProcessTextFileResponse 日本語メッセージ | 日本語文字列 | 正常生成 |
| API-013 | Base64TextRequest 日本語ファイル名 | 日本語ファイル名 | 正常生成 |
| API-014 | ProcessTextFileResponse ネストしたComplianceItem | sourceDocument付き | 正常生成 |
| API-015 | model_dump by_aliasパラメータ検証 | by_alias=True/False | 両方の出力が正常 |

### 2.1 ProcessTextFileResponse テスト

```python
# test/unit/models/test_api.py
import pytest
from app.models.api import ProcessTextFileResponse, Base64TextRequest
from app.models.compliance import ComplianceItem, SourceDocumentInfoModel, RelatedControlMappingModel


class TestProcessTextFileResponse:
    """ProcessTextFileResponseモデルのテスト"""

    def test_minimal_config(self):
        """API-001: ProcessTextFileResponse 最小構成"""
        # Arrange & Act
        response = ProcessTextFileResponse(
            structured_items=[],
            message="Processing completed",
            source_filename="test.pdf"
        )

        # Assert
        assert response.structured_items == []
        assert response.message == "Processing completed"
        assert response.source_filename == "test.pdf"

    def test_single_compliance_item(self):
        """API-002: ProcessTextFileResponse 単一ComplianceItem"""
        # Arrange
        item = ComplianceItem(
            recommendationId="REC-001",
            title="Test Recommendation"
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[item],
            message="Found 1 item",
            source_filename="compliance.pdf"
        )

        # Assert
        assert len(response.structured_items) == 1
        assert response.structured_items[0].recommendationId == "REC-001"
        assert response.structured_items[0].title == "Test Recommendation"

    def test_multiple_compliance_items(self):
        """API-003: ProcessTextFileResponse 複数ComplianceItem"""
        # Arrange
        items = [
            ComplianceItem(recommendationId="REC-001", title="First"),
            ComplianceItem(recommendationId="REC-002", title="Second"),
            ComplianceItem(recommendationId="REC-003", title="Third"),
        ]

        # Act
        response = ProcessTextFileResponse(
            structured_items=items,
            message="Found 3 items",
            source_filename="multi.pdf"
        )

        # Assert
        assert len(response.structured_items) == 3
        assert response.structured_items[0].title == "First"
        assert response.structured_items[2].title == "Third"

    def test_full_compliance_item(self):
        """API-004: ProcessTextFileResponse 完全構成ComplianceItem"""
        # Arrange
        source_doc = SourceDocumentInfoModel(
            filename="CIS_AWS_v1.5.pdf",
            type="CIS Benchmark",
            version="1.5"
        )
        related_control = RelatedControlMappingModel(
            framework="NIST",
            controlId="AC-2",
            version="Rev 5",
            description="Account Management"
        )
        item = ComplianceItem(
            recommendationId="CIS-1.1",
            title="Ensure MFA is enabled for root account",
            sourceDocument=source_doc,
            targetClouds=["aws"],
            description="Enable MFA for the root account",
            rationale="Root account has full access",
            impact="Low",
            audit=["Check AWS Console", "Use CLI"],
            remediation=["Enable MFA in IAM"],
            relatedControls=[related_control],
            severity="High",
            category=["Identity and Access Management"]
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[item],
            message="Extracted CIS benchmark",
            source_filename="CIS_AWS_v1.5.pdf"
        )

        # Assert
        assert response.structured_items[0].sourceDocument.type == "CIS Benchmark"
        assert response.structured_items[0].targetClouds == ["aws"]
        assert response.structured_items[0].relatedControls[0].framework == "NIST"

    def test_nested_compliance_item(self):
        """API-014: ProcessTextFileResponse ネストしたComplianceItem"""
        # Arrange
        source_doc = SourceDocumentInfoModel(
            filename="NIST_SP_800-53.pdf",
            type="NIST SP 800-53",
            version="Rev 5"
        )
        item = ComplianceItem(
            recommendationId="NIST-AC-1",
            title="Access Control Policy",
            sourceDocument=source_doc,
            targetClouds=["aws", "azure", "gcp"]
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[item],
            message="NIST framework processed",
            source_filename="nist.pdf"
        )

        # Assert
        assert response.structured_items[0].sourceDocument is not None
        assert response.structured_items[0].sourceDocument.filename == "NIST_SP_800-53.pdf"

    def test_japanese_message(self):
        """API-012: ProcessTextFileResponse 日本語メッセージ"""
        # Arrange & Act
        response = ProcessTextFileResponse(
            structured_items=[],
            message="処理が完了しました。5件のアイテムを抽出しました。",
            source_filename="セキュリティ基準.pdf"
        )

        # Assert
        assert "処理が完了しました" in response.message
        assert response.source_filename == "セキュリティ基準.pdf"
```

### 2.2 Base64TextRequest テスト

```python
import base64


class TestBase64TextRequest:
    """Base64TextRequestモデルのテスト"""

    def test_minimal_config(self):
        """API-005: Base64TextRequest 最小構成"""
        # Arrange
        content = base64.b64encode(b"Hello, World!").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64=content
        )

        # Assert
        assert request.filename == "test.txt"
        assert request.file_content_base64 == content
        assert request.session_id is None

    def test_with_session_id(self):
        """API-006: Base64TextRequest session_id付き"""
        # Arrange
        content = base64.b64encode(b"Test content").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="document.pdf",
            file_content_base64=content,
            session_id="user123:session-456"
        )

        # Assert
        assert request.filename == "document.pdf"
        assert request.session_id == "user123:session-456"

    def test_empty_session_id(self):
        """API-007: Base64TextRequest 空session_id"""
        # Arrange
        content = base64.b64encode(b"Content").decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64=content,
            session_id=""
        )

        # Assert
        assert request.session_id == ""

    def test_large_base64_content(self):
        """API-011: Base64TextRequest 大きなBase64コンテンツ"""
        # Arrange
        # 1MBのバイナリデータをBase64エンコード
        large_content = b"A" * (1 * 1024 * 1024)
        large_base64 = base64.b64encode(large_content).decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="large_file.bin",
            file_content_base64=large_base64
        )

        # Assert
        # Base64は約33%サイズ増加するため、約1.37MB
        assert len(request.file_content_base64) > 1 * 1024 * 1024

    def test_japanese_filename(self):
        """API-013: Base64TextRequest 日本語ファイル名"""
        # Arrange
        content = base64.b64encode("日本語コンテンツ".encode('utf-8')).decode('utf-8')

        # Act
        request = Base64TextRequest(
            filename="コンプライアンス規約書.pdf",
            file_content_base64=content
        )

        # Assert
        assert request.filename == "コンプライアンス規約書.pdf"
```

### 2.3 シリアライズ/デシリアライズ テスト

```python
class TestApiModelSerialization:
    """APIモデルのシリアライズ/デシリアライズテスト"""

    def test_model_dump_dict(self):
        """API-008: model_dump 辞書変換検証

        Note: model_dump()は辞書を返す。JSON文字列はmodel_dump_json()で取得。
        """
        # Arrange
        item = ComplianceItem(recommendationId="REC-001", title="Test")
        response = ProcessTextFileResponse(
            structured_items=[item],
            message="OK",
            source_filename="test.pdf"
        )
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64="dGVzdA==",
            session_id="session-123"
        )

        # Act
        response_dict = response.model_dump()
        request_dict = request.model_dump()

        # Assert
        assert isinstance(response_dict, dict)
        assert isinstance(request_dict, dict)
        assert response_dict["message"] == "OK"
        assert response_dict["source_filename"] == "test.pdf"
        assert len(response_dict["structured_items"]) == 1
        assert request_dict["filename"] == "test.txt"
        assert request_dict["session_id"] == "session-123"

    def test_model_validate_from_dict(self):
        """API-009: model_validate 辞書からの生成"""
        # Arrange
        response_data = {
            "structured_items": [
                {"recommendationId": "REC-001", "title": "Test Item"}
            ],
            "message": "Processed successfully",
            "source_filename": "input.pdf"
        }
        request_data = {
            "filename": "document.txt",
            "file_content_base64": "SGVsbG8=",
            "session_id": "user:session"
        }

        # Act
        response = ProcessTextFileResponse.model_validate(response_data)
        request = Base64TextRequest.model_validate(request_data)

        # Assert
        assert response.structured_items[0].recommendationId == "REC-001"
        assert response.message == "Processed successfully"
        assert request.filename == "document.txt"
        assert request.session_id == "user:session"

    def test_model_json_round_trip(self):
        """API-010: JSON往復変換テスト"""
        # Arrange
        original_item = ComplianceItem(
            recommendationId="REC-001",
            title="Original Title",
            targetClouds=["aws", "azure"]
        )
        original_response = ProcessTextFileResponse(
            structured_items=[original_item],
            message="Original message",
            source_filename="original.pdf"
        )
        original_request = Base64TextRequest(
            filename="round_trip.txt",
            file_content_base64="cm91bmQgdHJpcA==",
            session_id="round-trip-session"
        )

        # Act
        response_json = original_response.model_dump_json()
        request_json = original_request.model_dump_json()
        restored_response = ProcessTextFileResponse.model_validate_json(response_json)
        restored_request = Base64TextRequest.model_validate_json(request_json)

        # Assert
        assert restored_response.message == original_response.message
        assert restored_response.source_filename == original_response.source_filename
        assert restored_response.structured_items[0].title == "Original Title"
        assert restored_request.filename == original_request.filename
        assert restored_request.session_id == original_request.session_id

    def test_model_dump_by_alias_parameter(self):
        """API-015: model_dump の by_alias パラメータ動作検証

        model_dump(by_alias=True/False) の動作を確認。
        現行モデルではフィールド名とエイリアスが同一のため出力結果は同じだが、
        by_alias パラメータが正しく機能することを検証する。

        Note: 真のエイリアス検証が必要な場合は、フィールド名とエイリアスが
        異なるフィールドをモデルに追加する必要がある。
        """
        # Arrange
        item_data = {
            "recommendationId": "REC-001",
            "sourceDocument": {
                "filename": "test.pdf",
                "type": "CIS Benchmark",
                "version": "1.0"
            },
            "targetClouds": ["aws", "azure"],
            "relatedControls": [
                {"framework": "NIST", "controlId": "AC-1", "version": "Rev 5"}
            ]
        }

        # Act
        item = ComplianceItem.model_validate(item_data)
        dumped_with_alias = item.model_dump(by_alias=True)
        dumped_without_alias = item.model_dump(by_alias=False)

        # Assert - by_alias パラメータが受け入れられることを確認
        # 現行モデルではフィールド名=エイリアスのため、両方の出力は同一
        assert "recommendationId" in dumped_with_alias
        assert "recommendationId" in dumped_without_alias
        assert dumped_with_alias["relatedControls"][0]["controlId"] == "AC-1"
        assert dumped_without_alias["relatedControls"][0]["controlId"] == "AC-1"

        # モデル属性へのアクセスは常にフィールド名
        assert item.recommendationId == "REC-001"
        assert item.relatedControls[0].controlId == "AC-1"

        # by_alias=True と by_alias=False の結果が同一であることを確認
        # （フィールド名とエイリアスが同一のモデル設計のため）
        assert dumped_with_alias == dumped_without_alias
```

---

## 3. 異常系テストケース

| ID | テスト名 | 入力 | 期待結果 |
|----|---------|------|---------|
| API-E01 | ProcessTextFileResponse structured_items欠落 | message + source_filename | ValidationError |
| API-E02 | ProcessTextFileResponse message欠落 | structured_items + source_filename | ValidationError |
| API-E03 | ProcessTextFileResponse source_filename欠落 | structured_items + message | ValidationError |
| API-E04 | ProcessTextFileResponse structured_items型不正 | string | ValidationError |
| API-E05 | ProcessTextFileResponse 全フィールド欠落 | なし | ValidationError |
| API-E06 | Base64TextRequest filename欠落 | file_content_base64 | ValidationError |
| API-E07 | Base64TextRequest file_content_base64欠落 | filename | ValidationError |
| API-E08 | Base64TextRequest 全フィールド欠落 | なし | ValidationError |
| API-E09 | Base64TextRequest filename型不正 | int | ValidationError |
| API-E10 | ProcessTextFileResponse message型不正 | int | ValidationError |
| API-E11 | ProcessTextFileResponse source_filename型不正 | list | ValidationError |
| API-E12 | Base64TextRequest file_content_base64型不正 | int | ValidationError |
| API-E13 | Base64TextRequest session_id型不正 | int | ValidationError |

### 3.1 バリデーションエラーテスト

```python
from pydantic import ValidationError


class TestApiValidationErrors:
    """APIモデルのバリデーションエラーテスト"""

    def test_response_missing_structured_items(self):
        """API-E01: ProcessTextFileResponse structured_items欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                message="Test",
                source_filename="test.pdf"
            )

        # バリデーションエラーの詳細確認
        errors = exc_info.value.errors()
        assert any("structured_items" in str(e) for e in errors)

    def test_response_missing_message(self):
        """API-E02: ProcessTextFileResponse message欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                source_filename="test.pdf"
            )

        errors = exc_info.value.errors()
        assert any("message" in str(e) for e in errors)

    def test_response_missing_source_filename(self):
        """API-E03: ProcessTextFileResponse source_filename欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                message="Test"
            )

        errors = exc_info.value.errors()
        assert any("source_filename" in str(e) for e in errors)

    def test_response_structured_items_wrong_type(self):
        """API-E04: ProcessTextFileResponse structured_items型不正"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items="not a list",  # type: ignore  # 意図的な型違反テスト
                message="Test",
                source_filename="test.pdf"
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_response_all_fields_missing(self):
        """API-E05: ProcessTextFileResponse 全フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse()

        errors = exc_info.value.errors()
        # 3つの必須フィールドが欠落
        assert len(errors) >= 3

    def test_request_missing_filename(self):
        """API-E06: Base64TextRequest filename欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                file_content_base64="dGVzdA=="
            )

        errors = exc_info.value.errors()
        assert any("filename" in str(e) for e in errors)

    def test_request_missing_file_content_base64(self):
        """API-E07: Base64TextRequest file_content_base64欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename="test.txt"
            )

        errors = exc_info.value.errors()
        assert any("file_content_base64" in str(e) for e in errors)

    def test_request_all_fields_missing(self):
        """API-E08: Base64TextRequest 全フィールド欠落"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest()

        errors = exc_info.value.errors()
        # 2つの必須フィールドが欠落
        assert len(errors) >= 2

    def test_request_filename_wrong_type(self):
        """API-E09: Base64TextRequest filename型不正"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename=12345,  # type: ignore  # 意図的な型違反テスト
                file_content_base64="dGVzdA=="
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_response_message_wrong_type(self):
        """API-E10: ProcessTextFileResponse message型不正"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                message=12345,  # type: ignore  # 意図的な型違反テスト
                source_filename="test.pdf"
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_response_source_filename_wrong_type(self):
        """API-E11: ProcessTextFileResponse source_filename型不正"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ProcessTextFileResponse(
                structured_items=[],
                message="Test",
                source_filename=["not", "a", "string"]  # type: ignore  # 意図的な型違反テスト
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_request_file_content_base64_wrong_type(self):
        """API-E12: Base64TextRequest file_content_base64型不正"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename="test.txt",
                file_content_base64=12345  # type: ignore  # 意図的な型違反テスト
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1

    def test_request_session_id_wrong_type(self):
        """API-E13: Base64TextRequest session_id型不正"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            Base64TextRequest(
                filename="test.txt",
                file_content_base64="dGVzdA==",
                session_id=12345  # type: ignore  # 意図的な型違反テスト
            )

        errors = exc_info.value.errors()
        assert len(errors) >= 1
```

---

## 4. セキュリティテストケース

| ID | テスト名 | 入力 | 期待結果 | OWASP項目 |
|----|---------|------|---------|-----------|
| API-SEC-01 | Base64TextRequestパストラバーサル | ../../../etc/passwd | 文字列として格納 | A01 |
| API-SEC-02 | Base64TextRequest NULLバイトインジェクション | test.txt\x00.exe | 文字列として格納 | A03 |
| API-SEC-03 | ProcessTextFileResponse XSSペイロード | scriptタグ | 文字列として格納 | A03 |
| API-SEC-04 | Base64TextRequest 不正なBase64文字列 | 不正な文字を含む | 文字列として格納 | A02 |
| API-SEC-05 | session_id SQLインジェクション | SQLインジェクション文字列 | 文字列として格納 | A03 |
| API-SEC-06 | 巨大文字列入力によるDoS | 1MB文字列 | 受け入れ（サイズ制限は上位層） | A05 |
| API-SEC-07 | session_id JWT署名改ざん検出 | 改ざんされたJWT | 文字列として格納 | A07 |
| API-SEC-08 | OpenSearchインジェクション | OpenSearchクエリ | 文字列として格納 | A03 |
| API-SEC-09 | SSRF URL in filename | 内部IP URL | 文字列として格納 | A10 |
| API-SEC-10 | Commandインジェクション | シェルメタ文字 | 文字列として格納 | A03 |
| API-SEC-11 | CRLFインジェクション | \r\n含むfilename | 文字列として格納 | A03 |
| API-SEC-12 | JWT alg=none攻撃 | alg=noneのJWT | 文字列として格納 | A07 |
| API-SEC-13 | Unicode正規化攻撃 | 紛らわしい文字 | 文字列として格納 | A03 |
| API-SEC-14 | 未定義フィールドの無視（extra） | 未定義フィールド含む入力 | 無視される | A08 |
| API-SEC-15 | ビジネスロジック不整合 | 空items + 成功メッセージ | 許容される | A04 |

```python
@pytest.mark.security
class TestApiModelsSecurity:
    """APIモデルのセキュリティテスト

    Note: これらのテストはPydanticモデルがセキュリティ制限を行わないことを
    文書化するためのものです。実際の防御は上位層で実装する必要があります。
    """

    def test_path_traversal_filename(self):
        """API-SEC-01: Base64TextRequestパストラバーサル

        OWASP A01: Broken Access Control
        Note: Pydanticモデルはファイル名のバリデーションを行わない。
        パストラバーサル対策はファイル保存時に行う必要がある。
        """
        # Arrange
        malicious_filename = "../../../etc/passwd"

        # Act
        request = Base64TextRequest(
            filename=malicious_filename,
            file_content_base64="dGVzdA=="
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert request.filename == malicious_filename
        # 重要: ファイル保存時にパスの正規化と検証が必要

    def test_null_byte_injection_filename(self):
        """API-SEC-02: Base64TextRequest NULLバイトインジェクション

        OWASP A03: Injection
        Note: NULLバイトを含むファイル名は一部システムで切り詰められる可能性がある。
        """
        # Arrange
        malicious_filename = "safe.txt\x00.exe"

        # Act
        request = Base64TextRequest(
            filename=malicious_filename,
            file_content_base64="dGVzdA=="
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert "\x00" in request.filename
        # 重要: ファイル保存前にNULLバイトを除去する必要がある

    def test_xss_payload_in_message(self):
        """API-SEC-03: ProcessTextFileResponse XSSペイロード

        OWASP A03: Injection
        Note: Pydanticモデルは入力サニタイズを行わない。
        XSS対策はフロントエンド/レスポンス生成時に行う。
        """
        # Arrange
        xss_payload = "<script>alert('XSS')</script>"
        item = ComplianceItem(
            recommendationId="REC-001",
            title=xss_payload,
            description="<img src=x onerror=alert('XSS')>"
        )

        # Act
        response = ProcessTextFileResponse(
            structured_items=[item],
            message=xss_payload,
            source_filename="test.pdf"
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert response.message == xss_payload
        assert response.structured_items[0].title == xss_payload
        # 重要: レスポンス時にHTMLエスケープが必要

    def test_invalid_base64_content(self):
        """API-SEC-04: Base64TextRequest 不正なBase64文字列

        OWASP A02: Cryptographic Failures
        Note: PydanticはBase64フォーマットの検証を行わない。
        デコード時にエラーが発生する可能性がある。
        """
        # Arrange
        invalid_base64 = "Not!Valid@Base64#Content$"

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64=invalid_base64
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert request.file_content_base64 == invalid_base64

        # 追加検証: 実際のデコードが失敗することを確認
        import base64
        with pytest.raises(Exception):
            base64.b64decode(request.file_content_base64, validate=True)
        # 重要: デコード時に適切なエラーハンドリングが必要

    def test_sql_injection_session_id(self):
        """API-SEC-05: session_id SQLインジェクション

        OWASP A03: Injection
        Note: Pydanticモデルは入力サニタイズを行わない。
        SQLインジェクション対策はDB層（パラメータ化クエリ）で行う。
        """
        # Arrange
        sql_injection = "'; DROP TABLE sessions; --"

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64="dGVzdA==",
            session_id=sql_injection
        )

        # Assert - Pydanticは文字列をそのまま受け入れる
        assert request.session_id == sql_injection
        # 重要: DB操作時にパラメータ化クエリを使用すること

    @pytest.mark.slow
    def test_large_string_dos(self):
        """API-SEC-06: 巨大文字列入力によるDoS

        OWASP A05: Security Misconfiguration
        Note: 大きな文字列入力によるメモリ消費を確認。
        本番環境ではリクエストサイズ制限をミドルウェアで設定すべき。
        """
        # Arrange
        # 1MBの文字列（テスト実行時間を考慮して10MBから縮小）
        large_string = "A" * (1 * 1024 * 1024)

        # Act
        request = Base64TextRequest(
            filename="large.txt",
            file_content_base64=large_string
        )

        # Assert
        assert len(request.file_content_base64) == 1 * 1024 * 1024
        # 注意: FastAPIのRequestBodySizeLimitMiddlewareで制限すべき

    def test_session_id_jwt_signature_tampering(self):
        """API-SEC-07: session_id JWT署名改ざん検出

        OWASP A07: Identification and Authentication Failures
        Note: Pydanticモデルは署名検証を行わない。
        認証ミドルウェアでJWT検証が必須。
        """
        # Arrange
        # SECURITY WARNING: この文字列はJWT署名が改ざんされている例
        tampered_jwt = "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYWRtaW4ifQ.TAMPERED_SIGNATURE"

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64="dGVzdA==",
            session_id=tampered_jwt
        )

        # Assert - Pydanticは文字列として受け入れる
        assert request.session_id == tampered_jwt
        # 重要: 認証ミドルウェアでjwt.decode()時に署名検証エラーが発生すべき

    def test_opensearch_injection_in_filename(self):
        """API-SEC-08: filename内のOpenSearchクエリインジェクション

        OWASP A03: Injection
        Note: filenameがOpenSearch検索クエリに直接使用される場合、
        インジェクション攻撃が可能。エスケープ処理が必須。
        """
        # Arrange
        malicious_filename = '{"query": {"match_all": {}}}'

        # Act
        request = Base64TextRequest(
            filename=malicious_filename,
            file_content_base64="dGVzdA=="
        )

        # Assert - Pydanticは文字列として受け入れる
        assert request.filename == malicious_filename
        # 重要: OpenSearch検索時にクエリパラメータのエスケープ/サニタイズが必要

    def test_ssrf_url_in_filename(self):
        """API-SEC-09: filenameにURL含む場合のSSRF対策

        OWASP A10: Server-Side Request Forgery (SSRF)
        Note: filenameがファイルダウンロード等に使用される場合、
        外部リソースへのアクセスが発生する可能性がある。
        """
        # Arrange
        ssrf_payload = "http://169.254.169.254/latest/meta-data/iam/security-credentials/"

        # Act
        request = Base64TextRequest(
            filename=ssrf_payload,
            file_content_base64="dGVzdA=="
        )

        # Assert - Pydanticは文字列として受け入れる
        assert request.filename == ssrf_payload
        # 重要: ファイル操作前にプロトコルスキーム（http/https/ftp）の検証が必要

    def test_command_injection_filename(self):
        """API-SEC-10: filenameにシェルメタ文字を含む場合

        OWASP A03: Injection
        Note: filenameがsubprocess等で使用される場合、
        コマンドインジェクションが発生する可能性がある。
        """
        # Arrange
        malicious_payloads = [
            "test.pdf; rm -rf /",
            "test.pdf && whoami",
            "test.pdf | cat /etc/passwd",
            "$(cat /etc/shadow).pdf",
            "`id`.pdf"
        ]

        for payload in malicious_payloads:
            # Act
            request = Base64TextRequest(
                filename=payload,
                file_content_base64="dGVzdA=="
            )

            # Assert - Pydanticは文字列として受け入れる
            assert payload in request.filename
        # CRITICAL: filenameをshellコマンドで使用することは絶対禁止

    def test_crlf_injection_filename(self):
        """API-SEC-11: filenameにCRLFを含む場合のHTTPレスポンス分割

        OWASP A03: Injection
        Note: filenameがHTTPヘッダー（Content-Disposition等）に使用される場合、
        HTTPレスポンス分割攻撃が可能になる。
        """
        # Arrange
        crlf_payload = "test.pdf\r\nContent-Type: text/html\r\n\r\n<script>alert('XSS')</script>"

        # Act
        request = Base64TextRequest(
            filename=crlf_payload,
            file_content_base64="dGVzdA=="
        )

        # Assert - Pydanticは文字列として受け入れる
        assert "\r\n" in request.filename
        # CRITICAL: HTTPヘッダー設定前に\r\nを除去すること

    def test_jwt_algorithm_confusion_attack(self):
        """API-SEC-12: session_idにalg=noneのJWTを含む場合

        OWASP A07: Identification and Authentication Failures
        Note: JWT検証時にalg=noneを許可すると署名検証がバイパスされる。
        """
        # Arrange
        # JWTヘッダー: {"alg": "none", "typ": "JWT"}
        # JWTペイロード: {"user": "admin"}
        none_alg_jwt = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJ1c2VyIjoiYWRtaW4ifQ."

        # Act
        request = Base64TextRequest(
            filename="test.txt",
            file_content_base64="dGVzdA==",
            session_id=none_alg_jwt
        )

        # Assert - Pydanticは文字列として受け入れる
        assert request.session_id == none_alg_jwt
        # CRITICAL: jwt.decode()では必ずalgorithms=['HS256']等を明示すること

    def test_unicode_normalization_attack(self):
        """API-SEC-13: filenameにUnicode紛らわしい文字を含む場合

        OWASP A03: Injection
        Note: Cyrillic 'а' (U+0430) はLatin 'a' (U+0061) と見た目が同じ。
        ファイル名衝突やフィルタバイパスに悪用される可能性がある。
        """
        # Arrange
        # "testаdmin.pdf" - 'а' はCyrillic文字
        confusable_filename = "test\u0430dmin.pdf"

        # Act
        request = Base64TextRequest(
            filename=confusable_filename,
            file_content_base64="dGVzdA=="
        )

        # Assert - Pydanticは文字列として受け入れる
        assert "\u0430" in request.filename
        # 重要: ファイル操作前にNFC/NFKC正規化を適用すること

    def test_extra_fields_ignored(self):
        """API-SEC-14: 未定義フィールドの無視検証（extraフィールド）

        OWASP A08: Software and Data Integrity Failures
        Note: Pydanticはデフォルトで未定義フィールドを無視する（extra='ignore'）。
        悪意のあるフィールド（__proto__等）が含まれても、モデルには反映されない。

        前提: モデルに extra='forbid' が設定されていないこと。
        """
        # Arrange - 未定義フィールドを含む入力データ
        data_with_extra_fields = {
            "recommendationId": "REC-001",
            "title": "Test",
            "__proto__": {"isAdmin": True},  # JavaScript由来の攻撃パターン
            "constructor": {"prototype": {"isAdmin": True}},
            "unknown_field": "malicious_value",
            "admin": True
        }

        # Act
        item = ComplianceItem.model_validate(data_with_extra_fields)

        # Assert - Pydanticは未定義フィールドを無視する
        assert not hasattr(item, "isAdmin")
        assert not hasattr(item, "admin")
        assert not hasattr(item, "unknown_field")
        assert "__proto__" not in item.model_dump()
        assert "constructor" not in item.model_dump()
        assert "unknown_field" not in item.model_dump()
        # 注記: dictに変換後の処理では、元の入力データを直接使用しないこと

    def test_business_logic_inconsistency(self):
        """API-SEC-15: ビジネスロジックの不整合（空items + 成功メッセージ）

        OWASP A04: Insecure Design
        Note: Pydanticモデルはビジネスロジックの整合性を検証しない。
        矛盾した状態が許容される。
        """
        # Arrange & Act
        response = ProcessTextFileResponse(
            structured_items=[],
            message="Successfully processed 100 items",
            source_filename="test.pdf"
        )

        # Assert - Pydanticは矛盾した状態を許容する
        assert len(response.structured_items) == 0
        assert "100 items" in response.message
        # 重要: ビジネスロジックの整合性検証はサービス層で実装すること
```

---

## 5. フィクスチャ

| フィクスチャ名 | 用途 | スコープ | autouse |
|--------------|------|---------|---------|
| `sample_compliance_item` | ComplianceItemサンプル | function | No |
| `sample_base64_content` | Base64エンコードされたテストコンテンツ | function | No |
| `sample_process_response` | ProcessTextFileResponseサンプル | function | No |

> **注記**: `reset_api_module`フィクスチャ（sys.modules削除）は削除しました。Pydanticモデルはステートレスなため不要であり、sys.modules削除は型同一性の問題を引き起こす可能性があるためです。

### 共通フィクスチャ定義

```python
# test/unit/models/conftest.py に追加
import base64
import pytest
from app.models.api import ProcessTextFileResponse, Base64TextRequest
from app.models.compliance import ComplianceItem, SourceDocumentInfoModel


@pytest.fixture
def sample_compliance_item():
    """ComplianceItemサンプル"""
    source_doc = SourceDocumentInfoModel(
        filename="CIS_AWS_Benchmark.pdf",
        type="CIS Benchmark",
        version="1.5"
    )
    return ComplianceItem(
        recommendationId="CIS-1.1",
        title="Ensure MFA is enabled for root account",
        sourceDocument=source_doc,
        targetClouds=["aws"],
        description="Enable MFA for the root account to enhance security",
        severity="High",
        category=["Identity and Access Management"]
    )


@pytest.fixture
def sample_base64_content():
    """Base64エンコードされたテストコンテンツ"""
    test_content = b"This is a test PDF content for compliance document."
    return base64.b64encode(test_content).decode('utf-8')


@pytest.fixture
def sample_process_response(sample_compliance_item):
    """ProcessTextFileResponseサンプル"""
    return ProcessTextFileResponse(
        structured_items=[sample_compliance_item],
        message="Successfully processed 1 compliance item",
        source_filename="CIS_AWS_Benchmark.pdf"
    )
```

---

## 6. テスト実行例

```bash
# models/api関連テストのみ実行
pytest test/unit/models/test_api.py -v

# 特定のテストクラスのみ実行
pytest test/unit/models/test_api.py::TestProcessTextFileResponse -v
pytest test/unit/models/test_api.py::TestBase64TextRequest -v

# カバレッジ付きで実行
pytest test/unit/models/test_api.py --cov=app.models.api --cov-report=term-missing -v

# 分岐カバレッジ付きで実行
pytest test/unit/models/test_api.py --cov=app.models.api --cov-branch --cov-report=term-missing -v

# セキュリティマーカーで実行
# pyproject.toml: markers = ["security: セキュリティ関連テスト"]
pytest test/unit/models/test_api.py -m "security" -v

# 失敗したテストのみ再実行
pytest test/unit/models/test_api.py --lf -v

# 遅いテスト（DoSテスト等）を除外して実行
pytest test/unit/models/test_api.py -m "not slow" -v
```

---

## 7. テストケース一覧（サマリー）

| カテゴリ | 件数 | ID範囲 |
|---------|------|--------|
| 正常系 | 15 | API-001 〜 API-015 |
| 異常系 | 13 | API-E01 〜 API-E13 |
| セキュリティ | 15 | API-SEC-01 〜 API-SEC-15 |
| **合計** | **43** | - |

### テストクラス構成

| クラス名 | テストID | 件数 |
|---------|---------|------|
| `TestProcessTextFileResponse` | API-001〜API-004, API-012, API-014 | 6 |
| `TestBase64TextRequest` | API-005〜API-007, API-011, API-013 | 5 |
| `TestApiModelSerialization` | API-008〜API-010, API-015 | 4 |
| `TestApiValidationErrors` | API-E01〜API-E13 | 13 |
| `TestApiModelsSecurity` | API-SEC-01〜API-SEC-15 | 15 |

### 実装失敗が予想されるテスト

現時点で失敗が予想されるテストはありません。

> **注記**: セキュリティテスト（API-SEC-01〜API-SEC-15）は現在の実装で「パスする」が、これらはPydanticモデルレベルでのセキュリティ制限がないことを文書化するためのものです。入力サニタイズやフォーマット検証は上位層（ルーター、サービス）での実装を推奨しています。

### セキュリティテストカバレッジチェックリスト

**Injection Attacks (A03):**
- [x] Path Traversal (API-SEC-01)
- [x] NULL Byte Injection (API-SEC-02)
- [x] XSS Payload (API-SEC-03)
- [x] SQL Injection (API-SEC-05)
- [x] OpenSearch Injection (API-SEC-08)
- [x] Command Injection (API-SEC-10)
- [x] CRLF Injection (API-SEC-11)
- [x] Unicode Normalization (API-SEC-13)

**Authentication/Authorization (A01, A07):**
- [x] JWT Signature Tampering (API-SEC-07)
- [x] JWT Algorithm Confusion (API-SEC-12)

**Cryptographic Failures (A02):**
- [x] Invalid Base64 (API-SEC-04)

**Insecure Design (A04):**
- [x] Business Logic Inconsistency (API-SEC-15)

**Security Misconfiguration (A05):**
- [x] Large String DoS (API-SEC-06)

**Software Integrity (A08):**
- [x] Extra Fields Ignored (API-SEC-14)

**SSRF (A10):**
- [x] URL in filename (API-SEC-09)

### 注意事項

- Pydanticモデルのテストのため、`pytest-asyncio` は不要
- **カスタムマーカーの登録要**（`pyproject.toml` に追加）：
  ```toml
  [tool.pytest.ini_options]
  markers = [
      "security: セキュリティ関連テスト",
      "slow: 実行時間の長いテスト（DoSテスト等）",
  ]
  ```
  > **注記**: `--strict-markers` オプション使用時、未登録マーカーは警告/失敗になります
- `app/models/compliance.py` の `ComplianceItem` への依存あり
- Base64エンコード/デコードのテストには標準ライブラリの `base64` モジュールを使用
- `# type: ignore` コメントには理由を明示（意図的な型違反テスト）

### 実装時の検討事項

以下はセキュリティ観点から推奨される将来の改善項目です：

1. **filenameのパストラバーサル防止**
   ```python
   from pydantic import field_validator

   @field_validator('filename')
   @classmethod
   def validate_filename(cls, v):
       import os
       if '..' in v or v.startswith('/'):
           raise ValueError('Invalid filename')
       return os.path.basename(v)
   ```

2. **file_content_base64のフォーマット検証**
   ```python
   @field_validator('file_content_base64')
   @classmethod
   def validate_base64(cls, v):
       import base64
       try:
           base64.b64decode(v, validate=True)
       except Exception:
           raise ValueError('Invalid base64 encoding')
       return v
   ```

3. **session_idのフォーマット検証**
   ```python
   session_id: Optional[str] = Field(
       None,
       pattern=r"^[\w-]+:[\w-]+$"
   )
   ```

---

## 8. 既知の制限事項

| # | 制限事項 | 影響 | 対応策 | OWASP |
|---|---------|------|--------|-------|
| 1 | filenameのパストラバーサル検証なし | 悪意あるファイル名が受け入れられる | ファイル保存時にパス正規化 | A01 |
| 2 | file_content_base64のフォーマット検証なし | 不正なBase64が受け入れられる | デコード時に例外処理 | A02 |
| 3 | session_idのフォーマット検証なし | 任意の文字列が受け入れられる | ルーター層で検証 | A07 |
| 4 | 大きな文字列のサイズ制限なし | メモリ消費リスク | FastAPIミドルウェアで制限 | A05 |
| 5 | ComplianceItemの複雑なネスト構造 | テストが複雑になる | compliance.pyのテストで詳細カバー | - |
| 6 | session_idのJWT署名検証なし | 改ざんされたJWTが受け入れられる | 認証ミドルウェアで検証 | A07 |
| 7 | OpenSearchインジェクション対策なし | クエリインジェクションリスク | OpenSearch層でエスケープ | A03 |
| 8 | SSRF対策なし | 内部リソースへのアクセスリスク | URL検証を上位層で実装 | A10 |
| 9 | CRLFインジェクション対策なし | HTTPレスポンス分割リスク | HTTPヘッダー設定前に`\r\n`除去 | A03 |
| 10 | コマンドインジェクション対策なし | シェルコマンド実行リスク | filenameを絶対にshellに渡さない | A03 |
| 11 | Unicode正規化なし | ファイル名衝突リスク | NFC/NFKC正規化を適用 | A03 |
| 12 | ビジネスロジック検証なし | 不整合なレスポンス許容 | サービス層で整合性検証 | A04 |
| 13 | JWT alg=none検証なし | 署名バイパスリスク | JWT検証時にalg=noneを拒否 | A07 |

---

## 関連ドキュメント

- [compliance_tests.md](compliance_tests.md) - ComplianceItemモデルの詳細テスト（作成予定）
- [mcp_models_tests.md](mcp_models_tests.md) - MCPモデルのテスト（参考フォーマット）
- [TEMPLATE_test_spec.md](../TEMPLATE_test_spec.md) - テスト仕様書テンプレート
