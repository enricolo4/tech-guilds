from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.gamification.domain.model.quest import (
    Quest,
    QuestDifficulty,
    QuestStatus,
    QuestType,
)
from services.gamification.domain.ports.secondary.quest_repository import (
    QuestRepository,
)
from services.gamification.secondary.postgresql.models.quest_model import (
    QuestModel,
)


class InMemoryQuestRepository(QuestRepository):
    def __init__(self):
        self._storage: dict[UUID, Quest] = {}

    async def get_by_id(self, quest_id: UUID) -> Quest | None:
        return self._storage.get(quest_id)

    async def get_by_external_id(self, external_id: str) -> Quest | None:
        for q in self._storage.values():
            if q.external_id == external_id:
                return q
        return None

    async def save(self, quest: Quest) -> Quest:
        self._storage[quest.id] = quest
        return quest

    async def list_by_guild(self, guild_id: UUID) -> List[Quest]:
        return [q for q in self._storage.values() if q.guild_id == guild_id]

    async def list_all(self) -> List[Quest]:
        return list(self._storage.values())


class PostgresQuestRepository(QuestRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: QuestModel) -> Quest:
        return Quest(
            id=model.id,
            external_id=model.external_id,
            external_source=model.external_source,
            title=model.title,
            guild_id=model.guild_id,
            assignee_hero_id=model.assignee_hero_id,
            adventure_id=model.adventure_id,
            quest_type=QuestType(model.quest_type),
            status=QuestStatus(model.status),
            difficulty=QuestDifficulty(model.difficulty),
            is_pair_programming=model.is_pair_programming,
        )

    async def get_by_id(self, quest_id: UUID) -> Quest | None:
        stmt = select(QuestModel).where(QuestModel.id == quest_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_external_id(self, external_id: str) -> Quest | None:
        stmt = select(QuestModel).where(QuestModel.external_id == external_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, quest: Quest) -> Quest:
        stmt = select(QuestModel).where(QuestModel.id == quest.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        status_val = quest.status.value if hasattr(quest.status, "value") else str(quest.status)
        type_val = quest.quest_type.value if hasattr(quest.quest_type, "value") else str(quest.quest_type)
        diff_val = quest.difficulty.value if hasattr(quest.difficulty, "value") else str(quest.difficulty)

        if model is None:
            model = QuestModel(
                id=quest.id,
                external_id=quest.external_id,
                external_source=quest.external_source,
                title=quest.title,
                guild_id=quest.guild_id,
                assignee_hero_id=quest.assignee_hero_id,
                adventure_id=quest.adventure_id,
                quest_type=type_val,
                status=status_val,
                difficulty=diff_val,
                is_pair_programming=quest.is_pair_programming,
            )
            self.session.add(model)
        else:
            model.title = quest.title
            model.guild_id = quest.guild_id
            model.assignee_hero_id = quest.assignee_hero_id
            model.adventure_id = quest.adventure_id
            model.quest_type = type_val
            model.status = status_val
            model.difficulty = diff_val
            model.is_pair_programming = quest.is_pair_programming

        await self.session.flush()
        return self._to_domain(model)

    async def list_by_guild(self, guild_id: UUID) -> List[Quest]:
        stmt = select(QuestModel).where(QuestModel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def list_all(self) -> List[Quest]:
        stmt = select(QuestModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]
