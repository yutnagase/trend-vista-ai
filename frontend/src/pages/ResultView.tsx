/** 分析結果表示 */

import type { AnalysisResponse } from "../types";
import { AnalysisTypeBadge } from "../components/AnalysisTypeBadge";
import { SentimentGauge } from "../components/SentimentGauge";
import { TopicChart } from "../components/TopicChart";

interface ResultViewProps {
  data: AnalysisResponse;
}

export function ResultView({ data }: ResultViewProps) {
  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="space-y-2">
        <h2 className="text-2xl font-bold">「{data.keyword}」の分析結果</h2>
        <AnalysisTypeBadge types={data.analysis_types} />
      </div>

      {/* 温度計 */}
      <div className="grid gap-4 md:grid-cols-3">
        {data.news.stats && (
          <div className="rounded-lg border p-4">
            <SentimentGauge score={data.news.net_score} label="📰 メディア" />
            <p className="mt-2 text-xs text-gray-500">
              {data.news.results.length}件
            </p>
          </div>
        )}
        {data.bsky.stats && (
          <div className="rounded-lg border p-4">
            <SentimentGauge score={data.bsky.net_score} label="🦋 BlueSky" />
            <p className="mt-2 text-xs text-gray-500">
              {data.bsky.results.length}件
            </p>
          </div>
        )}
        {data.hatena.stats && (
          <div className="rounded-lg border p-4">
            <SentimentGauge score={data.hatena.net_score} label="📑 はてブ" />
            <p className="mt-2 text-xs text-gray-500">
              {data.hatena.results.length}件
            </p>
          </div>
        )}
      </div>

      {/* 乖離情報 */}
      {data.divergences.length > 0 && (
        <div className="rounded-lg border p-4">
          <h3 className="mb-2 font-semibold">📊 ソース間乖離</h3>
          <div className="space-y-1 text-sm">
            {data.divergences.map(([a, b, gap, label], i) => (
              <div key={i} className="flex justify-between">
                <span>{a} vs {b}</span>
                <span className="font-mono">
                  {gap.toFixed(2)} ({label})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* トピック別感情 */}
      {Object.entries(data.topic_sentiments).map(([source, topics]) => (
        <TopicChart key={source} title={`${source} トピック感情`} topics={topics} />
      ))}

      {/* AI総評 */}
      {data.ai_report && (
        <div className="rounded-lg border bg-slate-50 p-4">
          <h3 className="mb-2 font-semibold">🤖 AI総合インサイト</h3>
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {data.ai_report}
          </div>
        </div>
      )}
    </div>
  );
}
