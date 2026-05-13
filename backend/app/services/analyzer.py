"""感情分析モジュール - 複数BERTモデルのアンサンブルによる感情スコアリング."""

from typing import Any

import structlog
import torch
from torch.nn.functional import softmax
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = structlog.get_logger(__name__)

ENSEMBLE_MODELS: list[dict[str, str | float]] = [
    {"name": "koheiduck/bert-japanese-finetuned-sentiment", "weight": 0.334},
    {"name": "christian-phu/bert-finetuned-japanese-sentiment", "weight": 0.333},
    {"name": "llm-book/bert-base-japanese-v3-marc-ja", "weight": 0.333},
]

BATCH_SIZE = 16


class _ModelUnit:
    """単一モデルのロード・推論を担当する内部クラス."""

    def __init__(self, model_name: str, weight: float) -> None:
        self.model_name = model_name
        self.weight = weight
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        self.id2label: dict[int, str] = self.model.config.id2label
        self._label_map = self._build_label_map()

    def _build_label_map(self) -> dict[str, int]:
        label_map: dict[str, int] = {}
        for idx, label in self.id2label.items():
            normalized = label.upper().replace("LABEL_", "")
            if normalized in ("POSITIVE", "2", "POS"):
                label_map["positive"] = int(idx)
            elif normalized in ("NEGATIVE", "0", "NEG"):
                label_map["negative"] = int(idx)
            elif normalized in ("NEUTRAL", "1", "NEU"):
                label_map["neutral"] = int(idx)
        if "neutral" not in label_map:
            label_map["neutral"] = -1
        return label_map

    @torch.no_grad()
    def predict_batch(self, texts: list[str]) -> list[dict[str, float]]:
        encoded = self.tokenizer(
            texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
        )
        logits = self.model(**encoded).logits
        probs = softmax(logits, dim=-1)

        results = []
        for prob in probs:
            pos_idx = self._label_map.get("positive")
            neg_idx = self._label_map.get("negative")
            neu_idx = self._label_map.get("neutral")

            pos_score = prob[pos_idx].item() if pos_idx is not None and pos_idx >= 0 else 0.0
            neg_score = prob[neg_idx].item() if neg_idx is not None and neg_idx >= 0 else 0.0
            neu_score = prob[neu_idx].item() if neu_idx is not None and neu_idx >= 0 else 0.0

            if self._label_map.get("neutral", -1) == -1:
                neu_score = max(1.0 - pos_score - neg_score, 0.0)

            results.append({"positive": pos_score, "negative": neg_score, "neutral": neu_score})
        return results


class SentimentAnalyzer:
    """複数BERTモデルのアンサンブルによる感情分析クラス."""

    def __init__(self, models_config: list[dict[str, str | float]] | None = None) -> None:
        config = models_config or ENSEMBLE_MODELS
        logger.info("アンサンブルモデルをロード中", model_count=len(config))
        self._units: list[_ModelUnit] = []
        for cfg in config:
            try:
                unit = _ModelUnit(str(cfg["name"]), float(cfg["weight"]))
                self._units.append(unit)
            except Exception as e:
                logger.warning("モデルロード失敗", model=cfg["name"], error=str(e))
        if not self._units:
            raise RuntimeError("有効なモデルが1つもロードできませんでした")
        total_weight = sum(u.weight for u in self._units)
        for u in self._units:
            u.weight = u.weight / total_weight

    def analyze(self, text: str) -> dict[str, float | str]:
        return self.analyze_batch([text])[0]

    def analyze_batch(self, texts: list[str]) -> list[dict[str, float | str]]:
        if not texts:
            return []

        all_model_results: list[list[dict[str, float]]] = []
        for unit in self._units:
            model_results = []
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i : i + BATCH_SIZE]
                model_results.extend(unit.predict_batch(batch))
            all_model_results.append(model_results)

        final_results = []
        for idx in range(len(texts)):
            pos = sum(
                all_model_results[m][idx]["positive"] * self._units[m].weight
                for m in range(len(self._units))
            )
            neg = sum(
                all_model_results[m][idx]["negative"] * self._units[m].weight
                for m in range(len(self._units))
            )

            if abs(pos - neg) < 0.1:
                final_label = "neutral"
            elif pos > neg:
                final_label = "positive"
            else:
                final_label = "negative"

            final_results.append({"positive": pos, "negative": neg, "label": final_label})
        return final_results


def compute_sentiment_stats(results: list[dict[str, Any]]) -> dict[str, float]:
    total = len(results)
    if total == 0:
        return {"positive": 0.0, "neutral": 0.0, "negative": 0.0}
    pos_count = sum(1 for r in results if r["label"] == "positive")
    neg_count = sum(1 for r in results if r["label"] == "negative")
    neu_count = total - pos_count - neg_count
    return {
        "positive": pos_count / total,
        "neutral": neu_count / total,
        "negative": neg_count / total,
    }


def compute_net_score(stats: dict[str, float]) -> float:
    return stats["positive"] - stats["negative"]


def select_representative(results: list[dict[str, Any]], top_n: int = 1) -> dict[str, list[str]]:
    if not results:
        return {"positive": [], "negative": []}
    pos_items = [r for r in results if r["label"] == "positive"]
    neg_items = [r for r in results if r["label"] == "negative"]
    pos_sorted = sorted(pos_items, key=lambda r: r["positive"], reverse=True)
    neg_sorted = sorted(neg_items, key=lambda r: r["negative"], reverse=True)
    return {
        "positive": [r["title"][:80] for r in pos_sorted[:top_n]],
        "negative": [r["title"][:80] for r in neg_sorted[:top_n]],
    }
