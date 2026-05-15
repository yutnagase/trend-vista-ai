/** 温度計UI - Net Sentiment Scoreの視覚化（ドットプロット形式） */

interface SentimentGaugeProps {
  score: number; // -1.0 ~ +1.0
  label: string;
}

function getScoreColor(score: number): string {
  if (score >= 0.3) return "#22c55e";
  if (score >= 0.1) return "#86efac";
  if (score > -0.1) return "#9ca3af";
  if (score > -0.3) return "#f97316";
  return "#ef4444";
}

function getScoreLabel(score: number): string {
  if (score >= 0.3) return "ポジティブ優勢";
  if (score >= 0.1) return "ややポジ寄り";
  if (score > -0.1) return "中立的";
  if (score > -0.3) return "やや懸念寄り";
  return "ネガティブ優勢";
}

export function SentimentGauge({ score, label }: SentimentGaugeProps) {
  const position = ((score + 1) / 2) * 100;
  const color = getScoreColor(score);

  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-medium text-[var(--text-primary)]">{label}</span>
        <div className="text-right">
          <span className="font-mono text-lg font-bold" style={{ color }}>
            {score >= 0 ? "+" : ""}{score.toFixed(2)}
          </span>
          <p className="text-[10px] mt-0.5" style={{ color }}>
            {getScoreLabel(score)}
          </p>
        </div>
      </div>
      {/* トラック */}
      <div className="relative h-3 w-full rounded-full bg-gray-700/50">
        {/* 中央線 */}
        <div className="absolute left-1/2 top-0 h-full w-px bg-gray-600" />
        {/* ネガティブ領域（薄い赤） */}
        <div className="absolute left-0 top-0 h-full w-1/2 rounded-l-full bg-red-900/20" />
        {/* ポジティブ領域（薄い緑） */}
        <div className="absolute right-0 top-0 h-full w-1/2 rounded-r-full bg-green-900/20" />
        {/* ドット */}
        <div
          className="absolute top-1/2 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-lg transition-all duration-500"
          style={{
            left: `${position}%`,
            backgroundColor: color,
            boxShadow: `0 0 12px ${color}80`,
          }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-[var(--text-muted)]">
        <span>-1.0</span>
        <span>0</span>
        <span>+1.0</span>
      </div>
    </div>
  );
}
