# テスト戦略

## 方針

Protocol + DIアーキテクチャにより、LLM・ネットワーク・GPU不要でコアロジックを検証できる構成を採用している。FastAPI TestClientを使い、エンドポイント単位の統合テストも実行可能。

## テストピラミッド

```
        ┌─────────────┐
        │  E2E (手動)  │  ブラウザ操作
        ├─────────────┤
        │  統合テスト   │  FastAPI TestClient + モック注入
        ├─────────────┤
        │ ユニットテスト │  純粋関数・個別サービス
        └─────────────┘
```

| レベル | 対象 | 外部依存 | 実行速度 |
|--------|------|----------|----------|
| ユニット | analysis_type, topic_sentiment, insight, text_processor | なし | 高速 |
| 統合 | APIエンドポイント（モック注入経由） | なし | 高速 |
| スロー | SentimentAnalyzer（実BERTモデル） | モデルファイル | 低速 |
| E2E | ブラウザ操作 | 全依存 | 手動 |

## テスト実行方法

```bash
cd backend

# テスト実行
uv run pytest -x -q

# カバレッジ付き
uv run pytest --cov --cov-report=term-missing

# HTML形式のカバレッジレポート
uv run pytest --cov --cov-report=html
# → htmlcov/index.html をブラウザで確認

# 特定テストファイルのみ
uv run pytest tests/test_api.py -v
```

## テストファイル構成

```
backend/tests/
├── __init__.py
└── test_api.py          # APIエンドポイント統合テスト
```

今後の拡張予定:
```
backend/tests/
├── test_api.py                 # APIエンドポイント
├── test_analysis_type.py       # 分析タイプ判定（5パターン全条件網羅）
├── test_topic_sentiment.py     # トピック別感情集約（境界値テスト）
├── test_analysis_pipeline.py   # パイプライン統合テスト（モックanalyzer）
├── test_text_processor.py      # キーワード抽出
└── test_analyzer.py            # BERTアンサンブル実モデルテスト (@slow)
```

## モック戦略

### FastAPI Dependsのオーバーライド

FastAPIのDependency Injectionを活用し、テスト時にモックを注入する。

```python
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_history_empty():
    with patch("app.api.get_history_repository") as mock:
        repo = MagicMock()
        repo.load_all.return_value = []
        mock.return_value = repo
        response = client.get("/api/history")
        assert response.status_code == 200
```

### SentimentAnalyzerProtocolのモック

パイプラインテストでは、BERTモデルの代わりにルールベースのモックを注入する。

```python
class MockAnalyzer:
    def analyze(self, text: str) -> dict[str, float | str]:
        return self.analyze_batch([text])[0]

    def analyze_batch(self, texts: list[str]) -> list[dict[str, float | str]]:
        results = []
        for text in texts:
            if "良い" in text:
                results.append({"positive": 0.8, "negative": 0.1, "label": "positive"})
            elif "悪い" in text:
                results.append({"positive": 0.1, "negative": 0.8, "label": "negative"})
            else:
                results.append({"positive": 0.3, "negative": 0.3, "label": "neutral"})
        return results
```

このモックはProtocolに準拠しているため、型チェック（mypy）でも問題なく通る。

## カバレッジ方針

### 計測対象

コアロジック（テスト可能かつビジネス価値の高い部分）:

- `app/services/` — 分析パイプライン、タイプ判定、トピック感情、乖離検出
- `app/domain/` — ドメインモデル、例外
- `app/api/` — エンドポイント（TestClient経由）

### 計測対象外

外部依存が強く、モック化のコストが高い部分:

- `app/infrastructure/` — LLM推論、外部API通信（統合テストで間接的にカバー）
- `app/core/dependencies.py` — ファクトリ関数（設定のみ）

## CI統合

GitHub Actionsで`uv run pytest -x -q`を実行している。テスト失敗時はPRのマージをブロックする。

```yaml
# .github/workflows/ci.yml
backend-test:
  runs-on: ubuntu-latest
  steps:
    - run: uv run pytest -x -q
```

## フロントエンドのテスト

現時点ではESLint + TypeScript型チェック + ビルド成功をCIで確認している。

```yaml
frontend-lint:
  steps:
    - run: npx eslint .
    - run: npx tsc --noEmit

frontend-build:
  steps:
    - run: npm run build
```

コンポーネントのユニットテスト（Vitest + Testing Library）は今後の拡張候補。

## テスト設計の原則

1. **純粋関数を優先的にテスト** — 入力→出力が決定的な関数は最もテストしやすく、バグの温床になりやすい
2. **DIの恩恵を最大化** — Protocolに依存する箇所はモック注入で外部依存を排除
3. **スローテストの分離** — BERTモデル依存テストは分離し、日常開発を高速に保つ
4. **境界値を重視** — min_count、閾値判定、空入力など、エッジケースを明示的にテスト
5. **テストが仕様書になる** — テスト名で「何が保証されているか」を読み取れるようにする
