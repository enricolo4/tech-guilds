from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Union
from uuid import UUID

from services.gamification.domain.model.hero_progression import HeroProgression
from services.gamification.domain.model.item import Equipment, EquipmentSlot


@dataclass
class EquipItemCommand:
    hero_id: UUID
    equipment: Equipment


@dataclass
class EquipItemResult:
    hero: HeroProgression
    equipped_item: Equipment
    unequipped_item: Any | None = None


@dataclass
class UnequipItemCommand:
    hero_id: UUID
    slot: Union[EquipmentSlot, str]


@dataclass
class UnequipItemResult:
    hero: HeroProgression
    unequipped_item: Any | None = None


class EquipItemPort(ABC):
    """Porta Primária para equipar e desequipar itens e armaduras."""

    @abstractmethod
    async def execute(
        self,
        cmd_or_hero_id: Union[EquipItemCommand, UUID],
        equipment: Equipment | None = None,
    ) -> EquipItemResult:
        pass

    @abstractmethod
    async def unequip(
        self,
        cmd_or_hero_id: Union[UnequipItemCommand, UUID],
        slot: Union[EquipmentSlot, str] | None = None,
    ) -> UnequipItemResult:
        pass
