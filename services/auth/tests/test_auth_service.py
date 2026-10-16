import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient

from services.auth.domain.model.token import AuthToken, Session, TokenPayload
from services.auth.domain.model.user_claims import UserClaims
from services.auth.domain.ports.primary.auth_port import (
    AuthenticateUserPort,
    LoginSSOCommand,
    LoginSSOResult,
    ValidateTokenCommand,
    ValidateTokenPort,
    ValidateTokenResult,
)
from services.auth.domain.ports.secondary.session_repository import SessionRepository
from services.auth.domain.ports.secondary.sso_port import SSOIdentityPort
from services.auth.domain.ports.secondary.token_service_port import TokenServicePort
from services.auth.domain.use_cases.authenticate_sso import AuthenticateSSOUseCase
from services.auth.domain.use_cases.validate_session import ValidateSessionUseCase
from services.auth.secondary.postgresql.models.session_model import SessionModel
from services.auth.secondary.postgresql.repositories.postgres_session_repository import (
    InMemorySessionRepository,
    PostgresSessionRepository,
)
from services.auth.secondary.sso.sso_adapter import MultiProviderSSOAdapter
from services.auth.secondary.token_service.jwt_service import JoseJWTService
from services.auth.primary.rest_api.controllers.auth_controller import router
from services.auth.primary.rest_api.dependencies.container import (
    AuthContainer,
    get_auth_port,
    get_validate_token_port,
)
from services.auth.primary.rest_api.main import app


class MockSSOAdapter(SSOIdentityPort):
    def __init__(self):
        self.users = {
            "valid-google-token": UserClaims(
                email="dev.player@google.corp",
                name="Google Dev",
                provider="google",
                provider_user_id="google-12345",
                avatar_url="https://google.corp/avatar.png",
            ),
            "valid-github-token": UserClaims(
                email="dev.octocat@github.corp",
                name="Octo Cat",
                provider="github",
                provider_user_id="github-9999",
                avatar_url="https://github.corp/octocat.png",
            ),
        }

    async def verify_token(self, token: str, provider: str) -> UserClaims:
        if token in self.users:
            return self.users[token]
        raise ValueError(f"Token do provedor {provider} inválido ou expirado")


# ==============================================================================
# 1. TESTES DE CONFORMIDADE ARQUITETURAL (HEXAGONAL)
# ==============================================================================

def test_hexagonal_architecture_compliance():
    """Garante que casos de uso e adaptadores implementam formalmente as portas."""
    assert issubclass(AuthenticateSSOUseCase, AuthenticateUserPort)
    assert issubclass(ValidateSessionUseCase, ValidateTokenPort)
    assert issubclass(JoseJWTService, TokenServicePort)
    assert issubclass(MultiProviderSSOAdapter, SSOIdentityPort)
    assert issubclass(InMemorySessionRepository, SessionRepository)
    assert issubclass(PostgresSessionRepository, SessionRepository)
    assert SessionModel.__table_args__ == {"schema": "auth"}


# ==============================================================================
# 2. TESTES DO SERVIÇO JWT (JoseJWTService)
# ==============================================================================

def test_jwt_issuance_and_verification():
    service = JoseJWTService(secret_key="secret-key-123", default_expires_in=3600)
    payload = TokenPayload(
        sub="user-42",
        email="hero@guild.local",
        name="Sir Arthur",
        provider="github",
        session_id="sess-abc",
        roles=["player", "guild_master"],
    )

    token = service.issue_token(payload)
    assert isinstance(token, str)
    assert len(token) > 20

    verified = service.verify_token(token)
    assert verified.sub == "user-42"
    assert verified.email == "hero@guild.local"
    assert verified.name == "Sir Arthur"
    assert verified.provider == "github"
    assert verified.session_id == "sess-abc"
    assert verified.roles == ["player", "guild_master"]


def test_jwt_rejection_on_invalid_or_tampered_token():
    service = JoseJWTService(secret_key="secret-key-123")
    with pytest.raises(ValueError, match="Assinatura do JWT inválida"):
        service.verify_token("invalid.token.signature")


