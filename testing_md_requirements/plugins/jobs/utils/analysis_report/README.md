# jobs/utils 分析・レポート テストケース (#17f)

> **チケット**: #17f
> **前提**: なし（独立して作成可能）

## テスト対象モジュール

| # | ファイル | 行数 | 仕様書 | ステータス |
|---|---------|------|--------|-----------|
| 1 | `violations_counter.py` (169行) | [violations_counter_tests.md](violations_counter_tests.md) | 完了 |
| 2 | `error_analysis.py` (147行) | [error_analysis_tests.md](error_analysis_tests.md) | 完了 |
| 3 | `summary_generation.py` (56行) | [summary_generation_tests.md](summary_generation_tests.md) | 完了 |
| 4 | `scan_analysis.py` (621行) | [scan_analysis_tests.md](scan_analysis_tests.md) | 完了 |

> **作成順序**: 小規模モジュールから順に作成（1→2→3→4）

## 推定テスト数

| モジュール | 推定件数 | 確定件数 |
|-----------|---------|---------|
| violations_counter | 15〜20 | 26 |
| error_analysis | 10〜15 | 17 |
| summary_generation | 5〜10 | 11 |
| scan_analysis | 20〜30 | 30 |
| **合計** | **50〜75** | **84** |

## 依存関係

- 他 utils ファイルへの依存なし（独立）
- 分析・レポート系の機能グループ
- conftest.py は `test/unit/jobs/utils/conftest.py`（#17a と共有）

## ディレクトリ構造

```
docs/testing/plugins/jobs/utils/analysis_report/
├── README.md                        ← このファイル
├── violations_counter_tests.md      ← 違反カウント集計
├── error_analysis_tests.md          ← エラー分析
├── summary_generation_tests.md      ← サマリー生成
└── scan_analysis_tests.md           ← スキャン結果分析
```
