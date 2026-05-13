"""APIエンドポイントのテスト."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_empty_keyword():
    response = client.post("/api/analyze", json={"keyword": ""})
    assert response.status_code == 422


def test_get_history_empty():
    with patch("app.api.get_history_repository") as mock:
        repo = MagicMock()
        repo.load_all.return_value = []
        mock.return_value = repo
        response = client.get("/api/history")
        assert response.status_code == 200


def test_get_history_detail_not_found():
    with patch("app.api.get_history_repository") as mock:
        repo = MagicMock()
        repo.load_by_id.return_value = None
        mock.return_value = repo
        response = client.get("/api/history/nonexistent-id")
        assert response.status_code == 404
