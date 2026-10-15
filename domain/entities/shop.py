from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from .hero import HeroClass
from .item import Equipment, create_weapon, create_armor, create_shield, create_charm


class ShopCategory(str, Enum):
    EQUIPMENT = "EQUIPMENT"
    GUILD_PERK = "GUILD_PERK"
    SKIN = "SKIN"
    CONSUMABLE = "CONSUMABLE"


class PurchaseTarget(str, Enum):
    HERO = "HERO"
    GUILD_TREASURY = "GUILD_TREASURY"


@dataclass
class ShopItem:
    """Item ou benefício listado para compra no Mercado da Guilda."""
    id: UUID = field(default_factory=uuid4)
    item_id: str = ""
    name: str = ""
    description: str = ""
    price: int = 0
    category: ShopCategory = ShopCategory.EQUIPMENT
    target: PurchaseTarget = PurchaseTarget.HERO
    equipment_payload: Optional[Equipment] = None
    effect_data: Dict[str, Any] = field(default_factory=dict)


# Guild Treasury Perks (comprados com ouro da Guilda)
PERK_COFFEE_BUDGET = ShopItem(
    item_id="COFFEE_BUDGET",
    name="Coffee Budget",
    description="Crédito mensal de café gourmet para o Squad oxigenar o foco e recuperar mana.",
    price=150,
    category=ShopCategory.GUILD_PERK,
    target=PurchaseTarget.GUILD_TREASURY,
    effect_data={"mana_restore": 30, "morale_boost": 10},
)

PERK_TEAM_DINNER = ShopItem(
    item_id="TEAM_DINNER",
    name="Team Dinner Perk",
    description="Jantar comemorativo de encerramento de sprint ou entrega de épico, concedendo EXP e cura coletiva.",
    price=500,
    category=ShopCategory.GUILD_PERK,
    target=PurchaseTarget.GUILD_TREASURY,
    effect_data={"guild_xp": 300, "heal_squad": 50},
)

# Custom Skins para Heróis
SKIN_CYBERPUNK = ShopItem(
    item_id="SKIN_CYBERPUNK",
    name="Cyberpunk Hacker Skin",
    description="Skin visual néon inspirada em terminais de matriz para o avatar do Herói.",
    price=100,
    category=ShopCategory.SKIN,
    target=PurchaseTarget.HERO,
    effect_data={"skin_id": "cyberpunk_hacker", "avatar_url": "/skins/cyberpunk_hacker.png"},
)

SKIN_DARK_MODE = ShopItem(
    item_id="SKIN_DARK_MODE",
    name="Dark Mode Terminal Skin",
    description="Skin minimalista de console escuro de alta performance para desenvolvedores.",
    price=80,
    category=ShopCategory.SKIN,
    target=PurchaseTarget.HERO,
    effect_data={"skin_id": "dark_mode_terminal", "avatar_url": "/skins/dark_mode_terminal.png"},
)

# Equipamentos disponíveis no Mercado
SHOP_WEAPON_KEYBOARD = ShopItem(
    item_id="WEAPON_MECHANICAL_KEYBOARD",
    name="Mechanical Keyboard of Precision",
    description="Teclado mecânico customizado que eleva o poder de refatoração (+10 STR, +4 INT).",
    price=120,
    category=ShopCategory.EQUIPMENT,
    target=PurchaseTarget.HERO,
    equipment_payload=create_weapon(
        name="Mechanical Keyboard of Precision",
        description="Teclado mecânico customizado (+10 STR, +4 INT)",
        price=120,
        strength=10,
        intelligence=4,
    ),
)

SHOP_ARMOR_HOODIE = ShopItem(
    item_id="ARMOR_HOODIE_CI",
    name="Hoodie of Continuous Integration",
    description="Moletom lendário que protege o desenvolvedor contra incidentes (+12 CON, +3 PER).",
    price=110,
    category=ShopCategory.EQUIPMENT,
    target=PurchaseTarget.HERO,
    equipment_payload=create_armor(
        name="Hoodie of Continuous Integration",
        description="Moletom com capuz e proteções contra incidentes (+12 CON, +3 PER)",
        price=110,
        constitution=12,
        perception=3,
    ),
)

SHOP_SHIELD_DOCKER = ShopItem(
    item_id="SHIELD_DOCKER_CONTAINER",
    name="Docker Container Shield",
    description="Escudo isolado que mitiga falhas em cascata de infraestrutura (+14 CON, +2 STR).",
    price=115,
    category=ShopCategory.EQUIPMENT,
    target=PurchaseTarget.HERO,
    equipment_payload=create_shield(
        name="Docker Container Shield",
        description="Escudo de conteinerização isolada (+14 CON, +2 STR)",
        price=115,
        constitution=14,
        strength=2,
    ),
)

SHOP_CHARM_RUBBER_DUCK = ShopItem(
    item_id="CHARM_RUBBER_DUCK",
    name="Rubber Duck of Debugging",
    description="Amuleto clássico de patinho de borracha para clareza mental e percepção de bugs (+8 PER, +6 INT).",
    price=95,
    category=ShopCategory.EQUIPMENT,
    target=PurchaseTarget.HERO,
    equipment_payload=create_charm(
        name="Rubber Duck of Debugging",
        description="Amuleto clássico de patinho de borracha (+8 PER, +6 INT)",
        price=95,
        perception=8,
        intelligence=6,
    ),
)

SHOP_CATALOG: Dict[str, ShopItem] = {
    "COFFEE_BUDGET": PERK_COFFEE_BUDGET,
    "TEAM_DINNER": PERK_TEAM_DINNER,
    "SKIN_CYBERPUNK": SKIN_CYBERPUNK,
    "SKIN_DARK_MODE": SKIN_DARK_MODE,
    "WEAPON_MECHANICAL_KEYBOARD": SHOP_WEAPON_KEYBOARD,
    "ARMOR_HOODIE_CI": SHOP_ARMOR_HOODIE,
    "SHIELD_DOCKER_CONTAINER": SHOP_SHIELD_DOCKER,
    "CHARM_RUBBER_DUCK": SHOP_CHARM_RUBBER_DUCK,
}


def get_shop_item(item_id_or_name: str) -> Optional[ShopItem]:
    """Busca item do catálogo por ID ou chave formatada."""
    key = item_id_or_name.strip().upper().replace(" ", "_").replace("-", "_")
    return SHOP_CATALOG.get(key)
