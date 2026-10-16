import pytest
from fastapi.testclient import TestClient

from services.gateway.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_gateway_health_endpoint(client):
    """O endpoint /health do gateway deve reportar status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "registration" in data["services"]
    assert "auth" in data["services"]
    assert "guilds" in data["services"]
    assert "gamification" in data["services"]


def test_gateway_root_redirects_to_dashboard(client):
    """A raiz / deve redirecionar para /dashboard."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/dashboard"


def test_gateway_dashboard_page(client):
    """A rota /dashboard deve servir o HTML da interface retro."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TECH GUILDS" in response.text or "Guild" in response.text


def test_gateway_mounts_registration_routes(client):
    """As rotas do microsserviço de cadastro devem estar disponíveis sob /api/registration."""
    response = client.get("/api/registration/health")
    assert response.status_code == 200
    assert response.json()["service"] == "registration"


def test_gateway_mounts_auth_routes(client):
    """As rotas do microsserviço de autenticação devem estar disponíveis sob /api/auth."""
    response = client.post("/api/auth/validate", json={"token": "invalid.jwt.token"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False


def test_gateway_mounts_guilds_routes(client):
    """As rotas do microsserviço de guildas devem estar disponíveis sob /api/guilds."""
    response = client.get("/api/guilds/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_gateway_mounts_gamification_routes(client):
    """As rotas do microsserviço de gamificação devem estar disponíveis sob /api/gamification."""
    response = client.get("/api/gamification/quests")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_gateway_serves_onboarding_page(client):
    """As rotas /onboarding e /dashboard/onboarding devem servir a página de onboarding."""
    resp1 = client.get("/onboarding")
    assert resp1.status_code == 200
    assert "text/html" in resp1.headers["content-type"]
    assert "HERO CREATION & SQUAD ONBOARDING" in resp1.text

    resp2 = client.get("/dashboard/onboarding")
    assert resp2.status_code == 200
    assert "text/html" in resp2.headers["content-type"]
    assert "IDENTIFICAÇÃO DO DESENVOLVEDOR" in resp2.text
