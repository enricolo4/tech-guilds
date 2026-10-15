import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from starlette.testclient import TestClient

from services.common.events import (
    NATS_SUBJECT_HERO_REGISTERED,
    HeroRegisteredEvent,
)
from services.registration.domain.model.hero import Hero, HeroClass, HeroStats
from services.registration.domain.model.user_claims import UserClaims
from services.registration.domain.ports.primary.register_hero_port import (
    RegisterHeroCommand,
    RegisterHeroResult,
    RegisterHeroPort,
)
from services.registration.domain.ports.secondary.hero_repository import HeroRepository
from services.registration.domain.ports.secondary.sso_port import SSOIdentityPort
from services.registration.domain.ports.secondary.event_publisher_port import EventPublisherPort
from services.registration.domain.use_cases.register_hero import RegisterHeroUseCase

from services.registration.secondary.nats_publisher.jetstream_publisher import (
    NatsJetStreamPublisher,
    InMemoryEventPublisher,
)
from services.registration.secondary.sso.sso_adapter import (
    MultiProviderSSOAdapter,
    MockSSOAdapter,
)
from services.registration.secondary.postgresql.models.hero_model import Base, HeroModel
from services.registration.secondary.postgresql.repositories.postgres_hero_repository import (
    PostgresHeroRepository,
    InMemoryHeroRepository,
)
from services.registration.primary.rest_api.dependencies.container import (
    RegistrationContainer,
    get_register_hero_port,
    get_hero_repository,
    get_sso_port,
    get_event_publisher_port,
)
from services.registration.primary.rest_api.app import app


# -------------------------------------------------------------------------
# Testes do Caso de Uso (Domain / Use Cases)
# -------------------------------------------------------------------------

