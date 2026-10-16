from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.gamification.domain.model.hero_progression import (
    HeroProgression,
    HeroProgressionStats,
)
from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)
from services.gamification.secondary.postgresql.models.hero_progression_model import (
    HeroProgressionModel,
)


class InMemoryHeroProgressionRepository(HeroProgressionRepository):
    def __init__(self):
        self._storage: dict[UUID, HeroProgression] = {}

    async def get_by_id(self, hero_id: UUID) -> HeroProgression | None:
        return self._storage.get(hero_id)

    async def get_by_email(self, email: str) -> HeroProgression | None:
        for h in self._storage.values():
            if h.email and h.email.lower() == email.lower():
                return h
        return None

    async def save(self, hero: HeroProgression) -> HeroProgression:
        self._storage[hero.hero_id] = hero
        return hero

    async def list_by_guild(self, guild_id: UUID) -> List[HeroProgression]:
        return [h for h in self._storage.values() if h.guild_id == guild_id]

    async def list_all(self) -> List[HeroProgression]:
        return list(self._storage.values())


class PostgresHeroProgressionRepository(HeroProgressionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: HeroProgressionModel) -> HeroProgression:
        stats = HeroProgressionStats.from_dict(model.stats or {})
        return HeroProgression(
            hero_id=model.hero_id,
            name=model.name,
            email=model.email,
            hero_class=model.hero_class,
            level=model.level,
            exp=model.exp,
            gold=model.gold,
            hp=model.hp,
            max_hp=model.max_hp,
            mana=model.mana,
            max_mana=model.max_mana,
            stats=stats,
            equipped_gear=dict(model.equipped_gear or {}),
            active_buffs=dict(model.active_buffs or {}),
            skill_cooldowns=dict(model.skill_cooldowns or {}),
            guild_id=model.guild_id,
        )

    async def get_by_id(self, hero_id: UUID) -> HeroProgression | None:
        stmt = select(HeroProgressionModel).where(HeroProgressionModel.hero_id == hero_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> HeroProgression | None:
        stmt = select(HeroProgressionModel).where(HeroProgressionModel.email == email)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, hero: HeroProgression) -> HeroProgression:
        stmt = select(HeroProgressionModel).where(HeroProgressionModel.hero_id == hero.hero_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        stats_dict = hero.stats.to_dict() if hasattr(hero.stats, "to_dict") else dict(hero.stats)

        if model is None:
            model = HeroProgressionModel(
                hero_id=hero.hero_id,
                name=hero.name,
                email=hero.email,
                hero_class=hero.hero_class,
                level=hero.level,
                exp=hero.exp,
                gold=hero.gold,
                hp=hero.hp,
                max_hp=hero.max_hp,
                mana=hero.mana,
                max_mana=hero.max_mana,
                stats=stats_dict,
                equipped_gear=hero.equipped_gear,
                active_buffs=hero.active_buffs,
                skill_cooldowns=hero.skill_cooldowns,
                guild_id=hero.guild_id,
            )
            self.session.add(model)
        else:
            model.name = hero.name
            model.email = hero.email
            model.hero_class = hero.hero_class
            model.level = hero.level
            model.exp = hero.exp
            model.gold = hero.gold
            model.hp = hero.hp
            model.max_hp = hero.max_hp
            model.mana = hero.mana
            model.max_mana = hero.max_mana
            model.stats = stats_dict
            model.equipped_gear = hero.equipped_gear
            model.active_buffs = hero.active_buffs
            model.skill_cooldowns = hero.skill_cooldowns
            model.guild_id = hero.guild_id

        await self.session.flush()
        return self._to_domain(model)

    async def list_by_guild(self, guild_id: UUID) -> List[HeroProgression]:
        stmt = select(HeroProgressionModel).where(HeroProgressionModel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list_all(self) -> List[HeroProgression]:
        stmt = select(HeroProgressionModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]
