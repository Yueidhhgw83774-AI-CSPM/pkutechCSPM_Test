# jobs/utils 独立ユーティリティ テストケース (#17h)

> **チケット**: #17h
> **前提**: なし（独立して作成可能）

## テスト対象モジュール

| # | ファイル | 行数 | 仕様書 | ステータス |
|---|---------|------|--------|-----------|
| 1 | `opensearch_v2_indexer.py` (616行) | [opensearch_v2_indexer_tests.md](opensearch_v2_indexer_tests.md) | 完了（53件） |
| 2 | `resource_id_extractor.py` (466行) | [resource_id_extractor_tests.md](resource_id_extractor_tests.md) | 完了（46件） |
| 3 | `recommendation_uuid_mapper.py` (253行) + `aws_resource_counter.py` (137行) | [recommendation_uuid_mapper_tests.md](recommendation_uuid_mapper_tests.md) | 完了（44件） |

> **作成順序**: 大規模・高複雑度モジュールから順に作成（1→2→3）
> **注記**: `aws_resource_counter.py` は大半がコメントアウト（スタブ関数2個のみ）のため、`recommendation_uuid_mapper_tests.md` に含める

## 推定テスト数

| モジュール | 推定件数 | 確定件数 |
|-----------|---------|---------|
| opensearch_v2_indexer | 15〜20 | 53 |
| resource_id_extractor | 12〜15 | 46 |
| recommendation_uuid_mapper + aws_resource_counter | 10〜15 | 44 |
| **合計** | **37〜50** | **143** |

## 依存関係

- 他 utils ファイルへの依存なし（独立）
- `opensearch_v2_indexer.py` は async / OpenSearch クライアント依存（全メソッドモック必須）
- `resource_id_extractor.py` は外部依存なし（`logging` のみ）
- `recommendation_uuid_mapper.py` はファイル I/O 依存（`tmp_path` または `os.path` モック）
- conftest.py は `test/unit/jobs/utils/conftest.py`（#17a と共有）

## ディレクトリ構造

```
docs/testing/plugins/jobs/utils/independent/
├── README.md                              ← このファイル
├── opensearch_v2_indexer_tests.md         ← OpenSearch v2インデクサー
├── resource_id_extractor_tests.md         ← リソースID抽出
└── recommendation_uuid_mapper_tests.md    ← UUID マッピング + AWSリソースカウント(スタブ)
```