class TestRegistrationUseCase:
    """Valida as regras de negócio puras do caso de uso de Registro de Herói."""

    @pytest.mark.asyncio
    async def test_direct_registration_success(self):
        repo = InMemoryHeroRepository()
        sso = MockSSOAdapter()
        publisher = InMemoryEventPublisher()
        use_case = RegisterHeroUseCase(hero_repository=repo, sso_port=sso, event_publisher=publisher)

        command = RegisterHeroCommand(
            email="linus@company.local",
            name="Linus Torvalds",
            hero_class="WARRIOR",
            avatar_url="https://avatars.test/linus.png",
        )

        result = await use_case.register(command)

        # 1. Valida resultado
        assert result.is_new_registration is True
        assert result.hero.email == "linus@company.local"
        assert result.hero.name == "Linus Torvalds"
        assert result.hero.hero_class == HeroClass.WARRIOR
        assert result.hero.stats.strength == 15  # 10 base + 5 bônus Warrior
        assert result.hero.avatar_url == "https://avatars.test/linus.png"

        # 2. Valida persistência no repositório
        saved = await repo.get_by_email("linus@company.local")
        assert saved is not None
        assert saved.id == result.hero.id

        # 3. Valida evento emitido no NATS JetStream
        assert len(publisher.published_events) == 1
        event = publisher.published_events[0]
        assert isinstance(event, HeroRegisteredEvent)
        assert event.hero_id == result.hero.id
        assert event.email == "linus@company.local"
        assert event.name == "Linus Torvalds"
        assert event.hero_class == "WARRIOR"
        assert event.level == 1
        assert event.experience == 0
        assert event.gold == 0

    @pytest.mark.asyncio
    async def test_sso_registration_success(self):
        repo = InMemoryHeroRepository()
        sso = MockSSOAdapter()
        sso.set_mock_claims(
            token="google-jwt-valid-token",
            claims=UserClaims(
                email="ada@google.com",
                name="Ada Lovelace",
                provider="google",
                provider_user_id="google-sub-123",
                avatar_url="https://avatars.test/ada.png",
            ),
        )
        publisher = InMemoryEventPublisher()
        use_case = RegisterHeroUseCase(hero_repository=repo, sso_port=sso, event_publisher=publisher)

        command = RegisterHeroCommand(
            sso_token="google-jwt-valid-token",
            sso_provider="google",
            hero_class="MAGE",
        )

        result = await use_case.register(command)

        assert result.is_new_registration is True
        assert result.hero.email == "ada@google.com"
        assert result.hero.name == "Ada Lovelace"
        assert result.hero.hero_class == HeroClass.MAGE
        assert result.hero.stats.intelligence == 15  # 10 base + 5 Mage
        assert len(publisher.published_events) == 1
        assert publisher.published_events[0].email == "ada@google.com"

    @pytest.mark.asyncio
    async def test_registration_idempotency_hero_already_exists(self):
        repo = InMemoryHeroRepository()
        sso = MockSSOAdapter()
        publisher = InMemoryEventPublisher()
        use_case = RegisterHeroUseCase(hero_repository=repo, sso_port=sso, event_publisher=publisher)

        # Cadastro inicial
        cmd1 = RegisterHeroCommand(email="turing@math.org", name="Alan Turing", hero_class="PALADIN")
        res1 = await use_case.register(cmd1)
        assert res1.is_new_registration is True
        assert len(publisher.published_events) == 1

        # Segundo cadastro com o mesmo email
        cmd2 = RegisterHeroCommand(email="turing@math.org", name="Alan Turing Clone", hero_class="MAGE")
        res2 = await use_case.register(cmd2)

        # Deve retornar o herói já existente sem duplicar e sem emitir novo evento
        assert res2.is_new_registration is False
        assert res2.hero.id == res1.hero.id
        assert res2.hero.hero_class == HeroClass.PALADIN
        assert len(publisher.published_events) == 1

    @pytest.mark.asyncio
    async def test_registration_validation_errors(self):
        repo = InMemoryHeroRepository()
        sso = MockSSOAdapter()
        publisher = InMemoryEventPublisher()
        use_case = RegisterHeroUseCase(hero_repository=repo, sso_port=sso, event_publisher=publisher)

        # Sem email
        with pytest.raises(ValueError, match="Email é obrigatório"):
            await use_case.register(RegisterHeroCommand(email="", name="Sem Email"))

        # Sem nome
        with pytest.raises(ValueError, match="Nome é obrigatório"):
            await use_case.register(RegisterHeroCommand(email="test@ok.com", name=""))

    @pytest.mark.asyncio
    async def test_registration_defaults_to_novice(self):
        repo = InMemoryHeroRepository()
        sso = MockSSOAdapter()
        publisher = InMemoryEventPublisher()
        use_case = RegisterHeroUseCase(hero_repository=repo, sso_port=sso, event_publisher=publisher)

        cmd = RegisterHeroCommand(email="novice@dev.local", name="Junior Dev", hero_class=None)
        res = await use_case.register(cmd)
        assert res.hero.hero_class == HeroClass.NOVICE
        assert res.hero.stats.strength == 10
        assert res.hero.stats.intelligence == 10


# -------------------------------------------------------------------------
# Testes do Publisher NATS JetStream e Eventos
# -------------------------------------------------------------------------

class TestNatsJetStreamPublisher:
    """Valida a emissão e serialização de eventos no barramento NATS."""

    @pytest.mark.asyncio
    async def test_in_memory_event_publisher(self):
        publisher = InMemoryEventPublisher()
        event = HeroRegisteredEvent(
            hero_id=uuid4(),
            email="hero@nats.io",
            name="Nats Hero",
            hero_class="WARRIOR",
        )

        await publisher.publish_hero_registered(event)
        assert len(publisher.published_events) == 1
        assert publisher.published_events[0] == event

        publisher.clear()
        assert len(publisher.published_events) == 0

    @pytest.mark.asyncio
    async def test_nats_jetstream_fallback_mode(self):
        # Fallback explícito sem conexão de rede ativa
        publisher = NatsJetStreamPublisher(
            nats_url="nats://non-existent-host:4222",
            fallback_mode=True,
        )
        connected = await publisher.connect()
        assert connected is False

        event = HeroRegisteredEvent(
            hero_id=uuid4(),
            email="fallback@nats.io",
            name="Fallback Hero",
            hero_class="RANGER",
        )
        # Deve publicar em buffer resiliente sem lançar exceção
        await publisher.publish_hero_registered(event)
        assert len(publisher.published_events) == 1
        assert publisher.published_events[0].email == "fallback@nats.io"

    def test_hero_registered_event_serialization(self):
        h_id = uuid4()
        event = HeroRegisteredEvent(
            hero_id=h_id,
            email="event@test.local",
            name="Event Hero",
            hero_class="MAGE",
            avatar_url="https://img.test/1.png",
            level=2,
            experience=150,
            gold=42,
        )

        json_str = event.to_json()
        assert "event@test.local" in json_str
        assert str(h_id) in json_str

        # Reconstrução a partir do JSON
        restored = HeroRegisteredEvent.from_json(json_str)
        assert restored.hero_id == h_id
        assert restored.email == event.email
        assert restored.level == 2
        assert restored.gold == 42

        # Serialização em bytes (formato de rede NATS)
        bytes_payload = event.to_bytes()
        restored_from_bytes = HeroRegisteredEvent.from_bytes(bytes_payload)
        assert restored_from_bytes.hero_id == h_id
        assert restored_from_bytes.email == event.email