def test_jwt_rejection_on_expired_token():
    service = JoseJWTService(secret_key="secret-key-123")
    payload = TokenPayload(
        sub="user-42",
        email="hero@guild.local",
        name="Sir Arthur",
        provider="github",
        session_id="sess-abc",
    )
    # Token expirado com TTL negativo
    token = service.issue_token(payload, expires_in_seconds=-10)
    with pytest.raises(ValueError, match="Assinatura do JWT inválida ou expirada"):
        service.verify_token(token)


# ==============================================================================
# 3. TESTES DO CASO DE USO DE AUTENTICAÇÃO SSO (AuthenticateSSOUseCase)
# ==============================================================================

@pytest.mark.asyncio
async def test_authenticate_sso_success():
    sso_mock = MockSSOAdapter()
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService(secret_key="secret-key-123")
    use_case = AuthenticateSSOUseCase(
        sso_port=sso_mock,
        session_repository=session_repo,
        token_service=token_service,
        token_ttl_seconds=1800,
        session_ttl_days=7,
    )

    command = LoginSSOCommand(token="valid-google-token", provider="google")
    result: LoginSSOResult = await use_case.login_sso(command)

    assert result.auth_token.access_token is not None
    assert result.auth_token.expires_in == 1800
    assert result.auth_token.token_type == "bearer"
    assert result.user.email == "dev.player@google.corp"
    assert result.user.provider == "google"
    assert result.session_id is not None

    # Sessão gravada no repositório
    saved_session = await session_repo.find_by_id(result.session_id)
    assert saved_session is not None
    assert saved_session.email == "dev.player@google.corp"
    assert saved_session.provider_user_id == "google-12345"
    assert saved_session.is_active() is True
    assert saved_session.is_revoked is False


@pytest.mark.asyncio
async def test_authenticate_sso_failure_invalid_sso_token():
    sso_mock = MockSSOAdapter()
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService()
    use_case = AuthenticateSSOUseCase(
        sso_port=sso_mock,
        session_repository=session_repo,
        token_service=token_service,
    )

    command = LoginSSOCommand(token="fake-bad-token", provider="google")
    with pytest.raises(ValueError, match="Token do provedor google inválido ou expirado"):
        await use_case.login_sso(command)


# ==============================================================================
# 4. TESTES DO CASO DE USO DE VALIDAÇÃO DE SESSÃO (ValidateSessionUseCase)
# ==============================================================================

@pytest.mark.asyncio
async def test_validate_session_active_and_valid():
    sso_mock = MockSSOAdapter()
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService(secret_key="secret-key-123")
    auth_use_case = AuthenticateSSOUseCase(sso_mock, session_repo, token_service)
    validate_use_case = ValidateSessionUseCase(token_service, session_repo)

    # Cria sessão inicial via login
    login_result = await auth_use_case.login_sso(
        LoginSSOCommand(token="valid-google-token", provider="google")
    )

    # Valida sessão ativa
    validation = await validate_use_case.validate_token(
        ValidateTokenCommand(token=login_result.auth_token.access_token)
    )
    assert validation.is_valid is True
    assert validation.payload is not None
    assert validation.payload.email == "dev.player@google.corp"
    assert validation.payload.session_id == login_result.session_id
    assert validation.error is None


@pytest.mark.asyncio
async def test_validate_session_revoked():
    sso_mock = MockSSOAdapter()
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService(secret_key="secret-key-123")
    auth_use_case = AuthenticateSSOUseCase(sso_mock, session_repo, token_service)
    validate_use_case = ValidateSessionUseCase(token_service, session_repo)

    login_result = await auth_use_case.login_sso(
        LoginSSOCommand(token="valid-google-token", provider="google")
    )

    # Revoga a sessão
    await session_repo.revoke(login_result.session_id)

    validation = await validate_use_case.validate_token(
        ValidateTokenCommand(token=login_result.auth_token.access_token)
    )
    assert validation.is_valid is False
    assert "revogada" in validation.error


