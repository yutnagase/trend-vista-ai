"""アプリケーション例外定義."""


class TrendVistaError(Exception):
    """アプリケーション基底例外."""

    user_message: str = "予期しないエラーが発生しました。"

    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(detail or self.user_message)


class DataCollectionError(TrendVistaError):
    user_message = "データの収集中にエラーが発生しました。"


class AnalysisPipelineError(TrendVistaError):
    user_message = "感情分析の処理中にエラーが発生しました。"


class ReportGenerationError(TrendVistaError):
    user_message = "AI総評レポートの生成に失敗しました。"


class HistoryError(TrendVistaError):
    user_message = "履歴操作に失敗しました。"
