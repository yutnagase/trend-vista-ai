"""依存性注入用のProtocolインターフェース定義."""

from typing import Any, Protocol

from app.domain.models import AnalysisResult, Article


class SentimentAnalyzerProtocol(Protocol):
    """感情分析器のインターフェース."""

    def analyze(self, text: str) -> dict[str, float | str]: ...

    def analyze_batch(self, texts: list[str]) -> list[dict[str, float | str]]: ...


class DataCollectorProtocol(Protocol):
    """データ収集のインターフェース."""

    def collect(
        self, keyword: str
    ) -> tuple[list[Article], list[Article], list[Article], list[dict[str, Any]]]: ...


class ReportGeneratorProtocol(Protocol):
    """AI総評レポート生成のインターフェース."""

    def generate(self, result: AnalysisResult) -> str: ...


class HistoryRepositoryProtocol(Protocol):
    """履歴永続化のインターフェース."""

    def save(self, result: AnalysisResult) -> None: ...

    def load_all(self) -> list[dict[str, Any]]: ...

    def load_by_id(self, analysis_id: str) -> dict[str, Any] | None: ...
