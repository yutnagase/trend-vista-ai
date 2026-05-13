/** トピック別感情チャート */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { TopicSentiment } from "../types";

interface TopicChartProps {
  topics: TopicSentiment[];
  title: string;
}

export function TopicChart({ topics, title }: TopicChartProps) {
  if (!topics.length) return null;

  const data = topics.slice(0, 10).map((t) => ({
    name: t.topic,
    score: t.net_score,
    count: t.count,
  }));

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium text-gray-600">{title}</h4>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ left: 60 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" domain={[-1, 1]} />
          <YAxis type="category" dataKey="name" width={50} />
          <Tooltip />
          <ReferenceLine x={0} stroke="#666" />
          <Bar
            dataKey="score"
            fill="#6366f1"
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
