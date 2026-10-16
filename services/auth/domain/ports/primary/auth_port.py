from abc import ABC, abstractmethod
from dataclasses import dataclass

from services.auth.domain.model.token import AuthToken, TokenPayload
from services.auth.domain.model.user_claims import UserClaims


@dataclass(frozen=True)
class LoginSSOCommand:
    """Comando de entrada para autenticação via provedor SSO."""
    token: str
    provider: str


@dataclass(frozen=True)
class LoginSSOResult:
    """Resultado da autenticação bem-sucedida contendo token e sessão."""
    auth_token: AuthToken
    user: UserClaims
    session_id: str


@dataclass(frozen=True)
class ValidateTokenCommand:
    """Comando de entrada para validação de token JWT."""
    token: str


@dataclass(frozen=True)
class ValidateTokenResult:
    """Resultado da validação do token JWT e verificação de sessão."""
    is_valid: bool
    payload: TokenPayload | None = None
    error: str | None = None


class AuthenticateUserPort(ABC):
    """Porta Primária (Driving Port) para autenticação de usuários via SSO."""

    @abstractmethod
    async def login_sso(self, command: LoginSSOCommand) -> LoginSSOResult:
        """Autentica o usuário validando a credencial do provedor SSO e gerando a sessão."""
        pass


class ValidateTokenPort(ABC):
    """Porta Primária (Driving Port) para validação e introspecção de tokens/sessões."""

    @abstractmethod
    async def validate_token(self, command: ValidateTokenCommand) -> ValidateTokenResult:
        """Valida a integridade do token JWT e o estado da sessão associada."""
        pass
