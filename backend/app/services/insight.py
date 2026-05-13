"""インサイト生成サービス - ルールベースのギャップ検出."""


def _divergence_label(gap: float) -> str:
    if gap > 0.5:
        return "構造的乖離"
    elif gap > 0.3:
        return "明確な意見差"
    elif gap > 0.2:
        return "やや差あり"
    return "大差なし"


def compute_divergences(scores: dict[str, float]) -> list[tuple[str, str, float, str]]:
    """全ソースペアの乖離を計算し、乖離幅降順で返す."""
    keys = list(scores.keys())
    pairs = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            gap = abs(scores[keys[i]] - scores[keys[j]])
            pairs.append((keys[i], keys[j], round(gap, 2), _divergence_label(gap)))
    return sorted(pairs, key=lambda x: x[2], reverse=True)
