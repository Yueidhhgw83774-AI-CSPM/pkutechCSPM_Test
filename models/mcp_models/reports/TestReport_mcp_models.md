# models/mcp.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/models/mcp.py` |
| テスト仕様 | `docs/testing/models/mcp_models_tests.md` |
| 実行時刻 | 2026-03-13 16:39:22 |
| 総実行時間 | 0.17s |
| カバレッジ目標 | 90% |

## テスト結果統計

| カテゴリ | 総数 | 合格 | 失敗 | 予期された失敗 |
|------|------|------|------|----------|
| 正常系 | 43 | 43 | 0 | 0 |
| 異常系 | 17 | 17 | 0 | 0 |
| セキュリティ | 0 | 0 | 0 | 0 |
| **合計** | **60** | **60** | **0** | **0** |

## テスト合格率

- **実際の合格率**: 100.0%
- **有効合格率** (予期された失敗を除く): 100.0%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_cloud_credentials_context_aws | CloudCredentialsContext AWS構成 | ✅ | 0.000s |
| test_cloud_credentials_context_azure | Azure構成 | ✅ | 0.000s |
| test_cloud_credentials_context_gcp | GCP構成 | ✅ | 0.000s |
| test_cloud_credentials_context_minimal | 最小構成 | ✅ | 0.000s |
| test_mcp_tool_type_enum | MCPToolType Enum | ✅ | 0.000s |
| test_sse_event_type_enum | SSEEventType Enum | ✅ | 0.000s |
| test_mcp_tool_parameter | MCPToolParameter | ✅ | 0.000s |
| test_mcp_tool_basic | MCPTool 基本構成 | ✅ | 0.000s |
| test_mcp_tool_with_parameters | パラメータ付き | ✅ | 0.000s |
| test_mcp_server_basic | MCPServer 基本構成 | ✅ | 0.000s |
| test_mcp_server_full | 完全構成 | ✅ | 0.000s |
| test_mcp_chat_message_basic | MCPChatMessage 基本 | ✅ | 0.000s |
| test_mcp_chat_message_with_tools | ツール呼び出し付き | ✅ | 0.000s |
| test_sub_task_result_completed | SubTaskResult 完了 | ✅ | 0.000s |
| test_todo_item_pending | TodoItem pending | ✅ | 0.000s |
| test_todo_item_completed | completed | ✅ | 0.000s |
| test_thinking_log | Test Thinking Log | ✅ | 0.000s |
| test_mcp_chat_request | MCPChatRequest | ✅ | 0.000s |
| test_mcp_chat_stream_request | MCPChatStreamRequest | ✅ | 0.000s |
| test_mcp_chat_response_full | 完全構成 | ✅ | 0.000s |
| test_session_info | SessionInfo | ✅ | 0.000s |
| test_session_list_response | SessionListResponse | ✅ | 0.000s |
| test_model_dump_and_validate | Test Model Dump And Validate | ✅ | 0.000s |
| test_mcp_tool_call_defaults | Test Mcp Tool Call Defaults | ✅ | 0.000s |
| test_mcp_tool_result_success | Test Mcp Tool Result Success | ✅ | 0.000s |
| test_mcp_tool_result_failure | Test Mcp Tool Result Failure | ✅ | 0.000s |
| test_validation_result_defaults | Test Validation Result Defaults | ✅ | 0.000s |
| test_mcp_progress_defaults | Test Mcp Progress Defaults | ✅ | 0.000s |
| test_validation_result_failure_case | Test Validation Result Failure Case | ✅ | 0.000s |
| test_mcp_progress_with_data | Test Mcp Progress With Data | ✅ | 0.000s |
| test_mcp_server_list_response_empty | Test Mcp Server List Response Empty | ✅ | 0.000s |
| test_mcp_server_list_response_multiple | Test Mcp Server List Response Multiple | ✅ | 0.000s |
| test_mcp_tool_list_response | Test Mcp Tool List Response | ✅ | 0.000s |
| test_mcp_server_status_defaults | Test Mcp Server Status Defaults | ✅ | 0.000s |
| test_mcp_status_response | Test Mcp Status Response | ✅ | 0.000s |
| test_mcp_chat_response_minimal | Test Mcp Chat Response Minimal | ✅ | 0.000s |
| test_mcp_chat_stream_request_with_credentials | Test Mcp Chat Stream Request With Credentials | ✅ | 0.000s |
| test_sub_task_result_with_tool_result | Test Sub Task Result With Tool Result | ✅ | 0.000s |
| test_session_update_request_boundary | Test Session Update Request Boundary | ✅ | 0.000s |
| test_session_info_full | Test Session Info Full | ✅ | 0.001s |
| test_session_list_response_with_data | Test Session List Response With Data | ✅ | 0.000s |
| test_json_round_trip | Test Json Round Trip | ✅ | 0.000s |
| test_mutable_default_independence | Test Mutable Default Independence | ✅ | 0.000s |

## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_cloud_credentials_invalid_provider | 無効なクラウドプロバイダー | ✅ | 0.000s |
| test_mcp_chat_request_missing_required | 必須フィールド欠落 | ✅ | 0.000s |
| test_mcp_chat_stream_request_invalid_type | Test Mcp Chat Stream Request Invalid Type | ✅ | 0.000s |
| test_validation_result_missing_required | Test Validation Result Missing Required | ✅ | 0.000s |
| test_session_update_request_name_too_long | Test Session Update Request Name Too Long | ✅ | 0.000s |
| test_cloud_credentials_missing_provider | Test Cloud Credentials Missing Provider | ✅ | 0.000s |
| test_mcp_chat_stream_request_missing_required | Test Mcp Chat Stream Request Missing Required | ✅ | 0.000s |
| test_mcp_chat_response_missing_response | Test Mcp Chat Response Missing Response | ✅ | 0.000s |
| test_mcp_chat_response_missing_session_id | Test Mcp Chat Response Missing Session Id | ✅ | 0.000s |
| test_sub_task_result_missing_required | Test Sub Task Result Missing Required | ✅ | 0.000s |
| test_todo_item_missing_required | Test Todo Item Missing Required | ✅ | 0.000s |
| test_thinking_log_missing_required | Test Thinking Log Missing Required | ✅ | 0.000s |
| test_mcp_tool_missing_required | Test Mcp Tool Missing Required | ✅ | 0.000s |
| test_mcp_tool_parameter_missing_required | Test Mcp Tool Parameter Missing Required | ✅ | 0.000s |
| test_mcp_server_status_missing_required | Test Mcp Server Status Missing Required | ✅ | 0.000s |
| test_mcp_status_response_missing_required | Test Mcp Status Response Missing Required | ✅ | 0.000s |
| test_session_list_response_missing_total | Test Session List Response Missing Total | ✅ | 0.000s |


---

## 結論

✅ すべてのテストに合格しました！

---

*レポート生成時刻: 2026-03-13 16:39:22*
