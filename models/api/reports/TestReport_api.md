# models/api.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/models/api.py` |
| テスト仕様 | `docs/testing/models/api_tests.md` |
| 実行時刻 | 2026-03-13 16:39:22 |
| 総実行時間 | 0.20s |
| カバレッジ目標 | 90% |

## テスト結果統計

| カテゴリ | 総数 | 合格 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | 15 | 15 | 0 | 0 |
| 異常系 | 11 | 11 | 0 | 0 |
| セキュリティ | 15 | 15 | 0 | 0 |
| **合計** | **41** | **41** | **0** | **0** |

## テスト合格率

- **実際の合格率**: 100.0%
- **有効合格率** (予期された失敗を除く): 100.0%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_process_text_file_response_minimal | ProcessTextFileResponse 最小構成 | ✅ | 0.000s |
| test_process_text_file_response_single_item | 単一ComplianceItem | ✅ | 0.000s |
| test_process_text_file_response_multiple_items | 複数ComplianceItem | ✅ | 0.000s |
| test_process_text_file_response_full_compliance_item | 完全構成ComplianceItem | ✅ | 0.000s |
| test_process_text_file_response_japanese_message | 日本語メッセージ | ✅ | 0.000s |
| test_process_text_file_response_nested_compliance | ネストしたComplianceItem | ✅ | 0.000s |
| test_base64_text_request_minimal | Base64TextRequest 最小構成 | ✅ | 0.000s |
| test_base64_text_request_with_session_id | session_id付き | ✅ | 0.000s |
| test_base64_text_request_empty_session_id | 空session_id | ✅ | 0.000s |
| test_base64_text_request_large_content | 大きなBase64コンテンツ | ✅ | 0.006s |
| test_base64_text_request_japanese_filename | 日本語ファイル名 | ✅ | 0.000s |
| test_model_dump_dict_conversion | model_dump 辞書変換 | ✅ | 0.000s |
| test_model_validate_from_dict | model_validate 辞書から生成 | ✅ | 0.000s |
| test_json_round_trip | JSON往復変換 | ✅ | 0.000s |
| test_model_dump_by_alias | by_aliasパラメータ検証 | ✅ | 0.000s |

## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_process_text_file_response_missing_required | 必須フィールド欠落 | ✅ | 0.000s |
| test_process_text_file_response_invalid_type | 無効な型 | ✅ | 0.000s |
| test_base64_text_request_missing_filename | filename欠落 | ✅ | 0.001s |
| test_base64_text_request_missing_content | file_content欠落 | ✅ | 0.000s |
| test_base64_text_request_invalid_type | 無効な型 | ✅ | 0.000s |
| test_response_all_fields_missing | Test Response All Fields Missing | ✅ | 0.000s |
| test_request_all_fields_missing | Test Request All Fields Missing | ✅ | 0.000s |
| test_response_message_wrong_type | Test Response Message Wrong Type | ✅ | 0.000s |
| test_response_source_filename_wrong_type | Test Response Source Filename Wrong Type | ✅ | 0.000s |
| test_request_file_content_base64_wrong_type | Test Request File Content Base64 Wrong Type | ✅ | 0.000s |
| test_request_session_id_wrong_type | Test Request Session Id Wrong Type | ✅ | 0.000s |

## セキュリティテスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_base64_request_path_traversal_warning | Path Traversal警告 | ✅ | 0.000s |
| test_base64_request_command_injection_warning | Command Injection警告 | ✅ | 0.000s |
| test_base64_request_crlf_injection_warning | CRLF Injection警告 | ✅ | 0.000s |
| test_null_byte_injection_filename | Test Null Byte Injection Filename | ✅ | 0.000s |
| test_xss_payload_in_message | Test Xss Payload In Message | ✅ | 0.000s |
| test_invalid_base64_content | Test Invalid Base64 Content | ✅ | 0.000s |
| test_sql_injection_session_id | Test Sql Injection Session Id | ✅ | 0.000s |
| test_large_string_dos | Test Large String Dos | ✅ | 0.003s |
| test_session_id_jwt_signature_tampering | Test Session Id Jwt Signature Tampering | ✅ | 0.000s |
| test_opensearch_injection_in_filename | Test Opensearch Injection In Filename | ✅ | 0.000s |
| test_ssrf_url_in_filename | Test Ssrf Url In Filename | ✅ | 0.000s |
| test_session_id_jwt_alg_none_attack | Test Session Id Jwt Alg None Attack | ✅ | 0.000s |
| test_unicode_normalization_attack | Test Unicode Normalization Attack | ✅ | 0.000s |
| test_extra_fields_ignored | Test Extra Fields Ignored | ✅ | 0.000s |
| test_business_logic_inconsistency | Test Business Logic Inconsistency | ✅ | 0.000s |


---

## 結論

✅ すべてのテストに合格しました！

---

*レポート生成時刻: 2026-03-13 16:39:22*
