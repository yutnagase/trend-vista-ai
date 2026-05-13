"""トピック別感情分析サービス."""

from collections import defaultdict
from typing import Any


def compute_topic_sentiments(
    results: list[dict[str, Any]],
    keywords: list[tuple[str, int]],
    min_count: int = 2,
) -> list[dict[str, Any]]:
    """キーワードごとに感情スコアを集約する."""
    topic_scores: dict[str, dict[str, int]] = defaultdict(lambda: {"pos": 0, "neg": 0, "count": 0})
    target_words = [w for w, _ in keywords[:20]]

    for r in results:
        text = (r.get("title", "") + " " + (r.get("content") or "")).lower()
        label = r.get("label", "neutral")
        for word in target_words:
            if word.lower() in text:
                topic_scores[word]["count"] += 1
                if label == "positive":
                    topic_scores[word]["pos"] += 1
                elif label == "negative":
                    topic_scores[word]["neg"] += 1

    output = []
    for word, scores in topic_scores.items():
        if scores["count"] < min_count:
            continue
        total = scores["pos"] + scores["neg"]
        if total < 2:
            continue
        net = (scores["pos"] - scores["neg"]) / total
        output.append({"topic": word, "net_score": net, **scores})

    return sorted(output, key=lambda x: x["net_score"])
