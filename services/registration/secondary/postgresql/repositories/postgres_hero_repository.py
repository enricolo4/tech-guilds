from typing import Dict, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.registration.domain.model.hero import Hero
from services.registration.domain.ports.secondary.hero_repository import HeroRepository
from services.registration.secondary.postgresql.models.hero_model import HeroModel


class PostgresHeroRepository(HeroRepository):
    """Implementação PostgreSQL da porta HeroRepository utilizando SQLAlchemy AsyncSession."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, hero_id: UUID) -> Hero | None:
        stmt = select(HeroModel).where(HeroModel.id == hero_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def get_by_email(self, email: str) -> Hero | None:
        clean_email = email.strip().lower()
        stmt = select(HeroModel).where(HeroModel.email == clean_email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def save(self, hero: Hero) -> Hero:
        model = HeroModel.from_domain(hero)
        self._session.add(model)
        await self._session.flush()
        return model.to_domain()

    async def update(self, hero: Hero) -> Hero:
        stmt = select(HeroModel).where(HeroModel.id == hero.id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Herói com ID {hero.id} não encontrado para atualização.")

        model.name = hero.name
        model.avatar_url = hero.avatar_url
        model.hero_class = hero.hero_class.value if hasattr(hero.hero_class, "value") else str(hero.hero_class)
        model.level = hero.level
        model.experience = hero.experience
        model.gold = hero.gold
        model.health = hero.health
        model.max_health = hero.max_health
        model.mana = hero.mana
        model.max_mana = hero.max_mana
        model.strength = hero.stats.strength
        model.intelligence = hero.stats.intelligence
        model.constitution = hero.stats.constitution
        model.perception = hero.stats.perception
        model.guild_id = hero.guild_id

        await self._session.flush()
        return model.to_domain()

    async def list_all(self) -> List[Hero]:
        stmt = select(HeroModel)
        result = await self._session.execute(stmt)
        return [m.to_domain() for m in result.scalars().all()]


class InMemoryHeroRepository(HeroRepository):
    """Implementação em memória da porta HeroRepository para testes rápidos e isolados."""

    def __init__(self, initial_heroes: List[Hero] | None = None):
        self._storage: Dict[UUID, Hero] = {}
        if initial_heroes:
            for hero in initial_heroes:
                self._storage[hero.id] = hero

    async def get_by_id(self, hero_id: UUID) -> Hero | None:
        return self._storage.get(hero_id)

    async def get_by_email(self, email: str) -> Hero | None:
        clean_email = email.strip().lower()
        for hero in self._storage.values():
            if hero.email.strip().lower() == clean_email:
                return hero
        return None

    async def save(self, hero: Hero) -> Hero:
        self._storage[hero.id] = hero
        return hero

    async def update(self, hero: Hero) -> Hero:
        if hero.id not in self._storage:
            raise ValueError(f"Herói com ID {hero.id} não encontrado para atualização.")
        self._storage[hero.id] = hero
        return hero

    async def list_all(self) -> List[Hero]:
        return list(self._storage.values())
