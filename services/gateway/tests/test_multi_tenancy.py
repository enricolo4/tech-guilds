import pytest
from uuid import uuid4
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.common.tenant import resolve_tenant_id, resolve_organization_name
from services.common.events import HeroRegisteredEvent
from services.auth.primary.rest_api.main import app as auth_app
from services.auth.primary.rest_api.dependencies.container import (
    AuthContainer,
    get_auth_port,
    get_validate_token_port,
)
from services.guilds.primary.rest_api.main import create_app as create_guilds_app
from services.guilds.primary.rest_api.dependencies.container import (
    DependencyContainer as GuildsContainer,
    get_container as get_guilds_container,
)
from services.gamification.primary.rest_api.controllers.gamification_controller import (
    router as gamification_router,
)
from services.gamification.primary.rest_api.dependencies.container import (
    GamificationContainer,
    get_gamification_container,
)
from services.gamification.primary.nats_consumer.hero_registered_consumer import (
    HeroRegisteredConsumer,
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


from services.auth.secondary.postgresql.repositories.postgres_session_repository import (
    InMemorySessionRepository,
)


def test_tenant_resolution_rules():
    """Valida a resolução automática de tenant_id por domínio corporativo, organização explícita ou fallback."""
    # Domínio corporativo
    assert resolve_tenant_id(email="enrico@o2inc.com") == "o2inc.com"
    assert resolve_organization_name("o2inc.com") == "O2Inc"

    # E-mail público com nome de organização explícito
    assert resolve_tenant_id(email="dev@gmail.com", organization_name="O2 Inc.") == "o2-inc"
    assert resolve_organization_name("o2-inc", explicit_name="O2 Inc.") == "O2 Inc."

    # Tenant explícito prevalece
    assert resolve_tenant_id(email="enrico@o2inc.com", explicit_tenant_id="O2_Enterprise") == "o2-enterprise"

    # Fallback default para e-mail público sem organização
    assert resolve_tenant_id(email="solo@gmail.com") == "default"


def test_auth_multi_tenant_jwt_and_isolation():
    """Valida que o serviço de Auth resolve o tenant_id no registro/login e o inclui no JWT."""
    container = AuthContainer(session_repository=InMemorySessionRepository())
    auth_app.dependency_overrides[get_auth_port] = lambda: container.auth_port
    auth_app.dependency_overrides[get_validate_token_port] = lambda: container.validate_token_port
    client = TestClient(auth_app)

    try:
        res_o2 = client.post(
            "/auth/register",
            json={
                "name": "Enrico O2",
                "email": "enrico@o2inc.com",
                "password": "secret-password",
            },
        )
        assert res_o2.status_code == 201
        data_o2 = res_o2.json()
        assert data_o2["tenant_id"] == "o2inc.com"
        assert data_o2["user"]["tenant_id"] == "o2inc.com"

        # Valida que o token carrega o tenant_id
        val_res = client.post("/auth/validate", json={"token": data_o2["access_token"]})
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["is_valid"] is True
        assert val_data["tenant_id"] == "o2inc.com"
    finally:
        auth_app.dependency_overrides.clear()


def test_guilds_multi_tenant_isolation_and_same_squad_name():
    """Duas empresas diferentes (o2inc.com e acme.io) podem ter squads com o mesmo nome e listagens isoladas."""
    container = GuildsContainer()
    GuildsContainer.reset(container)
    app = create_guilds_app()
    app.dependency_overrides[get_guilds_container] = lambda: container
    client = TestClient(app)

    # Cria 'Backend Squad' para o2inc.com
    r1 = client.post(
        "/guilds/",
        json={"name": "Backend Squad", "description": "Squad O2"},
        headers={"X-Tenant-ID": "o2inc.com"},
    )
    assert r1.status_code == 201
    assert r1.json()["tenant_id"] == "o2inc.com"

    # Cria 'Backend Squad' (mesmo nome!) para acme.io -> Deve permitir pois é outro tenant
    r2 = client.post(
        "/guilds/",
        json={"name": "Backend Squad", "description": "Squad Acme"},
        headers={"X-Tenant-ID": "acme.io"},
    )
    assert r2.status_code == 201
    assert r2.json()["tenant_id"] == "acme.io"

    # Tentar criar outro 'Backend Squad' no mesmo tenant (o2inc.com) deve falhar (400)
    r_dup = client.post(
        "/guilds/",
        json={"name": "Backend Squad", "description": "Duplicado O2"},
        headers={"X-Tenant-ID": "o2inc.com"},
    )
    assert r_dup.status_code == 400

    # Listagem filtrada por X-Tenant-ID retorna apenas as guildas daquela empresa
    list_o2 = client.get("/guilds/", headers={"X-Tenant-ID": "o2inc.com"}).json()
    assert len(list_o2) == 1
    assert list_o2[0]["description"] == "Squad O2"

    list_acme = client.get("/guilds/", headers={"X-Tenant-ID": "acme.io"}).json()
    assert len(list_acme) == 1
    assert list_acme[0]["description"] == "Squad Acme"


@pytest.mark.asyncio
async def test_gamification_tenant_scoped_webhooks_and_nats_event():
    """Valida que webhooks SaaS (/webhooks/{tenant_id}/card-event) isolam cards do Linear/Jira por empresa."""
    app = FastAPI()
    app.include_router(gamification_router)

    container = GamificationContainer(
        hero_repo=InMemoryHeroProgressionRepository(),
        quest_repo=InMemoryQuestRepository(),
        boss_repo=InMemoryMiniBossRepository(),
    )
    app.dependency_overrides[get_gamification_container] = lambda: container
    client = TestClient(app)

    hero_o2_id = uuid4()
    hero_acme_id = uuid4()
    guild_o2_id = uuid4()
    guild_acme_id = uuid4()

    nats_consumer = HeroRegisteredConsumer(container.sync_hero_progression)

    # Sincroniza heróis via NATS consumer carregando tenant_id
    await nats_consumer.process_event(
        HeroRegisteredEvent(
            hero_id=hero_o2_id,
            name="Enrico O2",
            email="enrico@o2inc.com",
            hero_class="WARRIOR",
            tenant_id="o2inc.com",
        )
    )
    await nats_consumer.process_event(
        HeroRegisteredEvent(
            hero_id=hero_acme_id,
            name="Alice Acme",
            email="alice@acme.io",
            hero_class="MAGE",
            tenant_id="acme.io",
        )
    )

    # Ambas as empresas enviam um card com o mesmo ID 'LIN-101' em seus respectivos webhooks de tenant
    w_o2 = client.post(
        "/gamification/webhooks/o2inc.com/card-event",
        json={
            "external_id": "LIN-101",
            "external_source": "linear",
            "title": "O2 Multi-Tenant Architecture",
            "guild_id": str(guild_o2_id),
            "new_status": "DONE",
            "assignee_email": "enrico@o2inc.com",
            "difficulty": "HARD",
        },
    )
    assert w_o2.status_code == 200
    assert w_o2.json()["tenant_id"] == "o2inc.com"
    assert w_o2.json()["reward"]["hero_xp"] > 0

    w_acme = client.post(
        "/gamification/webhooks/acme.io/card-event",
        json={
            "external_id": "LIN-101",
            "external_source": "linear",
            "title": "Acme Billing Integration",
            "guild_id": str(guild_acme_id),
            "new_status": "IN_PROGRESS",
            "assignee_email": "alice@acme.io",
            "difficulty": "MEDIUM",
        },
    )
    assert w_acme.status_code == 200
    assert w_acme.json()["tenant_id"] == "acme.io"

    # Verifica isolamento na listagem de quests por tenant
    quests_o2 = client.get("/gamification/quests", headers={"X-Tenant-ID": "o2inc.com"}).json()
    assert len(quests_o2) == 1
    assert quests_o2[0]["title"] == "O2 Multi-Tenant Architecture"

    quests_acme = client.get("/gamification/quests", headers={"X-Tenant-ID": "acme.io"}).json()
    assert len(quests_acme) == 1
    assert quests_acme[0]["title"] == "Acme Billing Integration"