@pytest.mark.asyncio
async def test_validate_session_expired():
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService(secret_key="secret-key-123")
    validate_use_case = ValidateSessionUseCase(token_service, session_repo)

    # Cria sessão expirada
    past_date = datetime.now(timezone.utc) - timedelta(days=2)
    session = Session(
        id="expired-session-id",
        user_id="user-1",
        email="expired@test.corp",
        provider="google",
        provider_user_id="user-1",
        created_at=past_date - timedelta(days=5),
        expires_at=past_date,
        token="some-token",
        is_revoked=False,
    )
    await session_repo.save(session)

    # Emite token válido criptograficamente para essa sessão
    payload = TokenPayload(
        sub="user-1",
        email="expired@test.corp",
        name="Expired User",
        provider="google",
        session_id="expired-session-id",
    )
    token = token_service.issue_token(payload, expires_in_seconds=3600)

    validation = await validate_use_case.validate_token(ValidateTokenCommand(token=token))
    assert validation.is_valid is False
    assert "expirada" in validation.error


@pytest.mark.asyncio
async def test_validate_token_malformed_or_missing():
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService()
    validate_use_case = ValidateSessionUseCase(token_service, session_repo)

    res_empty = await validate_use_case.validate_token(ValidateTokenCommand(token=""))
    assert res_empty.is_valid is False
    assert "não fornecido" in res_empty.error

    res_garbage = await validate_use_case.validate_token(ValidateTokenCommand(token="not.a.valid.jwt"))
    assert res_garbage.is_valid is False
    assert "Token inválido" in res_garbage.error


# ==============================================================================
# 5. TESTES DO ADAPTADOR SSO MULTI-PROVIDER COM MOCK HTTPX
# ==============================================================================

