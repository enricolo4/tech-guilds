from typing import Optional, Union
from uuid import UUID

from services.gamification.domain.model.skill import Skill, get_skill
from services.gamification.domain.model.mini_boss import MiniBoss
from services.gamification.domain.ports.primary.cast_skill_port import (
    CastSkillPort,
    CastSkillCommand,
    CastSkillResult,
)
from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)
from services.gamification.domain.ports.secondary.mini_boss_repository import (
    MiniBossRepository,
)


class CastSkillUseCase(CastSkillPort):
    """Implementação da Porta Primária para conjuração de habilidades ativas de classe."""

    def __init__(
        self,
        hero_progression_repo: HeroProgressionRepository,
        boss_repo: Optional[MiniBossRepository] = None,
    ):
        self.hero_progression_repo = hero_progression_repo
        self.boss_repo = boss_repo

    async def execute(
        self,
        cmd_or_hero_id: Union[CastSkillCommand, UUID],
        skill_id: Optional[str] = None,
        target_boss_id: Optional[UUID] = None,
        target_guild_id: Optional[UUID] = None,
    ) -> CastSkillResult:
        if isinstance(cmd_or_hero_id, CastSkillCommand):
            cmd = cmd_or_hero_id
        else:
            if skill_id is None:
                raise ValueError("Skill ID must be provided")
            cmd = CastSkillCommand(
                hero_id=cmd_or_hero_id,
                skill_id=skill_id,
                target_boss_id=target_boss_id,
                target_guild_id=target_guild_id,
            )

        hero = await self.hero_progression_repo.get_by_id(cmd.hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {cmd.hero_id} not found")

        skill = get_skill(cmd.skill_id)
        if skill is None:
            raise ValueError(f"Skill '{cmd.skill_id}' not found in registry")

        # Validação de classe (se o herói já tiver classe definida diferente de NOVICE)
        if hero.hero_class != "NOVICE" and hero.hero_class != skill.hero_class:
            raise ValueError(
                f"Hero class {hero.hero_class} cannot cast {skill.name} (requires {skill.hero_class})"
            )

        # Validação de mana
        if hero.mana < skill.mana_cost:
            raise ValueError(
                f"Insufficient mana to cast {skill.name}: requires {skill.mana_cost}, available {hero.mana}"
            )

        # Validação de cooldown
        if hero.is_skill_on_cooldown(skill.id):
            turns = hero.skill_cooldowns[skill.id]
            raise ValueError(
                f"Skill '{skill.name}' is on cooldown for {turns} more turn(s)"
            )

        # Consome mana e aplica recarga
        hero.use_mana(skill.mana_cost)
        if skill.cooldown_turns > 0:
            hero.set_skill_cooldown(skill.id, skill.cooldown_turns)

        damage_dealt = 0
        boss_defeated = False
        exp_multiplier = 1.0
        squad_damage_reduction = 0.0
        squad_exp_buff = 0
        message = ""

        # Aplica efeito baseado na habilidade
        if skill.id == "BRUTAL_REFACTOR":
            boss = await self._get_target_boss(cmd.target_boss_id)
            damage_dealt = int(skill.base_power + (hero.stats.strength * 3))
            boss_defeated = boss.take_damage(damage_dealt)
            if self.boss_repo:
                await self.boss_repo.save(boss)

            message = f"{hero.name} desfere Brutal Refactor causando {damage_dealt} de dano ao Boss!"
            if boss_defeated:
                hero.gain_experience(boss.bounty_hero_xp)
                hero.gain_gold(boss.bounty_gold)
                message += f" Mini-Boss {boss.title} foi derrotado!"

        elif skill.id == "SCRIPT_AUTOMATION":
            exp_multiplier = round(2.0 + max(0, (hero.stats.intelligence - 10) * 0.05), 2)
            hero.active_buffs["exp_multiplier"] = exp_multiplier
            message = f"{hero.name} ativou Script Automation! EXP multiplicada por {exp_multiplier}x."

        elif skill.id == "CICD_SHIELD":
            squad_damage_reduction = round(
                min(0.75, 0.40 + max(0, (hero.stats.constitution - 10) * 0.02)), 2
            )
            hero.active_buffs["squad_damage_reduction"] = squad_damage_reduction
            message = f"{hero.name} ergueu CI/CD Shield! Redução de dano de {int(squad_damage_reduction * 100)}%."

        elif skill.id == "EDGE_CASE_STRIKE":
            boss = await self._get_target_boss(cmd.target_boss_id)
            crit_multiplier = 2.5
            damage_dealt = int((skill.base_power + hero.stats.perception * 2) * crit_multiplier)
            boss_defeated = boss.take_damage(damage_dealt)
            if self.boss_repo:
                await self.boss_repo.save(boss)

            message = f"{hero.name} acertou Edge Case Strike Crítico causando {damage_dealt} de dano!"
            if boss_defeated:
                hero.gain_experience(boss.bounty_hero_xp)
                hero.gain_gold(boss.bounty_gold)
                message += f" Mini-Boss {boss.title} foi aniquilado!"

        elif skill.id == "SPRINT_RALLY":
            squad_exp_buff = int(skill.base_power + hero.stats.intelligence * 2 + hero.stats.perception * 2)
            hero.active_buffs["squad_exp_buff"] = float(squad_exp_buff)
            message = f"{hero.name} liderou Sprint Rally concedendo +{squad_exp_buff} EXP de bônus."

        await self.hero_progression_repo.save(hero)

        return CastSkillResult(
            hero=hero,
            skill=skill,
            success=True,
            message=message,
            damage_dealt=damage_dealt,
            boss_defeated=boss_defeated,
            exp_multiplier=exp_multiplier,
            squad_damage_reduction=squad_damage_reduction,
            squad_exp_buff=squad_exp_buff,
        )

    async def _get_target_boss(self, boss_id: Optional[UUID]) -> MiniBoss:
        if boss_id is None:
            raise ValueError("Target boss ID is required for this skill")
        if self.boss_repo is None:
            raise ValueError("MiniBossRepository is not configured")
        boss = await self.boss_repo.get_by_id(boss_id)
        if boss is None:
            raise ValueError(f"Target Mini-Boss with ID {boss_id} not found")
        return boss
