# AWS Plugin テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 14:49:28 |
| 総テスト数 | 70 |
| 通過 | 70 |
| 失敗 | 0 |
| 通過率 | 100.0% |

## 正常系テスト (25)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | AssumeRoleでリージョン一覧取得成功 | ✅ | 12.11ms |
| N/A | リージョンマッピング（us-east-1） | ✅ | 0.58ms |
| N/A | リージョンマッピング（Tokyo） | ✅ | 0.37ms |
| N/A | Test Region Name Mapping Unknown | ✅ | 0.36ms |
| N/A | Test Opt In Status Available | ✅ | 2.64ms |
| N/A | Test Opt In Status Opt In Required | ✅ | 2.22ms |
| N/A | AWS操作実行成功 | ✅ | 2.41ms |
| N/A | Test Response Metadata Removal | ✅ | 2.03ms |
| N/A | Test Datetime To Iso Datetime | ✅ | 0.64ms |
| N/A | Test Datetime To Iso Date | ✅ | 0.41ms |
| N/A | Test Datetime To Iso Nested Dict | ✅ | 0.37ms |
| N/A | Test Datetime To Iso List | ✅ | 0.37ms |
| N/A | Test Datetime To Iso Non Datetime | ✅ | 0.37ms |
| N/A | アクション一覧取得成功 | ✅ | 1.25ms |
| N/A | Test To Snake Case | ✅ | 0.23ms |
| N/A | Test Get Help Service Only | ✅ | 1.08ms |
| N/A | Test Get Help With Action | ✅ | 0.92ms |
| N/A | Test Handle Aws Execute Success | ✅ | 1.29ms |
| N/A | Test Handle Aws Execute With Context | ✅ | 1.55ms |
| N/A | Test Handle Aws List Actions Success | ✅ | 0.81ms |
| N/A | Test Handle Aws Get Help Success | ✅ | 0.77ms |
| N/A | Test Register Aws Internal Tools Success | ✅ | 1.11ms |
| N/A | Test Aws Internal Tools Count | ✅ | 0.35ms |
| N/A | Test Aws Tool Handlers Count | ✅ | 0.43ms |
| N/A | Test Aws Internal Server Name | ✅ | 0.33ms |

## 異常系テスト (35)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | AccessDenied（ロール不存在） | ✅ | 2.21ms |
| N/A | Test Access Denied No Assume Role Permission | ✅ | 2.03ms |
| N/A | Test Access Denied Invalid External Id | ✅ | 1.89ms |
| N/A | Test Access Denied Ip Restriction | ✅ | 2.66ms |
| N/A | Test Access Denied Time Restriction | ✅ | 2.47ms |
| N/A | Test Access Denied Mfa Required | ✅ | 1.98ms |
| N/A | Test Access Denied Other | ✅ | 1.94ms |
| N/A | Test Invalid User Id Not Found | ✅ | 2.32ms |
| N/A | Test Validation Exception Role Arn | ✅ | 1.98ms |
| N/A | Test Validation Exception External Id | ✅ | 1.47ms |
| N/A | Test Validation Exception Other | ✅ | 1.98ms |
| N/A | Test Malformed Policy Document | ✅ | 2.43ms |
| N/A | Test Token Refresh Required | ✅ | 1.46ms |
| N/A | Test Other Client Error | ✅ | 2.01ms |
| N/A | NoCredentialsError | ✅ | 1.6ms |
| N/A | Test Botocore Error Role Arn | ✅ | 1.19ms |
| N/A | Test Botocore Error External Id | ✅ | 1.15ms |
| N/A | Test Botocore Error Other | ✅ | 1.45ms |
| N/A | Test Unexpected Exception | ✅ | 1.17ms |
| N/A | Test Execute Invalid Action | ✅ | 2.2ms |
| N/A | Test Execute Client Error | ✅ | 3.05ms |
| N/A | Test Execute No Credentials | ✅ | 2.79ms |
| N/A | Test List Actions Invalid Service | ✅ | 1.46ms |
| N/A | Test Get Help Timeout | ✅ | 0.71ms |
| N/A | Test Get Help Exception | ✅ | 1.29ms |
| N/A | Test Handle Aws Execute No Role Arn | ✅ | 0.69ms |
| N/A | Test Handle Aws Execute No Service | ✅ | 0.72ms |
| N/A | Test Handle Aws Execute No Action | ✅ | 0.62ms |
| N/A | Test Handle Aws Execute Non Aws Provider | ✅ | 0.57ms |
| N/A | Test Handle Aws List Actions No Service | ✅ | 0.23ms |
| N/A | Test Handle Aws List Actions Empty List | ✅ | 0.79ms |
| N/A | Test Handle Aws Get Help No Service | ✅ | 0.33ms |
| N/A | Test Register Aws Internal Tools Failure | ✅ | 1.97ms |
| N/A | Test Register Aws Internal Tools Exception | ✅ | 1.78ms |
| N/A | Test Handle Aws Execute Empty Regions List | ✅ | 1.09ms |

## セキュリティテスト (10)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | Test Role Arn Format Validation | ✅ | 1.28ms |
| N/A | Test External Id Required | ✅ | 1.28ms |
| N/A | Test Credentials Not Logged | ✅ | 2.19ms |
| N/A | Test Sql Injection In Role Arn | ✅ | 1.21ms |
| N/A | Test Xss In Error Message | ✅ | 1.75ms |
| N/A | Test Rate Limiting Protection | ✅ | 4.12ms |
| N/A | Test Sensitive Data Not In Exception Message | ✅ | 0.33ms |
| N/A | Test Command Injection In Get Help | ✅ | 0.83ms |
| N/A | Test Session Token Expiry | ✅ | 1.79ms |
| N/A | Test Cross Account Isolation | ✅ | 2.4ms |

---
*生成時刻: 2026-03-13 14:49:36*
