"""分析タイプ判定サービス - ルールベースのパターン分類."""

from typing import Any

MIN_SAMPLE_COUNT = 5


def detect_analysis_types(
    net_scores: dict[str, float],
    max_divergence: float,
    topic_sentiments: list[dict[str, Any]],
    neutral_ratios: dict[str, float],
    sample_counts: dict[str, int] | None = None,
) -> list[dict[str, str]]:
    """分析結果から該当する分析タイプを判定する."""
    types: list[dict[str, str]] = []

    reliable_scores = net_scores
    if sample_counts:
        reliable_scores = {
            k: v for k, v in net_scores.items() if sample_counts.get(k, 0) >= MIN_SAMPLE_COUNT
        }

    reliable_max_div = 0.0
    if len(reliable_scores) >= 2:
        vals = list(reliable_scores.values())
        reliable_max_div = max(vals) - min(vals)

    # 構造的乖離
    if reliable_max_div > 0.5:
        has_pos = any(s > 0.1 for s in reliable_scores.values())
        has_neg = any(s < -0.1 for s in reliable_scores.values())
        if has_pos and has_neg:
            types.append(
                {
                    "type": "structural_divergence",
                    "emoji": "🔥",
                    "label": "構造的乖離",
                    "reason": f"最大乖離 {reliable_max_div:.2f}、ソース間で評価方向が逆転",
                }
            )

    # トピック集中型
    if len(topic_sentiments) >= 3:
        scores_list = [t["net_score"] for t in topic_sentiments]
        mean = sum(scores_list) / len(scores_list)
        variance = sum((s - mean) ** 2 for s in scores_list) / len(scores_list)
        std = variance**0.5

        if std > 0.1:
            neg_outliers = [
                t for t in topic_sentiments if t["net_score"] < mean - std and t["count"] >= 5
            ]
            pos_outliers = [
                t for t in topic_sentiments if t["net_score"] > mean + std and t["count"] >= 5
            ]
            if neg_outliers:
                types.append(
                    {
                        "type": "topic_concentrated_neg",
                        "emoji": "⚡",
                        "label": "トピック集中型ネガティブ",
                        "reason": f"「{neg_outliers[0]['topic']}」等がネガティブ文脈で多く出現",
                    }
                )
            if pos_outliers:
                types.append(
                    {
                        "type": "topic_concentrated_pos",
                        "emoji": "🌟",
                        "label": "トピック集中型ポジティブ",
                        "reason": f"「{pos_outliers[-1]['topic']}」等がポジティブ文脈で多く出現",
                    }
                )

    # 中立支配
    reliable_neutral = {
        k: v
        for k, v in neutral_ratios.items()
        if not sample_counts or sample_counts.get(k, 0) >= MIN_SAMPLE_COUNT
    }
    if reliable_neutral and all(r > 0.6 for r in reliable_neutral.values()):
        avg_neutral = sum(reliable_neutral.values()) / len(reliable_neutral)
        types.append(
            {
                "type": "neutral_dominant",
                "emoji": "⚪",
                "label": "中立支配",
                "reason": f"全ソースの中立率が60%超（平均{avg_neutral:.0%}）",
            }
        )

    # 感情一致
    if len(reliable_scores) >= 2 and reliable_max_div < 0.2:
        all_pos = all(s > 0.05 for s in reliable_scores.values())
        all_neg = all(s < -0.05 for s in reliable_scores.values())
        if all_pos or all_neg:
            direction = "ポジティブ" if all_pos else "ネガティブ"
            types.append(
                {
                    "type": "consensus",
                    "emoji": "🤝",
                    "label": "感情一致",
                    "reason": f"全ソースが{direction}方向で一致（乖離{reliable_max_div:.2f}）",
                }
            )

    if not types:
        types.append(
            {
                "type": "mixed",
                "emoji": "🔀",
                "label": "混在型",
                "reason": "明確な単一パターンに分類されない複合的な状態",
            }
        )

    return types
