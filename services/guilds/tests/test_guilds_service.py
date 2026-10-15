import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from services.common.events import HeroRegisteredEvent
from services.guilds.domain.model.guild import Guild, SquadLevel, Treasury
from services.guilds.domain.model.guild_member import GuildMember
from services.guilds.domain.ports.primary.guild_ports import (
    AddMemberCommand,
    AddMemberPort,
    CreateGuildCommand,
    CreateGuildPort,
    SyncHeroMemberCommand,
    SyncHeroMemberPort,
)
from services.guilds.domain.use_cases.add_member import AddMemberUseCase
from services.guilds.domain.use_cases.create_guild import CreateGuildUseCase
from services.guilds.domain.use_cases.sync_hero_member import SyncHeroMemberUseCase
from services.guilds.primary.nats_consumer.hero_registered_consumer import HeroRegisteredConsumer
from services.guilds.primary.rest_api.dependencies.container import DependencyContainer
from services.guilds.primary.rest_api.main import create_app
from services.guilds.secondary.postgresql.database import Base
from services.guilds.secondary.postgresql.models.guild_member_model import GuildMemberModel
from services.guilds.secondary.postgresql.models.guild_model import GuildModel
from services.guilds.secondary.postgresql.repositories.postgres_guild_repository import (
    InMemoryGuildMemberRepository,
    InMemoryGuildRepository,
    PostgresGuildMemberRepository,
    PostgresGuildRepository,
)


# =====================================================================
# 1. TESTES DE DOMÍNIO PURO
# =====================================================================
class TestGuildDomain:
    def test_guild_initialization(self):
        guild = Guild(name="Backend Wizards", description="Squad de Arquitetura")
        assert guild.name == "Backend Wizards"
        assert guild.level == 1
        assert guild.experience == 0
        assert guild.treasury_gold == 0
        assert guild.member_ids == []

    def test_treasury_deposit_and_spend(self):
        treasury = Treasury()
        treasury.deposit(100)
        assert treasury.gold == 100

        with pytest.raises(ValueError, match="positivo"):
            treasury.deposit(-10)

        # Gasto com saldo suficiente
        assert treasury.spend(40) is True
        assert treasury.gold == 60

        # Gasto com saldo insuficiente
        assert treasury.spend(100) is False
        assert treasury.gold == 60

        with pytest.raises(ValueError, match="positivo"):
            treasury.spend(0)

    def test_squad_level_progression(self):
        squad_level = SquadLevel(level=1, experience=0)
        # Nível 1 precisa de 500 exp
        assert squad_level.experience_to_next_level == 500

        leveled_up = squad_level.gain_experience(200)
        assert not leveled_up
        assert squad_level.level == 1
        assert squad_level.experience == 200

        leveled_up = squad_level.gain_experience(350)
        assert leveled_up
        assert squad_level.level == 2
        assert squad_level.experience == 50

    def test_guild_members_management(self):
        guild = Guild(name="DevOps Titans")
        hero_id = uuid4()

        guild.add_member(hero_id)
        assert hero_id in guild.member_ids
        # Evita duplicidade
        guild.add_member(hero_id)
        assert len(guild.member_ids) == 1

        guild.remove_member(hero_id)
        assert hero_id not in guild.member_ids

    def test_guild_member_projection(self):
        hero_id = uuid4()
        guild_id = uuid4()
        member = GuildMember(
            hero_id=hero_id,
            name="Alice",
            email="alice@tech.io",
            hero_class="MAGE",
            guild_id=guild_id,
            level=5,
        )
        assert member.hero_id == hero_id
        assert member.guild_id == guild_id

        member.leave_guild()
        assert member.guild_id is None

        new_guild_id = uuid4()
        member.assign_to_guild(new_guild_id)
        assert member.guild_id == new_guild_id


