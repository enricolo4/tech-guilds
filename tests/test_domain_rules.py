import unittest
from tech_guilds.domain.model.hero import Hero, HeroClass
from tech_guilds.domain.model.guild import Guild
from tech_guilds.domain.model.quest import Quest, QuestStatus, QuestDifficulty
from tech_guilds.domain.model.adventure import Adventure
from tech_guilds.domain.model.mini_boss import MiniBoss, BossSeverity
from tech_guilds.domain.model.user_claims import UserClaims
from tech_guilds.domain.use_cases.authenticate_hero import AuthenticateHeroUseCase
from tech_guilds.domain.use_cases.process_card_event import ProcessCardEventUseCase, ProcessCardEventCommand
from tech_guilds.domain.use_cases.process_bug_event import ProcessBugEventUseCase, BugEventCommand
from tech_guilds.secondary.postgresql.repositories.repositories_impl import (
    InMemoryHeroRepository,
    InMemoryGuildRepository,
    InMemoryQuestRepository,
    InMemoryAdventureRepository,
    InMemoryMiniBossRepository,
)
from tech_guilds.secondary.slack_adapter.slack_notifier import SlackNotificationAdapter


class TestTechGuildsDomainRules(unittest.IsolatedAsyncioTestCase):

    async def test_hero_progression_and_level_up(self):
        hero = Hero(email="dev@company.com", name="Alice")
        self.assertEqual(hero.level, 1)
        self.assertEqual(hero.experience, 0)

        # EXP necessária para nível 2: 100 * (1 ** 1.5) = 100
        leveled = hero.gain_experience(120)
        self.assertTrue(leveled)
        self.assertEqual(hero.level, 2)
        self.assertEqual(hero.experience, 20)  # 120 - 100 = 20
        self.assertEqual(hero.health, 110)
        self.assertEqual(hero.max_health, 110)

    async def test_quest_pair_programming_coop_buff(self):
        quest_solo = Quest(
            title="Implementar API de Pagamento",
            difficulty=QuestDifficulty.MEDIUM,
            is_pair_programming=False,
        )
        reward_solo = quest_solo.calculate_rewards()

        quest_pair = Quest(
            title="Implementar API de Pagamento",
            difficulty=QuestDifficulty.MEDIUM,
            is_pair_programming=True,
        )
        reward_pair = quest_pair.calculate_rewards()

        # Pair programming dá 30% a mais de EXP individual
        self.assertGreater(reward_pair.hero_xp, reward_solo.hero_xp)
        self.assertEqual(reward_pair.guild_xp, reward_solo.guild_xp)

    async def test_authenticate_hero_auto_provisioning(self):
        hero_repo = InMemoryHeroRepository()

        class MockSSO:
            async def verify_token(self, token: str, provider: str) -> UserClaims:
                return UserClaims(
                    email="bob@company.com",
                    name="Bob Engineer",
                    provider=provider,
                    provider_user_id="12345",
                )

        use_case = AuthenticateHeroUseCase(sso_port=MockSSO(), hero_repo=hero_repo)
        result = await use_case.execute(token="valid_token", provider="google")

        self.assertTrue(result.is_new_player)
        self.assertEqual(result.hero.email, "bob@company.com")
        self.assertEqual(result.hero.hero_class, HeroClass.NOVICE)
        self.assertEqual(result.hero.level, 1)

        # Segunda chamada com o mesmo token não cria novo herói
        result2 = await use_case.execute(token="valid_token", provider="google")
        self.assertFalse(result2.is_new_player)
        self.assertEqual(result2.hero.id, result.hero.id)

    async def test_process_card_event_rewards_hero_and_guild(self):
        hero_repo = InMemoryHeroRepository()
        guild_repo = InMemoryGuildRepository()
        quest_repo = InMemoryQuestRepository()
        adventure_repo = InMemoryAdventureRepository()
        notifier = SlackNotificationAdapter()

        # Cria herói e guilda
        hero = Hero(email="carol@company.com", name="Carol")
        await hero_repo.save(hero)

        guild = Guild(name="Squad Checkout")
        await guild_repo.save(guild)

        # Cria aventura (Épico com 2 quests)
        adv = Adventure(
            external_id="EPIC-10",
            title="Novo Checkout Transparente",
            guild_id=guild.id,
            total_quests=2,
            completed_quests=1,
            reward_guild_xp=500,
        )
        await adventure_repo.save(adv)

        use_case = ProcessCardEventUseCase(
            quest_repo=quest_repo,
            hero_repo=hero_repo,
            guild_repo=guild_repo,
            adventure_repo=adventure_repo,
            notification_port=notifier,
        )

        cmd = ProcessCardEventCommand(
            external_id="LIN-501",
            external_source="linear",
            title="Refatorar gateway de pagamento",
            assignee_email="carol@company.com",
            guild_id=guild.id,
            new_status=QuestStatus.DONE,
            difficulty=QuestDifficulty.HARD,
            is_pair_programming=True,
            adventure_external_id="EPIC-10",
        )

        result = await use_case.execute(cmd)

        self.assertEqual(result.quest.status, QuestStatus.DONE)
        self.assertIsNotNone(result.reward)
        self.assertGreater(result.reward.hero_xp, 0)
        self.assertGreater(result.reward.guild_xp, 0)
        self.assertTrue(result.adventure_completed)  # Era 1 de 2, agora virou 2 de 2!

        # Verifica saldo final do Herói e da Guilda
        updated_hero = await hero_repo.get_by_id(hero.id)
        self.assertGreater(updated_hero.experience, 0)

        updated_guild = await guild_repo.get_by_id(guild.id)
        # Guilda subiu de nível para nível 2 e manteve o excedente de EXP
        self.assertEqual(updated_guild.level, 2)
        self.assertEqual(updated_guild.experience, 60)

    async def test_mini_boss_bug_lifecycle(self):
        boss_repo = InMemoryMiniBossRepository()
        hero_repo = InMemoryHeroRepository()
        guild_repo = InMemoryGuildRepository()
        notifier = SlackNotificationAdapter()

        hero = Hero(email="dave@company.com", name="Dave")
        await hero_repo.save(hero)

        guild = Guild(name="Squad Core")
        await guild_repo.save(guild)

        use_case = ProcessBugEventUseCase(
            boss_repo=boss_repo,
            hero_repo=hero_repo,
            guild_repo=guild_repo,
            notification_port=notifier,
        )

        # 1. Bug aberto -> Spawna o Mini-Boss
        spawn_cmd = BugEventCommand(
            external_id="BUG-999",
            title="Memória vazando no pod do Kubernetes",
            guild_id=guild.id,
            severity=BossSeverity.HIGH,
            is_resolved=False,
        )
        res_spawn = await use_case.execute(spawn_cmd)
        self.assertFalse(res_spawn.is_defeated)
        self.assertEqual(res_spawn.mini_boss.current_health, 200)

        # 2. Bug corrigido -> Derrota o Mini-Boss e dá bounty
        resolve_cmd = BugEventCommand(
            external_id="BUG-999",
            title="Memória vazando no pod do Kubernetes",
            guild_id=guild.id,
            severity=BossSeverity.HIGH,
            is_resolved=True,
            resolver_email="dave@company.com",
        )
        res_resolve = await use_case.execute(resolve_cmd)
        self.assertTrue(res_resolve.is_defeated)
        self.assertEqual(res_resolve.mini_boss.current_health, 0)
        self.assertEqual(res_resolve.bounty_hero_xp, 100)
        self.assertEqual(res_resolve.bounty_guild_xp, 200)

        # O herói ganhou 100 XP e subiu para o nível 2!
        updated_hero = await hero_repo.get_by_id(hero.id)
        self.assertEqual(updated_hero.level, 2)
        self.assertEqual(updated_hero.experience, 0)


if __name__ == "__main__":
    unittest.main()
