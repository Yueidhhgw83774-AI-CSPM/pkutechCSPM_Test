# jobs/utils テスト仕様書一覧

> `app/jobs/utils/` 配下のユーティリティモジュール群に対するテスト仕様書を管理する。

## チケット・仕様書マップ

| チケット | グループ名 | 仕様書 | テスト数 | ステータス |
|---------|-----------|--------|---------|-----------|
| #17a | ヘルパー・正規化基盤 | [jobs_utils_helper_normalizer_tests.md](jobs_utils_helper_normalizer_tests.md) | 62 | 完了 |
| #17b | ドキュメント生成・抽出 | [jobs_utils_document_tests.md](jobs_utils_document_tests.md) | 45 | 完了 |
| #17c | v2フォーマットヘルパー群 | [jobs_utils_v2_format_helpers_tests.md](jobs_utils_v2_format_helpers_tests.md) | 52 | 完了 |
| #17d | v2フォーマットコンバーター | [jobs_utils_v2_format_converter_tests.md](jobs_utils_v2_format_converter_tests.md) | 47 | 完了 |
| #17e | メタデータ・アカウント抽出 | [jobs_utils_metadata_account_tests.md](jobs_utils_metadata_account_tests.md) | 50 | 完了 |
| #17f | 分析・レポート | [analysis_report/](analysis_report/README.md) (4ファイル) | 84 | 完了 |
| #17g | ストレージ統合・再エクスポート | [jobs_utils_storage_export_tests.md](jobs_utils_storage_export_tests.md) | 28 | 完了 |
| #17h | 独立ユーティリティ | [independent/](independent/README.md) (3ファイル) | 143 | 完了 |
| | **合計** | | **511** | |

## 依存関係（作成順序）

```
#17a ヘルパー・正規化基盤（依存なし）
  │
  ├─▶ #17b ドキュメント生成・抽出
  │     │
  │     └─▶ #17g ストレージ統合・再エクスポート（#17a, #17b, #17e 必要）
  │
  ├─▶ #17c v2フォーマットヘルパー群
  │     │
  │     └─▶ #17d v2フォーマットコンバーター（#17c 必要）
  │
  └─▶ #17e メタデータ・アカウント抽出

#17f 分析・レポート（独立）
#17h 独立ユーティリティ（独立）
```

## 共有リソース

| リソース | パス | 説明 |
|---------|------|------|
| conftest.py | `test/unit/jobs/utils/conftest.py` | `reset_utils_module` フィクスチャ（#17a で定義、全チケット共有） |
| テストコード | `test/unit/jobs/utils/test_*.py` | 各仕様書に対応するテストファイル |

## ディレクトリ構造

```
docs/testing/plugins/jobs/utils/
├── README.md                                  ← このファイル
├── jobs_utils_helper_normalizer_tests.md      ← #17a ヘルパー・正規化
├── jobs_utils_document_tests.md               ← #17b ドキュメント生成
├── jobs_utils_v2_format_helpers_tests.md      ← #17c v2ヘルパー群
├── jobs_utils_v2_format_converter_tests.md    ← #17d v2コンバーター
├── jobs_utils_metadata_account_tests.md       ← #17e メタデータ
├── jobs_utils_storage_export_tests.md         ← #17g ストレージ
├── analysis_report/                           ← #17f 分析・レポート
│   ├── README.md
│   ├── violations_counter_tests.md            ← 26件
│   ├── error_analysis_tests.md                ← 17件
│   ├── summary_generation_tests.md            ← 11件
│   └── scan_analysis_tests.md                 ← 30件
└── independent/                               ← #17h 独立ユーティリティ
    ├── README.md
    ├── opensearch_v2_indexer_tests.md         ← 53件（完了）
    ├── resource_id_extractor_tests.md         ← 46件（完了）
    └── recommendation_uuid_mapper_tests.md    ← 42件（完了、aws_resource_counter含む）
```
