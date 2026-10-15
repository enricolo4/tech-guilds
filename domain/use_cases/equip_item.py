from typing import Any, Optional, Union
from uuid import UUID

from ..model.hero import Hero
from ..model.item import Equipment, EquipmentSlot
from ..ports.primary.item_port import (
    EquipItemPort,
    EquipItemCommand,
    EquipItemResult,
    UnequipItemCommand,
    UnequipItemResult,
)
from ..ports.secondary.repositories import HeroRepository


class EquipItemUseCase(EquipItemPort):
    """Implementação da Porta Primária para gerenciamento de equipamentos de Heróis.
    Equipa itens de Weapon, Armor, Shield e Charm, atualizando instantaneamente os atributos de RPG.
    """
    def __init__(self, hero_repo: HeroRepository):
        self.hero_repo = hero_repo

    async def execute(
        self,
        cmd_or_hero_id: Union[EquipItemCommand, UUID],
        equipment: Optional[Equipment] = None,
    ) -> EquipItemResult:
        if isinstance(cmd_or_hero_id, EquipItemCommand):
            cmd = cmd_or_hero_id
        else:
            if equipment is None:
                raise ValueError("Equipment must be provided")
            cmd = EquipItemCommand(hero_id=cmd_or_hero_id, equipment=equipment)

        hero = await self.hero_repo.get_by_id(cmd.hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {cmd.hero_id} not found")

        # hero.equip valida nível, restrições de classe e atualiza HeroStats
        unequipped = hero.equip(cmd.equipment)
        await self.hero_repo.save(hero)

        return EquipItemResult(
            hero=hero,
            equipped_item=cmd.equipment,
            unequipped_item=unequipped,
        )

    async def unequip(
        self,
        cmd_or_hero_id: Union[UnequipItemCommand, UUID],
        slot: Optional[Union[EquipmentSlot, str]] = None,
    ) -> UnequipItemResult:
        if isinstance(cmd_or_hero_id, UnequipItemCommand):
            cmd = cmd_or_hero_id
        else:
            if slot is None:
                raise ValueError("Slot must be provided")
            cmd = UnequipItemCommand(hero_id=cmd_or_hero_id, slot=slot)

        hero = await self.hero_repo.get_by_id(cmd.hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {cmd.hero_id} not found")

        unequipped = hero.unequip(cmd.slot)
        await self.hero_repo.save(hero)

        return UnequipItemResult(
            hero=hero,
            unequipped_item=unequipped,
        )
