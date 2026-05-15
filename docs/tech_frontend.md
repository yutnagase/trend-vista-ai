# フロントエンド — React 19 + TanStack Query + Recharts

## 技術選定

_referenceプロジェクトではStreamlitを使っていたが、本プロジェクトではReact + TypeScriptに移行した。移行の判断理由は [ARCHITECTURE.md](ARCHITECTURE.md) に記載している。

| 技術 | 役割 |
|------|------|
| React 19 | UIフレームワーク |
| TypeScript 5.6 | 型安全性 |
| Vite 6 | ビルドツール・開発サーバー |
| TanStack Query v5 | サーバー状態管理 |
| Recharts | チャート描画 |
| Tailwind CSS | スタイリング |
| Lucide React | アイコン |

## TanStack Query — サーバー状態管理

### なぜTanStack Queryか

バックエンドAPIからのデータ取得には、ローディング状態・エラーハンドリング・キャッシュ・再取得といった共通の関心事がある。これらを毎回useStateとuseEffectで書くのは冗長だし、バグの温床になる。

TanStack Queryはこれらを宣言的に管理してくれる。

```typescript
// hooks/useAnalysis.ts
export function useAnalyze() {
  return useMutation({
    mutationFn: (keyword: string) => api.analyze(keyword),
  });
}

export function useHistory() {
  return useQuery({
    queryKey: ["history"],
    queryFn: () => api.getHistory(),
  });
}
```

コンポーネント側では`isLoading`、`error`、`data`を受け取るだけで済む。

### mutationとqueryの使い分け

- **useQuery** — GETリクエスト（履歴一覧、個別結果）。キャッシュ・自動再取得あり
- **useMutation** — POST/PUT/DELETEリクエスト（分析実行、AI総評生成）。明示的にトリガーする操作

分析実行は副作用を伴う操作なのでmutationとして扱う。

## APIクライアント

```typescript
// api/client.ts
const BASE_URL = "/api";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
```

エラーハンドリングを一箇所に集約している。FastAPIが返す`detail`フィールドをそのままErrorメッセージとして使う。

axiosを使わずfetch APIを直接使っている理由:
- ブラウザ標準APIで追加依存なし
- レスポンスのJSON変換とエラーハンドリングだけなら薄いラッパーで十分
- バンドルサイズを不要に増やしたくない

## 型定義 — バックエンドとの同期

```typescript
// types/index.ts
export interface AnalysisResponse {
  id: string;
  keyword: string;
  timestamp: string;
  news: SourceAnalysis;
  bsky: SourceAnalysis;
  hatena: SourceAnalysis;
  topic_sentiments: Record<string, TopicSentiment[]>;
  analysis_types: AnalysisType[];
  divergences: [string, string, number, string][];
  ai_report: string;
}
```

バックエンドのPydanticスキーマと1:1対応するTypeScript型を手動で定義している。OpenAPI自動生成も検討したが、現時点ではスキーマ変更頻度が低いため手動管理で十分と判断した。スキーマが乖離した場合はTypeScriptのコンパイルエラーで検知できる。

## コンポーネント設計

### SentimentGauge — Net Sentiment Scoreの可視化

ドットプロット形式の温度計UI。スコアの位置と色でポジティブ/ネガティブの度合いを直感的に表現する。

```typescript
function getScoreColor(score: number): string {
  if (score >= 0.3) return "#22c55e";  // 緑
  if (score >= 0.1) return "#86efac";  // 薄緑
  if (score > -0.1) return "#9ca3af";  // グレー
  if (score > -0.3) return "#f97316";  // オレンジ
  return "#ef4444";                     // 赤
}
```

閾値はバックエンドのNet Sentiment Scoreのラベル区間と一致させている。

### TopicChart — トピック別感情のチャート

Rechartsを使い、トピックごとのNet Sentiment Scoreを棒グラフで表示する。ポジティブは緑、ネガティブは赤で色分けし、どの話題が全体のスコアに寄与しているかを視覚化する。

### AnalysisTypeBadge — 分析タイプの表示

分析タイプ（構造的乖離、トピック集中型等）をバッジ形式で表示するコンポーネント。emoji + ラベル + 判定理由を表示する。

## 状態管理の方針

グローバルな状態管理ライブラリ（Redux, Zustand等）は導入していない。

- サーバー状態 → TanStack Queryが管理
- クライアント状態 → ページ内のuseStateで十分

この規模のアプリケーションでは、不要な抽象化を入れるとかえってコードの追跡が困難になる。TanStack Queryがキャッシュ・ローディング・エラーを管理してくれるので、コンポーネント側のロジックは最小限で済む。

## Vite — ビルドと開発サーバー

### 開発時

Viteの開発サーバーがHMR（Hot Module Replacement）を提供する。ファイル保存時に変更箇所だけが即座にブラウザに反映される。

バックエンドAPIへのリクエストはViteのプロキシ設定で`/api`を`localhost:8000`に転送している。

### ビルド

```bash
npm run build
# → dist/ に静的ファイルが生成される
```

TypeScriptのコンパイルとViteのバンドルを実行する。CIでもこのコマンドでビルドが通ることを確認している。

## Tailwind CSS

ユーティリティファーストのCSSフレームワーク。クラス名でスタイルを直接指定する方式で、CSSファイルの肥大化を防ぐ。

```tsx
<div className="space-y-3">
  <span className="text-sm font-medium text-[var(--text-primary)]">{label}</span>
  <div className="relative h-3 w-full rounded-full bg-gray-700/50">
    ...
  </div>
</div>
```

CSS変数（`var(--text-primary)`等）を併用し、ダークテーマ対応の余地を残している。

## 参考リンク

- [React 公式ドキュメント](https://react.dev/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Recharts](https://recharts.org/)
- [Vite](https://vite.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