# -------------------------------------------------------------------------
# Testes de Persistência (PostgreSQL / SQLite In-Memory)
# -------------------------------------------------------------------------

class TestRepositories:
    """Valida os adaptadores secundários de repositório (Postgres e InMemory)."""

    @pytest.mark.asyncio
    async def test_in_memory_hero_repository_crud(self):
        repo = InMemoryHeroRepository()
        hero = Hero(email="inmem@test.com", name="InMem Hero", hero_class=HeroClass.RANGER)

        # Save
        saved = await repo.save(hero)
        assert saved.id == hero.id

        # Get by id
        by_id = await repo.get_by_id(hero.id)
        assert by_id is not None
        assert by_id.name == "InMem Hero"

        # Get by email
        by_email = await repo.get_by_email("inmem@test.com")
        assert by_email is not None
        assert by_email.id == hero.id

        # Update
        by_id.name = "Updated InMem Hero"
        updated = await repo.update(by_id)
        assert updated.name == "Updated InMem Hero"

        # List all
        all_heroes = await repo.list_all()
        assert len(all_heroes) == 1

    @pytest.mark.asyncio
    async def test_postgres_hero_repository_with_attached_schema(self):
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.execute(text('ATTACH DATABASE ":memory:" AS registration'))
            await conn.run_sync(Base.metadata.create_all)

        session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with session_maker() as session:
            repo = PostgresHeroRepository(session)
            hero = Hero(
                id=uuid4(),
                email="pg@registration.local",
                name="Postgres Hero",
                hero_class=HeroClass.TACTICIAN,
            )

            # Save
            saved = await repo.save(hero)
            await session.commit()
            assert saved.id == hero.id
            assert saved.hero_class == HeroClass.TACTICIAN

            # Get by email
            found = await repo.get_by_email("pg@registration.local")
            assert found is not None
            assert found.name == "Postgres Hero"
            assert found.hero_class == HeroClass.TACTICIAN

            # Get by id
            found_by_id = await repo.get_by_id(hero.id)
            assert found_by_id is not None
            assert found_by_id.id == hero.id

            # Update
            found.name = "Postgres Master"
            updated = await repo.update(found)
            await session.commit()
            assert updated.name == "Postgres Master"

            # List all
            all_heroes = await repo.list_all()
            assert len(all_heroes) == 1
            assert all_heroes[0].name == "Postgres Master"


# -------------------------------------------------------------------------
# Testes da API REST (Primary Driving Adapter)
# -------------------------------------------------------------------------

