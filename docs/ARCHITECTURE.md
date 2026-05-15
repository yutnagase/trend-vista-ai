# Architecture — 設計思想とStreamlitからの移行

## なぜReact + FastAPIに移行したか

_referenceプロジェクト（TrendInsight AI）はStreamlit単体で構築していた。Streamlitはプロトタイピングには最適だが、以下の制約が顕在化していた。

| 制約 | 具体的な問題 |
|------|-------------|
| 再実行モデル | ボタン押下のたびにスクリプト全体が再実行される。部分更新ができない |
| UI自由度 | 提供コンポーネントに縛られ、カスタムチャートやインタラクションが困難 |
| テスタビリティ | UI層とロジックが密結合し、ユニットテストが書きにくい |
| スケーラビリティ | シングルプロセス前提。バックグラウンドタスクの分離が困難 |
| フロントエンド技術の習得 | 技術力アピールとしてReact + TypeScriptの実装力を示したい |

_referenceのREADMEにも「React + FastAPI移行トレードオフ」のセクションがあり、移行が妥当になる条件として「UIの細かいインタラクション」「テスタビリティ」を挙げていた。本プロジェクトはその判断を実行に移したものである。

## 全体構成

```
┌─────────────────────────────────────────────────────────┐
│  Browser                                                 │
│  React SPA (Vite dev server / nginx)                    │
│    └── TanStack Query → fetch("/api/...")                │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (JSON)
┌────────────────────────▼────────────────────────────────┐
│  FastAPI                                                 │
│    ├── api/          エンドポイント定義                   │
│    ├── application/  ユースケース (AnalyzeUseCase)        │
│    ├── domain/       Protocol + ドメインモデル            │
│    ├── services/     分析ロジック（純粋関数中心）          │
│    └── infrastructure/ 外部依存アダプター                  │
└──────────────────────────────────────────────────────────┘
```

フロントエンドとバックエンドはHTTP APIのみで接続される。開発時はViteのプロキシ、本番ではnginxやdocker-composeのネットワークで接続する想定。

## バックエンドのレイヤー構成

クリーンアーキテクチャの原則に従い、依存方向を内側（ドメイン）に向けている。

### domain/ — ドメイン層

外部依存ゼロ。ビジネスルールの核心を定義する。

- `models.py` — Article, AnalysisResult等のPydanticモデル
- `__init__.py` — Protocol定義（SentimentAnalyzerProtocol, DataCollectorProtocol等）
- `exceptions.py` — カスタム例外階層

### services/ — サービス層

ドメインモデルを操作する純粋なロジック。外部I/Oに依存しない。

- `analyzer.py` — BERTアンサンブル（唯一PyTorch依存だが、Protocolで抽象化済み）
- `analysis_pipeline.py` — パイプライン全体のオーケストレーション
- `analysis_type.py` — ルールベースのパターン分類
- `topic_sentiment.py` — トピック別感情集約
- `insight.py` — 乖離検出
- `text_processor.py` — 形態素解析・キーワード抽出

### application/ — ユースケース層

1つのユーザー操作に対応するフロー制御を担当する。

- `AnalyzeUseCase` — データ収集→分析→保存の一連のフローを実行

ユースケースはProtocolにのみ依存し、具象クラスを知らない。

### infrastructure/ — インフラ層

外部システムとの接続を担当するアダプター群。

- `collectors.py` — MultiSourceCollector（RSS, AT Protocol, はてなAPI）
- `llm_reporter.py` — LLMReportGenerator（llama-cpp-python）
- `history_repository.py` — JsonHistoryRepository（ファイルI/O）

各アダプターはdomain/のProtocolを実装する。

### core/ — 設定・DI

- `config.py` — pydantic-settingsによる環境変数管理
- `dependencies.py` — FastAPI Depends用のファクトリ（Composition Root）

### api/ — エンドポイント

FastAPIのルーター定義。HTTPリクエストの受け取りとレスポンス変換のみを担当し、ビジネスロジックは持たない。

## FastAPI — API層の設計

### エンドポイント設計

