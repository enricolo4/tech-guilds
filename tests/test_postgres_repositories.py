import unittest
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from tech_guilds.secondary.postgresql.database import Base, init_models
from tech_guilds.secondary.postgresql.repositories.postgres_repositories import (
    PostgresHeroRepository,
    PostgresGuildRepository,
    PostgresQuestRepository,
    PostgresAdventureRepository,
    PostgresMiniBossRepository,
)
from tech_guilds.domain.entities.hero import Hero, HeroClass
from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.entities.quest import Quest, QuestDifficulty, QuestStatus
from tech_guilds.domain.entities.adventure import Adventure
from tech_guilds.domain.entities.mini_boss import MiniBoss, BossSeverity


class TestPostgresRepositoriesIntegration(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Utiliza SQLite assíncrono em memória para testar os repositórios SQLAlchemy
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        await init_models(self.engine)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_guild_and_hero_persistence_lifecycle(self):
        async with self.session_maker() as session:
            guild_repo = PostgresGuildRepository(session)
            hero_repo = PostgresHeroRepository(session)

            # 1. Salva Guilda
            guild = Guild(
                name="Squad Payments",
                description="Squad responsável pelo checkout e faturamento",
            )
            saved_guild = await guild_repo.save(guild)
            await session.commit()

            # 2. Salva Herói associado à guilda
            hero = Hero(
                email="dev.backend@company.com",
                name="Arthur",
                guild_id=saved_guild.id,
                hero_class=HeroClass.WARRIOR_BACKEND,
                level=3,
                gold=150,
            )
            await hero_repo.save(hero)
            await session.commit()

            # 3. Consulta Herói por e-mail
            loaded_hero = await hero_repo.get_by_email("dev.backend@company.com")
            self.assertIsNotNone(loaded_hero)
            self.assertEqual(loaded_hero.name, "Arthur")
            self.assertEqual(loaded_hero.hero_class, HeroClass.WARRIOR_BACKEND)
            self.assertEqual(loaded_hero.level, 3)
            self.assertEqual(loaded_hero.gold, 150)
            self.assertEqual(loaded_hero.guild_id, saved_guild.id)

            # 4. Consulta Guilda por nome
            loaded_guild = await guild_repo.get_by_name("Squad Payments")
            self.assertIsNotNone(loaded_guild)
            self.assertEqual(loaded_guild.name, "Squad Payments")
            self.assertIn(loaded_hero.id, loaded_guild.member_ids)

    async def test_quest_adventure_and_miniboss_persistence(self):
        async with self.session_maker() as session:
            guild_repo = PostgresGuildRepository(session)
            quest_repo = PostgresQuestRepository(session)
            adv_repo = PostgresAdventureRepository(session)
            boss_repo = PostgresMiniBossRepository(session)

            guild = Guild(name="Squad Mobile")
            await guild_repo.save(guild)
            await session.commit()

            # Salva Aventura (Épico)
            adv = Adventure(
                external_id="EPIC-202",
                title="Novo App Mobile iOS e Android",
                guild_id=guild.id,
                total_quests=5,
            )
            await adv_repo.save(adv)
            await session.commit()

            # Salva Quest
            quest = Quest(
                external_id="MOB-10",
                external_source="linear",
                title="Tela de Splash Animada",
                guild_id=guild.id,
                adventure_id=adv.id,
                difficulty=QuestDifficulty.MEDIUM,
                status=QuestStatus.IN_PROGRESS,
            )
            await quest_repo.save(quest)
            await session.commit()

            # Salva MiniBoss
            boss = MiniBoss.spawn_from_bug(
                external_id="BUG-404",
                title="Crash na inicialização no iOS 18",
                guild_id=guild.id,
                severity=BossSeverity.CRITICAL,
            )
            await boss_repo.save(boss)
            await session.commit()

            # Verificações
            loaded_adv = await adv_repo.get_by_external_id("EPIC-202")
            self.assertIsNotNone(loaded_adv)
            self.assertEqual(loaded_adv.title, "Novo App Mobile iOS e Android")

            loaded_quests = await quest_repo.list_by_adventure(adv.id)
            self.assertEqual(len(loaded_quests), 1)
            self.assertEqual(loaded_quests[0].external_id, "MOB-10")

            active_bosses = await boss_repo.list_active_by_guild(guild.id)
            self.assertEqual(len(active_bosses), 1)
            self.assertEqual(active_bosses[0].external_id, "BUG-404")
            self.assertEqual(active_bosses[0].current_health, 400)


if __name__ == "__main__":
    unittest.main()
