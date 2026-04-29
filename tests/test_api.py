from fastapi.testclient import TestClient

from kagcrawl.api import app


client = TestClient(app)


def test_health_is_public() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_doctor_requires_api_key(monkeypatch) -> None:
    monkeypatch.setenv("KAGCRAWL_API_KEY", "secret-key")
    response = client.get("/doctor")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_doctor_accepts_x_api_key(monkeypatch) -> None:
    monkeypatch.setenv("KAGCRAWL_API_KEY", "secret-key")
    response = client.get("/doctor", headers={"X-API-Key": "secret-key"})
    assert response.status_code == 200
    body = response.json()
    assert "recommended_modes" in body


def test_doctor_accepts_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("KAGCRAWL_API_KEY", "secret-key")
    response = client.get("/doctor", headers={"Authorization": "Bearer secret-key"})
    assert response.status_code == 200


def test_doctor_fails_closed_when_server_missing_key(monkeypatch) -> None:
    monkeypatch.delenv("KAGCRAWL_API_KEY", raising=False)
    response = client.get("/doctor", headers={"X-API-Key": "anything"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Server missing KAGCRAWL_API_KEY"
