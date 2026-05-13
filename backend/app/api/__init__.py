"""APIエンドポイント."""

from fastapi import APIRouter, Depends, HTTPException

from app.application import AnalyzeUseCase
from app.core.dependencies import (
    get_analyzer,
    get_collector,
    get_history_repository,
    get_report_generator,
)
from app.domain.exceptions import DataCollectionError, TrendVistaError
from app.infrastructure.history_repository import JsonHistoryRepository
from app.schemas import (
    AnalysisResponse,
    AnalyzeRequest,
    HistorySummaryResponse,
)

router = APIRouter(prefix="/api")


def _get_use_case(
    analyzer=Depends(get_analyzer),
    collector=Depends(get_collector),
    report_generator=Depends(get_report_generator),
    history=Depends(get_history_repository),
) -> AnalyzeUseCase:
    return AnalyzeUseCase(
        analyzer=analyzer,
        collector=collector,
        report_generator=report_generator,
        history=history,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    request: AnalyzeRequest,
    use_case: AnalyzeUseCase = Depends(_get_use_case),
) -> AnalysisResponse:
    """キーワードを受け取り、完全な分析結果を返す."""
    try:
        result = use_case.execute(request.keyword)
    except DataCollectionError as e:
        raise HTTPException(status_code=404, detail=e.user_message) from e
    except TrendVistaError as e:
        raise HTTPException(status_code=500, detail=e.user_message) from e

    return AnalysisResponse(
        id=result.id,
        keyword=result.keyword,
        timestamp=result.timestamp,
        news=result.news.model_dump(),  # type: ignore[arg-type]
        bsky=result.bsky.model_dump(),  # type: ignore[arg-type]
        hatena=result.hatena.model_dump(),  # type: ignore[arg-type]
        hatena_entry_data=result.hatena_entry_data,
        topic_sentiments=result.topic_sentiments,
        analysis_types=result.analysis_types,
        divergences=[list(d) for d in result.divergences],
        wordcloud_images=result.wordcloud_images,
        ai_report=result.ai_report,
    )


@router.get("/history", response_model=list[HistorySummaryResponse])
async def get_history(
    repo: JsonHistoryRepository = Depends(get_history_repository),
) -> list[HistorySummaryResponse]:
    """過去分析一覧を返す."""
    entries = repo.load_all()
    return [
        HistorySummaryResponse(
            id=e.get("id", ""),
            keyword=e.get("keyword", ""),
            timestamp=e.get("timestamp", ""),
            news_count=len(e.get("news", {}).get("results", [])),
            bsky_count=len(e.get("bsky", {}).get("results", [])),
            hatena_count=len(e.get("hatena", {}).get("results", [])),
        )
        for e in entries
    ]


@router.get("/history/{analysis_id}", response_model=AnalysisResponse)
async def get_history_detail(
    analysis_id: str,
    repo: JsonHistoryRepository = Depends(get_history_repository),
) -> AnalysisResponse:
    """個別分析結果を返す."""
    entry = repo.load_by_id(analysis_id)
    if not entry:
        raise HTTPException(status_code=404, detail="分析結果が見つかりません")
    return AnalysisResponse(**entry)
