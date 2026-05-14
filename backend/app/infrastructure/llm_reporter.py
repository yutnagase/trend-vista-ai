"""LLMレポート生成アダプター."""

import time
from pathlib import Path
from typing import Any

import structlog
from huggingface_hub import hf_hub_download
from llama_cpp import Llama

from app.core.config import settings
from app.domain.models import AnalysisResult

logger = structlog.get_logger(__name__)

MODEL_DIR = Path("models")
_llm_instance: Llama | None = None


def _get_llm() -> Llama:
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / settings.llm_model_file

    if not model_path.exists():
        logger.info("LLMモデルダウンロード開始")
        hf_hub_download(
            repo_id=settings.llm_model_repo,
            filename=settings.llm_model_file,
            local_dir=str(MODEL_DIR),
        )

    _llm_instance = Llama(
        model_path=str(model_path),
        n_ctx=settings.llm_n_ctx,
        n_threads=settings.llm_n_threads,
        n_gpu_layers=0,
        verbose=False,
    )
    return _llm_instance


def _build_prompt(result: AnalysisResult) -> str:
    """分析結果からLLMプロンプトを構築する."""

    def fmt_stats(stats: Any) -> str:
        if not stats:
            return "データなし"
        score = stats.positive - stats.negative
        return f"スコア {score:+.2f}（ポジ{stats.positive:.0%} / 中立{stats.neutral:.0%} / ネガ{stats.negative:.0%}）"

    def fmt_kw(kws: list[tuple[str, int]]) -> str:
        return "、".join(w for w, _ in kws[:5])

    sections = []
    sections.append(f"■ メディア（{len(result.news.results)}件）")
    sections.append(f"  感情: {fmt_stats(result.news.stats)}")
    if result.news.keywords:
        sections.append(f"  頻出語: {fmt_kw(result.news.keywords)}")

    if result.bsky.stats:
        sections.append(f"■ SNS（BlueSky {len(result.bsky.results)}件）")
        sections.append(f"  感情: {fmt_stats(result.bsky.stats)}")
        if result.bsky.keywords:
            sections.append(f"  頻出語: {fmt_kw(result.bsky.keywords)}")

    if result.hatena.stats:
        sections.append(f"■ はてなブックマーク（{len(result.hatena.results)}件）")
        sections.append(f"  感情: {fmt_stats(result.hatena.stats)}")
        if result.hatena.keywords:
            sections.append(f"  頻出語: {fmt_kw(result.hatena.keywords)}")

    data_section = "\n".join(sections)

    # 分析タイプ
    type_text = ""
    if result.analysis_types:
        type_labels = [
            f"{at['emoji']} {at['label']}（{at['reason']}）" for at in result.analysis_types
        ]
        type_text = "\n■ 分析タイプ\n  " + "\n  ".join(type_labels)

    return f"""以下は「{result.keyword}」に関する複数ソースの感情分析データです。

{data_section}
{type_text}

上記データに基づき、総合インサイトを日本語で作成してください。

■ 総合インサイト
① 概要（乖離の有無と程度）
② 数値根拠（スコアと乖離幅）
③ トピック分析（どの話題がポジ／ネガに寄与しているか）
④ 結論（このトピックの空気感）

■ 総合インサイト
①"""


class LLMReportGenerator:
    """LLMベースのレポート生成."""

    def generate(self, result: AnalysisResult) -> str:
        llm = _get_llm()
        prompt = _build_prompt(result)

        start = time.perf_counter()
        output: dict[str, Any] = llm(
            prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.9,
            stop=["\n\n\n", "---", "以上"],
        )  # type: ignore[assignment]
        elapsed = time.perf_counter() - start

        generated: str = output["choices"][0]["text"].strip()
        logger.info("LLM推論完了", elapsed_sec=round(elapsed, 2))

        text = f"① {generated}" if not generated.startswith("①") else generated
        for marker in ["②", "③", "④"]:
            text = text.replace(marker, f"\n\n{marker}")
        return text
