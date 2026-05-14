"""APIリクエスト/レスポンススキーマ."""

from typing import Any

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """分析リクエスト."""

    keyword: str = Field(min_length=1, max_length=100)


class SourceStatsResponse(BaseModel):
    positive: float
    neutral: float
    negative: float


class AnalyzedArticleResponse(BaseModel):
    title: str
    url: str
    source: str
    author: str | None = None
    positive: float
    negative: float
    label: str


class SourceAnalysisResponse(BaseModel):
    results: list[AnalyzedArticleResponse] = []
    stats: SourceStatsResponse | None = None
    keywords: list[list[Any]] = []  # [[word, count], ...]
    samples: dict[str, list[str]] = {}
    net_score: float = 0.0


class AnalysisResponse(BaseModel):
    """分析結果レスポンス."""

    id: str
    keyword: str
    timestamp: str
    news: SourceAnalysisResponse
    bsky: SourceAnalysisResponse
    hatena: SourceAnalysisResponse
    hatena_entry_data: list[dict[str, str | int]] = []
    topic_sentiments: dict[str, list[dict[str, Any]]] = {}
    analysis_types: list[dict[str, str]] = []
    divergences: list[list[Any]] = []  # [[srcA, srcB, gap, label], ...]
    wordcloud_images: dict[str, str] = {}
    ai_report: str = ""


class HistorySummaryResponse(BaseModel):
    """履歴一覧の1件."""

    id: str
    keyword: str
    timestamp: str
    news_count: int = 0
    bsky_count: int = 0
    hatena_count: int = 0


class ErrorResponse(BaseModel):
    detail: str
