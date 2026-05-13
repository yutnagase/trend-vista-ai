"""依存注入 - FastAPI Depends用のファクトリ."""

from functools import lru_cache

from app.core.config import settings
from app.infrastructure.collectors import MultiSourceCollector
from app.infrastructure.history_repository import JsonHistoryRepository
from app.infrastructure.llm_reporter import LLMReportGenerator
from app.services.analyzer import SentimentAnalyzer


@lru_cache
def get_analyzer() -> SentimentAnalyzer:
    return SentimentAnalyzer()


@lru_cache
def get_collector() -> MultiSourceCollector:
    return MultiSourceCollector(
        bsky_handle=settings.bsky_handle,
        bsky_password=settings.bsky_password,
    )


@lru_cache
def get_report_generator() -> LLMReportGenerator:
    return LLMReportGenerator()


@lru_cache
def get_history_repository() -> JsonHistoryRepository:
    return JsonHistoryRepository()
