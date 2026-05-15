/** トピック別感情チャート — スコアに応じた色分け */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import type { TopicSentiment } from "../types";

interface TopicChartProps {
  topics: TopicSentiment[];
  title: string;
}

function getBarColor(score: number): string {
  if (score >= 0.3) return "#22c55e";
  if (score >= 0.1) return "#86efac";
  if (score > -0.1) return "#6b7280";
  if (score > -0.3) return "#f97316";
  return "#ef4444";
}

export function TopicChart({ topics, title }: TopicChartProps) {
  if (!topics.length) return null;

  const data = topics.slice(0, 8).map((t) => ({
    name: t.topic,
    score: t.net_score,
    count: t.count,
  }));

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium text-[var(--text-secondary)]">{title}</h4>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ left: 70, right: 20 }}>
          <XAxis
            type="number"
            domain={[-1, 1]}
            tick={{ fill: "#a0a3b1", fontSize: 11 }}
            axisLine={{ stroke: "#3a3d4e" }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={60}
            tick={{ fill: "#ededf0", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--bg-elevated)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              color: "var(--text-primary)",
            }}
            formatter={(value: number) => [value.toFixed(2), "スコア"]}
          />
          <ReferenceLine x={0} stroke="#4a4d5e" strokeDasharray="3 3" />
          <Bar dataKey="score" radius={[0, 4, 4, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={getBarColor(entry.score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
