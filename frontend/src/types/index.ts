/** API型定義 */

export interface SourceStats {
  positive: number;
  neutral: number;
  negative: number;
}

export interface AnalyzedArticle {
  title: string;
  url: string;
  source: string;
  author: string | null;
  positive: number;
  negative: number;
  label: string;
}

export interface SourceAnalysis {
  results: AnalyzedArticle[];
  stats: SourceStats | null;
  keywords: [string, number][];
  samples: Record<string, string[]>;
  net_score: number;
}

export interface AnalysisType {
  type: string;
  emoji: string;
  label: string;
  reason: string;
}

export interface AnalysisResponse {
  id: string;
  keyword: string;
  timestamp: string;
  news: SourceAnalysis;
  bsky: SourceAnalysis;
  hatena: SourceAnalysis;
  hatena_entry_data: Record<string, unknown>[];
  topic_sentiments: Record<string, TopicSentiment[]>;
  analysis_types: AnalysisType[];
  divergences: [string, string, number, string][];
  wordcloud_images: Record<string, string>;
  ai_report: string;
}

export interface TopicSentiment {
  topic: string;
  net_score: number;
  pos: number;
  neg: number;
  count: number;
}

export interface HistorySummary {
  id: string;
  keyword: string;
  timestamp: string;
  news_count: number;
  bsky_count: number;
  hatena_count: number;
}
