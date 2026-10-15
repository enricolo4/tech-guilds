from typing import Any, Optional, Union
from uuid import UUID

from services.gamification.domain.model.item import Equipment, EquipmentSlot
from services.gamification.domain.ports.primary.equip_item_port import (
    EquipItemPort,
    EquipItemCommand,
    EquipItemResult,
    UnequipItemCommand,
    UnequipItemResult,
)
from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)


class EquipItemUseCase(EquipItemPort):
    """Implementação da Porta Primária para equipar e desequipar itens."""

    def __init__(self, hero_progression_repo: HeroProgressionRepository):
        self.hero_progression_repo = hero_progression_repo

    async def execute(
        self,
        cmd_or_hero_id: Union[EquipItemCommand, UUID],
        equipment: Optional[Equipment] = None,
    ) -> EquipItemResult:
        if isinstance(cmd_or_hero_id, EquipItemCommand):
            hero_id = cmd_or_hero_id.hero_id
            item = cmd_or_hero_id.equipment
        else:
            hero_id = cmd_or_hero_id
            if equipment is None:
                raise ValueError("Equipment must be provided")
            item = equipment

        hero = await self.hero_progression_repo.get_by_id(hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {hero_id} not found")

        old_item = hero.equip(item)
        saved_hero = await self.hero_progression_repo.save(hero)

        return EquipItemResult(
            hero=saved_hero,
            equipped_item=item,
            unequipped_item=old_item,
        )

    async def unequip(
        self,
        cmd_or_hero_id: Union[UnequipItemCommand, UUID],
        slot: Optional[Union[EquipmentSlot, str]] = None,
    ) -> UnequipItemResult:
        if isinstance(cmd_or_hero_id, UnequipItemCommand):
            hero_id = cmd_or_hero_id.hero_id
            target_slot = cmd_or_hero_id.slot
        else:
            hero_id = cmd_or_hero_id
            if slot is None:
                raise ValueError("Slot must be provided")
            target_slot = slot

        hero = await self.hero_progression_repo.get_by_id(hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {hero_id} not found")

        old_item = hero.unequip(target_slot)
        saved_hero = await self.hero_progression_repo.save(hero)

        return UnequipItemResult(
            hero=saved_hero,
            unequipped_item=old_item,
        )
