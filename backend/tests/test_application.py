"""ユースケース層・インフラ層のテスト."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.application import AnalyzeUseCase
from app.domain.exceptions import DataCollectionError
from app.domain.models import AnalysisResult, Article
from app.infrastructure.history_repository import JsonHistoryRepository


class TestAnalyzeUseCase:
    def _make_use_case(self, *, articles=None, analyzer_results=None):
        analyzer = MagicMock()
        analyzer.analyze_batch.return_value = analyzer_results or [
            {"positive": 0.8, "negative": 0.1, "label": "positive"},
            {"positive": 0.2, "negative": 0.7, "label": "negative"},
        ]
        collector = MagicMock()
        news = articles or [
            Article(title="テスト記事1", url="http://example.com/1", source="news"),
            Article(title="テスト記事2", url="http://example.com/2", source="news"),
        ]
        collector.collect.return_value = (news, [], [], [])
        report_generator = MagicMock()
        history = MagicMock()
        uc = AnalyzeUseCase(
            analyzer=analyzer,
            collector=collector,
            report_generator=report_generator,
            history=history,
        )
        return uc, history

    def test_execute_success(self):
        uc, history = self._make_use_case()
        result = uc.execute("テスト")
        assert result.keyword == "テスト"
        assert result.id != ""
        history.save.assert_called_once()

    def test_execute_no_data(self):
        analyzer = MagicMock()
        collector = MagicMock()
        collector.collect.return_value = ([], [], [], [])
        uc = AnalyzeUseCase(
            analyzer=analyzer,
            collector=collector,
            report_generator=MagicMock(),
            history=MagicMock(),
        )
        with pytest.raises(DataCollectionError):
            uc.execute("テスト")

    def test_execute_collector_error(self):
        analyzer = MagicMock()
        collector = MagicMock()
        collector.collect.side_effect = RuntimeError("network error")
        uc = AnalyzeUseCase(
            analyzer=analyzer,
            collector=collector,
            report_generator=MagicMock(),
            history=MagicMock(),
        )
        with pytest.raises(DataCollectionError):
            uc.execute("テスト")

    def test_history_save_failure_does_not_raise(self):
        uc, history = self._make_use_case()
        history.save.side_effect = RuntimeError("disk full")
        result = uc.execute("テスト")
        assert result.keyword == "テスト"


class TestJsonHistoryRepository:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "history.json"
        with patch("app.infrastructure.history_repository.HISTORY_PATH", path):
            repo = JsonHistoryRepository()
            result = AnalysisResult(keyword="テスト", id="test-id-1", timestamp="2024-01-01")
            repo.save(result)

            all_entries = repo.load_all()
            assert len(all_entries) == 1
            assert all_entries[0]["keyword"] == "テスト"

    def test_load_by_id(self, tmp_path):
        path = tmp_path / "history.json"
        with patch("app.infrastructure.history_repository.HISTORY_PATH", path):
            repo = JsonHistoryRepository()
            result = AnalysisResult(keyword="テスト", id="abc-123", timestamp="2024-01-01")
            repo.save(result)

            found = repo.load_by_id("abc-123")
            assert found is not None
            assert found["id"] == "abc-123"

            assert repo.load_by_id("nonexistent") is None

    def test_load_all_empty(self, tmp_path):
        path = tmp_path / "history.json"
        with patch("app.infrastructure.history_repository.HISTORY_PATH", path):
            repo = JsonHistoryRepository()
            assert repo.load_all() == []

    def test_save_raw(self, tmp_path):
        path = tmp_path / "history.json"
        with patch("app.infrastructure.history_repository.HISTORY_PATH", path):
            repo = JsonHistoryRepository()
            result = AnalysisResult(keyword="テスト", id="id-1", timestamp="2024-01-01")
            repo.save(result)

            entry = repo.load_by_id("id-1")
            entry["ai_report"] = "生成されたレポート"
            repo.save_raw(entry)

            updated = repo.load_by_id("id-1")
            assert updated["ai_report"] == "生成されたレポート"
