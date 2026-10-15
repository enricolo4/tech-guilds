from typing import Optional, Union
from uuid import UUID

from ..model.hero import Hero, HeroClass
from ..model.guild import Guild
from ..model.mini_boss import MiniBoss
from ..model.skill import Skill, SkillTargetType, get_skill
from ..ports.primary.skill_port import (
    CastSkillPort,
    CastSkillCommand,
    CastSkillResult,
)
from ..ports.secondary.repositories import HeroRepository, MiniBossRepository, GuildRepository
from ..ports.secondary.notification_port import NotificationPort


class CastSkillUseCase(CastSkillPort):
    """Implementação da Porta Primária para conjuração de habilidades de classe de RPG.
    Valida classe exigida, disponibilidade de mana e cooldowns,
    aplicando efeitos no Herói, no Mini-Boss ou na Guilda/Squad.
    """
    def __init__(
        self,
        hero_repo: HeroRepository,
        boss_repo: Optional[MiniBossRepository] = None,
        guild_repo: Optional[GuildRepository] = None,
        notification_port: Optional[NotificationPort] = None,
    ):
        self.hero_repo = hero_repo
        self.boss_repo = boss_repo
        self.guild_repo = guild_repo
        self.notification_port = notification_port

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

        hero = await self.hero_repo.get_by_id(cmd.hero_id)
        if hero is None:
            raise ValueError(f"Hero with ID {cmd.hero_id} not found")

        skill = get_skill(cmd.skill_id)
        if skill is None:
            raise ValueError(f"Skill '{cmd.skill_id}' not found in registry")

        # 1. Validação de classe
        if hero.hero_class != skill.hero_class:
            raise ValueError(
                f"Hero class {hero.hero_class} cannot cast {skill.name} (requires {skill.hero_class})"
            )

        # 2. Validação de mana
        if hero.mana < skill.mana_cost:
            raise ValueError(
                f"Insufficient mana to cast {skill.name}: requires {skill.mana_cost}, available {hero.mana}"
            )

        # 3. Validação de cooldown
        if hero.is_skill_on_cooldown(skill.id):
            turns = hero.skill_cooldowns[skill.id]
            raise ValueError(
                f"Skill '{skill.name}' is on cooldown for {turns} more turn(s)"
            )

        # Consome mana e aplica tempo de recarga
        hero.use_mana(skill.mana_cost)
        if skill.cooldown_turns > 0:
            hero.set_skill_cooldown(skill.id, skill.cooldown_turns)

        damage_dealt = 0
        boss_defeated = False
        exp_multiplier = 1.0
        squad_damage_reduction = 0.0
        squad_exp_buff = 0
        message = ""

        # 4. Aplicação do efeito baseado na habilidade
        if skill.id == "BRUTAL_REFACTOR":
            # Warrior: Dano pesado no boss escalado por STR
            boss = await self._get_target_boss(cmd.target_boss_id)
            damage_dealt = int(skill.base_power + (hero.stats.strength * 3))
            boss_defeated = boss.take_damage(damage_dealt)
            if self.boss_repo:
                await self.boss_repo.save(boss)

            message = f"{hero.name} desfere Brutal Refactor causando {damage_dealt} de dano massivo no Boss!"
            if boss_defeated:
                await self._reward_boss_defeat(hero, boss)
                message += f" Mini-Boss {boss.title} foi derrotado!"

        elif skill.id == "SCRIPT_AUTOMATION":
            # Mage: Multiplicador de EXP escalado por INT
            exp_multiplier = round(2.0 + max(0, (hero.stats.intelligence - 10) * 0.05), 2)
            hero.active_buffs["exp_multiplier"] = exp_multiplier
            message = f"{hero.name} ativou Script Automation! Ganho de EXP multiplicado por {exp_multiplier}x."

        elif skill.id == "CICD_SHIELD":
            # Paladin: Reduz dano sofrido pelo Squad e adiciona pontos de escudo
            guild = await self._get_target_guild(cmd.target_guild_id, hero.guild_id)
            squad_damage_reduction = round(min(0.75, 0.40 + max(0, (hero.stats.constitution - 10) * 0.02)), 2)
            shield_points = int(skill.base_power + hero.stats.constitution * 2)

            guild.active_buffs["damage_reduction"] = squad_damage_reduction
            guild.apply_shield(shield_points)
            if self.guild_repo:
                await self.guild_repo.save(guild)

            message = (
                f"{hero.name} ergueu o CI/CD Shield! Redução de dano do Squad em "
                f"{int(squad_damage_reduction * 100)}% e +{shield_points} pontos de escudo."
            )

        elif skill.id == "EDGE_CASE_STRIKE":
            # Ranger: Acerto crítico devastador no Bug escalado por PER
            boss = await self._get_target_boss(cmd.target_boss_id)
            crit_multiplier = 2.5
            damage_dealt = int((skill.base_power + hero.stats.perception * 2) * crit_multiplier)
            boss_defeated = boss.take_damage(damage_dealt)
            if self.boss_repo:
                await self.boss_repo.save(boss)

            message = f"{hero.name} acertou um Edge Case Strike Crítico causando {damage_dealt} de dano!"
            if boss_defeated:
                await self._reward_boss_defeat(hero, boss)
                message += f" Mini-Boss {boss.title} foi aniquilado!"

        elif skill.id == "SPRINT_RALLY":
            # Tactician: Buff de EXP para o Squad
            guild = await self._get_target_guild(cmd.target_guild_id, hero.guild_id)
            squad_exp_buff = int(skill.base_power + hero.stats.intelligence * 2 + hero.stats.perception * 2)
            guild.gain_experience(squad_exp_buff)
            guild.active_buffs["squad_exp_multiplier"] = 1.3
            if self.guild_repo:
                await self.guild_repo.save(guild)

            message = (
                f"{hero.name} liderou o Sprint Rally! O Squad recebeu +{squad_exp_buff} EXP "
                f"e buff de 30% em tarefas futuras."
            )

        # Salva o herói com a mana consumida e cooldown atualizado
        await self.hero_repo.save(hero)

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

    async def _get_target_guild(
        self,
        target_guild_id: Optional[UUID],
        hero_guild_id: Optional[UUID],
    ) -> Guild:
        effective_id = target_guild_id or hero_guild_id
        if effective_id is None:
            raise ValueError("Target guild ID is required for this skill")
        if self.guild_repo is None:
            raise ValueError("GuildRepository is not configured")
        guild = await self.guild_repo.get_by_id(effective_id)
        if guild is None:
            raise ValueError(f"Guild with ID {effective_id} not found")
        return guild

    async def _reward_boss_defeat(self, hero: Hero, boss: MiniBoss) -> None:
        hero.gain_experience(boss.bounty_hero_xp)
        hero.gain_gold(boss.bounty_gold)

        if self.guild_repo and boss.guild_id:
            guild = await self.guild_repo.get_by_id(boss.guild_id)
            if guild:
                guild.gain_experience(boss.bounty_guild_xp)
                guild.deposit_gold(boss.bounty_gold)
                await self.guild_repo.save(guild)

        if self.notification_port:
            await self.notification_port.notify_boss_defeated(
                guild_id=boss.guild_id,
                boss_title=boss.title,
                hero_name=hero.name,
            )
