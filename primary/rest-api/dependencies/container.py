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
from tech_guilds.domain.use_cases.authenticate_hero import AuthenticateHeroUseCase
from tech_guilds.domain.use_cases.process_card_event import ProcessCardEventUseCase
from tech_guilds.domain.use_cases.process_bug_event import ProcessBugEventUseCase
from tech_guilds.domain.use_cases.process_code_review import ProcessCodeReviewUseCase


class DependencyContainer:
    """Container singleton para injeção de dependências nos controladores FastAPI."""
    _instance = None

    def __init__(self):
        # Repositórios Secundários
        self.hero_repo = InMemoryHeroRepository()
        self.guild_repo = InMemoryGuildRepository()
        self.quest_repo = InMemoryQuestRepository()
        self.adventure_repo = InMemoryAdventureRepository()
        self.boss_repo = InMemoryMiniBossRepository()

        # Adaptadores de Integração
        self.sso_adapter = MultiProviderSSOAdapter()
        self.notification_adapter = SlackNotificationAdapter()
        self.discord_adapter = DiscordNotificationAdapter()

        # Casos de Uso do Domínio
        self.auth_use_case = AuthenticateHeroUseCase(
            sso_port=self.sso_adapter,
            hero_repo=self.hero_repo,
        )
        self.process_card_use_case = ProcessCardEventUseCase(
            quest_repo=self.quest_repo,
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
            adventure_repo=self.adventure_repo,
            notification_port=self.notification_adapter,
        )
        self.process_bug_use_case = ProcessBugEventUseCase(
            boss_repo=self.boss_repo,
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
            notification_port=self.notification_adapter,
        )
        self.process_code_review_use_case = ProcessCodeReviewUseCase(
            hero_repo=self.hero_repo,
            guild_repo=self.guild_repo,
            notification_port=self.notification_adapter,
        )

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
