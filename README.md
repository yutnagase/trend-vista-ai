# 🔭 TrendVista AI（トレンドヴィスタ AI）

多角的な視点から世の中の空気感を読み解くAIインサイト抽出ツール。

React(TypeScript) + FastAPI構成のフルスタックアプリケーション。

## アーキテクチャ

```
trend-vista-ai/
├── backend/          # FastAPI (Python 3.12+)
│   ├── app/
│   │   ├── api/          # エンドポイント
│   │   ├── application/  # ユースケース
│   │   ├── core/         # 設定・DI
│   │   ├── domain/       # ドメインモデル・Protocol
│   │   ├── infrastructure/ # アダプター（LLM, Clients）
│   │   ├── schemas/      # Pydanticスキーマ
│   │   └── services/     # 分析ロジック
│   └── tests/
├── frontend/         # React + TypeScript + Vite
│   └── src/
│       ├── api/          # APIクライアント
│       ├── components/   # UIコンポーネント
│       ├── hooks/        # TanStack Query hooks
│       ├── pages/        # ページ
│       └── types/        # 型定義
└── docker-compose.yml
```

## 設計原則

- **LLMは「説明のみ」担当** — 感情スコア・乖離分析・トピック分析・分析タイプ判定はすべてPythonコードで実行
- **クリーンアーキテクチャ + 依存逆転原則** — Python側はProtocol、TypeScript側はInterface
- **ローカル完結** — データ外部送信禁止
- **テスト容易性** — ProtocolベースDI、APIモック容易な設計

## Analysis Pipeline

1. **データ収集** — Google News RSS / BlueSky AT Protocol / はてなブックマーク（並列フェッチ）
2. **感情分析** — 3つのBERTモデルによるアンサンブル（ソフト投票）
3. **統計量算出** — ソース別Net Sentiment Score、キーワード抽出
4. **トピック別感情分析** — キーワード×感情の交差分析
5. **乖離検出** — ソース間のスコア差を定量化
6. **分析タイプ判定** — ルールベースのパターン分類
7. **AI総評生成** — ローカルLLM（Llama-3-ELYZA-JP-8B）による説明生成

## セットアップ

### Docker（推奨）

```bash
cp backend/.env.example backend/.env
docker compose up
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### ローカル開発

```bash
# Backend
cd backend
uv sync
cp .env.example .env
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | キーワード分析実行 |
| GET | `/api/history` | 過去分析一覧 |
| GET | `/api/history/{id}` | 個別分析結果 |
| GET | `/health` | ヘルスチェック |

## 技術スタック

### Backend
- Python 3.12+ / FastAPI / Pydantic v2
- PyTorch + Transformers（BERTアンサンブル）
- llama-cpp-python（ローカルLLM）
- Janome（形態素解析）
- structlog（構造化ログ）

### Frontend
- React 19 / TypeScript / Vite
- TanStack Query（状態管理）
- Recharts（チャート）
- Tailwind CSS（スタイリング）
