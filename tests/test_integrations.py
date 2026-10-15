import unittest
from uuid import uuid4
from fastapi.testclient import TestClient

from tech_guilds.primary.rest_api.main import app
from tech_guilds.primary.rest_api.dependencies.container import DependencyContainer
from tech_guilds.domain.model.hero import Hero, HeroClass
from tech_guilds.domain.model.guild import Guild
from tech_guilds.domain.model.quest import QuestStatus, QuestDifficulty
from tech_guilds.domain.model.mini_boss import BossSeverity
from tech_guilds.secondary.linear_adapter.linear_parser import LinearWebhookParser
from tech_guilds.secondary.linear_adapter.linear_client import LinearClient
from tech_guilds.secondary.github_adapter.github_parser import GitHubWebhookParser
from tech_guilds.secondary.github_adapter.github_client import (
    GitHubClient,
    verify_github_signature,
)
from tech_guilds.secondary.slack_adapter.slack_notifier import (
    SlackNotificationAdapter,
    build_progress_bar,
)
from tech_guilds.secondary.discord_adapter.discord_notifier import (
    DiscordNotificationAdapter,
    build_discord_progress_bar,
)


class TestIntegrationsAndWebhooks(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Reinicia o container de dependências para cada teste
        self.container = DependencyContainer.reset_instance()
        self.client = TestClient(app)

    # =========================================================================
    # 1. TESTES DO ADAPTADOR LINEAR (Parser e Client)
    # =========================================================================

    def test_linear_webhook_parser_issue_states(self):
        # 1. State: Todo / Backlog
        payload_todo = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "lin-1",
                "identifier": "ENG-101",
                "title": "Implementar Cache Redis",
                "state": {"name": "Backlog", "type": "backlog"},
                "assignee": {"name": "Alice", "email": "alice@company.local"},
                "labels": [{"name": "Feature"}],
                "estimate": 2,
            },
        }
        event_todo = LinearWebhookParser.parse(payload_todo)
        self.assertEqual(event_todo.status, QuestStatus.TODO)
        self.assertEqual(event_todo.difficulty, QuestDifficulty.EASY)
        self.assertFalse(event_todo.is_bug)
        self.assertEqual(event_todo.assignee_email, "alice@company.local")

        # 2. State: In Progress
        payload_progress = {
            "action": "update",
            "type": "Issue",
            "data": {
                "id": "lin-1",
                "identifier": "ENG-101",
                "title": "Implementar Cache Redis",
                "state": {"name": "In Progress", "type": "started"},
            },
        }
        event_progress = LinearWebhookParser.parse(payload_progress)
        self.assertEqual(event_progress.status, QuestStatus.IN_PROGRESS)

        # 3. State: In Review
        payload_review = {
            "action": "update",
            "type": "Issue",
            "data": {
                "id": "lin-1",
                "identifier": "ENG-101",
                "title": "Implementar Cache Redis",
                "state": {"name": "In Review", "type": "in_review"},
            },
        }
        event_review = LinearWebhookParser.parse(payload_review)
        self.assertEqual(event_review.status, QuestStatus.IN_REVIEW)

        # 4. State: Done
        payload_done = {
            "action": "update",
            "type": "Issue",
            "data": {
                "id": "lin-1",
                "identifier": "ENG-101",
                "title": "Implementar Cache Redis",
                "state": {"name": "Done", "type": "completed"},
            },
        }
        event_done = LinearWebhookParser.parse(payload_done)
        self.assertEqual(event_done.status, QuestStatus.DONE)
        self.assertTrue(event_done.is_resolved)

        # 5. State: Canceled
        payload_canceled = {
            "action": "update",
            "type": "Issue",
            "data": {
                "id": "lin-1",
                "identifier": "ENG-101",
                "title": "Implementar Cache Redis",
                "state": {"name": "Canceled", "type": "canceled"},
            },
        }
        event_canceled = LinearWebhookParser.parse(payload_canceled)
        self.assertEqual(event_canceled.status, QuestStatus.CANCELLED)

    def test_linear_webhook_parser_bug_and_severity(self):
        payload_bug = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "bug-99",
                "identifier": "BUG-99",
                "title": "Falha crítica no cluster de banco de dados",
                "priority": 1,
                "labels": [{"name": "Bug"}, {"name": "p0"}],
                "assignee": {"name": "SRE Hero", "email": "sre@company.local"},
                "state": {"name": "Todo", "type": "unstarted"},
            },
        }
        event = LinearWebhookParser.parse(payload_bug)
        self.assertTrue(event.is_bug)
        self.assertEqual(event.severity, BossSeverity.CRITICAL)
        self.assertFalse(event.is_resolved)

    def test_linear_webhook_parser_cycle_project_and_coop(self):
        payload = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "lin-200",
                "identifier": "ENG-200",
                "title": "Migração de Arquitetura",
                "description": "Tarefa realizada com pareamento entre backend e devops.",
                "project": {"id": "proj-1", "name": "Épico Modernização"},
                "cycle": {"id": "cyc-5", "number": 5, "name": "Sprint 5"},
                "labels": [{"name": "pair-programming"}],
                "estimate": 8,
            },
        }
        event = LinearWebhookParser.parse(payload)
        self.assertEqual(event.project_name, "Épico Modernização")
        self.assertEqual(event.cycle_number, 5)
        self.assertEqual(event.cycle_name, "Sprint 5")
        self.assertTrue(event.is_pair_programming)
        self.assertEqual(event.difficulty, QuestDifficulty.HARD)

    async def test_linear_client_mock_and_queries(self):
        async with LinearClient(api_key="mock") as client:
            issue_res = await client.get_issue("issue-123")
            self.assertIn("data", issue_res)
            self.assertEqual(issue_res["data"]["issue"]["identifier"], "LIN-101")

            update_res = await client.update_issue_status("issue-123", "state-done")
            self.assertTrue(update_res["data"]["issueUpdate"]["success"])

            proj_res = await client.get_project("proj-abc")
            self.assertEqual(proj_res["data"]["project"]["name"], "Épico Linear Mock")

            viewer_res = await client.get_viewer()
            self.assertEqual(viewer_res["data"]["viewer"]["name"], "Tech Guild Master")

    # =========================================================================
    # 2. TESTES DO ADAPTADOR GITHUB (Parser e Client)
    # =========================================================================

    def test_github_webhook_parser_pull_request_opened_and_merged(self):
        # PR Aberto
        payload_opened = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "feat: Gateway Pix",
                "body": "Suporte a pagamento instantâneo",
                "merged": False,
                "user": {"login": "arthur_dev", "email": "arthur@company.local"},
                "additions": 120,
                "deletions": 10,
            },
        }
        event_opened = GitHubWebhookParser.parse(payload_opened, event_header="pull_request")
        self.assertEqual(event_opened.event_type, "pull_request")
        self.assertEqual(event_opened.identifier, "GH-PR-42")
        self.assertEqual(event_opened.status, QuestStatus.IN_REVIEW)
        self.assertEqual(event_opened.difficulty, QuestDifficulty.EASY)

        # PR Mergeado (Concluído)
        payload_merged = {
            "action": "closed",
            "pull_request": {
                "number": 42,
                "title": "feat: Gateway Pix",
                "merged": True,
                "user": {"login": "arthur_dev", "email": "arthur@company.local"},
            },
        }
        event_merged = GitHubWebhookParser.parse(payload_merged, event_header="pull_request")
        self.assertEqual(event_merged.status, QuestStatus.DONE)
        self.assertTrue(event_merged.is_merged)

    def test_github_webhook_parser_code_review_guardian_blessing(self):
        # Review Aprovado
        payload_approved = {
            "action": "submitted",
            "review": {
                "id": 1001,
                "state": "approved",
                "body": "Código excelente e bem coberto por testes!",
                "user": {"login": "galahad_paladin", "email": "galahad@company.local"},
            },
            "pull_request": {
                "number": 42,
                "title": "feat: Gateway Pix",
            },
        }
        event_approved = GitHubWebhookParser.parse(payload_approved, event_header="pull_request_review")
        self.assertEqual(event_approved.event_type, "pull_request_review")
        self.assertTrue(event_approved.is_review_approved)
        self.assertEqual(event_approved.reviewer_login, "galahad_paladin")
        self.assertEqual(event_approved.reviewer_email, "galahad@company.local")

        # Review com comentário (não aprovado)
        payload_commented = {
            "action": "submitted",
            "review": {"state": "commented", "user": {"login": "reviewer"}},
            "pull_request": {"number": 42, "title": "feat: Gateway Pix"},
        }
        event_commented = GitHubWebhookParser.parse(payload_commented, event_header="pull_request_review")
        self.assertFalse(event_commented.is_review_approved)

    def test_github_webhook_parser_issues_bug_lifecycle(self):
        # Issue Bug Aberta
        payload_bug_open = {
            "action": "opened",
            "issue": {
                "number": 88,
                "title": "[Bug] Timeout na autenticação OAuth2",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "p1"}],
                "user": {"login": "qa_tester", "email": "qa@company.local"},
            },
        }
        event_open = GitHubWebhookParser.parse(payload_bug_open, event_header="issues")
        self.assertTrue(event_open.is_bug)
        self.assertEqual(event_open.severity, BossSeverity.HIGH)
        self.assertFalse(event_open.is_resolved)

        # Issue Bug Fechada
        payload_bug_closed = {
            "action": "closed",
            "issue": {
                "number": 88,
                "title": "[Bug] Timeout na autenticação OAuth2",
                "state": "closed",
                "labels": [{"name": "bug"}],
                "closed_by": {"login": "solver_dev", "email": "solver@company.local"},
            },
        }
        event_closed = GitHubWebhookParser.parse(payload_bug_closed, event_header="issues")
        self.assertTrue(event_closed.is_resolved)
        self.assertEqual(event_closed.resolver_email, "solver@company.local")

    def test_github_signature_verification(self):
        import hmac, hashlib
        secret = "super_webhook_secret_key"
        payload = b'{"action":"opened"}'
        expected_sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

        # Válida
        self.assertTrue(verify_github_signature(payload, expected_sig, secret))
        # Inválida
        self.assertFalse(verify_github_signature(payload, "sha256=invalidhash", secret))
        # Ausente
        self.assertFalse(verify_github_signature(payload, None, secret))

    async def test_github_client_mock_methods(self):
        async with GitHubClient(token="mock") as client:
            pr = await client.get_pull_request("org", "repo", 42)
            self.assertEqual(pr["number"], 42)

            issue = await client.get_issue("org", "repo", 88)
            self.assertEqual(issue["number"], 88)

            comment = await client.add_comment("org", "repo", 42, "LGTM!")
            self.assertEqual(comment["body"], "LGTM!")

            labels = await client.add_labels("org", "repo", 42, ["rpg-rewarded"])
            self.assertEqual(labels[0]["name"], "rpg-rewarded")

    # =========================================================================
    # 3. TESTES DO ADAPTADOR SLACK (Block Kit e RPG Features)
    # =========================================================================

    async def test_slack_block_kit_boss_spawned_and_defeated(self):
        adapter = SlackNotificationAdapter()
        guild_id = uuid4()

        # 1. Mini-Boss Spawned
        await adapter.notify_boss_spawned(guild_id, "Demônio do Memory Leak", "CRITICAL", "BUG-666")
        payload = adapter.last_payload
        self.assertIsNotNone(payload)
        self.assertIn("blocks", payload)
        blocks = payload["blocks"]

        # Verifica Header
        header = blocks[0]
        self.assertEqual(header["type"], "header")
        self.assertIn("MINI-BOSS DETECTADO", header["text"]["text"])

        # Verifica Fields
        fields_section = blocks[2]
        self.assertEqual(fields_section["type"], "section")
        fields_text = "".join([f["text"] for f in fields_section["fields"]])
        self.assertIn("Demônio do Memory Leak", fields_text)
        self.assertIn("P0 - CRÍTICO", fields_text)

        # Verifica Ações e Botões
        actions = blocks[3]
        self.assertEqual(actions["type"], "actions")
        buttons = actions["elements"]
        self.assertEqual(len(buttons), 2)
        self.assertIn("Atacar Boss", buttons[0]["text"]["text"])
        self.assertEqual(buttons[0]["style"], "danger")

        # 2. Mini-Boss Defeated
        await adapter.notify_boss_defeated(guild_id, "Demônio do Memory Leak", "Lancelot")
        payload_defeated = adapter.last_payload
        self.assertIn("VITÓRIA", payload_defeated["blocks"][0]["text"]["text"])
        fields_defeated = "".join([f["text"] for f in payload_defeated["blocks"][2]["fields"]])
        self.assertIn("Lancelot", fields_defeated)

    async def test_slack_block_kit_level_up_and_blessing(self):
        adapter = SlackNotificationAdapter()
        guild_id = uuid4()

        # Level Up
        await adapter.notify_level_up(guild_id, "Merlin", 5, "MAGE")
        p_lvl = adapter.last_payload
        self.assertIn("LEVEL UP", p_lvl["blocks"][0]["text"]["text"])
        self.assertIn("Merlin", p_lvl["blocks"][1]["text"]["text"])

        # Guardian Blessing
        await adapter.notify_guardian_blessing(guild_id, "Galahad", 50, "feat: Payment Gateway")
        p_bless = adapter.last_payload
        self.assertIn("BÊNÇÃO DO GUARDIÃO", p_bless["blocks"][0]["text"]["text"])
        self.assertIn("Galahad", p_bless["blocks"][1]["text"]["text"])

    def test_build_progress_bar_helper(self):
        # 100%
        self.assertEqual(build_progress_bar(100, 100, length=10), "[██████████] 100%")
        # 50%
        self.assertEqual(build_progress_bar(50, 100, length=10), "[█████░░░░░] 50%")
        # 0%
        self.assertEqual(build_progress_bar(0, 100, length=10), "[░░░░░░░░░░] 0%")

    # =========================================================================
    # 4. TESTES DO ADAPTADOR DISCORD (Rich Embeds e Cores)
    # =========================================================================

    async def test_discord_embed_notifications(self):
        adapter = DiscordNotificationAdapter()
        guild_id = uuid4()

        # 1. Boss Spawned (Crítico - Vermelho)
        await adapter.notify_boss_spawned(guild_id, "Dragon of Deadlocks", "CRITICAL", "BUG-900")
        p_boss = adapter.last_payload
        embed_boss = p_boss["embeds"][0]
        self.assertEqual(embed_boss["color"], DiscordNotificationAdapter.COLOR_CRITICAL)
        self.assertIn("ALERTA", embed_boss["title"])
        self.assertIn("Dragon of Deadlocks", embed_boss["fields"][0]["value"])

        # 2. Boss Defeated (Vitória - Verde)
        await adapter.notify_boss_defeated(guild_id, "Dragon of Deadlocks", "Perceval")
        p_def = adapter.last_payload
        embed_def = p_def["embeds"][0]
        self.assertEqual(embed_def["color"], DiscordNotificationAdapter.COLOR_VICTORY)
        self.assertIn("VITÓRIA", embed_def["title"])
        self.assertIn("Perceval", embed_def["fields"][1]["value"])

        # 3. Level Up (Púrpura)
        await adapter.notify_level_up(guild_id, "Kay", 4, "PALADIN")
        p_lvl = adapter.last_payload
        embed_lvl = p_lvl["embeds"][0]
        self.assertEqual(embed_lvl["color"], DiscordNotificationAdapter.COLOR_LEVEL_UP)
        self.assertIn("Nível 4", embed_lvl["fields"][1]["value"])

        # 4. Guardian Blessing (Blurple)
        await adapter.notify_guardian_blessing(guild_id, "Kay", 60, "fix: Race condition")
        p_bless = adapter.last_payload
        embed_bless = p_bless["embeds"][0]
        self.assertEqual(embed_bless["color"], DiscordNotificationAdapter.COLOR_GUARDIAN)
        self.assertIn("+60 EXP", embed_bless["fields"][1]["value"])

    # =========================================================================
    # 5. TESTES END-TO-END DE ROTAS FASTAPI (/webhooks/linear e /webhooks/github)
    # =========================================================================

    async def test_api_linear_webhook_quest_lifecycle(self):
        # Cria guilda e herói no repositório
        guild = Guild(name="Squad Linear Alpha")
        await self.container.guild_repo.save(guild)

        hero = Hero(email="dev.linear@company.local", name="Linear Hero")
        await self.container.hero_repo.save(hero)

        # 1. Evento de criação de Issue no Linear (Feature / Quest)
        create_payload = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "lin-card-1",
                "identifier": "ALPHA-10",
                "title": "Criar Módulo de Autenticação",
                "state": {"name": "In Progress", "type": "started"},
                "assignee": {"name": "Linear Hero", "email": "dev.linear@company.local"},
                "labels": [{"name": "Feature"}],
                "estimate": 3,
            },
        }
        res_create = self.client.post(
            f"/webhooks/linear?guild_id={guild.id}",
            json=create_payload,
        )
        self.assertEqual(res_create.status_code, 200)
        data_create = res_create.json()
        self.assertTrue(data_create["success"])
        self.assertEqual(data_create["event_type"], "LINEAR_CARD")

        # 2. Evento de conclusão de Issue no Linear (Done -> concede XP!)
        done_payload = {
            "action": "update",
            "type": "Issue",
            "data": {
                "id": "lin-card-1",
                "identifier": "ALPHA-10",
                "title": "Criar Módulo de Autenticação",
                "state": {"name": "Done", "type": "completed"},
                "assignee": {"name": "Linear Hero", "email": "dev.linear@company.local"},
                "labels": [{"name": "Feature"}],
                "estimate": 3,
            },
        }
        res_done = self.client.post(
            f"/webhooks/linear?guild_id={guild.id}",
            json=done_payload,
        )
        self.assertEqual(res_done.status_code, 200)
        data_done = res_done.json()
        self.assertTrue(data_done["success"])
        self.assertGreater(data_done["reward_hero_xp"], 0)
        self.assertGreater(data_done["reward_guild_xp"], 0)

        # Verifica persistência de XP no herói
        updated_hero = await self.container.hero_repo.get_by_email("dev.linear@company.local")
        self.assertGreater(updated_hero.experience, 0)

    async def test_api_linear_webhook_bug_lifecycle(self):
        guild = Guild(name="Squad Linear Beta")
        await self.container.guild_repo.save(guild)

        hero = Hero(email="bug.buster@company.local", name="Bug Buster")
        await self.container.hero_repo.save(hero)

        # 1. Bug criado no Linear -> Spawna MiniBoss
        spawn_payload = {
            "action": "create",
            "type": "Issue",
            "data": {
                "id": "lin-bug-50",
                "identifier": "BUG-50",
                "title": "Erro 500 no checkout ao aplicar cupom",
                "priority": 1,
                "labels": [{"name": "Bug"}],
                "state": {"name": "Todo", "type": "unstarted"},
            },
        }
        res_spawn = self.client.post(
            f"/webhooks/linear?guild_id={guild.id}",
            json=spawn_payload,
        )
        self.assertEqual(res_spawn.status_code, 200)
        data_spawn = res_spawn.json()
        self.assertEqual(data_spawn["event_type"], "LINEAR_BUG")
        self.assertIn("invadiu a Guilda", data_spawn["message"])

        # Verifica se o boss foi criado
        boss = await self.container.boss_repo.get_by_external_id("BUG-50")
        self.assertIsNotNone(boss)
        self.assertFalse(boss.is_defeated)

        # 2. Bug marcado como Done -> Derrota o MiniBoss e concede Bounty
        defeat_payload = {
            "action": "update",
            "type": "Issue",
            "data": {
                "id": "lin-bug-50",
                "identifier": "BUG-50",
                "title": "Erro 500 no checkout ao aplicar cupom",
                "priority": 1,
                "labels": [{"name": "Bug"}],
                "state": {"name": "Done", "type": "completed"},
                "assignee": {"name": "Bug Buster", "email": "bug.buster@company.local"},
            },
        }
        res_defeat = self.client.post(
            f"/webhooks/linear?guild_id={guild.id}",
            json=defeat_payload,
        )
        self.assertEqual(res_defeat.status_code, 200)
        data_defeat = res_defeat.json()
        self.assertEqual(data_defeat["event_type"], "LINEAR_BUG")
        self.assertIn("derrotado", data_defeat["message"])
        self.assertGreater(data_defeat["reward_hero_xp"], 0)

        # Verifica se o boss está morto e o herói recebeu recompensa
        boss_after = await self.container.boss_repo.get_by_external_id("BUG-50")
        self.assertTrue(boss_after.is_defeated)
        hero_after = await self.container.hero_repo.get_by_email("bug.buster@company.local")
        self.assertGreater(hero_after.experience, 0)

    async def test_api_github_webhook_pull_request_flow(self):
        guild = Guild(name="Squad GitHub")
        await self.container.guild_repo.save(guild)

        hero = Hero(email="octo.dev@company.local", name="Octo Dev")
        await self.container.hero_repo.save(hero)

        # 1. PR Aberto -> Quest em Review
        pr_open_payload = {
            "action": "opened",
            "pull_request": {
                "number": 77,
                "title": "feat: Nova Dashboard de Métricas",
                "merged": False,
                "user": {"login": "octo_dev", "email": "octo.dev@company.local"},
            },
        }
        res_open = self.client.post(
            f"/webhooks/github?guild_id={guild.id}",
            headers={"X-GitHub-Event": "pull_request"},
            json=pr_open_payload,
        )
        self.assertEqual(res_open.status_code, 200)
        self.assertEqual(res_open.json()["event_type"], "GITHUB_PULL_REQUEST")

        # 2. PR Mergeado -> Quest Concluída e Recompensada
        pr_merge_payload = {
            "action": "closed",
            "pull_request": {
                "number": 77,
                "title": "feat: Nova Dashboard de Métricas",
                "merged": True,
                "user": {"login": "octo_dev", "email": "octo.dev@company.local"},
            },
        }
        res_merge = self.client.post(
            f"/webhooks/github?guild_id={guild.id}",
            headers={"X-GitHub-Event": "pull_request"},
            json=pr_merge_payload,
        )
        self.assertEqual(res_merge.status_code, 200)
        data_merge = res_merge.json()
        self.assertGreater(data_merge["reward_hero_xp"], 0)

    async def test_api_github_webhook_guardian_blessing_review(self):
        guild = Guild(name="Squad Guardians")
        await self.container.guild_repo.save(guild)

        reviewer = Hero(email="guardian.paladin@company.local", name="Sir Guardian")
        await self.container.hero_repo.save(reviewer)

        review_payload = {
            "action": "submitted",
            "review": {
                "id": 9999,
                "state": "approved",
                "body": "Revisão detalhada, código limpo!",
                "user": {"login": "guardian_paladin", "email": "guardian.paladin@company.local"},
            },
            "pull_request": {
                "number": 88,
                "title": "refactor: Core domain logic",
            },
        }

        res_review = self.client.post(
            f"/webhooks/github?guild_id={guild.id}",
            headers={"X-GitHub-Event": "pull_request_review"},
            json=review_payload,
        )
        self.assertEqual(res_review.status_code, 200)
        data_review = res_review.json()
        self.assertEqual(data_review["event_type"], "GITHUB_CODE_REVIEW")
        self.assertIn("Bênção do Guardião", data_review["message"])
        self.assertGreater(data_review["reward_hero_xp"], 0)

        # Verifica se o revisor recebeu o XP
        updated_reviewer = await self.container.hero_repo.get_by_email("guardian.paladin@company.local")
        self.assertGreater(updated_reviewer.experience, 0)

    async def test_api_github_webhook_issue_bug_flow(self):
        guild = Guild(name="Squad Issue Testers")
        await self.container.guild_repo.save(guild)

        # 1. Issue com label bug criada -> MiniBoss
        open_bug_payload = {
            "action": "opened",
            "issue": {
                "number": 12,
                "title": "Crash inesperado ao carregar perfil",
                "labels": [{"name": "bug"}, {"name": "critical"}],
                "user": {"login": "tester"},
            },
        }
        res_open = self.client.post(
            f"/webhooks/github?guild_id={guild.id}",
            headers={"X-GitHub-Event": "issues"},
            json=open_bug_payload,
        )
        self.assertEqual(res_open.status_code, 200)
        self.assertEqual(res_open.json()["event_type"], "GITHUB_BUG")

        # 2. Issue fechada -> MiniBoss derrotado
        hero = Hero(email="fixer@company.local", name="Fixer Hero")
        await self.container.hero_repo.save(hero)

        close_bug_payload = {
            "action": "closed",
            "issue": {
                "number": 12,
                "title": "Crash inesperado ao carregar perfil",
                "labels": [{"name": "bug"}],
                "closed_by": {"login": "fixer", "email": "fixer@company.local"},
            },
        }
        res_close = self.client.post(
            f"/webhooks/github?guild_id={guild.id}",
            headers={"X-GitHub-Event": "issues"},
            json=close_bug_payload,
        )
        self.assertEqual(res_close.status_code, 200)
        self.assertEqual(res_close.json()["event_type"], "GITHUB_BUG")
        self.assertIn("derrotado", res_close.json()["message"])


if __name__ == "__main__":
    unittest.main()
