from abc import ABC, abstractmethod
from dataclasses import dataclass

from services.auth.domain.model.token import AuthToken, TokenPayload
from services.auth.domain.model.user_claims import UserClaims


@dataclass(frozen=True)
class RegisterAccountCommand:
    """Comando de entrada para criação de conta direta com e-mail corporativo."""
    email: str
    name: str
    password: str | None = None
    avatar_url: str | None = None
    tenant_id: str | None = None
    organization_name: str | None = None


@dataclass(frozen=True)
class LoginDirectCommand:
    """Comando de entrada para login direto com e-mail corporativo."""
    email: str
    password: str | None = None
    tenant_id: str | None = None


@dataclass(frozen=True)
class LoginSSOCommand:
    """Comando de entrada para autenticação via provedor SSO."""
    token: str
    provider: str
    tenant_id: str | None = None


@dataclass(frozen=True)
class LoginSSOResult:
    """Resultado da autenticação bem-sucedida contendo token e sessão."""
    auth_token: AuthToken
    user: UserClaims
    session_id: str
    tenant_id: str = "default"


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
    """Porta Primária (Driving Port) para autenticação e cadastro de usuários."""

    @abstractmethod
    async def register_account(self, command: RegisterAccountCommand) -> LoginSSOResult:
        """Cria uma conta real para o usuário, salvando a sessão e emitindo o token JWT."""
        pass

    @abstractmethod
    async def login_direct(self, command: LoginDirectCommand) -> LoginSSOResult:
        """Autentica o usuário diretamente com seu e-mail corporativo."""
        pass

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