class TestRegistrationControllerRestApi:
    """Valida as rotas HTTP FastAPI do microsserviço de Registration."""

    @pytest.fixture(autouse=True)
    def setup_container(self):
        repo = InMemoryHeroRepository()
        sso = MockSSOAdapter()
        sso.set_mock_claims(
            token="azure-valid-token",
            claims=UserClaims(
                email="satya@microsoft.com",
                name="Satya Nadella",
                provider="azure",
                provider_user_id="azure-guid-001",
            ),
        )
        publisher = InMemoryEventPublisher()
        RegistrationContainer.configure(
            hero_repository=repo,
            sso_port=sso,
            event_publisher=publisher,
        )
        self.repo = repo
        self.publisher = publisher
        self.client = TestClient(app)

    def test_api_register_hero_direct(self):
        payload = {
            "email": "dev1@habitica.local",
            "name": "Warrior Dev",
            "hero_class": "WARRIOR",
            "avatar_url": "https://img.test/warrior.png",
        }
        response = self.client.post("/registration/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["is_new_registration"] is True
        assert data["hero"]["email"] == "dev1@habitica.local"
        assert data["hero"]["hero_class"] == "WARRIOR"
        assert data["hero"]["stats"]["strength"] == 15
        assert len(self.publisher.published_events) == 1

    def test_api_register_hero_sso(self):
        payload = {
            "sso_token": "azure-valid-token",
            "sso_provider": "azure",
            "hero_class": "PALADIN",
        }
        response = self.client.post("/registration/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["is_new_registration"] is True
        assert data["hero"]["email"] == "satya@microsoft.com"
        assert data["hero"]["name"] == "Satya Nadella"
        assert data["hero"]["hero_class"] == "PALADIN"

    def test_api_register_hero_duplicate(self):
        payload = {"email": "dupe@test.local", "name": "Dupe", "hero_class": "MAGE"}
        res1 = self.client.post("/registration/register", json=payload)
        assert res1.status_code == 201
        assert res1.json()["is_new_registration"] is True

        res2 = self.client.post("/registration/register", json=payload)
        assert res2.status_code == 201
        assert res2.json()["is_new_registration"] is False

    def test_api_register_validation_error(self):
        payload = {"email": "", "name": "No Email"}
        response = self.client.post("/registration/register", json=payload)
        assert response.status_code == 400

    def test_api_get_hero_by_id(self):
        hero = Hero(email="getbyid@test.local", name="GetById", hero_class=HeroClass.RANGER)
        self.repo._storage[hero.id] = hero

        response = self.client.get(f"/registration/heroes/{hero.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(hero.id)
        assert data["email"] == "getbyid@test.local"

    def test_api_get_hero_by_id_not_found(self):
        missing_id = uuid4()
        response = self.client.get(f"/registration/heroes/{missing_id}")
        assert response.status_code == 404

    def test_api_list_heroes(self):
        h1 = Hero(email="h1@test.local", name="Hero 1")
        h2 = Hero(email="h2@test.local", name="Hero 2")
        self.repo._storage[h1.id] = h1
        self.repo._storage[h2.id] = h2

        response = self.client.get("/registration/heroes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_api_health_check(self):
        response = self.client.get("/registration/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "registration"}


# -------------------------------------------------------------------------
# Testes de Conformidade com Arquitetura Hexagonal
# -------------------------------------------------------------------------

class TestHexagonalArchitectureCompliance:
    """Garante adesão estrita ao desacoplamento hexagonal e contratos de portas."""

    def test_use_case_implements_primary_port(self):
        assert issubclass(RegisterHeroUseCase, RegisterHeroPort)

    def test_repositories_implement_secondary_port(self):
        assert issubclass(PostgresHeroRepository, HeroRepository)
        assert issubclass(InMemoryHeroRepository, HeroRepository)

    def test_sso_adapters_implement_secondary_port(self):
        assert issubclass(MultiProviderSSOAdapter, SSOIdentityPort)
        assert issubclass(MockSSOAdapter, SSOIdentityPort)

    def test_nats_publishers_implement_secondary_port(self):
        assert issubclass(NatsJetStreamPublisher, EventPublisherPort)
        assert issubclass(InMemoryEventPublisher, EventPublisherPort)

    def test_container_exposes_ports(self):
        container = RegistrationContainer.get_instance()
        assert isinstance(container.register_hero_port, RegisterHeroPort)
        assert isinstance(container.hero_repo, HeroRepository)
        assert isinstance(container.sso_adapter, SSOIdentityPort)
        assert isinstance(container.event_publisher, EventPublisherPort)

        assert isinstance(get_register_hero_port(), RegisterHeroPort)
        assert isinstance(get_hero_repository(), HeroRepository)
        assert isinstance(get_sso_port(), SSOIdentityPort)
        assert isinstance(get_event_publisher_port(), EventPublisherPort)
