from typing import Any, Dict, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.gamification.domain.model.quest import (
    QuestStatus,
    QuestDifficulty,
)
from services.gamification.domain.model.mini_boss import BossSeverity
from services.gamification.domain.model.item import Equipment, EquipmentSlot
from services.gamification.domain.ports.primary.process_card_event_port import (
    ProcessCardEventCommand,
)
from services.gamification.domain.ports.primary.process_bug_event_port import (
    ProcessBugEventCommand,
)
from services.gamification.domain.ports.primary.cast_skill_port import (
    CastSkillCommand,
)
from services.gamification.domain.ports.primary.equip_item_port import (
    EquipItemCommand,
    UnequipItemCommand,
)
from services.gamification.primary.rest_api.dependencies.container import (
    GamificationContainer,
    get_gamification_container,
)

router = APIRouter(prefix="/gamification", tags=["Gamification"])


# --- Request Schemas ---

class CardEventRequest(BaseModel):
    external_id: str = Field(..., description="ID no Linear/GitHub, ex: LIN-101")
    external_source: str = Field("linear", description="Origem da tarefa: linear, github, jira")
    title: str = Field(..., description="Título da tarefa")
    guild_id: UUID = Field(..., description="ID da Guilda (Squad)")
    new_status: QuestStatus = Field(..., description="Novo status da Quest")
    assignee_email: str | None = None
    assignee_hero_id: UUID | None = None
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False
    adventure_id: UUID | None = None


class BugEventRequest(BaseModel):
    external_id: str = Field(..., description="ID do Bug no tracker, ex: BUG-404")
    title: str = Field(..., description="Descrição / Título do Bug")
    guild_id: UUID = Field(..., description="ID da Guilda impactada")
    severity: BossSeverity = BossSeverity.MEDIUM
    is_resolved: bool = Field(False, description="True se o bug foi fechado/resolvido")
    resolver_email: str | None = None
    resolver_hero_id: UUID | None = None


class CastSkillRequest(BaseModel):
    hero_id: UUID
    skill_id: str
    target_boss_id: UUID | None = None
    target_guild_id: UUID | None = None


class EquipmentRequest(BaseModel):
    name: str
    description: str = ""
    slot: EquipmentSlot = EquipmentSlot.WEAPON
    price: int = 50
    bonus_strength: int = 0
    bonus_intelligence: int = 0
    bonus_constitution: int = 0
    bonus_perception: int = 0
    required_level: int = 1
    allowed_class: str | None = None


class EquipItemRequest(BaseModel):
    hero_id: UUID
    equipment: EquipmentRequest


class UnequipItemRequest(BaseModel):
    hero_id: UUID
    slot: EquipmentSlot


# --- Endpoints ---

@router.post("/webhooks/card-event", summary="Processa webhook de tarefas (Linear/GitHub)")
async def handle_card_event(
    req: CardEventRequest,
    container: GamificationContainer = Depends(get_gamification_container),
):
    cmd = ProcessCardEventCommand(
        external_id=req.external_id,
        external_source=req.external_source,
        title=req.title,
        guild_id=req.guild_id,
        new_status=req.new_status,
        assignee_email=req.assignee_email,
        assignee_hero_id=req.assignee_hero_id,
        difficulty=req.difficulty,
        is_pair_programming=req.is_pair_programming,
        adventure_id=req.adventure_id,
    )
    result = await container.process_card_event.execute(cmd)
    return {
        "quest_id": str(result.quest.id),
        "external_id": result.quest.external_id,
        "status": result.quest.status.value,
        "reward": (
            {
                "hero_xp": result.reward.hero_xp,
                "hero_gold": result.reward.hero_gold,
                "guild_xp": result.reward.guild_xp,
                "guild_gold": result.reward.guild_gold,
            }
            if result.reward
            else None
        ),
        "hero_leveled_up": result.hero_leveled_up,
        "hero_progression": (
            {
                "hero_id": str(result.hero_progression.hero_id),
                "level": result.hero_progression.level,
                "exp": result.hero_progression.exp,
                "gold": result.hero_progression.gold,
            }
            if result.hero_progression
            else None
        ),
    }


@router.post("/webhooks/bug-event", summary="Processa evento de Bug / Incidente (Mini-Boss)")
async def handle_bug_event(
    req: BugEventRequest,
    container: GamificationContainer = Depends(get_gamification_container),
):
    cmd = ProcessBugEventCommand(
        external_id=req.external_id,
        title=req.title,
        guild_id=req.guild_id,
        severity=req.severity,
        is_resolved=req.is_resolved,
        resolver_email=req.resolver_email,
        resolver_hero_id=req.resolver_hero_id,
    )
    result = await container.process_bug_event.execute(cmd)
    return {
        "mini_boss_id": str(result.mini_boss.id),
        "external_id": result.mini_boss.external_id,
        "is_defeated": result.is_defeated,
        "current_health": result.mini_boss.current_health,
        "max_health": result.mini_boss.max_health,
        "bounty_hero_xp": result.bounty_hero_xp,
        "bounty_gold": result.bounty_gold,
        "hero_leveled_up": result.hero_leveled_up,
    }


