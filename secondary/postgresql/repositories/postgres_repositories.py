from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tech_guilds.domain.model.hero import Hero, HeroClass, HeroStats
from tech_guilds.domain.model.guild import Guild
from tech_guilds.domain.model.quest import Quest, QuestType, QuestStatus, QuestDifficulty
from tech_guilds.domain.model.adventure import Adventure
from tech_guilds.domain.model.mini_boss import MiniBoss, BossSeverity
from tech_guilds.domain.ports.repositories import (
    HeroRepository,
    GuildRepository,
    QuestRepository,
    AdventureRepository,
    MiniBossRepository,
)
from ..models.hero_model import HeroModel
from ..models.guild_model import GuildModel
from ..models.quest_model import QuestModel
from ..models.adventure_model import AdventureModel
from ..models.mini_boss_model import MiniBossModel


class PostgresHeroRepository(HeroRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, hero_id: UUID) -> Optional[Hero]:
        stmt = select(HeroModel).where(HeroModel.id == hero_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_email(self, email: str) -> Optional[Hero]:
        stmt = select(HeroModel).where(HeroModel.email == email.strip().lower())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, hero: Hero) -> Hero:
        stmt = select(HeroModel).where(HeroModel.id == hero.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = HeroModel(
                id=hero.id,
                email=hero.email.strip().lower(),
                name=hero.name,
                avatar_url=hero.avatar_url,
                guild_id=hero.guild_id,
                hero_class=hero.hero_class.value,
                level=hero.level,
                experience=hero.experience,
                gold=hero.gold,
                health=hero.health,
                max_health=hero.max_health,
                mana=hero.mana,
                max_mana=hero.max_mana,
                strength=hero.stats.strength,
                intelligence=hero.stats.intelligence,
                constitution=hero.stats.constitution,
                perception=hero.stats.perception,
                unlocked_skins=hero.unlocked_skins,
            )
            self.session.add(model)
        else:
            model.name = hero.name
            model.avatar_url = hero.avatar_url
            model.guild_id = hero.guild_id
            model.hero_class = hero.hero_class.value
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
            model.unlocked_skins = hero.unlocked_skins

        await self.session.flush()
        return hero

    async def list_by_guild(self, guild_id: UUID) -> List[Hero]:
        stmt = select(HeroModel).where(HeroModel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: HeroModel) -> Hero:
        return Hero(
            id=model.id,
            email=model.email,
            name=model.name,
            avatar_url=model.avatar_url,
            guild_id=model.guild_id,
            hero_class=HeroClass(model.hero_class),
            level=model.level,
            experience=model.experience,
            gold=model.gold,
            health=model.health,
            max_health=model.max_health,
            mana=getattr(model, "mana", 100) or 100,
            max_mana=getattr(model, "max_mana", 100) or 100,
            stats=HeroStats(
                strength=model.strength,
                intelligence=model.intelligence,
                constitution=model.constitution,
                perception=model.perception,
            ),
            unlocked_skins=getattr(model, "unlocked_skins", []) or [],
        )


class PostgresGuildRepository(GuildRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, guild_id: UUID) -> Optional[Guild]:
        stmt = select(GuildModel).where(GuildModel.id == guild_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        members = await self._get_member_ids(model.id)
        return self._to_domain(model, members)

    async def get_by_name(self, name: str) -> Optional[Guild]:
        stmt = select(GuildModel).where(GuildModel.name == name.strip())
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        members = await self._get_member_ids(model.id)
        return self._to_domain(model, members)

    async def save(self, guild: Guild) -> Guild:
        stmt = select(GuildModel).where(GuildModel.id == guild.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = GuildModel(
                id=guild.id,
                name=guild.name,
                description=guild.description,
                level=guild.level,
                experience=guild.experience,
                treasury_gold=guild.treasury_gold,
                active_adventure_id=guild.active_adventure_id,
                shield_points=guild.shield_points,
                purchased_perks=guild.purchased_perks,
            )
            self.session.add(model)
        else:
            model.name = guild.name
            model.description = guild.description
            model.level = guild.level
            model.experience = guild.experience
            model.treasury_gold = guild.treasury_gold
            model.active_adventure_id = guild.active_adventure_id
            model.shield_points = guild.shield_points
            model.purchased_perks = guild.purchased_perks

        await self.session.flush()
        return guild

    async def list_all(self) -> List[Guild]:
        stmt = select(GuildModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        guilds = []
        for m in models:
            members = await self._get_member_ids(m.id)
            guilds.append(self._to_domain(m, members))
        return guilds

    async def _get_member_ids(self, guild_id: UUID) -> List[UUID]:
        stmt = select(HeroModel.id).where(HeroModel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _to_domain(self, model: GuildModel, member_ids: List[UUID]) -> Guild:
        return Guild(
            id=model.id,
            name=model.name,
            description=model.description,
            level=model.level,
            experience=model.experience,
            treasury_gold=model.treasury_gold,
            active_adventure_id=model.active_adventure_id,
            member_ids=member_ids,
            shield_points=getattr(model, "shield_points", 0) or 0,
            purchased_perks=getattr(model, "purchased_perks", []) or [],
        )


class PostgresQuestRepository(QuestRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, quest_id: UUID) -> Optional[Quest]:
        stmt = select(QuestModel).where(QuestModel.id == quest_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_external_id(self, external_id: str) -> Optional[Quest]:
        stmt = select(QuestModel).where(QuestModel.external_id == external_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, quest: Quest) -> Quest:
        stmt = select(QuestModel).where(QuestModel.id == quest.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = QuestModel(
                id=quest.id,
                external_id=quest.external_id,
                external_source=quest.external_source,
                title=quest.title,
                guild_id=quest.guild_id,
                assignee_hero_id=quest.assignee_hero_id,
                adventure_id=quest.adventure_id,
                quest_type=quest.quest_type.value,
                status=quest.status.value,
                difficulty=quest.difficulty.value,
                is_pair_programming=quest.is_pair_programming,
            )
            self.session.add(model)
        else:
            model.title = quest.title
            model.status = quest.status.value
            model.assignee_hero_id = quest.assignee_hero_id
            model.adventure_id = quest.adventure_id
            model.difficulty = quest.difficulty.value
            model.is_pair_programming = quest.is_pair_programming

        await self.session.flush()
        return quest

    async def list_by_adventure(self, adventure_id: UUID) -> List[Quest]:
        stmt = select(QuestModel).where(QuestModel.adventure_id == adventure_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_guild(self, guild_id: UUID) -> List[Quest]:
        stmt = select(QuestModel).where(QuestModel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

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


class PostgresAdventureRepository(AdventureRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, adventure_id: UUID) -> Optional[Adventure]:
        stmt = select(AdventureModel).where(AdventureModel.id == adventure_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_external_id(self, external_id: str) -> Optional[Adventure]:
        stmt = select(AdventureModel).where(AdventureModel.external_id == external_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, adventure: Adventure) -> Adventure:
        stmt = select(AdventureModel).where(AdventureModel.id == adventure.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = AdventureModel(
                id=adventure.id,
                external_id=adventure.external_id,
                title=adventure.title,
                guild_id=adventure.guild_id,
                total_quests=adventure.total_quests,
                completed_quests=adventure.completed_quests,
                is_completed=adventure.is_completed,
                reward_guild_xp=adventure.reward_guild_xp,
                reward_guild_gold=adventure.reward_guild_gold,
            )
            self.session.add(model)
        else:
            model.title = adventure.title
            model.total_quests = adventure.total_quests
            model.completed_quests = adventure.completed_quests
            model.is_completed = adventure.is_completed
            model.reward_guild_xp = adventure.reward_guild_xp
            model.reward_guild_gold = adventure.reward_guild_gold

        await self.session.flush()
        return adventure

    async def get_active_by_guild(self, guild_id: UUID) -> Optional[Adventure]:
        stmt = select(AdventureModel).where(
            AdventureModel.guild_id == guild_id,
            AdventureModel.is_completed == False,
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: AdventureModel) -> Adventure:
        return Adventure(
            id=model.id,
            external_id=model.external_id,
            title=model.title,
            guild_id=model.guild_id,
            total_quests=model.total_quests,
            completed_quests=model.completed_quests,
            is_completed=model.is_completed,
            reward_guild_xp=model.reward_guild_xp,
            reward_guild_gold=model.reward_guild_gold,
        )


class PostgresMiniBossRepository(MiniBossRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, boss_id: UUID) -> Optional[MiniBoss]:
        stmt = select(MiniBossModel).where(MiniBossModel.id == boss_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_external_id(self, external_id: str) -> Optional[MiniBoss]:
        stmt = select(MiniBossModel).where(MiniBossModel.external_id == external_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, boss: MiniBoss) -> MiniBoss:
        stmt = select(MiniBossModel).where(MiniBossModel.id == boss.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = MiniBossModel(
                id=boss.id,
                external_id=boss.external_id,
                title=boss.title,
                guild_id=boss.guild_id,
                severity=boss.severity.value,
                max_health=boss.max_health,
                current_health=boss.current_health,
                is_defeated=boss.is_defeated,
                bounty_hero_xp=boss.bounty_hero_xp,
                bounty_guild_xp=boss.bounty_guild_xp,
                bounty_gold=boss.bounty_gold,
            )
            self.session.add(model)
        else:
            model.current_health = boss.current_health
            model.is_defeated = boss.is_defeated

        await self.session.flush()
        return boss

    async def list_active_by_guild(self, guild_id: UUID) -> List[MiniBoss]:
        stmt = select(MiniBossModel).where(
            MiniBossModel.guild_id == guild_id,
            MiniBossModel.is_defeated == False,
        )
        result = await self.session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

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
