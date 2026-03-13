# AWS Plugin テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-13 16:59:47 |
| 総テスト数 | 70 |
| 通過 | 70 |
| 失敗 | 0 |
| 通過率 | 100.0% |

## 正常系テスト (25)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | AssumeRoleでリージョン一覧取得成功 | ✅ | 1.63ms |
| N/A | リージョンマッピング（us-east-1） | ✅ | 0.21ms |
| N/A | リージョンマッピング（Tokyo） | ✅ | 0.2ms |
| N/A | Test Region Name Mapping Unknown | ✅ | 0.2ms |
| N/A | Test Opt In Status Available | ✅ | 1.99ms |
| N/A | Test Opt In Status Opt In Required | ✅ | 1.41ms |
| N/A | AWS操作実行成功 | ✅ | 1.29ms |
| N/A | Test Response Metadata Removal | ✅ | 1.47ms |
| N/A | Test Datetime To Iso Datetime | ✅ | 0.24ms |
| N/A | Test Datetime To Iso Date | ✅ | 0.27ms |
| N/A | Test Datetime To Iso Nested Dict | ✅ | 0.21ms |
| N/A | Test Datetime To Iso List | ✅ | 0.24ms |
| N/A | Test Datetime To Iso Non Datetime | ✅ | 0.23ms |
| N/A | アクション一覧取得成功 | ✅ | 0.67ms |
| N/A | Test To Snake Case | ✅ | 0.22ms |
| N/A | Test Get Help Service Only | ✅ | 0.63ms |
| N/A | Test Get Help With Action | ✅ | 0.45ms |
| N/A | Test Handle Aws Execute Success | ✅ | 0.75ms |
| N/A | Test Handle Aws Execute With Context | ✅ | 0.81ms |
| N/A | Test Handle Aws List Actions Success | ✅ | 0.46ms |
| N/A | Test Handle Aws Get Help Success | ✅ | 0.42ms |
| N/A | Test Register Aws Internal Tools Success | ✅ | 1.03ms |
| N/A | Test Aws Internal Tools Count | ✅ | 0.22ms |
| N/A | Test Aws Tool Handlers Count | ✅ | 0.21ms |
| N/A | Test Aws Internal Server Name | ✅ | 0.19ms |

## 異常系テスト (35)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | AccessDenied（ロール不存在） | ✅ | 1.23ms |
| N/A | Test Access Denied No Assume Role Permission | ✅ | 1.12ms |
| N/A | Test Access Denied Invalid External Id | ✅ | 1.78ms |
| N/A | Test Access Denied Ip Restriction | ✅ | 1.69ms |
| N/A | Test Access Denied Time Restriction | ✅ | 1.13ms |
| N/A | Test Access Denied Mfa Required | ✅ | 1.45ms |
| N/A | Test Access Denied Other | ✅ | 1.38ms |
| N/A | Test Invalid User Id Not Found | ✅ | 1.15ms |
| N/A | Test Validation Exception Role Arn | ✅ | 1.22ms |
| N/A | Test Validation Exception External Id | ✅ | 1.05ms |
| N/A | Test Validation Exception Other | ✅ | 1.06ms |
| N/A | Test Malformed Policy Document | ✅ | 1.4ms |
| N/A | Test Token Refresh Required | ✅ | 1.29ms |
| N/A | Test Other Client Error | ✅ | 0.93ms |
| N/A | NoCredentialsError | ✅ | 1.18ms |
| N/A | Test Botocore Error Role Arn | ✅ | 1.03ms |
| N/A | Test Botocore Error External Id | ✅ | 1.12ms |
| N/A | Test Botocore Error Other | ✅ | 0.97ms |
| N/A | Test Unexpected Exception | ✅ | 1.35ms |
| N/A | Test Execute Invalid Action | ✅ | 1.03ms |
| N/A | Test Execute Client Error | ✅ | 1.31ms |
| N/A | Test Execute No Credentials | ✅ | 2.01ms |
| N/A | Test List Actions Invalid Service | ✅ | 1.06ms |
| N/A | Test Get Help Timeout | ✅ | 0.65ms |
| N/A | Test Get Help Exception | ✅ | 0.75ms |
| N/A | Test Handle Aws Execute No Role Arn | ✅ | 0.31ms |
| N/A | Test Handle Aws Execute No Service | ✅ | 0.33ms |
| N/A | Test Handle Aws Execute No Action | ✅ | 0.39ms |
| N/A | Test Handle Aws Execute Non Aws Provider | ✅ | 0.35ms |
| N/A | Test Handle Aws List Actions No Service | ✅ | 0.21ms |
| N/A | Test Handle Aws List Actions Empty List | ✅ | 0.49ms |
| N/A | Test Handle Aws Get Help No Service | ✅ | 0.22ms |
| N/A | Test Register Aws Internal Tools Failure | ✅ | 1.5ms |
| N/A | Test Register Aws Internal Tools Exception | ✅ | 1.23ms |
| N/A | Test Handle Aws Execute Empty Regions List | ✅ | 0.67ms |

## セキュリティテスト (10)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | Test Role Arn Format Validation | ✅ | 0.79ms |
| N/A | Test External Id Required | ✅ | 0.85ms |
| N/A | Test Credentials Not Logged | ✅ | 1.46ms |
| N/A | Test Sql Injection In Role Arn | ✅ | 0.71ms |
| N/A | Test Xss In Error Message | ✅ | 1.2ms |
| N/A | Test Rate Limiting Protection | ✅ | 2.53ms |
| N/A | Test Sensitive Data Not In Exception Message | ✅ | 0.21ms |
| N/A | Test Command Injection In Get Help | ✅ | 0.54ms |
| N/A | Test Session Token Expiry | ✅ | 1.15ms |
| N/A | Test Cross Account Isolation | ✅ | 2.01ms |

---
*生成時刻: 2026-03-13 17:02:27*
