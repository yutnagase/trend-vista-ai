"""分析パイプライン - 感情分析から統計量算出までのオーケストレーション."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from app.domain.models import AnalysisResult, AnalyzedArticle, SourceAnalysis, SourceStats
from app.services.analysis_type import detect_analysis_types
from app.services.analyzer import compute_net_score, compute_sentiment_stats, select_representative
from app.services.insight import compute_divergences
from app.services.text_processor import create_tokenizer, extract_keywords, extract_media_names
from app.services.topic_sentiment import compute_topic_sentiments

if TYPE_CHECKING:
    from app.domain import SentimentAnalyzerProtocol
    from app.domain.models import Article

logger = structlog.get_logger(__name__)


def _build_source_analysis(
    results: list[AnalyzedArticle],
    titles: list[str],
    search_keyword: str,
    tokenizer: Any,
    extra_stop_words: set[str] | None = None,
) -> SourceAnalysis:
    if not results:
        return SourceAnalysis()

    results_dicts = [r.model_dump() for r in results]
    stats_dict = compute_sentiment_stats(results_dicts)
    keywords = extract_keywords(
        titles, search_keyword, tokenizer=tokenizer, extra_stop_words=extra_stop_words
    )
    samples = select_representative(results_dicts)

    return SourceAnalysis(
        results=results,
        stats=SourceStats(**stats_dict),
        keywords=keywords,
        samples=samples,
        net_score=compute_net_score(stats_dict),
    )


def run_analysis(
    keyword: str,
    news_articles: list[Article],
    sns_articles: list[Article],
    hatena_articles: list[Article],
    hatena_entry_data: list[dict[str, Any]],
    analyzer: SentimentAnalyzerProtocol,
) -> AnalysisResult:
    """分析パイプラインを実行し、構造化された結果を返す."""
    tokenizer = create_tokenizer()

    def analyze_articles(articles: list[Article]) -> list[AnalyzedArticle]:
        if not articles:
            return []
        texts = [a.title for a in articles]
        scores_list = analyzer.analyze_batch(texts)
        return [
            AnalyzedArticle(
                title=article.title,
                url=article.url,
                source=article.source,
                author=article.author,
                positive=float(scores["positive"]),
                negative=float(scores["negative"]),
                label=str(scores["label"]),
                metadata=article.metadata,
            )
            for article, scores in zip(articles, scores_list, strict=True)
        ]

    news_results = analyze_articles(news_articles)
    sns_results = analyze_articles(sns_articles)
    hatena_results = analyze_articles(hatena_articles)

    news_titles = [r.title for r in news_results]
    bsky_titles = [r.title for r in sns_results]
    hatena_texts = [r.title for r in hatena_results]

    news_media_names = extract_media_names(news_titles)

    news_analysis = _build_source_analysis(
        news_results, news_titles, keyword, tokenizer, extra_stop_words=news_media_names
    )
    bsky_analysis = _build_source_analysis(sns_results, bsky_titles, keyword, tokenizer)
    hatena_analysis = _build_source_analysis(hatena_results, hatena_texts, keyword, tokenizer)

    # トピック別感情分析
    all_topic_sentiments: dict[str, list[dict[str, Any]]] = {}
    for src_name, src_analysis in [
        ("メディア", news_analysis),
        ("BlueSky", bsky_analysis),
        ("はてブ", hatena_analysis),
    ]:
        if src_analysis.results and src_analysis.keywords:
            results_dicts = [r.model_dump() for r in src_analysis.results]
            topics = compute_topic_sentiments(results_dicts, src_analysis.keywords)
            all_topic_sentiments[src_name] = topics

    # 乖離検出
    net_scores: dict[str, float] = {"news": news_analysis.net_score}
    neutral_ratios: dict[str, float] = {}
    if news_analysis.stats:
        neutral_ratios["news"] = news_analysis.stats.neutral
    if bsky_analysis.stats:
        net_scores["bsky"] = bsky_analysis.net_score
        neutral_ratios["bsky"] = bsky_analysis.stats.neutral
    if hatena_analysis.stats:
        net_scores["hatena"] = hatena_analysis.net_score
        neutral_ratios["hatena"] = hatena_analysis.stats.neutral

    divergences = compute_divergences(net_scores) if len(net_scores) >= 2 else []

    # 分析タイプ判定
    combined_topics = [t for topics in all_topic_sentiments.values() for t in topics]
    max_div = divergences[0][2] if divergences else 0.0

    analysis_types = detect_analysis_types(
        net_scores=net_scores,
        max_divergence=max_div,
        topic_sentiments=combined_topics,
        neutral_ratios=neutral_ratios,
        sample_counts={
            "news": len(news_results),
            "bsky": len(sns_results),
            "hatena": len(hatena_results),
        },
    )

    return AnalysisResult(
        keyword=keyword,
        news=news_analysis,
        bsky=bsky_analysis,
        hatena=hatena_analysis,
        hatena_entry_data=hatena_entry_data,
        topic_sentiments=all_topic_sentiments,
        analysis_types=analysis_types,
        divergences=divergences,
    )
