from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union
from uuid import UUID
from ...model.hero import Hero
from ...model.guild import Guild
from ...model.shop import ShopItem


@dataclass
class PurchaseShopItemCommand:
    item_id: str
    hero_id: Optional[UUID] = None
    guild_id: Optional[UUID] = None
    use_treasury: bool = False
    custom_item: Optional[ShopItem] = None


@dataclass
class PurchaseShopItemResult:
    item: ShopItem
    hero: Optional[Hero] = None
    guild: Optional[Guild] = None
    paid_from_treasury: bool = False
    gold_spent: int = 0
    message: str = ""


class PurchaseShopItemPort(ABC):
    """Porta Primária (Driving/Input Port) para compra de itens, skins e perks da guilda."""

    @abstractmethod
    async def execute(
        self,
        cmd_or_item_id: Union[PurchaseShopItemCommand, str],
        hero_id: Optional[UUID] = None,
        guild_id: Optional[UUID] = None,
        use_treasury: bool = False,
    ) -> PurchaseShopItemResult:
        pass