# =====================================================================
# 2. TESTES DE PORTAS PRIMÁRIAS E CASOS DE USO
# =====================================================================
class TestGuildUseCases:
    @pytest.mark.asyncio
    async def test_create_guild_use_case_success(self):
        guild_repo = InMemoryGuildRepository()
        member_repo = InMemoryGuildMemberRepository()
        creator_id = uuid4()

        use_case = CreateGuildUseCase(guild_repository=guild_repo, member_repository=member_repo)
        assert issubclass(CreateGuildUseCase, CreateGuildPort)

        cmd = CreateGuildCommand(
            name="Cloud Guardians",
            description="Protegendo a infraestrutura",
            creator_hero_id=creator_id,
        )
        result = await use_case.execute(cmd)

        assert result.success is True
        assert result.guild.name == "Cloud Guardians"
        assert creator_id in result.guild.member_ids

        # Verifica persistência
        found = await guild_repo.find_by_name("Cloud Guardians")
        assert found is not None
        assert found.id == result.guild.id

    @pytest.mark.asyncio
    async def test_create_guild_duplicate_name_rejected(self):
        guild_repo = InMemoryGuildRepository()
        use_case = CreateGuildUseCase(guild_repository=guild_repo)

        await use_case.execute(CreateGuildCommand(name="QA Ninjas"))
        with pytest.raises(ValueError, match="Já existe uma guilda"):
            await use_case.execute(CreateGuildCommand(name="QA Ninjas"))

    @pytest.mark.asyncio
    async def test_create_guild_empty_name_rejected(self):
        guild_repo = InMemoryGuildRepository()
        use_case = CreateGuildUseCase(guild_repository=guild_repo)

        with pytest.raises(ValueError, match="não pode ser vazio"):
            await use_case.execute(CreateGuildCommand(name="   "))

    @pytest.mark.asyncio
    async def test_add_member_use_case(self):
        guild_repo = InMemoryGuildRepository()
        member_repo = InMemoryGuildMemberRepository()

        # Cria guilda
        guild = await guild_repo.save(Guild(name="Data Guild"))

        # Cadastra projeção de membro
        hero_id = uuid4()
        await member_repo.save(
            GuildMember(hero_id=hero_id, name="Bob", email="bob@tech.io", hero_class="WARRIOR")
        )

        use_case = AddMemberUseCase(guild_repository=guild_repo, member_repository=member_repo)
        assert issubclass(AddMemberUseCase, AddMemberPort)

        result = await use_case.execute(AddMemberCommand(guild_id=guild.id, hero_id=hero_id))
        assert result.success is True

        # Verifica que o herói está na guilda
        updated_guild = await guild_repo.find_by_id(guild.id)
        assert hero_id in updated_guild.member_ids

        # Verifica que a projeção do membro foi atualizada com o guild_id
        updated_member = await member_repo.find_by_hero_id(hero_id)
        assert updated_member.guild_id == guild.id

    @pytest.mark.asyncio
    async def test_sync_hero_member_use_case_insert_and_update(self):
        member_repo = InMemoryGuildMemberRepository()
        use_case = SyncHeroMemberUseCase(member_repository=member_repo)
        assert issubclass(SyncHeroMemberUseCase, SyncHeroMemberPort)

        hero_id = uuid4()

        # 1. Inserção de novo membro
        cmd1 = SyncHeroMemberCommand(
            hero_id=hero_id,
            name="Charlie",
            email="charlie@tech.io",
            hero_class="HEALER",
            avatar_url="https://avatar.io/charlie.png",
            level=1,
        )
        res1 = await use_case.execute(cmd1)
        assert res1.is_new is True
        assert res1.member.name == "Charlie"
        assert res1.member.hero_id == hero_id

        # 2. Atualização de membro existente
        cmd2 = SyncHeroMemberCommand(
            hero_id=hero_id,
            name="Charlie The Great",
            email="charlie@tech.io",
            hero_class="ARCHMAGE",
            avatar_url="https://avatar.io/charlie_archmage.png",
            level=10,
        )
        res2 = await use_case.execute(cmd2)
        assert res2.is_new is False
        assert res2.member.name == "Charlie The Great"
        assert res2.member.hero_class == "ARCHMAGE"
        assert res2.member.level == 10


# =====================================================================
# 3. TESTES DO CONSUMIDOR NATS JETSTREAM
# =====================================================================
class TestHeroRegisteredConsumer:
    @pytest.mark.asyncio
    async def test_handle_hero_registered_event_success(self):
        member_repo = InMemoryGuildMemberRepository()
        sync_port = SyncHeroMemberUseCase(member_repository=member_repo)
        consumer = HeroRegisteredConsumer(sync_port=sync_port)

        hero_id = uuid4()
        event = HeroRegisteredEvent(
            hero_id=hero_id,
            email="artemis@olympus.local",
            name="Artemis Hunter",
            hero_class="RANGER",
            avatar_url="https://olympus.local/artemis.png",
            level=3,
        )

        mock_msg = AsyncMock()
        mock_msg.data = event.to_bytes()

        result = await consumer.handle_message(mock_msg)

        assert result.is_new is True
        assert result.member.hero_id == hero_id
        assert result.member.name == "Artemis Hunter"
        assert result.member.hero_class == "RANGER"
        mock_msg.ack.assert_awaited_once()

        # Verifica projeção gravada
        saved_member = await member_repo.find_by_hero_id(hero_id)
        assert saved_member is not None
        assert saved_member.email == "artemis@olympus.local"

    @pytest.mark.asyncio
    async def test_handle_hero_registered_event_error_nak(self):
        member_repo = InMemoryGuildMemberRepository()
        sync_port = SyncHeroMemberUseCase(member_repository=member_repo)
        consumer = HeroRegisteredConsumer(sync_port=sync_port)

        mock_msg = AsyncMock()
        mock_msg.data = b"INVALID JSON DATA"

        with pytest.raises(Exception):
            await consumer.handle_message(mock_msg)

        mock_msg.nak.assert_awaited_once()


