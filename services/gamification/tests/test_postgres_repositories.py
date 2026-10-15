import unittest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from services.gamification.domain.model.hero_progression import (
    HeroProgression,
    HeroProgressionStats,
)
from services.gamification.domain.model.quest import (
    Quest,
    QuestStatus,
    QuestDifficulty,
    QuestType,
)
from services.gamification.domain.model.mini_boss import (
    MiniBoss,
    BossSeverity,
)
from services.gamification.secondary.postgresql.database import init_models
from services.gamification.secondary.postgresql.repositories.hero_progression_repository import (
    PostgresHeroProgressionRepository,
)
from services.gamification.secondary.postgresql.repositories.quest_repository import (
    PostgresQuestRepository,
)
from services.gamification.secondary.postgresql.repositories.mini_boss_repository import (
    PostgresMiniBossRepository,
)


class TestPostgresRepositoriesIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        await init_models(self.engine)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_postgres_hero_progression_repository(self):
        async with self.session_maker() as session:
            repo = PostgresHeroProgressionRepository(session)
            hero_id = uuid4()
            hero = HeroProgression(
                hero_id=hero_id,
                name="Galahad",
                email="galahad@guild.com",
                hero_class="PALADIN",
                level=3,
                exp=250,
                gold=120,
                hp=120,
                mana=120,
                stats=HeroProgressionStats(strength=12, intelligence=10, constitution=15, perception=11),
            )

            # Save
            saved = await repo.save(hero)
            assert saved.hero_id == hero_id
            assert saved.name == "Galahad"

            # Get by ID
            fetched = await repo.get_by_id(hero_id)
            assert fetched is not None
            assert fetched.name == "Galahad"
            assert fetched.email == "galahad@guild.com"
            assert fetched.stats.constitution == 15

            # Get by Email
            by_email = await repo.get_by_email("galahad@guild.com")
            assert by_email is not None
            assert by_email.hero_id == hero_id

            # Update
            fetched.gold = 300
            updated = await repo.save(fetched)
            assert updated.gold == 300

    async def test_postgres_quest_repository(self):
        async with self.session_maker() as session:
            repo = PostgresQuestRepository(session)
            guild_id = uuid4()
            quest = Quest(
                external_id="LIN-888",
                external_source="linear",
                title="Deploy canary no Kubernetes",
                guild_id=guild_id,
                quest_type=QuestType.FEATURE,
                status=QuestStatus.IN_PROGRESS,
                difficulty=QuestDifficulty.HARD,
            )

            saved = await repo.save(quest)
            assert saved.external_id == "LIN-888"

            fetched = await repo.get_by_external_id("LIN-888")
            assert fetched is not None
            assert fetched.title == "Deploy canary no Kubernetes"

            by_guild = await repo.list_by_guild(guild_id)
            assert len(by_guild) == 1

    async def test_postgres_mini_boss_repository(self):
        async with self.session_maker() as session:
            repo = PostgresMiniBossRepository(session)
            guild_id = uuid4()
            boss = MiniBoss.spawn_from_bug(
                external_id="BUG-777",
                title="Deadlock no banco",
                guild_id=guild_id,
                severity=BossSeverity.CRITICAL,
            )

            saved = await repo.save(boss)
            assert saved.external_id == "BUG-777"
            assert saved.max_health == 400

            active_bosses = await repo.list_active_by_guild(guild_id)
            assert len(active_bosses) == 1

            saved.take_damage(400)
            await repo.save(saved)

            active_bosses_after = await repo.list_active_by_guild(guild_id)
            assert len(active_bosses_after) == 0
