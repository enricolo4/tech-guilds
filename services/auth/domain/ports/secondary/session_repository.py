from abc import ABC, abstractmethod
from typing import List
from services.auth.domain.model.token import Session


class SessionRepository(ABC):
    """Porta Secundária (Driven Port) para persistência de sessões de usuário."""

    @abstractmethod
    async def save(self, session: Session) -> Session:
        """Salva ou atualiza uma sessão de usuário."""
        pass

    @abstractmethod
    async def find_by_id(self, session_id: str) -> Session | None:
        """Recupera uma sessão pelo seu ID."""
        pass

    @abstractmethod
    async def revoke(self, session_id: str) -> None:
        """Revoga uma sessão tornando-a inativa."""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[Session]:
        """Retorna todas as sessões associadas a um usuário."""
        pass

    @abstractmethod
    async def find_by_email(self, email: str, tenant_id: str | None = None) -> Session | None:
        """Recupera a sessão mais recente associada a um e-mail corporativo."""
        pass


