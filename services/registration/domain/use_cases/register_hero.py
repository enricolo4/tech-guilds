from uuid import uuid4
from services.common.events import HeroRegisteredEvent
from services.common.tenant import resolve_tenant_id
from services.registration.domain.model.hero import Hero, HeroClass, HeroStats
from services.registration.domain.ports.primary.register_hero_port import (
    RegisterHeroCommand,
    RegisterHeroResult,
    RegisterHeroPort,
)
from services.registration.domain.ports.secondary.hero_repository import HeroRepository
from services.registration.domain.ports.secondary.sso_port import SSOIdentityPort
from services.registration.domain.ports.secondary.event_publisher_port import EventPublisherPort


class RegisterHeroUseCase(RegisterHeroPort):
    """Caso de uso de cadastro/onboarding de Herói.
    Implementa formalmente a porta primária RegisterHeroPort.
    """

    def __init__(
        self,
        hero_repository: HeroRepository,
        sso_port: SSOIdentityPort,
        event_publisher: EventPublisherPort,
    ):
        self._hero_repository = hero_repository
        self._sso_port = sso_port
        self._event_publisher = event_publisher

    async def register(self, command: RegisterHeroCommand) -> RegisterHeroResult:
        # 1. Resolução de identidade (SSO ou cadastro direto)
        claims_tenant_id = None
        if command.sso_token and command.sso_provider:
            try:
                claims = await self._sso_port.verify_token(command.sso_token, command.sso_provider)
                email = claims.email or command.email
                name = command.name or claims.name
                avatar_url = command.avatar_url or claims.avatar_url
                claims_tenant_id = getattr(claims, "tenant_id", None)
            except Exception as e:
                if command.email and "@" in command.email:
                    email = command.email
                    name = command.name or command.email.split("@")[0].capitalize()
                    avatar_url = command.avatar_url
                else:
                    raise e
        else:
            email = command.email
            name = command.name
            avatar_url = command.avatar_url

        if not email or not email.strip():
            raise ValueError("Email é obrigatório para cadastro.")
        if not name or not name.strip():
            raise ValueError("Nome é obrigatório para cadastro.")

        email = email.strip().lower()
        name = name.strip()

        tenant_id = resolve_tenant_id(
            email=email,
            explicit_tenant_id=command.tenant_id or (claims_tenant_id if claims_tenant_id != "default" else None),
        )

        # 2. Idempotência / Verificação de existência prévia dentro do Tenant
        existing_hero = await self._hero_repository.get_by_email(email, tenant_id=tenant_id)
        if existing_hero is not None:
            return RegisterHeroResult(
                hero=existing_hero,
                is_new_registration=False,
                message="Herói já cadastrado no sistema.",
            )

        # 3. Definição da classe inicial do Herói
        hero_class = HeroClass.NOVICE
        if command.hero_class:
            raw_class = command.hero_class.upper().strip()
            try:
                hero_class = HeroClass(raw_class)
            except ValueError:
                hero_class = HeroClass.NOVICE

        # 4. Criação da instância de domínio
        new_hero = Hero(
            id=uuid4(),
            email=email,
            name=name,
            tenant_id=tenant_id,
            avatar_url=avatar_url,
            hero_class=HeroClass.NOVICE,
            stats=HeroStats(),
        )
        if hero_class != HeroClass.NOVICE:
            new_hero.assign_class(hero_class)

        # 5. Persistência via porta secundária
        saved_hero = await self._hero_repository.save(new_hero)

        # 6. Disparo do evento de domínio no NATS JetStream com isolamento por tenant
        event = HeroRegisteredEvent(
            hero_id=saved_hero.id,
            email=saved_hero.email,
            name=saved_hero.name,
            hero_class=saved_hero.hero_class.value if hasattr(saved_hero.hero_class, "value") else str(saved_hero.hero_class),
            tenant_id=saved_hero.tenant_id,
            avatar_url=saved_hero.avatar_url,
            level=saved_hero.level,
            experience=saved_hero.experience,
            gold=saved_hero.gold,
        )
        await self._event_publisher.publish_hero_registered(event)

        return RegisterHeroResult(
            hero=saved_hero,
            is_new_registration=True,
            message="Herói cadastrado com sucesso.",
        )

