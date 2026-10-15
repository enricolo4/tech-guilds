import pytest
from unittest.mock import AsyncMock

from tech_guilds.domain.ports.primary import (
    AuthenticateHeroPort,
    AuthenticateHeroResult,
    ProcessCardEventPort,
    ProcessCardEventCommand,
    ProcessCardEventResult,
    ProcessBugEventPort,
    BugEventCommand,
    BugEventResult,
    ProcessCodeReviewPort,
    ProcessCodeReviewCommand,
    ProcessCodeReviewResult,
    CastSkillPort,
    CastSkillCommand,
    CastSkillResult,
    EquipItemPort,
    EquipItemCommand,
    EquipItemResult,
    PurchaseShopItemPort,
    PurchaseShopItemCommand,
    PurchaseShopItemResult,
)
from tech_guilds.domain.use_cases import (
    AuthenticateHeroUseCase,
    ProcessCardEventUseCase,
    ProcessBugEventUseCase,
    ProcessCodeReviewUseCase,
    CastSkillUseCase,
    EquipItemUseCase,
    PurchaseShopItemUseCase,
)
from tech_guilds.primary.rest_api.dependencies.container import (
    DependencyContainer,
    get_auth_port,
    get_card_event_port,
    get_bug_event_port,
    get_code_review_port,
    get_skill_port,
    get_item_port,
    get_shop_port,
)


class TestPortsArchitecture:
    """Valida a conformidade estrita da arquitetura hexagonal em relação às Portas Primárias e Secundárias."""

    def test_use_cases_implement_primary_ports(self):
        """Todo caso de uso deve herdar e implementar formalmente a sua Porta Primária correspondente."""
        assert issubclass(AuthenticateHeroUseCase, AuthenticateHeroPort)
        assert issubclass(ProcessCardEventUseCase, ProcessCardEventPort)
        assert issubclass(ProcessBugEventUseCase, ProcessBugEventPort)
        assert issubclass(ProcessCodeReviewUseCase, ProcessCodeReviewPort)
        assert issubclass(CastSkillUseCase, CastSkillPort)
        assert issubclass(EquipItemUseCase, EquipItemPort)
        assert issubclass(PurchaseShopItemUseCase, PurchaseShopItemPort)

    def test_dependency_container_exposes_primary_ports(self):
        """O container de injeção de dependências deve fornecer as portas primárias tipadas."""
        container = DependencyContainer.get_instance()

        assert isinstance(container.auth_port, AuthenticateHeroPort)
        assert isinstance(container.card_event_port, ProcessCardEventPort)
        assert isinstance(container.bug_event_port, ProcessBugEventPort)
        assert isinstance(container.code_review_port, ProcessCodeReviewPort)
        assert isinstance(container.skill_port, CastSkillPort)
        assert isinstance(container.item_port, EquipItemPort)
        assert isinstance(container.shop_port, PurchaseShopItemPort)

    def test_fastapi_dependency_providers(self):
        """As funções injetoras do FastAPI devem retornar as interfaces das portas primárias."""
        assert isinstance(get_auth_port(), AuthenticateHeroPort)
        assert isinstance(get_card_event_port(), ProcessCardEventPort)
        assert isinstance(get_bug_event_port(), ProcessBugEventPort)
        assert isinstance(get_code_review_port(), ProcessCodeReviewPort)
        assert isinstance(get_skill_port(), CastSkillPort)
        assert isinstance(get_item_port(), EquipItemPort)
        assert isinstance(get_shop_port(), PurchaseShopItemPort)
