import os
from typing import Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)
from services.gamification.domain.ports.secondary.quest_repository import (
    QuestRepository,
)
from services.gamification.domain.ports.secondary.mini_boss_repository import (
    MiniBossRepository,
)
from services.gamification.secondary.postgresql.repositories.hero_progression_repository import (
    PostgresHeroProgressionRepository,
    InMemoryHeroProgressionRepository,
)
from services.gamification.secondary.postgresql.repositories.quest_repository import (
    PostgresQuestRepository,
    InMemoryQuestRepository,
)
from services.gamification.secondary.postgresql.repositories.mini_boss_repository import (
    PostgresMiniBossRepository,
    InMemoryMiniBossRepository,
)
from services.gamification.secondary.postgresql.database import get_db_session
from services.gamification.domain.use_cases.sync_hero_progression import (
    SyncHeroProgressionUseCase,
)
from services.gamification.domain.use_cases.process_card_event import (
    ProcessCardEventUseCase,
)
from services.gamification.domain.use_cases.process_bug_event import (
    ProcessBugEventUseCase,
)
from services.gamification.domain.use_cases.cast_skill import (
    CastSkillUseCase,
)
from services.gamification.domain.use_cases.equip_item import (
    EquipItemUseCase,
)


class GamificationContainer:
    """Contêiner de injeção de dependências para o microsserviço de Gamificação."""

    def __init__(
        self,
        hero_repo: HeroProgressionRepository,
        quest_repo: QuestRepository,
        boss_repo: MiniBossRepository,
    ):
        self.hero_repo = hero_repo
        self.quest_repo = quest_repo
        self.boss_repo = boss_repo

        self.sync_hero_progression = SyncHeroProgressionUseCase(hero_repo)
        self.process_card_event = ProcessCardEventUseCase(quest_repo, hero_repo)
        self.process_bug_event = ProcessBugEventUseCase(boss_repo, hero_repo)
        self.cast_skill = CastSkillUseCase(hero_repo, boss_repo)
        self.equip_item = EquipItemUseCase(hero_repo)


# Singleton in-memory para testes ou modo sem banco relacional
_in_memory_container: Optional[GamificationContainer] = None


def get_in_memory_container() -> GamificationContainer:
    global _in_memory_container
    if _in_memory_container is None:
        _in_memory_container = GamificationContainer(
            hero_repo=InMemoryHeroProgressionRepository(),
            quest_repo=InMemoryQuestRepository(),
            boss_repo=InMemoryMiniBossRepository(),
        )
    return _in_memory_container


def get_gamification_container(
    session: Optional[AsyncSession] = Depends(get_db_session),
) -> GamificationContainer:
    """Dependency do FastAPI para obter o contêiner conectado à sessão do PostgreSQL ou InMemory."""
    if session is None or os.getenv("TESTING", "false").lower() == "true":
        return get_in_memory_container()

    return GamificationContainer(
        hero_repo=PostgresHeroProgressionRepository(session),
        quest_repo=PostgresQuestRepository(session),
        boss_repo=PostgresMiniBossRepository(session),
    )
