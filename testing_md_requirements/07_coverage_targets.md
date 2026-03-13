# カバレッジ目標

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトのコードカバレッジ目標を定義します。

## 2. 全体カバレッジ目標

### 2.1 目標値

| カテゴリ | 最低目標 | 推奨目標 | 備考 |
|---------|---------|---------|------|
| 全体コードカバレッジ | 70% | 80% | プロジェクト全体 |
| コアサービス | 85% | 95% | 認証、設定、LLMファクトリ |
| APIエンドポイント | 80% | 90% | 全HTTPエンドポイント |
| ビジネスロジック | 80% | 90% | エージェント、ツール |
| ユーティリティ | 70% | 80% | ヘルパー関数 |

### 2.2 カバレッジタイプ

| タイプ | 説明 | 目標 |
|--------|------|------|
| Line Coverage | 実行された行の割合 | 主要指標 |
| Branch Coverage | 分岐網羅率 | 補助指標 |
| Function Coverage | 実行された関数の割合 | 参考指標 |

## 3. プラグイン別カバレッジ目標

### 3.1 優先度高（必須）

| プラグイン | 最低目標 | 推奨目標 | 理由 |
|-----------|---------|---------|------|
| cspm_plugin | 85% | 95% | コア機能、セキュリティ重要 |
| auth | 90% | 95% | セキュリティ重要 |
| jobs | 80% | 90% | ジョブ管理の信頼性 |

### 3.2 優先度中

| プラグイン | 最低目標 | 推奨目標 | 理由 |
|-----------|---------|---------|------|
| chat_dashboard | 70% | 85% | ユーザー対話機能 |
| mcp_plugin | 75% | 85% | 外部連携の安定性 |
| report_plugin | 70% | 80% | レポート生成 |

### 3.3 優先度低

| プラグイン | 最低目標 | 推奨目標 | 理由 |
|-----------|---------|---------|------|
| rag | 60% | 75% | 検索機能 |
| doc_reader_plugin | 60% | 75% | ドキュメント読み込み |
| custodian_scan | 65% | 80% | 外部ツール連携 |
| logchecker | 60% | 75% | ログ解析 |
| aws_plugin | 60% | 75% | AWS操作 |

## 4. コアサービス別カバレッジ目標

| サービス | 最低目標 | 推奨目標 | 対象ファイル |
|---------|---------|---------|-------------|
| config | 85% | 95% | `app/core/config.py` |
| auth (core) | 90% | 95% | `app/core/auth.py` |
| llm_factory | 85% | 95% | `app/core/llm_factory.py` |
| clients | 80% | 90% | `app/core/clients.py` |
| permission_checker | 85% | 90% | `app/core/permission_checker.py` |
| checkpointer | 75% | 85% | `app/core/checkpointer.py` |

## 5. カバレッジ除外対象

### 5.1 除外ルール

以下のコードはカバレッジ計測から除外します：

```python
# .coveragerc または pyproject.toml で設定
[tool.coverage.run]
omit = [
    "*/tests/*",           # テストコード自体
    "*/__init__.py",       # 初期化ファイル
    "*/migrations/*",      # マイグレーションファイル
    "*/conftest.py",       # テスト設定ファイル
    "*_pb2.py",           # Protocol Buffer生成ファイル
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "@abstractmethod",
]
```

### 5.2 除外理由

| 除外対象 | 理由 |
|---------|------|
| テストコード | テスト対象ではない |
| `__init__.py` | インポート文のみ |
| 抽象メソッド | 実装がない |
| 型チェック専用コード | 実行時に不要 |
| デバッグ用コード | 本番環境で不要 |

## 6. カバレッジ測定方法

### 6.1 基本的な実行

```bash
# カバレッジ付きテスト実行
pytest --cov=app --cov-report=term-missing

# HTMLレポート生成
pytest --cov=app --cov-report=html

# XMLレポート生成（CI用）
pytest --cov=app --cov-report=xml
```

### 6.2 pyproject.toml設定

```toml
[tool.coverage.run]
source = ["app"]
branch = true
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/conftest.py",
]

[tool.coverage.report]
show_missing = true
skip_covered = false
fail_under = 70
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]

[tool.coverage.html]
directory = "htmlcov"
```

### 6.3 プラグイン別カバレッジ

```bash
# 特定プラグインのカバレッジ
pytest --cov=app/cspm_plugin test/unit/cspm_plugin/

# 複数プラグインのカバレッジ
pytest --cov=app/cspm_plugin --cov=app/auth test/
```

## 7. カバレッジレポート

### 7.1 レポートの読み方

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
app/cspm_plugin/router.py           50      5    90%   45-49
app/cspm_plugin/refinement.py       80     12    85%   22-33
app/cspm_plugin/agent_executor.py  120     30    75%   55-70, 90-104
---------------------------------------------------------------
TOTAL                              250     47    81%
```

| 列 | 説明 |
|-----|------|
| Stmts | 実行可能な文の数 |
| Miss | 実行されなかった文の数 |
| Cover | カバレッジ率 |
| Missing | カバーされていない行番号 |

### 7.2 カバレッジ改善の優先順位

1. **Missing行が多いファイル**: 未テスト機能が多い
2. **重要度の高いモジュール**: コア機能、セキュリティ関連
3. **複雑度の高い関数**: 分岐が多い、エラー処理が多い

## 8. カバレッジ改善戦略

### 8.1 低カバレッジ領域の特定

```bash
# カバレッジが低いファイルを特定
pytest --cov=app --cov-report=term-missing --cov-fail-under=0 | grep -E "^\s+\d+%"
```

### 8.2 改善アクション

| カバレッジ | アクション |
|-----------|-----------|
| 0-30% | 基本的なユニットテスト追加が必要 |
| 30-60% | 主要パスのテスト追加 |
| 60-80% | エッジケース、エラーケース追加 |
| 80-90% | 分岐網羅、境界値テスト追加 |
| 90%+ | 維持管理、リファクタリング時に注意 |

### 8.3 テスト追加の優先順位

1. **未テストの公開API**: エンドポイント、公開関数
2. **エラーハンドリング**: try-except ブロック
3. **条件分岐**: if-else、switch文
4. **ループ処理**: for、while ループの境界
5. **例外的なケース**: null、空、境界値

## 9. カバレッジ監視

### 9.1 定期レビュー

| 頻度 | アクション |
|------|-----------|
| PR毎 | カバレッジ低下の検出 |
| 週次 | 低カバレッジ領域の確認 |
| 月次 | 全体カバレッジの推移確認 |

### 9.2 カバレッジトレンド

目標達成に向けたマイルストーン：

| フェーズ | 期間 | 目標 |
|---------|------|------|
| Phase 1 | 初期 | 50% 達成 |
| Phase 2 | 中期 | 70% 達成（最低目標） |
| Phase 3 | 後期 | 80% 達成（推奨目標） |
| 維持 | 継続 | 80%以上維持 |