@router.post("/skills/cast", summary="Conjura habilidade especial consumindo mana")
async def cast_skill_endpoint(
    req: CastSkillRequest,
    container: GamificationContainer = Depends(get_gamification_container),
):
    try:
        cmd = CastSkillCommand(
            hero_id=req.hero_id,
            skill_id=req.skill_id,
            target_boss_id=req.target_boss_id,
            target_guild_id=req.target_guild_id,
        )
        result = await container.cast_skill.execute(cmd)
        return {
            "success": result.success,
            "message": result.message,
            "damage_dealt": result.damage_dealt,
            "boss_defeated": result.boss_defeated,
            "exp_multiplier": result.exp_multiplier,
            "squad_damage_reduction": result.squad_damage_reduction,
            "hero_mana": result.hero.mana,
            "skill_id": result.skill.id,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/equipment/equip", summary="Equipa item de equipamento no herói")
async def equip_item_endpoint(
    req: EquipItemRequest,
    container: GamificationContainer = Depends(get_gamification_container),
):
    try:
        equipment = Equipment(
            name=req.equipment.name,
            description=req.equipment.description,
            slot=req.equipment.slot,
            price=req.equipment.price,
            bonus_strength=req.equipment.bonus_strength,
            bonus_intelligence=req.equipment.bonus_intelligence,
            bonus_constitution=req.equipment.bonus_constitution,
            bonus_perception=req.equipment.bonus_perception,
            required_level=req.equipment.required_level,
            allowed_class=req.equipment.allowed_class,
        )
        cmd = EquipItemCommand(hero_id=req.hero_id, equipment=equipment)
        result = await container.equip_item.execute(cmd)
        return {
            "hero_id": str(result.hero.hero_id),
            "equipped_slot": req.equipment.slot.value,
            "stats": result.hero.stats.to_dict(),
            "unequipped_item": result.unequipped_item,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/equipment/unequip", summary="Desequipa item de um slot do herói")
async def unequip_item_endpoint(
    req: UnequipItemRequest,
    container: GamificationContainer = Depends(get_gamification_container),
):
    try:
        cmd = UnequipItemCommand(hero_id=req.hero_id, slot=req.slot)
        result = await container.equip_item.unequip(cmd)
        return {
            "hero_id": str(result.hero.hero_id),
            "unequipped_item": result.unequipped_item,
            "stats": result.hero.stats.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/heroes/{hero_id}/progression", summary="Obtém a ficha de RPG do herói")
async def get_hero_progression(
    hero_id: UUID,
    container: GamificationContainer = Depends(get_gamification_container),
):
    hero = await container.hero_repo.get_by_id(hero_id)
    if not hero:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hero not found")
    return {
        "hero_id": str(hero.hero_id),
        "name": hero.name,
        "email": hero.email,
        "hero_class": hero.hero_class,
        "level": hero.level,
        "exp": hero.exp,
        "experience_to_next_level": hero.experience_to_next_level,
        "gold": hero.gold,
        "hp": hero.hp,
        "max_hp": hero.max_hp,
        "mana": hero.mana,
        "max_mana": hero.max_mana,
        "stats": hero.stats.to_dict(),
        "equipped_gear": hero.equipped_gear,
        "active_buffs": hero.active_buffs,
        "skill_cooldowns": hero.skill_cooldowns,
    }


@router.get("/quests", summary="Lista todas as quests da guilda")
async def list_quests(
    guild_id: UUID | None = None,
    container: GamificationContainer = Depends(get_gamification_container),
):
    if guild_id:
        quests = await container.quest_repo.list_by_guild(guild_id)
    else:
        quests = await container.quest_repo.list_all()
    return [
        {
            "id": str(q.id),
            "external_id": q.external_id,
            "external_source": q.external_source,
            "title": q.title,
            "status": q.status.value,
            "difficulty": q.difficulty.value,
            "is_pair_programming": q.is_pair_programming,
            "assignee_hero_id": str(q.assignee_hero_id) if q.assignee_hero_id else None,
        }
        for q in quests
    ]


@router.get("/combat/mini-bosses", summary="Lista mini-bosses ativos")
async def list_mini_bosses(
    guild_id: UUID | None = None,
    container: GamificationContainer = Depends(get_gamification_container),
):
    if guild_id:
        bosses = await container.boss_repo.list_active_by_guild(guild_id)
    else:
        bosses = await container.boss_repo.list_all()
    return [
        {
            "id": str(b.id),
            "external_id": b.external_id,
            "title": b.title,
            "severity": b.severity.value,
            "current_health": b.current_health,
            "max_health": b.max_health,
            "is_defeated": b.is_defeated,
            "bounty_hero_xp": b.bounty_hero_xp,
            "bounty_gold": b.bounty_gold,
        }
        for b in bosses
    ]
