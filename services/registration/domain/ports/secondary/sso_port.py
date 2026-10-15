from abc import ABC, abstractmethod
from services.registration.domain.model.user_claims import UserClaims


class SSOIdentityPort(ABC):
    """Porta Secundária para validação de identidade SSO corporativa (Google, GitHub, Azure, Microsoft)."""

    @abstractmethod
    async def verify_token(self, token: str, provider: str) -> UserClaims:
        """Valida o token de autenticação junto ao provedor SSO e retorna as claims normalizadas."""
        pass
