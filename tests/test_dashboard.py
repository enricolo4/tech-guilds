import unittest
from uuid import uuid4
from fastapi.testclient import TestClient

from tech_guilds.primary.rest_api.main import app
from tech_guilds.primary.rest_api.dependencies.container import get_container
from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.entities.hero import Hero, HeroClass, HeroStats
from tech_guilds.domain.entities.quest import Quest, QuestStatus, QuestDifficulty, QuestType
from tech_guilds.domain.entities.adventure import Adventure
from tech_guilds.domain.entities.mini_boss import MiniBoss, BossSeverity


class TestDashboardAndUI(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.container = get_container()

    def test_serve_dashboard_html_page(self):
        """Verifica se a rota GET /dashboard entrega o HTML do dashboard com todos os módulos de RPG."""
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        
        html_content = response.text
        # Verifica se os elementos essenciais da UI retrô estão presentes
        self.assertIn("Tech Guilds — Retro RPG Squad Dashboard", html_content)
        self.assertIn("GUILD HEADQUARTERS HEADER", html_content)
        self.assertIn("MINI-BOSS ARENA", html_content)
        self.assertIn("ACTIVE EPIC ADVENTURE", html_content)
        self.assertIn("HALL OF HEROES", html_content)
        self.assertIn("QUEST BOARD", html_content)
        self.assertIn("ARMORY & GUILD SHOP", html_content)
        self.assertIn("LIVE COMBAT LOG", html_content)
        self.assertIn("alpinejs", html_content)
        self.assertIn("tailwindcss", html_content)
        self.assertIn("/dashboard/static/css/retro.css", html_content)

    def test_serve_retro_static_css(self):
        """Verifica se os arquivos estáticos de CSS retrô são servidos corretamente."""
        response = self.client.get("/dashboard/static/css/retro.css")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/css", response.headers.get("content-type", ""))
        self.assertIn("pixel-box", response.text)
        self.assertIn("shake-boss", response.text)
        self.assertIn("--o2-vivid-green", response.text)

    def test_get_dashboard_data_demo_payload(self):
        """Verifica se a rota /dashboard/data/demo retorna um payload completo e rico."""
        response = self.client.get("/dashboard/data/demo")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validação do Guild Header
        self.assertIn("guild", data)
        guild = data["guild"]
        self.assertEqual(guild["name"], "The Byte Crusaders")
        self.assertGreater(guild["level"], 0)
        self.assertGreater(guild["treasury_gold"], 0)
        self.assertIn("experience_percent", guild)

        # Validação do Hall of Heroes
        self.assertIn("heroes", data)
        heroes = data["heroes"]
        self.assertGreaterEqual(len(heroes), 4)
        hero = heroes[0]
        self.assertIn("hero_class", hero)
        self.assertIn("health", hero)
        self.assertIn("max_health", hero)
        self.assertIn("stats", hero)
        self.assertIn("equipped_items", hero)

        # Validação da Mini-Boss Arena
        self.assertIn("active_boss", data)
        boss = data["active_boss"]
        self.assertIsNotNone(boss)
        self.assertEqual(boss["severity"], "CRITICAL")
        self.assertGreater(boss["current_health"], 0)
        self.assertIn("bounty_guild_xp", boss)

        # Validação do Active Adventure / Epic
        self.assertIn("active_adventure", data)
        adv = data["active_adventure"]
        self.assertIsNotNone(adv)
        self.assertGreater(adv["total_quests"], 0)
        self.assertGreater(adv["progress_percentage"], 0)

        # Validação do Quest Board
        self.assertIn("quests", data)
        quests = data["quests"]
        self.assertGreaterEqual(len(quests), 3)
        statuses = {q["status"] for q in quests}
        self.assertTrue({"TODO", "IN_PROGRESS", "IN_REVIEW", "DONE"}.issubset(statuses) or len(statuses) >= 2)

        # Validação da Armory & Shop
        self.assertIn("shop_items", data)
        shop = data["shop_items"]
        self.assertGreaterEqual(len(shop), 4)
        types = {item["type"] for item in shop}
        self.assertIn("weapon", types)
        self.assertIn("skin", types)
        self.assertIn("perk", types)

        # Validação do Combat Log
        self.assertIn("combat_log", data)
        self.assertGreaterEqual(len(data["combat_log"]), 1)

    async def test_get_dashboard_data_live_guild(self):
        """Cria uma guilda completa com heróis, épico, boss e quests no repositório e valida o retorno da API."""
        # 1. Guilda
        guild = Guild(
            name="Shadow Byte Knights",
            description="Core Platform & Microservices Squad",
            level=3,
            experience=250,
            treasury_gold=800,
        )
        saved_guild = await self.container.guild_repo.save(guild)

        # 2. Heróis
        hero1 = Hero(
            name="Merlin Frontend",
            email="merlin@company.com",
            guild_id=saved_guild.id,
            hero_class=HeroClass.MAGE_FRONTEND,
            level=3,
            experience=120,
            health=90,
            max_health=100,
            stats=HeroStats(strength=10, intelligence=22, constitution=12, perception=14),
        )
        await self.container.hero_repo.save(hero1)
        saved_guild.add_member(hero1.id)

        hero2 = Hero(
            name="Arthur Backend",
            email="arthur@company.com",
            guild_id=saved_guild.id,
            hero_class=HeroClass.WARRIOR_BACKEND,
            level=4,
            experience=220,
            health=120,
            max_health=120,
            stats=HeroStats(strength=22, intelligence=11, constitution=18, perception=12),
        )
        await self.container.hero_repo.save(hero2)
        saved_guild.add_member(hero2.id)
        await self.container.guild_repo.save(saved_guild)

        # 3. Mini-Boss
        boss = MiniBoss.spawn_from_bug(
            external_id="BUG-777",
            title="Deadlock em Transações Concorrentes",
            guild_id=saved_guild.id,
            severity=BossSeverity.HIGH,
        )
        boss.take_damage(50)  # Reduz vida para testar porcentagem
        await self.container.boss_repo.save(boss)

        # 4. Aventura / Épico
        adventure = Adventure(
            external_id="EPIC-50",
            title="Decomposição do Monólito em Microsserviços",
            guild_id=saved_guild.id,
            total_quests=5,
            completed_quests=3,
            reward_guild_xp=800,
            reward_guild_gold=300,
        )
        await self.container.adventure_repo.save(adventure)

        # 5. Quests
        q1 = Quest(
            external_id="LIN-801",
            title="Separar domínio de pagamentos",
            guild_id=saved_guild.id,
            adventure_id=adventure.id,
            assignee_hero_id=hero2.id,
            status=QuestStatus.DONE,
            difficulty=QuestDifficulty.HARD,
            is_pair_programming=True,
        )
        await self.container.quest_repo.save(q1)

        q2 = Quest(
            external_id="LIN-802",
            title="Criar BFF para mobile e web",
            guild_id=saved_guild.id,
            adventure_id=adventure.id,
            assignee_hero_id=hero1.id,
            status=QuestStatus.IN_PROGRESS,
            difficulty=QuestDifficulty.MEDIUM,
            is_pair_programming=False,
        )
        await self.container.quest_repo.save(q2)

        # Chamada à API
        response = self.client.get(f"/dashboard/data/{saved_guild.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Validação do Squad
        self.assertEqual(data["guild"]["name"], "Shadow Byte Knights")
        self.assertEqual(data["guild"]["active_members_count"], 2)
        self.assertEqual(data["guild"]["treasury_gold"], 800)
        self.assertGreater(data["guild"]["experience_percent"], 0)

        # Validação dos Heróis
        self.assertEqual(len(data["heroes"]), 2)
        hero_names = {h["name"] for h in data["heroes"]}
        self.assertIn("Merlin Frontend", hero_names)
        self.assertIn("Arthur Backend", hero_names)

        # Validação do Boss
        self.assertIsNotNone(data["active_boss"])
        self.assertEqual(data["active_boss"]["external_id"], "BUG-777")
        self.assertEqual(data["active_boss"]["severity"], "HIGH")
        self.assertEqual(data["active_boss"]["current_health"], 150)
        self.assertEqual(data["active_boss"]["max_health"], 200)
        self.assertEqual(data["active_boss"]["health_percent"], 75.0)

        # Validação do Épico
        self.assertIsNotNone(data["active_adventure"])
        self.assertEqual(data["active_adventure"]["external_id"], "EPIC-50")
        self.assertEqual(data["active_adventure"]["progress_percentage"], 60.0)

        # Validação das Quests
        self.assertEqual(len(data["quests"]), 2)
        q1_data = next(q for q in data["quests"] if q["external_id"] == "LIN-801")
        self.assertEqual(q1_data["status"], "DONE")
        self.assertTrue(q1_data["is_pair_programming"])
        self.assertEqual(q1_data["assignee_name"], "Arthur Backend")

    def test_get_dashboard_data_invalid_and_not_found(self):
        """Verifica tratamento de erros para ID inválido e guilda inexistente."""
        # UUID inexistente
        random_uuid = uuid4()
        res_404 = self.client.get(f"/dashboard/data/{random_uuid}")
        self.assertEqual(res_404.status_code, 404)
        self.assertIn("Guilda não encontrada", res_404.json()["detail"])

        # String não-UUID
        res_400 = self.client.get("/dashboard/data/not-a-valid-uuid")
        self.assertEqual(res_400.status_code, 400)
        self.assertIn("UUID válido", res_400.json()["detail"])


if __name__ == "__main__":
    unittest.main()
