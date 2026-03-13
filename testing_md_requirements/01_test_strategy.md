# テスト戦略

## 1. 概要

本ドキュメントでは、python-fastapiプロジェクトのテスト戦略を定義します。

## 2. テストピラミッド

プロジェクトでは、以下のテストピラミッド構造を採用します：

```
          /\
         /  \
        / E2E \        <- 少数（手動 + 自動）
       /--------\
      /  統合   \      <- 中程度
     /-----------\
    /  ユニット   \    <- 多数
   /---------------\
```

| レベル | 割合目安 | 実行頻度 | 実行時間 |
|--------|---------|---------|---------|
| ユニットテスト | 70% | 毎コミット | 秒単位 |
| 統合テスト | 20% | 毎PR | 分単位 |
| E2Eテスト | 10% | デプロイ前 | 分〜時間単位 |

## 3. テストレベル別戦略

### 3.1 ユニットテスト

**目的**: 個々の関数・クラスの動作検証

**対象**:
- ビジネスロジック（エージェント、ツール、サービス）
- ユーティリティ関数
- データ変換・バリデーション
- エラーハンドリング

**特徴**:
- 外部依存は全てモック化
- 高速実行（数秒以内）
- 独立して実行可能

**ツール**: pytest, pytest-mock, unittest.mock

```python
# ユニットテストの例
import pytest
from unittest.mock import AsyncMock, patch

class TestValidatePolicy:
    """ポリシー検証のユニットテスト"""

    @pytest.mark.asyncio
    async def test_valid_policy_returns_success(self, mock_yaml_parser):
        """有効なポリシーで成功を返す"""
        # Arrange
        policy_content = "policies:\n  - name: test"
        mock_yaml_parser.return_value = {"policies": [{"name": "test"}]}

        # Act
        result = validate_policy(policy_content)

        # Assert
        assert result.is_valid is True
```

### 3.2 統合テスト

**目的**: コンポーネント間の連携検証

**対象**:
- APIエンドポイント（FastAPI TestClient使用）
- データベース連携（OpenSearch）
- 外部サービス連携（LLM API、AWS）
- 認証・認可フロー

**特徴**:
- 実際のコンポーネントを使用（一部モック）
- 中程度の実行時間
- テスト環境での実行

**ツール**: pytest, httpx.AsyncClient, TestClient

```python
# 統合テストの例
import pytest
from httpx import AsyncClient

class TestCSPMEndpoint:
    """CSPMエンドポイントの統合テスト"""

    @pytest.mark.asyncio
    async def test_refine_policy_endpoint(self, async_client, mock_llm):
        """ポリシー修正エンドポイントの統合テスト"""
        # Arrange
        request_data = {
            "prompt": "S3バケットの暗号化を追加",
            "policy_context": "policies:\n  - name: s3-check"
        }

        # Act
        response = await async_client.post(
            "/api/cspm/chat/refine",
            json=request_data
        )

        # Assert
        assert response.status_code == 200
        assert "response" in response.json()
```

### 3.3 E2Eテスト

**目的**: システム全体の動作検証

**対象**:
- 完全なユーザーフロー
- 実環境に近い条件でのテスト
- パフォーマンス検証

**特徴**:
- 実際の外部サービスに接続（テスト環境）
- 長い実行時間
- 環境依存が高い

**実行タイミング**:
- デプロイ前の最終確認
- 定期的な回帰テスト

## 4. リスクベーステスト

### 4.1 リスク評価マトリクス

| 機能領域 | 影響度 | 発生可能性 | リスクレベル | テスト優先度 |
|---------|--------|-----------|-------------|-------------|
| 認証・認可 | 高 | 中 | 高 | 最優先 |
| CSPMポリシー生成 | 高 | 中 | 高 | 最優先 |
| LLM連携 | 中 | 高 | 高 | 最優先 |
| ジョブ管理 | 中 | 中 | 中 | 優先 |
| レポート生成 | 中 | 低 | 中 | 標準 |
| ログ解析 | 低 | 低 | 低 | 標準 |

### 4.2 重点テスト領域

**最優先テスト（リスク高）**:
1. **認証・JWT処理**
   - トークン生成・検証
   - 権限チェック
   - セッション管理

2. **CSPMポリシー生成・検証**
   - YAMLパース・バリデーション
   - ポリシー修正ロジック
   - エージェント実行フロー

3. **LLM連携**
   - プロンプト処理
   - レスポンスパース
   - エラーハンドリング

## 5. テストデータ管理

### 5.1 テストデータ戦略

| データタイプ | 管理方法 | 例 |
|-------------|---------|-----|
| 固定データ | フィクスチャファイル | 有効なポリシーYAML |
| 動的データ | ファクトリ関数 | ランダムUUID生成 |
| 大規模データ | 外部ストレージ | テスト用OpenSearchインデックス |

### 5.2 データ分離

- 本番データへのアクセス禁止
- テスト専用インデックス使用（プレフィックス: `test_`）
- テスト終了後のクリーンアップ必須

## 6. テスト品質基準

### 6.1 テストコード品質

- **命名規則**: `test_<対象>_<条件>_<期待結果>`
- **AAA パターン**: Arrange, Act, Assert の明確な分離
- **単一責任**: 1テスト1検証
- **独立性**: テスト間の依存なし

### 6.2 レビュー基準

テストコードのレビューでは以下を確認：
- [ ] テストケースが要件をカバーしている
- [ ] エッジケースが考慮されている
- [ ] モックが適切に設定されている
- [ ] アサーションが明確
- [ ] テストが独立して実行可能
