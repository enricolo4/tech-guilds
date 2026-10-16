from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.gamification.domain.model.mini_boss import (
    MiniBoss,
    BossSeverity,
)
from services.gamification.domain.ports.secondary.mini_boss_repository import (
    MiniBossRepository,
)
from services.gamification.secondary.postgresql.models.mini_boss_model import (
    MiniBossModel,
)


class InMemoryMiniBossRepository(MiniBossRepository):
    def __init__(self):
        self._storage: dict[UUID, MiniBoss] = {}

    async def get_by_id(self, boss_id: UUID) -> MiniBoss | None:
        return self._storage.get(boss_id)

    async def get_by_external_id(self, external_id: str) -> MiniBoss | None:
        for b in self._storage.values():
            if b.external_id == external_id:
                return b
        return None

    async def save(self, boss: MiniBoss) -> MiniBoss:
        self._storage[boss.id] = boss
        return boss

    async def list_active_by_guild(self, guild_id: UUID) -> List[MiniBoss]:
        return [b for b in self._storage.values() if b.guild_id == guild_id and not b.is_defeated]

    async def list_all(self) -> List[MiniBoss]:
        return list(self._storage.values())


class PostgresMiniBossRepository(MiniBossRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: MiniBossModel) -> MiniBoss:
        return MiniBoss(
            id=model.id,
            external_id=model.external_id,
            title=model.title,
            guild_id=model.guild_id,
            severity=BossSeverity(model.severity),
            max_health=model.max_health,
            current_health=model.current_health,
            is_defeated=model.is_defeated,
            bounty_hero_xp=model.bounty_hero_xp,
            bounty_guild_xp=model.bounty_guild_xp,
            bounty_gold=model.bounty_gold,
        )

    async def get_by_id(self, boss_id: UUID) -> MiniBoss | None:
        stmt = select(MiniBossModel).where(MiniBossModel.id == boss_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_external_id(self, external_id: str) -> MiniBoss | None:
        stmt = select(MiniBossModel).where(MiniBossModel.external_id == external_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, boss: MiniBoss) -> MiniBoss:
        stmt = select(MiniBossModel).where(MiniBossModel.id == boss.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        sev_val = boss.severity.value if hasattr(boss.severity, "value") else str(boss.severity)

        if model is None:
            model = MiniBossModel(
                id=boss.id,
                external_id=boss.external_id,
                title=boss.title,
                guild_id=boss.guild_id,
                severity=sev_val,
                max_health=boss.max_health,
                current_health=boss.current_health,
                is_defeated=boss.is_defeated,
                bounty_hero_xp=boss.bounty_hero_xp,
                bounty_guild_xp=boss.bounty_guild_xp,
                bounty_gold=boss.bounty_gold,
            )
            self.session.add(model)
        else:
            model.title = boss.title
            model.guild_id = boss.guild_id
            model.severity = sev_val
            model.max_health = boss.max_health
            model.current_health = boss.current_health
            model.is_defeated = boss.is_defeated
            model.bounty_hero_xp = boss.bounty_hero_xp
            model.bounty_guild_xp = boss.bounty_guild_xp
            model.bounty_gold = boss.bounty_gold

        await self.session.flush()
        return self._to_domain(model)

    async def list_active_by_guild(self, guild_id: UUID) -> List[MiniBoss]:
        stmt = select(MiniBossModel).where(
            MiniBossModel.guild_id == guild_id,
            MiniBossModel.is_defeated == False,
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list_all(self) -> List[MiniBoss]:
        stmt = select(MiniBossModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]