# =====================================================================
# 4. TESTES DA REST API FASTAPI
# =====================================================================
class TestGuildsRestApi:
    @pytest.fixture(autouse=True)
    def setup_container(self):
        self.guild_repo = InMemoryGuildRepository()
        self.member_repo = InMemoryGuildMemberRepository()
        self.container = DependencyContainer(
            guild_repository=self.guild_repo,
            member_repository=self.member_repo,
        )
        DependencyContainer.reset(self.container)
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_check(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "guilds"}

    def test_create_and_get_guild_flow(self):
        # 1. Cria Guilda
        payload = {
            "name": "Frontend Warriors",
            "description": "Focados em UI/UX e Micro-frontends",
        }
        res = self.client.post("/guilds/", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Frontend Warriors"
        assert "id" in data
        guild_id = data["id"]

        # 2. Busca Guilda criada
        get_res = self.client.get(f"/guilds/{guild_id}")
        assert get_res.status_code == 200
        assert get_res.json()["name"] == "Frontend Warriors"

        # 3. Lista Guildas
        list_res = self.client.get("/guilds/")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

    def test_create_guild_duplicate_name_returns_400(self):
        payload = {"name": "SRE Squad", "description": "Confiabilidade"}
        res1 = self.client.post("/guilds/", json=payload)
        assert res1.status_code == 201

        res2 = self.client.post("/guilds/", json=payload)
        assert res2.status_code == 400
        assert "Já existe uma guilda" in res2.json()["detail"]

    def test_add_and_list_members_flow(self):
        # Cria guilda
        create_res = self.client.post("/guilds/", json={"name": "Security Knights"})
        guild_id = create_res.json()["id"]

        hero_id = str(uuid4())
        # Adiciona membro
        add_res = self.client.post(f"/guilds/{guild_id}/members", json={"hero_id": hero_id})
        assert add_res.status_code == 200
        assert add_res.json()["success"] is True

        # Verifica membros
        members_res = self.client.get(f"/guilds/{guild_id}/members")
        assert members_res.status_code == 200


# =====================================================================
# 5. TESTES DE REPOSITÓRIO POSTGRESQL & SCHEMA 'guilds'
# =====================================================================
class TestPostgresRepositoriesAndSchema:
    def test_schema_configuration(self):
        """Verifica se os modelos SQLAlchemy pertencem estritamente ao schema 'guilds'."""
        assert GuildModel.__table_args__ == {"schema": "guilds"}
        assert GuildMemberModel.__table_args__ == {"schema": "guilds"}
        assert GuildModel.__tablename__ == "guilds"
        assert GuildMemberModel.__tablename__ == "members"

    @pytest.mark.asyncio
    async def test_postgres_repositories_integration(self):
        """Testa o ciclo de persistência e consulta nos repositórios SQLAlchemy com schema 'guilds'."""
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.execute(text("ATTACH DATABASE ':memory:' AS guilds"))
            await conn.run_sync(Base.metadata.create_all)

        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            guild_repo = PostgresGuildRepository(session)
            member_repo = PostgresGuildMemberRepository(session)

            # 1. Salva Guilda
            guild = Guild(
                name="Cyber Guild",
                description="Squad de Segurança Ofensiva",
            )
            saved_guild = await guild_repo.save(guild)
            await session.commit()

            assert saved_guild.id == guild.id
            assert saved_guild.name == "Cyber Guild"

            # 2. Salva Projeção de Membro recebida do NATS
            hero_id = uuid4()
            member = GuildMember(
                hero_id=hero_id,
                name="Neo",
                email="neo@matrix.io",
                hero_class="HACKER",
                level=99,
            )
            saved_member = await member_repo.save(member)
            await session.commit()

            assert saved_member.hero_id == hero_id
            assert saved_member.name == "Neo"

            # 3. Associa membro à guilda
            updated_member = await member_repo.update_guild_assignment(
                hero_id=hero_id,
                guild_id=saved_guild.id,
            )
            await session.commit()
            assert updated_member.guild_id == saved_guild.id

            # 4. Consulta membros por guild_id
            members_of_guild = await member_repo.find_by_guild_id(saved_guild.id)
            assert len(members_of_guild) == 1
            assert members_of_guild[0].hero_id == hero_id
            assert members_of_guild[0].name == "Neo"

            # 5. Consulta guilda por nome e por id
            found_by_id = await guild_repo.find_by_id(saved_guild.id)
            assert found_by_id is not None
            assert found_by_id.name == "Cyber Guild"

            found_by_name = await guild_repo.find_by_name("Cyber Guild")
            assert found_by_name is not None
            assert found_by_name.id == saved_guild.id

            # 6. Lista todas as guildas
            all_guilds = await guild_repo.list_all()
            assert len(all_guilds) == 1
