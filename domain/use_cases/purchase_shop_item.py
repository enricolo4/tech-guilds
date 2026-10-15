from dataclasses import dataclass
from typing import Optional, Union
from uuid import UUID

from ..model.hero import Hero
from ..model.guild import Guild
from ..model.item import Item, ItemType
from ..model.shop import ShopItem, ShopCategory, PurchaseTarget, get_shop_item
from ..ports.repositories import HeroRepository, GuildRepository


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


class PurchaseShopItemUseCase:
    """Caso de uso de compra no Mercado da Guilda.
    Permite a compra de Equipamentos e Skins pessoais com ouro do Herói,
    ou a aquisição de Perks da Guilda (Coffee Budget, Team Dinner) utilizando o Tesouro da Guilda.
    """
    def __init__(
        self,
        hero_repo: HeroRepository,
        guild_repo: GuildRepository,
    ):
        self.hero_repo = hero_repo
        self.guild_repo = guild_repo

    async def execute(
        self,
        cmd_or_item_id: Union[PurchaseShopItemCommand, str],
        hero_id: Optional[UUID] = None,
        guild_id: Optional[UUID] = None,
        use_treasury: bool = False,
        custom_item: Optional[ShopItem] = None,
    ) -> PurchaseShopItemResult:
        if isinstance(cmd_or_item_id, PurchaseShopItemCommand):
            cmd = cmd_or_item_id
        else:
            cmd = PurchaseShopItemCommand(
                item_id=cmd_or_item_id,
                hero_id=hero_id,
                guild_id=guild_id,
                use_treasury=use_treasury,
                custom_item=custom_item,
            )

        item = cmd.custom_item or get_shop_item(cmd.item_id)
        if item is None:
            raise ValueError(f"Shop item '{cmd.item_id}' not found in catalog")

        is_treasury = cmd.use_treasury or item.target == PurchaseTarget.GUILD_TREASURY

        if is_treasury:
            return await self._purchase_from_treasury(cmd, item)
        else:
            return await self._purchase_for_hero(cmd, item)

    async def _purchase_from_treasury(
        self,
        cmd: PurchaseShopItemCommand,
        item: ShopItem,
    ) -> PurchaseShopItemResult:
        guild = None
        hero = None

        if cmd.guild_id:
            guild = await self.guild_repo.get_by_id(cmd.guild_id)
        elif cmd.hero_id:
            hero = await self.hero_repo.get_by_id(cmd.hero_id)
            if hero and hero.guild_id:
                guild = await self.guild_repo.get_by_id(hero.guild_id)

        if guild is None:
            raise ValueError("Guild must be specified for treasury purchases")

        if guild.treasury_gold < item.price:
            raise ValueError(
                f"Insufficient guild treasury gold: needed {item.price}, available {guild.treasury_gold}"
            )

        # Deduz ouro do tesouro e adiciona perk
        guild.spend_gold(item.price)
        guild.add_perk(item.name or item.item_id)

        # Aplica efeitos coletivos do perk se configurados
        if "guild_xp" in item.effect_data:
            guild.gain_experience(item.effect_data["guild_xp"])
        if "shield" in item.effect_data:
            guild.apply_shield(item.effect_data["shield"])

        await self.guild_repo.save(guild)

        # Se houver efeito pessoal para o herói requisitante (ex: café restaurando mana)
        if cmd.hero_id:
            if hero is None:
                hero = await self.hero_repo.get_by_id(cmd.hero_id)
            if hero and "mana_restore" in item.effect_data:
                hero.restore_mana(item.effect_data["mana_restore"])
                await self.hero_repo.save(hero)

        return PurchaseShopItemResult(
            item=item,
            hero=hero,
            guild=guild,
            paid_from_treasury=True,
            gold_spent=item.price,
            message=f"Perk '{item.name}' adquirido com sucesso pelo Tesouro da Guilda por {item.price} ouro.",
        )

    async def _purchase_for_hero(
        self,
        cmd: PurchaseShopItemCommand,
        item: ShopItem,
    ) -> PurchaseShopItemResult:
        if cmd.hero_id is None:
            raise ValueError("Hero ID must be specified for hero purchases")

        hero = await self.hero_repo.get_by_id(cmd.hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {cmd.hero_id} not found")

        if hero.gold < item.price:
            raise ValueError(
                f"Insufficient hero gold: needed {item.price}, available {hero.gold}"
            )

        # Deduz ouro do herói
        hero.spend_gold(item.price)

        # Entrega o item comprado
        if item.equipment_payload:
            hero.inventory.append(item.equipment_payload)
        elif item.category == ShopCategory.SKIN:
            skin_id = item.effect_data.get("skin_id", item.item_id)
            if skin_id not in hero.unlocked_skins:
                hero.unlocked_skins.append(skin_id)
            if "avatar_url" in item.effect_data:
                hero.avatar_url = item.effect_data["avatar_url"]
        else:
            hero_item = Item(
                name=item.name,
                description=item.description,
                price=item.price,
                item_type=ItemType.CONSUMABLE if item.category == ShopCategory.CONSUMABLE else ItemType.PERK,
            )
            hero.inventory.append(hero_item)

        await self.hero_repo.save(hero)

        return PurchaseShopItemResult(
            item=item,
            hero=hero,
            guild=None,
            paid_from_treasury=False,
            gold_spent=item.price,
            message=f"{hero.name} adquiriu '{item.name}' por {item.price} ouro.",
        )
