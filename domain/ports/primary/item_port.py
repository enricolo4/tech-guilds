from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union
from uuid import UUID
from ...model.hero import Hero
from ...model.item import Equipment, EquipmentSlot


@dataclass
class EquipItemCommand:
    hero_id: UUID
    equipment: Equipment


@dataclass
class EquipItemResult:
    hero: Hero
    equipped_item: Equipment
    unequipped_item: Optional[Equipment] = None


@dataclass
class UnequipItemCommand:
    hero_id: UUID
    slot: Union[EquipmentSlot, str]


@dataclass
class UnequipItemResult:
    hero: Hero
    unequipped_item: Optional[Equipment] = None


class EquipItemPort(ABC):
    """Porta Primária (Driving/Input Port) para equipar e desequipar itens e armaduras."""

    @abstractmethod
    async def execute(
        self,
        cmd_or_hero_id: Union[EquipItemCommand, UUID],
        equipment: Optional[Equipment] = None,
    ) -> EquipItemResult:
        pass

    @abstractmethod
    async def unequip(
        self,
        cmd_or_hero_id: Union[UnequipItemCommand, UUID],
        slot: Optional[Union[EquipmentSlot, str]] = None,
    ) -> UnequipItemResult:
        pass
