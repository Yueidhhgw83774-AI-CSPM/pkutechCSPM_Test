# CI/CD統合（推奨）

> **注意**: 本ドキュメントは将来的なCI/CD導入に向けた推奨事項です。現時点では未実装です。

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトのCI/CD統合に関する推奨設定を説明します。

## 2. 推奨ツールチェーン

### 2.1 CI/CDプラットフォーム

| プラットフォーム | 推奨度 | 特徴 |
|----------------|--------|------|
| GitHub Actions | 推奨 | GitHubとの統合、無料枠あり |
| GitLab CI | 代替 | セルフホスト可能 |
| Jenkins | 代替 | 高度なカスタマイズ |

### 2.2 パイプライン構成

```
[Push/PR] → [Lint] → [Unit Test] → [Integration Test] → [Deploy]
                           ↓
                    [Coverage Report]
```

## 3. GitHub Actions設定例

### 3.1 基本的なワークフロー

```yaml
# .github/workflows/test.yml
name: Python Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      opensearch:
        image: opensearchproject/opensearch:2.11.0
        env:
          discovery.type: single-node
          DISABLE_SECURITY_PLUGIN: true
        ports:
          - 9200:9200
        options: >-
          --health-cmd="curl -f http://localhost:9200/_cluster/health"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv sync

      - name: Run linting
        run: uv run ruff check app/

      - name: Run unit tests
        run: uv run pytest test/unit/ -v --cov=app --cov-report=xml

      - name: Run integration tests
        run: uv run pytest test/integration/ -v -m "not slow"
        env:
          OPENSEARCH_HOST: localhost
          OPENSEARCH_PORT: 9200

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

### 3.2 PRコメントにカバレッジ表示

```yaml
# .github/workflows/coverage-report.yml
name: Coverage Report

on:
  pull_request:
    branches: [main]

jobs:
  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run tests with coverage
        run: uv run pytest --cov=app --cov-report=xml

      - name: Code Coverage Summary
        uses: irongut/CodeCoverageSummary@v1.3.0
        with:
          filename: coverage.xml
          badge: true
          format: markdown
          output: both

      - name: Add Coverage PR Comment
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          recreate: true
          path: code-coverage-results.md
```

## 4. テスト実行戦略

### 4.1 実行タイミング

| トリガー | 実行テスト | 目的 |
|---------|-----------|------|
| Push（feature branch） | ユニットテストのみ | 高速フィードバック |
| PR作成/更新 | ユニット + 統合 | マージ前検証 |
| mainマージ | 全テスト | リリース前検証 |
| 定期実行（毎日） | E2E + 全テスト | 回帰テスト |

### 4.2 並列実行

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - name: Run unit tests
        run: pytest test/unit/ -n auto

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests  # ユニットテスト成功後に実行
    steps:
      - name: Run integration tests
        run: pytest test/integration/
```

## 5. 品質ゲート

### 5.1 マージ条件

| 条件 | 閾値 | 強制 |
|------|------|------|
| 全テスト合格 | 100% | 必須 |
| カバレッジ | 70%以上 | 推奨 |
| カバレッジ低下 | 2%以内 | 推奨 |
| Lint エラー | 0 | 必須 |

### 5.2 ブランチ保護設定

```yaml
# リポジトリ設定（GitHub）
# Settings > Branches > Branch protection rules

# main ブランチ保護
- Require status checks to pass before merging:
  - test (ubuntu-latest)
  - lint
- Require branches to be up to date before merging
- Require conversation resolution before merging
```

## 6. 通知設定

### 6.1 Slack通知

```yaml
- name: Notify Slack on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    fields: repo,message,commit,author,action
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

### 6.2 メール通知

```yaml
- name: Send email on failure
  if: failure()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.example.com
    username: ${{ secrets.EMAIL_USER }}
    password: ${{ secrets.EMAIL_PASS }}
    subject: "CI Failed: ${{ github.repository }}"
    to: team@example.com
    body: |
      Workflow: ${{ github.workflow }}
      Run: ${{ github.run_number }}
      Branch: ${{ github.ref }}
```

## 7. セキュリティ考慮事項

### 7.1 シークレット管理

```yaml
# GitHub Secretsに保存すべき情報
secrets:
  - OPENAI_API_KEY        # LLM API キー（E2Eテスト用）
  - OPENSEARCH_PASSWORD   # OpenSearch認証情報
  - AWS_ACCESS_KEY_ID     # AWS認証情報
  - AWS_SECRET_ACCESS_KEY
  - SLACK_WEBHOOK_URL     # 通知用
```

### 7.2 依存関係スキャン

```yaml
- name: Run security scan
  uses: pyupio/safety@v2
  with:
    api-key: ${{ secrets.SAFETY_API_KEY }}
```

## 8. 導入ロードマップ

### Phase 1: 基本設定
- [ ] GitHub Actions ワークフロー作成
- [ ] ユニットテスト自動実行
- [ ] Lintチェック

### Phase 2: 統合テスト
- [ ] OpenSearch コンテナ設定
- [ ] 統合テスト自動実行
- [ ] カバレッジレポート

### Phase 3: 品質ゲート
- [ ] ブランチ保護設定
- [ ] カバレッジ閾値設定
- [ ] 通知設定

### Phase 4: 高度な機能
- [ ] 並列テスト実行
- [ ] セキュリティスキャン
- [ ] デプロイ自動化
