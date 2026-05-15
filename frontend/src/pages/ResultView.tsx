/** 分析結果表示 — ダッシュボードレイアウト */

import { useState, useEffect } from "react";
import type { AnalysisResponse, SourceAnalysis } from "../types";
import { AnalysisTypeBadge } from "../components/AnalysisTypeBadge";
import { SentimentGauge } from "../components/SentimentGauge";
import { TopicChart } from "../components/TopicChart";
import { api } from "../api/client";

interface ResultViewProps {
  data: AnalysisResponse;
}

export function ResultView({ data }: ResultViewProps) {
  const [aiReport, setAiReport] = useState<string | null>(data.ai_report || null);
  const [reportLoading, setReportLoading] = useState(!data.ai_report);

  useEffect(() => {
    if (data.ai_report) {
      setAiReport(data.ai_report);
      setReportLoading(false);
      return;
    }
    if (!data.id) return;
    setReportLoading(true);
    api.generateReport(data.id)
      .then((res) => setAiReport(res.ai_report))
      .catch(() => setAiReport("※ AI総評の生成に失敗しました"))
      .finally(() => setReportLoading(false));
  }, [data.id, data.ai_report]);
  const sources = [
    { key: "news" as const, label: "📰 メディア", data: data.news },
    { key: "bsky" as const, label: "🦋 BlueSky", data: data.bsky },
    { key: "hatena" as const, label: "📑 はてブ", data: data.hatena },
  ].filter((s) => s.data.stats);

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* ヘッダー */}
      <div className="space-y-3">
        <h2 className="text-2xl font-bold text-[var(--text-primary)]">
          「{data.keyword}」の分析結果
        </h2>
        <AnalysisTypeBadge types={data.analysis_types} />
      </div>

      {/* AI総合インサイト — 最上位に配置して目立たせる */}
      <div className="card-insight p-6">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">🤖</span>
          <h3 className="text-base font-bold text-[var(--accent-indigo)]">
            AI総合インサイト
          </h3>
        </div>
        {reportLoading ? (
          <div className="flex items-center gap-3 py-4">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-400/30 border-t-indigo-400" />
            <span className="text-sm text-[var(--text-secondary)] animate-pulse">
              AIが分析結果を読み解いています...
            </span>
          </div>
        ) : (
          <div className="whitespace-pre-wrap text-sm leading-relaxed text-[var(--text-secondary)]">
            {aiReport}
          </div>
        )}
      </div>

      {/* スコアカード */}
      <section className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          ソース別スコア
        </h3>
        <div className="grid gap-4 md:grid-cols-3">
          {sources.map((s) => (
            <div key={s.key} className="card-glass p-5">
              <SentimentGauge score={s.data.net_score} label={s.label} />
              <p className="mt-3 text-xs text-[var(--text-muted)]">
                {s.data.results.length}件の投稿を分析
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* 乖離情報 */}
      {data.divergences.length > 0 && (
        <section className="card-glass p-5">
          <h3 className="mb-3 text-sm font-semibold text-[var(--text-primary)]">
            📊 ソース間乖離
          </h3>
          <div className="space-y-2">
            {data.divergences.map(([a, b, gap, label], i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg bg-white/5 px-4 py-2"
              >
                <span className="text-sm text-[var(--text-secondary)]">
                  {a} vs {b}
                </span>
                <span
                  className="font-mono text-sm font-medium"
                  style={{
                    color: Math.abs(gap) > 0.3 ? "#f97316" : "var(--text-primary)",
                  }}
                >
                  {gap.toFixed(2)}{" "}
                  <span className="text-xs text-[var(--text-secondary)]">({label})</span>
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* トピック別感情 */}
      {Object.keys(data.topic_sentiments).length > 0 && (
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            トピック別感情分析
          </h3>
          <div className="grid gap-4 md:grid-cols-1 lg:grid-cols-2">
            {Object.entries(data.topic_sentiments).map(([source, topics]) => (
              <div key={source} className="card-glass p-5">
                <TopicChart
                  title={`${source} トピック感情`}
                  topics={topics}
                />
              </div>
            ))}
          </div>
        </section>
      )}
      {/* 代表意見 */}
      {sources.some((s) => Object.values(s.data.samples).some((v) => v.length > 0)) && (
        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
            代表意見
          </h3>
          <div className="grid gap-4 md:grid-cols-3">
            {sources.map((s) => (
              <div key={s.key} className="card-glass p-5 space-y-3">
                <span className="text-sm font-medium text-[var(--text-primary)]">{s.label}</span>
                {s.data.samples.positive?.map((text, i) => (
                  <p key={`p${i}`} className="text-xs text-green-400">🟢 {text}</p>
                ))}
                {s.data.samples.negative?.map((text, i) => (
                  <p key={`n${i}`} className="text-xs text-red-400">🔴 {text}</p>
                ))}
                {!s.data.samples.positive?.length && !s.data.samples.negative?.length && (
                  <p className="text-xs text-[var(--text-muted)]">データなし</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 記事・投稿一覧 */}
      <section className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
          記事・投稿一覧
        </h3>
        <ArticleTabs
          news={data.news}
          bsky={data.bsky}
          hatena={data.hatena}
        />
      </section>
    </div>
  );
}

/* タブ切り替えの記事一覧 */
function ArticleTabs({ news, bsky, hatena }: { news: SourceAnalysis; bsky: SourceAnalysis; hatena: SourceAnalysis }) {
  const tabs = [
    { key: "news", label: "📰 メディア", data: news },
    { key: "bsky", label: "🦋 BlueSky", data: bsky },
    { key: "hatena", label: "📑 はてブ", data: hatena },
  ].filter((t) => t.data.results.length > 0);

  const [active, setActive] = useState(tabs[0]?.key || "news");
  const current = tabs.find((t) => t.key === active);

  return (
    <div className="card-glass overflow-hidden">
      {/* タブヘッダー */}
      <div className="flex border-b border-white/5">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActive(t.key)}
            className={`px-4 py-3 text-sm transition-colors ${
              active === t.key
                ? "text-indigo-300 border-b-2 border-indigo-400 bg-white/5"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}
          >
            {t.label} ({t.data.results.length})
          </button>
        ))}
      </div>
      {/* 記事リスト */}
      <div className="max-h-80 overflow-y-auto p-4 space-y-2">
        {current?.data.results.map((r, i) => {
          const emoji = r.label === "positive" ? "🟢" : r.label === "negative" ? "🔴" : "⚪";
          return (
            <div key={i} className="flex items-start gap-2 text-sm">
              <span>{emoji}</span>
              <div className="min-w-0 flex-1">
                <a
                  href={r.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--text-primary)] hover:text-indigo-300 transition-colors line-clamp-1"
                >
                  {r.title}
                </a>
                <span className="text-xs text-[var(--text-secondary)] ml-2">
                  {r.author && `${r.author} · `}pos:{(r.positive * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
