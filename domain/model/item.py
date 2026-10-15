from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from .hero import HeroClass, HeroStats


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
    """Item base do inventário do Herói ou da Guilda."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    price: int = 0
    item_type: ItemType = ItemType.EQUIPMENT


@dataclass
class Equipment(Item):
    """Equipamento que pode ser empunhado/vestido por um Herói, concedendo bônus aos HeroStats."""
    slot: EquipmentSlot = EquipmentSlot.WEAPON
    bonus_stats: HeroStats = field(default_factory=HeroStats.empty)
    required_level: int = 1
    allowed_class: Optional[HeroClass] = None

    def __post_init__(self):
        self.item_type = ItemType.EQUIPMENT


# Helper factory functions para criação de equipamentos
def create_weapon(
    name: str,
    description: str,
    price: int = 50,
    strength: int = 0,
    intelligence: int = 0,
    constitution: int = 0,
    perception: int = 0,
    required_level: int = 1,
    allowed_class: Optional[HeroClass] = None,
) -> Equipment:
    return Equipment(
        name=name,
        description=description,
        price=price,
        slot=EquipmentSlot.WEAPON,
        bonus_stats=HeroStats(
            strength=strength,
            intelligence=intelligence,
            constitution=constitution,
            perception=perception,
        ),
        required_level=required_level,
        allowed_class=allowed_class,
    )


def create_armor(
    name: str,
    description: str,
    price: int = 50,
    strength: int = 0,
    intelligence: int = 0,
    constitution: int = 0,
    perception: int = 0,
    required_level: int = 1,
    allowed_class: Optional[HeroClass] = None,
) -> Equipment:
    return Equipment(
        name=name,
        description=description,
        price=price,
        slot=EquipmentSlot.ARMOR,
        bonus_stats=HeroStats(
            strength=strength,
            intelligence=intelligence,
            constitution=constitution,
            perception=perception,
        ),
        required_level=required_level,
        allowed_class=allowed_class,
    )


def create_shield(
    name: str,
    description: str,
    price: int = 50,
    strength: int = 0,
    intelligence: int = 0,
    constitution: int = 0,
    perception: int = 0,
    required_level: int = 1,
    allowed_class: Optional[HeroClass] = None,
) -> Equipment:
    return Equipment(
        name=name,
        description=description,
        price=price,
        slot=EquipmentSlot.SHIELD,
        bonus_stats=HeroStats(
            strength=strength,
            intelligence=intelligence,
            constitution=constitution,
            perception=perception,
        ),
        required_level=required_level,
        allowed_class=allowed_class,
    )


def create_charm(
    name: str,
    description: str,
    price: int = 50,
    strength: int = 0,
    intelligence: int = 0,
    constitution: int = 0,
    perception: int = 0,
    required_level: int = 1,
    allowed_class: Optional[HeroClass] = None,
) -> Equipment:
    return Equipment(
        name=name,
        description=description,
        price=price,
        slot=EquipmentSlot.CHARM,
        bonus_stats=HeroStats(
            strength=strength,
            intelligence=intelligence,
            constitution=constitution,
            perception=perception,
        ),
        required_level=required_level,
        allowed_class=allowed_class,
    )
