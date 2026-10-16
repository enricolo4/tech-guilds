import os

from services.auth.domain.ports.primary.auth_port import (
    AuthenticateUserPort,
    ValidateTokenPort,
)
from services.auth.domain.ports.secondary.session_repository import SessionRepository
from services.auth.domain.ports.secondary.sso_port import SSOIdentityPort
from services.auth.domain.ports.secondary.token_service_port import TokenServicePort
from services.auth.domain.use_cases.authenticate_sso import AuthenticateSSOUseCase
from services.auth.domain.use_cases.validate_session import ValidateSessionUseCase
from services.auth.secondary.postgresql.repositories.postgres_session_repository import (
    InMemorySessionRepository,
)
from services.auth.secondary.sso.sso_adapter import MultiProviderSSOAdapter
from services.auth.secondary.token_service.jwt_service import JoseJWTService


class AuthContainer:
    """Container de injeção de dependências do microsserviço de Autenticação."""
    _instance: "AuthContainer" | None = None

    def __init__(
        self,
        sso_adapter: SSOIdentityPort | None = None,
        session_repository: SessionRepository | None = None,
        token_service: TokenServicePort | None = None,
    ):
        self._sso_adapter = sso_adapter or MultiProviderSSOAdapter()
        if session_repository is not None:
            self._session_repository = session_repository
        elif os.getenv("TESTING", "false").lower() == "true":
            self._session_repository = InMemorySessionRepository()
        else:
            try:
                from services.auth.secondary.postgresql.database import async_session_maker
                from services.auth.secondary.postgresql.repositories.postgres_session_repository import PostgresSessionRepository
                self._session_repository = PostgresSessionRepository(async_session_maker)
            except Exception:
                self._session_repository = InMemorySessionRepository()
        jwt_secret = os.getenv(
            "AUTH_JWT_SECRET",
            "super-secret-auth-key-change-in-production-1234567890",
        )
        self._token_service = token_service or JoseJWTService(secret_key=jwt_secret)

        self._authenticate_use_case = AuthenticateSSOUseCase(
            sso_port=self._sso_adapter,
            session_repository=self._session_repository,
            token_service=self._token_service,
        )
        self._validate_session_use_case = ValidateSessionUseCase(
            token_service=self._token_service,
            session_repository=self._session_repository,
        )

    @classmethod
    def get_instance(cls) -> "AuthContainer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_instance(cls, container: "AuthContainer" | None) -> None:
        cls._instance = container

    @classmethod
    def reset(cls) -> None:
        cls._instance = None

    @property
    def auth_port(self) -> AuthenticateUserPort:
        return self._authenticate_use_case

    @property
    def validate_token_port(self) -> ValidateTokenPort:
        return self._validate_session_use_case

    @property
    def session_repository(self) -> SessionRepository:
        return self._session_repository

    @property
    def token_service(self) -> TokenServicePort:
        return self._token_service

    @property
    def sso_adapter(self) -> SSOIdentityPort:
        return self._sso_adapter


def get_auth_container() -> AuthContainer:
    return AuthContainer.get_instance()


def get_auth_port() -> AuthenticateUserPort:
    return get_auth_container().auth_port


def get_validate_token_port() -> ValidateTokenPort:
    return get_auth_container().validate_token_port
