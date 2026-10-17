from abc import ABC, abstractmethod
from typing import List
from uuid import UUID
from services.registration.domain.model.hero import Hero


class HeroRepository(ABC):
    """Porta Secundária (Driven Port) para persistência de Heróis."""

    @abstractmethod
    async def get_by_id(self, hero_id: UUID, tenant_id: str | None = None) -> Hero | None:
        """Recupera um herói pelo seu UUID único."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: str | None = None) -> Hero | None:
        """Recupera um herói pelo seu endereço de e-mail."""
        pass

    @abstractmethod
    async def save(self, hero: Hero) -> Hero:
        """Salva um novo herói no repositório."""
        pass

    @abstractmethod
    async def update(self, hero: Hero) -> Hero:
        """Atualiza os dados de um herói existente."""
        pass

    @abstractmethod
    async def list_all(self, tenant_id: str | None = None) -> List[Hero]:
        """Lista todos os heróis cadastrados."""
        pass

