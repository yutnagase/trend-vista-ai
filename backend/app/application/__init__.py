"""分析ユースケース - UIフレームワーク非依存のオーケストレーター."""

import uuid
from datetime import datetime

import structlog

from app.domain import (
    DataCollectorProtocol,
    HistoryRepositoryProtocol,
    ReportGeneratorProtocol,
    SentimentAnalyzerProtocol,
)
from app.domain.exceptions import AnalysisPipelineError, DataCollectionError
from app.domain.models import AnalysisResult
from app.services.analysis_pipeline import run_analysis

logger = structlog.get_logger(__name__)


class AnalyzeUseCase:
    """分析フロー全体を実行するユースケース."""

    def __init__(
        self,
        analyzer: SentimentAnalyzerProtocol,
        collector: DataCollectorProtocol,
        report_generator: ReportGeneratorProtocol,
        history: HistoryRepositoryProtocol,
    ) -> None:
        self._analyzer = analyzer
        self._collector = collector
        self._report_generator = report_generator
        self._history = history

    def execute(self, keyword: str) -> AnalysisResult:
        """分析を実行し結果を返す."""
        log = logger.bind(keyword=keyword)
        log.info("分析開始")

        # データ収集
        try:
            news, sns, hatena, hatena_entries = self._collector.collect(keyword)
        except Exception as e:
            raise DataCollectionError(str(e)) from e

        if not news and not sns and not hatena:
            raise DataCollectionError("記事・投稿が見つかりませんでした。")

        # 感情分析パイプライン
        try:
            result = run_analysis(
                keyword=keyword,
                news_articles=news,
                sns_articles=sns,
                hatena_articles=hatena,
                hatena_entry_data=hatena_entries,
                analyzer=self._analyzer,
            )
        except Exception as e:
            raise AnalysisPipelineError(str(e)) from e

        # メタデータ付与
        result.id = str(uuid.uuid4())
        result.timestamp = datetime.now().isoformat()

        # AI総評生成は別途実行（レスポンス高速化のためここではスキップ）

        # 履歴保存
        try:
            self._history.save(result)
        except Exception as e:
            log.warning("履歴保存失敗", error=str(e))

        log.info("分析完了", id=result.id)
        return result
