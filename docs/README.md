# docs - ドキュメント目次

## 技術解説

Tech Stackの各層について、設計判断とサンプルコード付きで解説している。

| ドキュメント | 内容 |
|-------------|------|
| [tech_sentiment_analysis.md](tech_sentiment_analysis.md) | 感情分析 — 複数BERTモデルアンサンブルによるソフト投票 |
| [tech_morphological_analysis.md](tech_morphological_analysis.md) | 形態素解析 — Janomeで日本語を単語に分割する |
| [tech_llm_inference.md](tech_llm_inference.md) | LLM推論 — llama-cpp-python + ELYZA-JP-8Bによる総評生成 |
| [tech_data_collection.md](tech_data_collection.md) | データ収集 — feedparser / atproto / requestsの使い分け |
| [tech_frontend.md](tech_frontend.md) | フロントエンド — React 19 + TanStack Query + Recharts |

## 設計・開発記録

| ドキュメント | 内容 |
|-------------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | アーキテクチャ設計 — Streamlitからの移行判断とクリーンアーキテクチャ |
| [DEVELOPMENT_INSIGHT.md](DEVELOPMENT_INSIGHT.md) | 技術設計の背景と意思決定（感情分析アンサンブル・トピック分析・分析タイプ判定・DI・エラーハンドリング） |
| [testing.md](testing.md) | テスト戦略 — モック戦略・カバレッジ方針 |