@pytest.mark.asyncio
async def test_sso_adapter_google_flow():
    mock_response = httpx.Response(
        200,
        json={
            "sub": "google-user-789",
            "email": "google.dev@company.com",
            "name": "Google Developer",
            "picture": "https://avatar.google.com/dev.png",
        },
        request=httpx.Request("GET", "https://oauth2.googleapis.com/tokeninfo"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = mock_response

    adapter = MultiProviderSSOAdapter(http_client=mock_client)
    claims = await adapter.verify_token("google-id-token", "google")

    assert claims.provider == "google"
    assert claims.email == "google.dev@company.com"
    assert claims.name == "Google Developer"
    assert claims.provider_user_id == "google-user-789"
    assert claims.avatar_url == "https://avatar.google.com/dev.png"


@pytest.mark.asyncio
async def test_sso_adapter_github_flow():
    user_response = httpx.Response(
        200,
        json={
            "id": 123456,
            "login": "octodev",
            "name": "Octo Dev",
            "email": None,
            "avatar_url": "https://github.com/octodev.png",
        },
        request=httpx.Request("GET", "https://api.github.com/user"),
    )
    emails_response = httpx.Response(
        200,
        json=[{"email": "octodev@github.corp", "primary": True}],
        request=httpx.Request("GET", "https://api.github.com/user/emails"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.side_effect = [user_response, emails_response]

    adapter = MultiProviderSSOAdapter(http_client=mock_client)
    claims = await adapter.verify_token("gh-token", "github")

    assert claims.provider == "github"
    assert claims.email == "octodev@github.corp"
    assert claims.name == "Octo Dev"
    assert claims.provider_user_id == "123456"


@pytest.mark.asyncio
async def test_sso_adapter_microsoft_azure_flow():
    azure_response = httpx.Response(
        200,
        json={
            "id": "azure-user-999",
            "displayName": "Azure Architect",
            "mail": "architect@azure.corp",
        },
        request=httpx.Request("GET", "https://graph.microsoft.com/v1.0/me"),
    )
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get.return_value = azure_response

    adapter = MultiProviderSSOAdapter(http_client=mock_client)
    claims = await adapter.verify_token("azure-token", "azure")

    assert claims.provider == "azure"
    assert claims.email == "architect@azure.corp"
    assert claims.name == "Azure Architect"
    assert claims.provider_user_id == "azure-user-999"


@pytest.mark.asyncio
async def test_sso_adapter_unsupported_provider():
    adapter = MultiProviderSSOAdapter()
    with pytest.raises(ValueError, match="Provedor de SSO não suportado"):
        await adapter.verify_token("token", "unsupported_provider")


# ==============================================================================
# 6. TESTES DE INTEGRAÇÃO DA REST API (FastAPI)
# ==============================================================================

def test_rest_api_full_flow():
    mock_sso = MockSSOAdapter()
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService(secret_key="api-secret-key-123")

    test_container = AuthContainer(
        sso_adapter=mock_sso,
        session_repository=session_repo,
        token_service=token_service,
    )
    AuthContainer.set_instance(test_container)

    client = TestClient(app)

    # 1. Login com SSO
    login_resp = client.post(
        "/auth/login/sso",
        json={"token": "valid-google-token", "provider": "google"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "dev.player@google.corp"
    assert data["session_id"] is not None
    jwt_token = data["access_token"]
    session_id = data["session_id"]

    # 2. Validação de token no corpo da requisição
    validate_resp = client.post("/auth/validate", json={"token": jwt_token})
    assert validate_resp.status_code == 200
    val_data = validate_resp.json()
    assert val_data["is_valid"] is True
    assert val_data["email"] == "dev.player@google.corp"
    assert val_data["session_id"] == session_id

    # 3. Validação de token via header Authorization: Bearer
    header_resp = client.post(
        "/auth/validate",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert header_resp.status_code == 200
    assert header_resp.json()["is_valid"] is True

    # 4. Validação com token falso / inválido
    bad_resp = client.post("/auth/validate", json={"token": "garbage.token.here"})
    assert bad_resp.status_code == 200
    assert bad_resp.json()["is_valid"] is False

    # 5. Login com credencial SSO inválida
    fail_login = client.post(
        "/auth/login/sso",
        json={"token": "invalid-sso-cred", "provider": "google"},
    )
    assert fail_login.status_code == 401


# ==============================================================================
# 7. TESTES DO REPOSITÓRIO EM MEMÓRIA E MODELO DE SESSÃO
# ==============================================================================

@pytest.mark.asyncio
async def test_session_model_and_in_memory_repository():
    repo = InMemorySessionRepository()
    now = datetime.now(timezone.utc)
    session = Session(
        id="test-session-1",
        user_id="user-123",
        email="test@domain.corp",
        provider="google",
        provider_user_id="p-123",
        created_at=now,
        expires_at=now + timedelta(days=1),
        token="some-jwt-token",
        is_revoked=False,
    )

    await repo.save(session)
    found = await repo.find_by_id("test-session-1")
    assert found is not None
    assert found.email == "test@domain.corp"

    user_sessions = await repo.find_by_user_id("user-123")
    assert len(user_sessions) == 1

    await repo.revoke("test-session-1")
    revoked = await repo.find_by_id("test-session-1")
    assert revoked.is_revoked is True
    assert revoked.is_active() is False

    # Valida conversão SQLAlchemy Model <-> Domain Session
    orm_model = SessionModel.from_domain(session)
    assert orm_model.id == session.id
    assert orm_model.email == session.email
    converted_domain = orm_model.to_domain()
    assert converted_domain.id == session.id
    assert converted_domain.email == session.email


def test_api_register_and_login_direct_flow():
    mock_sso = MockSSOAdapter()
    session_repo = InMemorySessionRepository()
    token_service = JoseJWTService(secret_key="api-secret-key-123")
    test_container = AuthContainer(
        sso_adapter=mock_sso,
        session_repository=session_repo,
        token_service=token_service,
    )
    AuthContainer.set_instance(test_container)
    client = TestClient(app)

    # Cadastro de conta real
    reg_resp = client.post("/auth/register", json={
        "name": "Alex Real Dev",
        "email": "alex.real@corp.com",
        "password": "secretpassword123",
    })
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert data["user"]["email"] == "alex.real@corp.com"
    assert data["user"]["name"] == "Alex Real Dev"
    assert data["access_token"] is not None

    # Login direto
    login_resp = client.post("/auth/login", json={
        "email": "alex.real@corp.com",
        "password": "secretpassword123",
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["user"]["email"] == "alex.real@corp.com"
    assert login_data["access_token"] is not None
