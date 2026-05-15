"""分析パイプラインのテスト."""

from unittest.mock import MagicMock

from app.domain.models import Article
from app.services.analysis_pipeline import run_analysis


class TestRunAnalysis:
    def _mock_analyzer(self, *call_results):
        """各呼び出しごとに返す結果を指定する."""
        analyzer = MagicMock()
        analyzer.analyze_batch.side_effect = list(call_results)
        return analyzer

    def test_basic_pipeline(self):
        news = [
            Article(title="経済成長が加速", url="http://a.com/1", source="news"),
            Article(title="株価が下落", url="http://a.com/2", source="news"),
        ]
        sns = [
            Article(title="景気良くなってきた", url="http://b.com/1", source="bluesky"),
        ]
        hatena = [
            Article(title="経済政策に疑問", url="http://c.com/1", source="hatena"),
        ]

        analyzer = self._mock_analyzer(
            # news (2件)
            [
                {"positive": 0.8, "negative": 0.1, "label": "positive"},
                {"positive": 0.1, "negative": 0.8, "label": "negative"},
            ],
            # sns (1件)
            [{"positive": 0.7, "negative": 0.2, "label": "positive"}],
            # hatena (1件)
            [{"positive": 0.2, "negative": 0.6, "label": "negative"}],
        )

        result = run_analysis(
            keyword="経済",
            news_articles=news,
            sns_articles=sns,
            hatena_articles=hatena,
            hatena_entry_data=[],
            analyzer=analyzer,
        )

        assert result.keyword == "経済"
        assert len(result.news.results) == 2
        assert len(result.bsky.results) == 1
        assert len(result.hatena.results) == 1
        assert result.news.stats is not None
        assert len(result.divergences) > 0
        assert len(result.analysis_types) > 0

    def test_empty_sources(self):
        news = [
            Article(title="テスト記事", url="http://a.com/1", source="news"),
        ]
        analyzer = self._mock_analyzer(
            [{"positive": 0.5, "negative": 0.3, "label": "neutral"}],
        )

        result = run_analysis(
            keyword="テスト",
            news_articles=news,
            sns_articles=[],
            hatena_articles=[],
            hatena_entry_data=[],
            analyzer=analyzer,
        )

        assert len(result.bsky.results) == 0
        assert result.bsky.stats is None
        assert result.divergences == []

    def test_all_sources_with_topic_sentiments(self):
        news = [
            Article(title="AI技術が進化している", url="http://a.com/1", source="news"),
            Article(title="AI活用で効率化", url="http://a.com/2", source="news"),
            Article(title="AI規制の議論", url="http://a.com/3", source="news"),
        ]
        analyzer = self._mock_analyzer(
            [
                {"positive": 0.8, "negative": 0.1, "label": "positive"},
                {"positive": 0.7, "negative": 0.2, "label": "positive"},
                {"positive": 0.2, "negative": 0.6, "label": "negative"},
            ],
        )

        result = run_analysis(
            keyword="テスト",
            news_articles=news,
            sns_articles=[],
            hatena_articles=[],
            hatena_entry_data=[],
            analyzer=analyzer,
        )

        assert result.news.keywords is not None
