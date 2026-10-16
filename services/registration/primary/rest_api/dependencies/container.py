import os
from typing import Optional

from services.registration.domain.ports.primary.register_hero_port import RegisterHeroPort
from services.registration.domain.ports.secondary.hero_repository import HeroRepository
from services.registration.domain.ports.secondary.sso_port import SSOIdentityPort
from services.registration.domain.ports.secondary.event_publisher_port import EventPublisherPort
from services.registration.domain.use_cases.register_hero import RegisterHeroUseCase
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.registration.secondary.postgresql.database import get_db_session
from services.registration.secondary.postgresql.repositories.postgres_hero_repository import (
    PostgresHeroRepository,
    InMemoryHeroRepository,
)
from services.registration.secondary.sso.sso_adapter import MultiProviderSSOAdapter
from services.registration.secondary.nats_publisher.jetstream_publisher import (
    NatsJetStreamPublisher,
    InMemoryEventPublisher,
)


class RegistrationContainer:
    """Container de Injeção de Dependências para o microsserviço de Registration.
    Expõe formalmente as Portas Primárias e Secundárias para os controladores FastAPI.
    """
    _instance: Optional["RegistrationContainer"] = None

    def __init__(
        self,
        hero_repository: Optional[HeroRepository] = None,
        sso_port: Optional[SSOIdentityPort] = None,
        event_publisher: Optional[EventPublisherPort] = None,
    ):
        # Driven / Secondary Adapters
        self.hero_repo: HeroRepository = hero_repository or InMemoryHeroRepository()
        self.sso_adapter: SSOIdentityPort = sso_port or MultiProviderSSOAdapter()

        use_nats_fallback = os.getenv("TESTING", "false").lower() == "true"
        if event_publisher is not None:
            self.event_publisher: EventPublisherPort = event_publisher
        elif use_nats_fallback:
            self.event_publisher = InMemoryEventPublisher()
        else:
            self.event_publisher = NatsJetStreamPublisher(fallback_mode=False)

        # Driving / Primary Port implementation
        self.register_hero_port: RegisterHeroPort = RegisterHeroUseCase(
            hero_repository=self.hero_repo,
            sso_port=self.sso_adapter,
            event_publisher=self.event_publisher,
        )

    @classmethod
    def get_instance(cls) -> "RegistrationContainer":
        if cls._instance is None:
            cls._instance = RegistrationContainer()
        return cls._instance

    @classmethod
    def configure(
        cls,
        hero_repository: Optional[HeroRepository] = None,
        sso_port: Optional[SSOIdentityPort] = None,
        event_publisher: Optional[EventPublisherPort] = None,
    ) -> "RegistrationContainer":
        cls._instance = RegistrationContainer(
            hero_repository=hero_repository,
            sso_port=sso_port,
            event_publisher=event_publisher,
        )
        return cls._instance

    @classmethod
    def reset_instance(cls) -> "RegistrationContainer":
        cls._instance = RegistrationContainer()
        return cls._instance


def get_container() -> RegistrationContainer:
    return RegistrationContainer.get_instance()


def get_hero_repository(
    session: Optional[AsyncSession] = Depends(get_db_session),
) -> HeroRepository:
    """Injetor FastAPI da Porta Secundária do Repositório de Heróis."""
    if session is not None and os.getenv("TESTING", "false").lower() != "true":
        return PostgresHeroRepository(session)
    return RegistrationContainer.get_instance().hero_repo


def get_register_hero_port(
    repo: HeroRepository = Depends(get_hero_repository),
) -> RegisterHeroPort:
    """Injetor FastAPI da Porta Primária de Registro de Herói."""
    container = RegistrationContainer.get_instance()
    if isinstance(repo, PostgresHeroRepository):
        return RegisterHeroUseCase(
            hero_repository=repo,
            sso_port=container.sso_adapter,
            event_publisher=container.event_publisher,
        )
    return container.register_hero_port


def get_sso_port() -> SSOIdentityPort:
    """Injetor FastAPI da Porta Secundária de SSO."""
    return RegistrationContainer.get_instance().sso_adapter


def get_event_publisher_port() -> EventPublisherPort:
    """Injetor FastAPI da Porta Secundária de Eventos NATS."""
    return RegistrationContainer.get_instance().event_publisher
