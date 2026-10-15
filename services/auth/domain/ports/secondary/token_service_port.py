from abc import ABC, abstractmethod
from services.auth.domain.model.token import TokenPayload


class TokenServicePort(ABC):
    """Porta Secundária (Driven Port) para geração e verificação de tokens criptográficos (JWT)."""

    @abstractmethod
    def issue_token(self, payload: TokenPayload, expires_in_seconds: int = 3600) -> str:
        """Emite uma nova representação serializada de token JWT."""
        pass

    @abstractmethod
    def verify_token(self, token: str) -> TokenPayload:
        """Verifica a assinatura e expiração do token JWT, extraindo o payload."""
        pass
