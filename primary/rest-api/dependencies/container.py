from tech_guilds.secondary.postgresql.repositories.repositories_impl import (
    InMemoryHeroRepository,
    InMemoryGuildRepository,
    InMemoryQuestRepository,
    InMemoryAdventureRepository,
    InMemoryMiniBossRepository,
)
from tech_guilds.secondary.sso_adapter.multi_provider_sso import MultiProviderSSOAdapter
from tech_guilds.secondary.slack_adapter.slack_notifier import SlackNotificationAdapter
from tech_guilds.secondary.discord_adapter.discord_notifier import DiscordNotificationAdapter

# Portas Primárias (Contratos para adaptadores de entrada REST, Kafka, NATS)
from tech_guilds.domain.ports.primary.auth_port import AuthenticateHeroPort
from tech_guilds.domain.ports.primary.card_event_port import ProcessCardEventPort
from tech_guilds.domain.ports.primary.bug_event_port import ProcessBugEventPort
from tech_guilds.domain.ports.primary.code_review_port import ProcessCodeReviewPort
from tech_guilds.domain.ports.primary.skill_port import CastSkillPort
from tech_guilds.domain.ports.primary.item_port import EquipItemPort
from tech_guilds.domain.ports.primary.shop_port import PurchaseShopItemPort

# Casos de Uso (Implementações das Portas Primárias)
from tech_guilds.domain.use_cases.authenticate_hero import AuthenticateHeroUseCase
from tech_guilds.domain.use_cases.process_card_event import ProcessCardEventUseCase
from tech_guilds.domain.use_cases.process_bug_event import ProcessBugEventUseCase
from tech_guilds.domain.use_cases.process_code_review import ProcessCodeReviewUseCase
from tech_guilds.domain.use_cases.cast_skill import CastSkillUseCase
from tech_guilds.domain.use_cases.equip_item import EquipItemUseCase
from tech_guilds.domain.use_cases.purchase_shop_item import PurchaseShopItemUseCase


class DependencyContainer:
    """Container de injeção de dependências.
    A camada REST e futuros consumidores Kafka/NATS injetam exclusivamente
    as Portas Primárias (Primary Ports) para segregação estrita do domínio.
    """
    _instance = None

    def __init__(self):
        # Repositórios Secundários (Driven)
        self.hero_repo = InMemoryHeroRepository()
        self.guild_repo = InMemoryGuildRepository()
        self.quest_repo = InMemoryQuestRepository()
        self.adventure_repo = InMemoryAdventureRepository()
        self.boss_repo = InMemoryMiniBossRepository()

        # Adaptadores de Notificação e Integração (Secondary Adapters)
        self.sso_adapter = MultiProviderSSOAdapter()
        self.notification_adapter = SlackNotificationAdapter()
        self.discord_adapter = DiscordNotificationAdapter()

        # Portas Primárias / Casos de Uso
        self.auth_port: AuthenticateHeroPort = AuthenticateHeroUseCase(
            sso_port=self.sso_adapter,
            hero_repo=self.hero_repo,
        )
        self.card_event_port: ProcessCardEventPort = ProcessCardEventUseCase(
            quest_repo=self.quest_repo,
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
            adventure_repo=self.adventure_repo,
            notification_port=self.notification_adapter,
        )
        self.bug_event_port: ProcessBugEventPort = ProcessBugEventUseCase(
            boss_repo=self.boss_repo,
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
            notification_port=self.notification_adapter,
        )
        self.code_review_port: ProcessCodeReviewPort = ProcessCodeReviewUseCase(
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
            notification_port=self.notification_adapter,
        )
        self.skill_port: CastSkillPort = CastSkillUseCase(
            hero_repo=self.hero_repo,
            boss_repo=self.boss_repo,
            guild_repo=self.guild_repo,
            notification_port=self.notification_adapter,
        )
        self.item_port: EquipItemPort = EquipItemUseCase(
            hero_repo=self.hero_repo,
        )
        self.shop_port: PurchaseShopItemPort = PurchaseShopItemUseCase(
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
        )

        # Aliases retrocompatíveis
        self.auth_use_case = self.auth_port
        self.process_card_use_case = self.card_event_port
        self.process_bug_use_case = self.bug_event_port
        self.process_code_review_use_case = self.code_review_port

    @classmethod
    def get_instance(cls) -> "DependencyContainer":
        if cls._instance is None:
            cls._instance = DependencyContainer()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> "DependencyContainer":
        cls._instance = DependencyContainer()
        return cls._instance


def get_container() -> DependencyContainer:
    return DependencyContainer.get_instance()


# Dependências FastAPI para injeção direta de Portas Primárias
def get_auth_port() -> AuthenticateHeroPort:
    return DependencyContainer.get_instance().auth_port


def get_card_event_port() -> ProcessCardEventPort:
    return DependencyContainer.get_instance().card_event_port


def get_bug_event_port() -> ProcessBugEventPort:
    return DependencyContainer.get_instance().bug_event_port


def get_code_review_port() -> ProcessCodeReviewPort:
    return DependencyContainer.get_instance().code_review_port


def get_skill_port() -> CastSkillPort:
    return DependencyContainer.get_instance().skill_port


def get_item_port() -> EquipItemPort:
    return DependencyContainer.get_instance().item_port


def get_shop_port() -> PurchaseShopItemPort:
    return DependencyContainer.get_instance().shop_port
