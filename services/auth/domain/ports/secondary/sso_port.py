from abc import ABC, abstractmethod
from services.auth.domain.model.user_claims import UserClaims


class SSOIdentityPort(ABC):
    """Porta Secundária (Driven Port) para validação de identidade junto a provedores SSO corporativos."""

    @abstractmethod
    async def verify_token(self, token: str, provider: str) -> UserClaims:
        """Valida o token de autenticação emitido pelo provedor SSO e retorna os claims do usuário."""
        pass
