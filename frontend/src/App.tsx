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
      <aside className="w-72 border-r bg-gray-50 p-4">
        <h1 className="mb-6 text-xl font-bold">🔭 TrendVista AI</h1>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="キーワードを入力..."
            className="w-full rounded border px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={analyze.isPending || !keyword.trim()}
            className="w-full rounded bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {analyze.isPending ? "分析中..." : "分析開始"}
          </button>
        </form>

        {analyze.isError && (
          <p className="mt-3 text-sm text-red-600">{analyze.error.message}</p>
        )}

        {/* 履歴 */}
        <div className="mt-8">
          <h2 className="mb-2 text-sm font-semibold text-gray-600">📋 履歴</h2>
          <div className="space-y-1">
            {history.data?.map((h) => (
              <button
                key={h.id}
                className="w-full rounded px-2 py-1 text-left text-xs hover:bg-gray-200"
                onClick={() => setKeyword(h.keyword)}
              >
                {h.keyword}
                <span className="ml-1 text-gray-400">
                  ({h.news_count + h.bsky_count + h.hatena_count}件)
                </span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* メインエリア */}
      <main className="flex-1 overflow-y-auto p-6">
        {result ? (
          <ResultView data={result} />
        ) : (
          <div className="flex h-full items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-4xl">🔭</p>
              <p className="mt-2">キーワードを入力して分析を開始してください</p>
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
