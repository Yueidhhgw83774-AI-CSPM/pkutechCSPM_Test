# config.py テストレポート

## テスト概要

| 項目 | 値 |
|------|-----|
| テスト対象 | `app/core/config.py` |
| テスト仕様 | `config_tests.md` |
| 実行日時 | 2026-03-13 16:39:10 |
| カバレッジ目標 | 85% |

## テスト結果集計

| カテゴリ | 総数 | 成功 | 失敗 | 予期失敗 |
|------|------|------|------|----------|
| 正常系 | 9 | 9 | 0 | 0 |
| 異常系 | 5 | 5 | 0 | 0 |
| セキュリティ | 0 | 0 | 0 | 0 |
| **合計** | **14** | **14** | **0** | **0** |

## 合格率

- **実際の合格率**: 100.0%
- **有効合格率** (予期失敗を除く): 100.0%

---

## 正常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_import_config_module | Test Import Config Module | ✅ | 0.000s |
| test_load_from_env | 環境変数から設定読み込み | ✅ | 0.000s |
| test_default_values | デフォルト値の適用 | ✅ | 0.000s |
| test_opensearch_url_generation | OpenSearch URL生成 | ✅ | 0.000s |
| test_min_interval_calculation | MIN_INTERVAL_SECONDS計算 | ✅ | 0.000s |
| test_settings_instance_exists | 設定インスタンス存在確認 | ✅ | 0.000s |
| test_is_aws_opensearch_service | AWS OpenSearch Service判定 | ✅ | 0.000s |
| test_settings_and_helper_function_work_together | Test Settings And Helper Function Work Together | ✅ | 0.000s |
| test_min_interval_updates_with_rpm_limit | Test Min Interval Updates With Rpm Limit | ✅ | 0.000s |

## 異常系テスト詳細

| ID | テスト名 | 結果 | 実行時間 |
|----|---------|------|----------|
| test_missing_required_fields | 必須設定の欠落 | ✅ | 0.003s |
| test_invalid_rpm_limit_type | Test Invalid Rpm Limit Type | ✅ | 0.002s |
| test_invalid_opensearch_url_format | Test Invalid Opensearch Url Format | ✅ | 0.002s |
| test_invalid_url_format | Test Invalid Url Format | ✅ | 0.000s |
| test_none_url | Test None Url | ✅ | 0.000s |

---

## 結論

✅ **すべてのテストが成功!** config.pyモジュールが正常に動作しています。

---

*レポート生成日時: 2026-03-13 16:39:10*
