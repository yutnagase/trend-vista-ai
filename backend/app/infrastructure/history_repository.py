"""履歴リポジトリ - JSON永続化."""

import json
from pathlib import Path
from typing import Any

import structlog

from app.domain.models import AnalysisResult

logger = structlog.get_logger(__name__)

HISTORY_PATH = Path("data/analysis_history.json")


class JsonHistoryRepository:
    """JSON履歴ファイルによる永続化."""

    def save(self, result: AnalysisResult) -> None:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        history = self._read_file()
        history.append(result.model_dump(mode="json"))
        HISTORY_PATH.write_text(
            json.dumps(history, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def load_all(self) -> list[dict[str, Any]]:
        history = self._read_file()
        return list(reversed(history))

    def load_by_id(self, analysis_id: str) -> dict[str, Any] | None:
        for entry in self._read_file():
            if entry.get("id") == analysis_id:
                return entry
        return None

    def _read_file(self) -> list[dict[str, Any]]:
        if not HISTORY_PATH.exists():
            return []
        return json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
