"""Health probe and error-envelope behaviour."""

from fastapi.testclient import TestClient

from app.config import get_settings


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert isinstance(body["model_loaded"], bool)


def test_health_flag_tracks_artifact_presence(client: TestClient) -> None:
    """`model_loaded` must reflect reality, not be hardcoded to False.

    This keeps passing once Phase 4 writes the artifacts.
    """
    settings = get_settings()
    expected = settings.model_path.is_file() and settings.vectorizer_path.is_file()

    assert client.get("/health").json()["model_loaded"] is expected


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/nope")

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "NOT_FOUND"
    assert "detail" not in body


def test_wrong_method_uses_error_envelope(client: TestClient) -> None:
    response = client.post("/health")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_openapi_documents_health(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
