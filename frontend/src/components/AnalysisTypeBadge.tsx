/** 分析タイプバッジ */

import type { AnalysisType } from "../types";

interface AnalysisTypeBadgeProps {
  types: AnalysisType[];
}

export function AnalysisTypeBadge({ types }: AnalysisTypeBadgeProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {types.map((t) => (
        <span
          key={t.type}
          className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-sm"
          title={t.reason}
        >
          <span>{t.emoji}</span>
          <span>{t.label}</span>
        </span>
      ))}
    </div>
  );
}
