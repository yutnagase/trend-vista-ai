/** 温度計UI - Net Sentiment Scoreの視覚化 */

import { cn } from "../lib/utils";

interface SentimentGaugeProps {
  score: number; // -1.0 ~ +1.0
  label: string;
}

export function SentimentGauge({ score, label }: SentimentGaugeProps) {
  const percentage = ((score + 1) / 2) * 100;
  const color =
    score > 0.1 ? "bg-green-500" : score < -0.1 ? "bg-red-500" : "bg-gray-400";

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-mono">{score >= 0 ? "+" : ""}{score.toFixed(2)}</span>
      </div>
      <div className="h-3 w-full rounded-full bg-gray-200">
        <div
          className={cn("h-full rounded-full transition-all", color)}
          style={{ width: `${Math.max(percentage, 5)}%` }}
        />
      </div>
    </div>
  );
}
