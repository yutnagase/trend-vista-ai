/** TrendVista AI - メインアプリケーション */

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAnalyze, useHistory } from "./hooks/useAnalysis";
import { ResultView } from "./pages/ResultView";
import type { AnalysisResponse } from "./types";

const queryClient = new QueryClient();

function AppContent() {
  const [keyword, setKeyword] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const analyze = useAnalyze();
  const history = useHistory();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyword.trim()) return;
    analyze.mutate(keyword.trim(), {
      onSuccess: (data) => setResult(data),
    });
  };

  return (
    <div className="flex min-h-screen">
      {/* サイドバー */}
      <aside className="sidebar-gradient w-72 flex flex-col p-6">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">
            🔭 TrendVista
          </h1>
          <p className="text-xs text-[var(--accent-indigo)] opacity-70 mt-1">AI Insight Explorer</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="キーワードを入力..."
            className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            type="submit"
            disabled={analyze.isPending || !keyword.trim()}
            className="w-full rounded-lg bg-indigo-600 px-3 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-40 transition-colors"
          >
            {analyze.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                分析中...
              </span>
            ) : (
              "分析開始"
            )}
          </button>
        </form>

        {analyze.isError && (
          <p className="mt-3 text-sm text-red-400">{analyze.error.message}</p>
        )}

        {/* 履歴 */}
        <div className="mt-8 flex-1 overflow-y-auto">
          <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            履歴
          </h2>
          <div className="space-y-1">
            {history.data?.map((h) => (
              <button
                key={h.id}
                className="w-full rounded-lg px-3 py-2 text-left text-xs text-[var(--text-secondary)] hover:bg-white/5 transition-colors"
                onClick={() => setKeyword(h.keyword)}
              >
                {h.keyword}
                <span className="ml-1 text-[var(--text-muted)]">
                  ({h.news_count + h.bsky_count + h.hatena_count}件)
                </span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* メインエリア */}
      <main className="flex-1 overflow-y-auto p-8">
        {result ? (
          <ResultView data={result} />
        ) : (
          <div className="flex h-full items-center justify-center">
            <div className="text-center">
              <p className="text-5xl">🔭</p>
              <p className="mt-3 text-[var(--text-muted)]">
                キーワードを入力して分析を開始してください
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
