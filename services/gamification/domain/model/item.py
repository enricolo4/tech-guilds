from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional
from uuid import UUID, uuid4


class ItemType(str, Enum):
    EQUIPMENT = "EQUIPMENT"
    PERK = "PERK"
    COSMETIC = "COSMETIC"
    CONSUMABLE = "CONSUMABLE"


class EquipmentSlot(str, Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    SHIELD = "SHIELD"
    CHARM = "CHARM"


@dataclass
class Item:
    """Item base do inventário do Herói."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    price: int = 0
    item_type: ItemType = ItemType.EQUIPMENT


@dataclass
class Equipment(Item):
    """Equipamento que concede bônus de atributos a quem o empunha."""
    slot: EquipmentSlot = EquipmentSlot.WEAPON
    bonus_strength: int = 0
    bonus_intelligence: int = 0
    bonus_constitution: int = 0
    bonus_perception: int = 0
    required_level: int = 1
    allowed_class: Optional[str] = None

    def __post_init__(self):
        self.item_type = ItemType.EQUIPMENT

    @property
    def bonus_stats(self) -> Dict[str, int]:
        return {
            "strength": self.bonus_strength,
            "intelligence": self.bonus_intelligence,
            "constitution": self.bonus_constitution,
            "perception": self.bonus_perception,
        }


def create_equipment(
    name: str,
    description: str,
    slot: EquipmentSlot,
    price: int = 50,
    strength: int = 0,
    intelligence: int = 0,
    constitution: int = 0,
    perception: int = 0,
    required_level: int = 1,
    allowed_class: Optional[str] = None,
) -> Equipment:
    return Equipment(
        name=name,
        description=description,
        price=price,
        slot=slot,
        bonus_strength=strength,
        bonus_intelligence=intelligence,
        bonus_constitution=constitution,
        bonus_perception=perception,
        required_level=required_level,
        allowed_class=allowed_class,
    )
