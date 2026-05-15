"""サービス層のユニットテスト."""

from app.services.analysis_type import detect_analysis_types
from app.services.analyzer import compute_net_score, compute_sentiment_stats, select_representative
from app.services.insight import compute_divergences
from app.services.text_processor import extract_keywords, extract_media_names
from app.services.topic_sentiment import compute_topic_sentiments


class TestComputeSentimentStats:
    def test_empty(self):
        assert compute_sentiment_stats([]) == {"positive": 0.0, "neutral": 0.0, "negative": 0.0}

    def test_mixed(self):
        results = [
            {"label": "positive"},
            {"label": "negative"},
            {"label": "neutral"},
            {"label": "neutral"},
        ]
        stats = compute_sentiment_stats(results)
        assert stats["positive"] == 0.25
        assert stats["negative"] == 0.25
        assert stats["neutral"] == 0.5


class TestComputeNetScore:
    def test_basic(self):
        assert abs(compute_net_score({"positive": 0.6, "negative": 0.2, "neutral": 0.2}) - 0.4) < 1e-9


class TestSelectRepresentative:
    def test_empty(self):
        assert select_representative([]) == {"positive": [], "negative": []}

    def test_selection(self):
        results = [
            {"title": "good news", "label": "positive", "positive": 0.9, "negative": 0.1},
            {"title": "bad news", "label": "negative", "positive": 0.1, "negative": 0.8},
            {"title": "great news", "label": "positive", "positive": 0.95, "negative": 0.05},
        ]
        samples = select_representative(results)
        assert samples["positive"] == ["great news"]
        assert samples["negative"] == ["bad news"]


class TestComputeDivergences:
    def test_two_sources(self):
        scores = {"news": 0.5, "bsky": -0.3}
        result = compute_divergences(scores)
        assert len(result) == 1
        assert result[0][0] == "news"
        assert result[0][1] == "bsky"
        assert result[0][2] == 0.8
        assert result[0][3] == "構造的乖離"

    def test_three_sources(self):
        scores = {"news": 0.1, "bsky": 0.15, "hatena": 0.12}
        result = compute_divergences(scores)
        assert len(result) == 3
        assert all(r[3] == "大差なし" for r in result)

    def test_labels(self):
        assert compute_divergences({"a": 0.0, "b": 0.25})[0][3] == "やや差あり"
        assert compute_divergences({"a": 0.0, "b": 0.4})[0][3] == "明確な意見差"


class TestDetectAnalysisTypes:
    def test_structural_divergence(self):
        types = detect_analysis_types(
            net_scores={"news": 0.5, "bsky": -0.3},
            max_divergence=0.8,
            topic_sentiments=[],
            neutral_ratios={"news": 0.3, "bsky": 0.4},
            sample_counts={"news": 10, "bsky": 10},
        )
        assert types[0]["type"] == "structural_divergence"

    def test_neutral_dominant(self):
        types = detect_analysis_types(
            net_scores={"news": 0.0, "bsky": 0.0},
            max_divergence=0.0,
            topic_sentiments=[],
            neutral_ratios={"news": 0.8, "bsky": 0.7},
            sample_counts={"news": 10, "bsky": 10},
        )
        assert any(t["type"] == "neutral_dominant" for t in types)

    def test_consensus_positive(self):
        types = detect_analysis_types(
            net_scores={"news": 0.3, "bsky": 0.25},
            max_divergence=0.05,
            topic_sentiments=[],
            neutral_ratios={"news": 0.3, "bsky": 0.3},
            sample_counts={"news": 10, "bsky": 10},
        )
        assert any(t["type"] == "consensus" for t in types)

    def test_mixed_fallback(self):
        types = detect_analysis_types(
            net_scores={"news": 0.1, "bsky": -0.05},
            max_divergence=0.15,
            topic_sentiments=[],
            neutral_ratios={"news": 0.4, "bsky": 0.5},
            sample_counts={"news": 10, "bsky": 10},
        )
        assert types[0]["type"] == "mixed"

    def test_topic_concentrated_neg(self):
        topics = [
            {"topic": "A", "net_score": -0.8, "count": 10},
            {"topic": "B", "net_score": 0.2, "count": 10},
            {"topic": "C", "net_score": 0.3, "count": 10},
            {"topic": "D", "net_score": 0.25, "count": 10},
        ]
        types = detect_analysis_types(
            net_scores={"news": 0.0},
            max_divergence=0.0,
            topic_sentiments=topics,
            neutral_ratios={"news": 0.5},
            sample_counts={"news": 10},
        )
        assert any(t["type"] == "topic_concentrated_neg" for t in types)

    def test_topic_concentrated_pos(self):
        topics = [
            {"topic": "A", "net_score": 0.9, "count": 10},
            {"topic": "B", "net_score": -0.2, "count": 10},
            {"topic": "C", "net_score": -0.1, "count": 10},
            {"topic": "D", "net_score": -0.15, "count": 10},
        ]
        types = detect_analysis_types(
            net_scores={"news": 0.0},
            max_divergence=0.0,
            topic_sentiments=topics,
            neutral_ratios={"news": 0.5},
            sample_counts={"news": 10},
        )
        assert any(t["type"] == "topic_concentrated_pos" for t in types)

    def test_low_sample_filtered(self):
        types = detect_analysis_types(
            net_scores={"news": 0.5, "bsky": -0.3},
            max_divergence=0.8,
            topic_sentiments=[],
            neutral_ratios={"news": 0.3, "bsky": 0.4},
            sample_counts={"news": 10, "bsky": 2},
        )
        # bsky filtered out due to low sample, only 1 reliable source -> no structural divergence
        assert types[0]["type"] == "mixed"


class TestTopicSentiment:
    def test_basic(self):
        results = [
            {"title": "Python最高", "content": "", "label": "positive"},
            {"title": "Pythonは難しい", "content": "", "label": "negative"},
            {"title": "Pythonを学ぶ", "content": "", "label": "positive"},
            {"title": "Javaは古い", "content": "", "label": "negative"},
            {"title": "Javaで開発", "content": "", "label": "negative"},
        ]
        keywords = [("python", 3), ("java", 2)]
        topics = compute_topic_sentiments(results, keywords, min_count=2)
        python_topic = next(t for t in topics if t["topic"] == "python")
        assert python_topic["net_score"] > 0

    def test_min_count_filter(self):
        results = [{"title": "Rust入門", "content": "", "label": "positive"}]
        keywords = [("rust", 1)]
        topics = compute_topic_sentiments(results, keywords, min_count=3)
        assert topics == []


class TestTextProcessor:
    def test_extract_media_names(self):
        titles = ["大谷翔平が活躍 - NHKニュース", "経済回復 - 日本経済新聞"]
        names = extract_media_names(titles)
        assert "NHKニュース" in names
        assert "日本経済新聞" in names

    def test_extract_keywords(self):
        titles = ["東京オリンピック開催", "東京の天気予報"]
        keywords = extract_keywords(titles, "テスト")
        words = [w for w, _ in keywords]
        assert "東京" in words

    def test_search_keyword_excluded(self):
        titles = ["AI技術の進化", "AI活用事例"]
        keywords = extract_keywords(titles, "AI")
        words = [w for w, _ in keywords]
        assert "AI" not in words
