/** 分析タイプバッジ + 根拠表示 + 凡例 */

import type { AnalysisType } from "../types";

interface AnalysisTypeBadgeProps {
  types: AnalysisType[];
}

const TYPE_DESCRIPTIONS: Record<string, string> = {
  structural_divergence: "ソース間で評価の方向が真逆になっている状態",
  topic_concentrated_neg: "特定トピックにネガティブ感情が集中している状態",
  topic_concentrated_pos: "特定トピックにポジティブ感情が集中している状態",
  neutral_dominant: "全ソースで中立的な記事・投稿が大半を占める状態",
  consensus: "全ソースが同じ感情方向で一致している状態",
  mixed: "明確な単一パターンに分類されない複合的な状態",
};

export function AnalysisTypeBadge({ types }: AnalysisTypeBadgeProps) {
  return (
    <div className="space-y-3">
      {types.map((t) => (
        <div
          key={t.type}
          className="rounded-lg bg-white/5 border border-white/10 px-4 py-3"
        >
          <div className="flex items-center gap-2">
            <span className="text-base">{t.emoji}</span>
            <span className="text-sm font-semibold text-[var(--text-primary)]">
              {t.label}
            </span>
          </div>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {t.reason}
          </p>
        </div>
      ))}

      {/* 凡例 */}
      <details className="mt-2">
        <summary className="text-xs text-[var(--text-muted)] cursor-pointer hover:text-[var(--text-secondary)] transition-colors">
          分析タイプの凡例を表示
        </summary>
        <div className="mt-2 rounded-lg bg-white/[0.03] border border-white/5 p-3 space-y-2">
          {Object.entries(TYPE_DESCRIPTIONS).map(([type, desc]) => {
            const emoji = { structural_divergence: "🔥", topic_concentrated_neg: "⚡", topic_concentrated_pos: "🌟", neutral_dominant: "⚪", consensus: "🤝", mixed: "🔀" }[type] || "❓";
            const label = { structural_divergence: "構造的乖離", topic_concentrated_neg: "トピック集中型ネガティブ", topic_concentrated_pos: "トピック集中型ポジティブ", neutral_dominant: "中立支配", consensus: "感情一致", mixed: "混在型" }[type] || type;
            return (
              <div key={type} className="flex items-start gap-2 text-xs">
                <span>{emoji}</span>
                <div>
                  <span className="font-medium text-[var(--text-secondary)]">{label}</span>
                  <span className="text-[var(--text-muted)]"> — {desc}</span>
                </div>
              </div>
            );
          })}
        </div>
      </details>
    </div>
  );
}