| Method | Endpoint | 責務 | レスポンス時間 |
|--------|----------|------|---------------|
| POST | `/api/analyze` | データ収集→感情分析→統計量算出→保存 | 10〜30秒 |
| POST | `/api/report/{id}` | 保存済み結果に対してLLM総評を生成 | 30〜120秒 |
| GET | `/api/history` | 過去分析一覧（サマリー） | <100ms |
| GET | `/api/history/{id}` | 個別分析結果（フル） | <100ms |
| GET | `/health` | ヘルスチェック | <10ms |

分析実行とAI総評生成を分離したのは意図的な設計判断である。LLM推論は30秒〜2分かかるため、分析結果を先に返してUIに表示し、総評は後から非同期で取得する。フロントエンド側ではTanStack Queryのmutationで総評生成を管理し、ローディング状態をUIに反映している。

### Dependsによる依存注入の流れ

FastAPIのDepends機構をDIコンテナとして活用している。リクエストが来たときの依存解決の流れは以下の通り。

```python
# api/__init__.py
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalyzeRequest,
    use_case: AnalyzeUseCase = Depends(_get_use_case),  # ← ここで注入
) -> AnalysisResponse:
    result = use_case.execute(request.keyword)
    return AnalysisResponse(...)

def _get_use_case(
    analyzer: Any = Depends(get_analyzer),          # ← @lru_cacheでシングルトン
    collector: Any = Depends(get_collector),
    report_generator: Any = Depends(get_report_generator),
    history: Any = Depends(get_history_repository),
) -> AnalyzeUseCase:
    return AnalyzeUseCase(
        analyzer=analyzer,
        collector=collector,
        report_generator=report_generator,
        history=history,
    )
```

```python
# core/dependencies.py
@lru_cache
def get_analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()  # 初回呼び出し時にBERTモデルをロード、以降はキャッシュ
```

ポイント:
- `@lru_cache`により、BERTモデルやLLMのような重いリソースはプロセス起動中に1回だけ生成される
- `_get_use_case`がComposition Rootとして機能し、具象クラスの組み立てをここに集約
- エンドポイント関数自体はユースケースを呼ぶだけで、依存の詳細を知らない
- テスト時は`app.dependency_overrides`でモックに差し替え可能

### Pydantic v2によるリクエスト/レスポンス

リクエストバリデーションとレスポンスシリアライズはPydantic v2に委譲している。

```python
# schemas/__init__.py
class AnalyzeRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=100)

class AnalysisResponse(BaseModel):
    id: str
    keyword: str
    timestamp: str
    news: dict[str, Any]
    bsky: dict[str, Any]
    hatena: dict[str, Any]
    topic_sentiments: dict[str, list[dict[str, Any]]]
    analysis_types: list[dict[str, str]]
    divergences: list[list[Any]]
    ai_report: str
```

`keyword`に`min_length=1`を設定しているため、空文字列のリクエストはFastAPIが自動的に422を返す。エンドポイント側でバリデーションコードを書く必要がない。

### エラーハンドリング

ドメイン例外をHTTPステータスコードにマッピングする。

```python
@router.post("/analyze")
async def analyze(request: AnalyzeRequest, use_case = Depends(_get_use_case)):
    try:
        result = use_case.execute(request.keyword)
    except DataCollectionError as e:
        raise HTTPException(status_code=404, detail=e.user_message) from e
    except TrendVistaError as e:
        raise HTTPException(status_code=500, detail=e.user_message) from e
```

- `DataCollectionError`（記事が見つからない）→ 404
- その他の`TrendVistaError` → 500
- Pydanticバリデーション失敗 → 422（FastAPI自動）

ユーザー向けメッセージ（`user_message`）のみをレスポンスに含め、スタックトレース等の技術的詳細はstructlogに記録する。

### CORSミドルウェア

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # デフォルト: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

開発時はViteの開発サーバー（port 5173）からFastAPI（port 8000）へのクロスオリジンリクエストが発生するため、CORSを許可している。`cors_origins`は環境変数で設定可能にしており、本番環境では適切なオリジンに絞る想定。

## フロントエンドの設計

