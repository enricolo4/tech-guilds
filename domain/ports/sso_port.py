from abc import ABC, abstractmethod
from ..model.user_claims import UserClaims


class SSOIdentityPort(ABC):
    """Porta para validação de tokens JWT emitidos pelos provedores SSO corporativos (Google, GitHub, Azure, Microsoft)."""
    @abstractmethod
    async def verify_token(self, token: str, provider: str) -> UserClaims:
        pass
