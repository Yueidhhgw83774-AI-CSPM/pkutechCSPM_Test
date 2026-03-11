# AWS Plugin テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| 実行日時 | 2026-03-11 13:45:08 |
| 総テスト数 | 70 |
| 通過 | 70 |
| 失敗 | 0 |
| 通過率 | 100.0% |

## 正常系テスト (25)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | AssumeRoleでリージョン一覧取得成功 | ✅ | 1.87ms |
| N/A | リージョンマッピング（us-east-1） | ✅ | 0.23ms |
| N/A | リージョンマッピング（Tokyo） | ✅ | 0.13ms |
| N/A | Test Region Name Mapping Unknown | ✅ | 0.12ms |
| N/A | Test Opt In Status Available | ✅ | 1.46ms |
| N/A | Test Opt In Status Opt In Required | ✅ | 1.06ms |
| N/A | AWS操作実行成功 | ✅ | 1.17ms |
| N/A | Test Response Metadata Removal | ✅ | 1.08ms |
| N/A | Test Datetime To Iso Datetime | ✅ | 0.28ms |
| N/A | Test Datetime To Iso Date | ✅ | 0.13ms |
| N/A | Test Datetime To Iso Nested Dict | ✅ | 0.13ms |
| N/A | Test Datetime To Iso List | ✅ | 0.13ms |
| N/A | Test Datetime To Iso Non Datetime | ✅ | 0.12ms |
| N/A | アクション一覧取得成功 | ✅ | 0.51ms |
| N/A | Test To Snake Case | ✅ | 0.17ms |
| N/A | Test Get Help Service Only | ✅ | 0.49ms |
| N/A | Test Get Help With Action | ✅ | 0.38ms |
| N/A | Test Handle Aws Execute Success | ✅ | 0.53ms |
| N/A | Test Handle Aws Execute With Context | ✅ | 0.46ms |
| N/A | Test Handle Aws List Actions Success | ✅ | 0.64ms |
| N/A | Test Handle Aws Get Help Success | ✅ | 0.3ms |
| N/A | Test Register Aws Internal Tools Success | ✅ | 0.68ms |
| N/A | Test Aws Internal Tools Count | ✅ | 0.12ms |
| N/A | Test Aws Tool Handlers Count | ✅ | 0.12ms |
| N/A | Test Aws Internal Server Name | ✅ | 0.13ms |

## 異常系テスト (35)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | AccessDenied（ロール不存在） | ✅ | 1.13ms |
| N/A | Test Access Denied No Assume Role Permission | ✅ | 0.91ms |
| N/A | Test Access Denied Invalid External Id | ✅ | 0.84ms |
| N/A | Test Access Denied Ip Restriction | ✅ | 0.83ms |
| N/A | Test Access Denied Time Restriction | ✅ | 0.91ms |
| N/A | Test Access Denied Mfa Required | ✅ | 1.51ms |
| N/A | Test Access Denied Other | ✅ | 0.98ms |
| N/A | Test Invalid User Id Not Found | ✅ | 0.98ms |
| N/A | Test Validation Exception Role Arn | ✅ | 0.97ms |
| N/A | Test Validation Exception External Id | ✅ | 0.98ms |
| N/A | Test Validation Exception Other | ✅ | 1.03ms |
| N/A | Test Malformed Policy Document | ✅ | 0.86ms |
| N/A | Test Token Refresh Required | ✅ | 1.25ms |
| N/A | Test Other Client Error | ✅ | 1.0ms |
| N/A | NoCredentialsError | ✅ | 1.04ms |
| N/A | Test Botocore Error Role Arn | ✅ | 0.85ms |
| N/A | Test Botocore Error External Id | ✅ | 0.94ms |
| N/A | Test Botocore Error Other | ✅ | 1.02ms |
| N/A | Test Unexpected Exception | ✅ | 1.2ms |
| N/A | Test Execute Invalid Action | ✅ | 1.45ms |
| N/A | Test Execute Client Error | ✅ | 1.4ms |
| N/A | Test Execute No Credentials | ✅ | 3.74ms |
| N/A | Test List Actions Invalid Service | ✅ | 0.45ms |
| N/A | Test Get Help Timeout | ✅ | 0.35ms |
| N/A | Test Get Help Exception | ✅ | 0.45ms |
| N/A | Test Handle Aws Execute No Role Arn | ✅ | 0.29ms |
| N/A | Test Handle Aws Execute No Service | ✅ | 0.27ms |
| N/A | Test Handle Aws Execute No Action | ✅ | 0.24ms |
| N/A | Test Handle Aws Execute Non Aws Provider | ✅ | 0.27ms |
| N/A | Test Handle Aws List Actions No Service | ✅ | 0.14ms |
| N/A | Test Handle Aws List Actions Empty List | ✅ | 0.39ms |
| N/A | Test Handle Aws Get Help No Service | ✅ | 0.13ms |
| N/A | Test Register Aws Internal Tools Failure | ✅ | 0.83ms |
| N/A | Test Register Aws Internal Tools Exception | ✅ | 0.99ms |
| N/A | Test Handle Aws Execute Empty Regions List | ✅ | 0.54ms |

## セキュリティテスト (10)

| ID | テスト名 | 結果 | 時間 |
|----|---------|------|------|
| N/A | Test Role Arn Format Validation | ✅ | 0.93ms |
| N/A | Test External Id Required | ✅ | 0.75ms |
| N/A | Test Credentials Not Logged | ✅ | 1.43ms |
| N/A | Test Sql Injection In Role Arn | ✅ | 0.66ms |
| N/A | Test Xss In Error Message | ✅ | 1.1ms |
| N/A | Test Rate Limiting Protection | ✅ | 2.27ms |
| N/A | Test Sensitive Data Not In Exception Message | ✅ | 0.14ms |
| N/A | Test Command Injection In Get Help | ✅ | 0.47ms |
| N/A | Test Session Token Expiry | ✅ | 1.43ms |
| N/A | Test Cross Account Isolation | ✅ | 1.37ms |

---
*生成時刻: 2026-03-11 13:45:13*