### ディレクトリ構成の意図

```
src/
├── api/client.ts       # HTTP通信の一元管理
├── components/         # 再利用可能なUI部品
├── hooks/              # TanStack Queryによるサーバー状態管理
├── pages/              # ページ単位の構成
├── types/index.ts      # バックエンドAPIの型定義
└── lib/utils.ts        # ユーティリティ
```

- `api/` — fetchのラッパー。エラーハンドリングを一箇所に集約
- `hooks/` — TanStack Queryのmutation/queryをカスタムフックとして公開。コンポーネントからはデータ取得の詳細を隠蔽
- `types/` — バックエンドのPydanticスキーマと1:1対応するTypeScript型。手動同期だが、スキーマ変更時に型エラーで検知できる

### 状態管理の方針

グローバルな状態管理ライブラリ（Redux, Zustand等）は導入していない。理由は以下の通り。

- サーバー状態はTanStack Queryが管理する（キャッシュ・再取得・ローディング状態）
- クライアント状態はページ内のuseStateで十分な規模
- 不要な抽象化を入れると、かえってコードの追跡が困難になる

## ProtocolベースのDI

Python 3.12の`typing.Protocol`を使い、構造的部分型でインターフェースを定義している。

```python
# domain/__init__.py
class SentimentAnalyzerProtocol(Protocol):
    def analyze(self, text: str) -> dict[str, float | str]: ...
    def analyze_batch(self, texts: list[str]) -> list[dict[str, float | str]]: ...
```

ユースケースはProtocolにのみ依存する。

```python
# application/__init__.py
class AnalyzeUseCase:
    def __init__(
        self,
        analyzer: SentimentAnalyzerProtocol,
        collector: DataCollectorProtocol,
        report_generator: ReportGeneratorProtocol,
        history: HistoryRepositoryProtocol,
    ) -> None: ...
```

FastAPIのDependsで具象を組み立てて注入する。

```python
# core/dependencies.py
@lru_cache
def get_analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()
```

テスト時はモックを渡すだけで外部依存ゼロの検証が可能になる。

### なぜDIフレームワークを使わないか

`dependency-injector`等のDIフレームワークも検討したが、以下の理由で不採用とした。

- FastAPIのDepends機構が十分にDIコンテナとして機能する
- Protocol + コンストラクタ注入で十分シンプルに実現できる
- 依存ライブラリを増やしたくない（ローカル完結の原則）

## _referenceからの主な変更点

| 観点 | _reference (Streamlit) | 本プロジェクト (React + FastAPI) |
|------|----------------------|-------------------------------|
| UI | Streamlit | React 19 + Tailwind CSS |
| API | なし（単一プロセス） | FastAPI REST API |
| 状態管理 | st.session_state | TanStack Query |
| DI | 手動コンストラクタ注入 | FastAPI Depends + Protocol |
| ユースケース | orchestrator.py | application/AnalyzeUseCase |
| AI総評 | 分析と同時に生成 | 別エンドポイントで非同期生成 |
| テスト | pytest + モック | pytest + FastAPI TestClient |
| CI | なし | GitHub Actions (lint/test/security) |

### AI総評の非同期化

_referenceではデータ収集→分析→LLM総評を直列実行していたため、レスポンスに1〜2分かかっていた。本プロジェクトでは分析結果を先に返し、AI総評は`POST /api/report/{id}`で別途リクエストする設計に変更した。

これにより、ユーザーは分析結果（スコア・乖離・トピック）を即座に確認でき、AI総評は必要に応じて後から生成できる。LLM推論が不要なユースケース（数値だけ見たい場合）ではレスポンスが大幅に高速化される。

## Docker構成

```yaml
services:
  backend:   # FastAPI + BERTモデル + LLM
  frontend:  # Vite dev server (開発時) / nginx (本番)
```

- バックエンドのモデルファイルはnamed volumeで永続化し、コンテナ再作成時の再ダウンロードを防止
- healthcheckでバックエンドの起動完了を待ってからフロントエンドを起動
- 開発時はホットリロード有効（backend: `--reload`, frontend: Vite HMR）
