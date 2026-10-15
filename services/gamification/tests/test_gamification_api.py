import pytest
from uuid import uuid4
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from services.gamification.domain.model.hero_progression import (
    HeroProgression,
    HeroProgressionStats,
)
from services.gamification.primary.rest_api.controllers.gamification_controller import (
    router,
)
from services.gamification.primary.rest_api.dependencies.container import (
    GamificationContainer,
    get_gamification_container,
)
from services.gamification.secondary.postgresql.repositories.hero_progression_repository import (
    InMemoryHeroProgressionRepository,
)
from services.gamification.secondary.postgresql.repositories.quest_repository import (
    InMemoryQuestRepository,
)
from services.gamification.secondary.postgresql.repositories.mini_boss_repository import (
    InMemoryMiniBossRepository,
)


@pytest.fixture
def app_with_test_container():
    app = FastAPI()
    app.include_router(router)

    hero_repo = InMemoryHeroProgressionRepository()
    quest_repo = InMemoryQuestRepository()
    boss_repo = InMemoryMiniBossRepository()

    test_container = GamificationContainer(
        hero_repo=hero_repo,
        quest_repo=quest_repo,
        boss_repo=boss_repo,
    )

    app.dependency_overrides[get_gamification_container] = lambda: test_container
    return app, test_container


@pytest.mark.asyncio
async def test_rest_api_card_and_bug_webhooks(app_with_test_container):
    app, container = app_with_test_container
    hero_id = uuid4()
    guild_id = uuid4()

    # Cria herói no repositório
    hero = HeroProgression(
        hero_id=hero_id,
        name="Morgana",
        email="morgana@guild.com",
        hero_class="WARRIOR",
        level=1,
        exp=0,
        gold=10,
        guild_id=guild_id,
    )
    await container.hero_repo.save(hero)

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Card Webhook
        card_payload = {
            "external_id": "LIN-202",
            "external_source": "linear",
            "title": "Configurar Cluster Kubernetes",
            "guild_id": str(guild_id),
            "new_status": "DONE",
            "assignee_email": "morgana@guild.com",
            "difficulty": "HARD",
            "is_pair_programming": False,
        }
        res = await client.post("/gamification/webhooks/card-event", json=card_payload)
        assert res.status_code == 200
        data = res.json()
        assert data["external_id"] == "LIN-202"
        assert data["reward"]["hero_xp"] > 0
        assert data["reward"]["hero_gold"] > 0

        # 2. Bug Webhook (Spawn)
        bug_payload = {
            "external_id": "BUG-101",
            "title": "Memory leak no worker de background",
            "guild_id": str(guild_id),
            "severity": "CRITICAL",
            "is_resolved": False,
        }
        res_bug = await client.post("/gamification/webhooks/bug-event", json=bug_payload)
        assert res_bug.status_code == 200
        bug_data = res_bug.json()
        assert bug_data["is_defeated"] is False
        assert bug_data["max_health"] == 400

        # 3. Cast Skill
        skill_payload = {
            "hero_id": str(hero_id),
            "skill_id": "BRUTAL_REFACTOR",
            "target_boss_id": bug_data["mini_boss_id"],
        }
        res_skill = await client.post("/gamification/skills/cast", json=skill_payload)
        assert res_skill.status_code == 200
        skill_data = res_skill.json()
        assert skill_data["success"] is True
        assert skill_data["damage_dealt"] > 0

        # 4. Get Hero Progression
        res_prog = await client.get(f"/gamification/heroes/{hero_id}/progression")
        assert res_prog.status_code == 200
        prog_data = res_prog.json()
        assert prog_data["name"] == "Morgana"
        assert prog_data["gold"] > 10
