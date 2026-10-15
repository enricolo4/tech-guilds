from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..model.mini_boss import MiniBoss, BossSeverity
from ..ports.primary.bug_event_port import (
    ProcessBugEventPort,
    BugEventCommand,
    BugEventResult,
)
from ..ports.secondary.repositories import (
    HeroRepository,
    GuildRepository,
    MiniBossRepository,
)
from ..ports.secondary.notification_port import NotificationPort


class ProcessBugEventUseCase(ProcessBugEventPort):
    """Implementação da Porta Primária para geração e combate de Mini-Bosses originados de Bugs e Incidentes."""
    def __init__(
        self,
        boss_repo: MiniBossRepository,
        hero_repo: HeroRepository,
        guild_repo: GuildRepository,
        notification_port: NotificationPort,
    ):
        self.boss_repo = boss_repo
        self.hero_repo = hero_repo
        self.guild_repo = guild_repo
        self.notification_port = notification_port

    async def execute(self, cmd: BugEventCommand) -> BugEventResult:
        boss = await self.boss_repo.get_by_external_id(cmd.external_id)

        # Se o bug foi aberto e o boss ainda não existe -> Spawna o Mini-Boss!
        if boss is None and not cmd.is_resolved:
            boss = MiniBoss.spawn_from_bug(
                external_id=cmd.external_id,
                title=cmd.title,
                guild_id=cmd.guild_id,
                severity=cmd.severity,
            )
            await self.boss_repo.save(boss)

            await self.notification_port.notify_boss_spawned(
                guild_id=cmd.guild_id,
                boss_title=boss.title,
                severity=boss.severity.value,
                bug_id=boss.external_id,
            )
            return BugEventResult(mini_boss=boss, is_defeated=False)

        # Se o bug foi resolvido -> Derrota o Mini-Boss e concede a recompensa (Bounty)
        if boss and cmd.is_resolved and not boss.is_defeated:
            boss.take_damage(boss.current_health)  # Zera o HP
            await self.boss_repo.save(boss)

            hero = None
            if cmd.resolver_email:
                hero = await self.hero_repo.get_by_email(cmd.resolver_email)
                if hero:
                    hero.gain_experience(boss.bounty_hero_xp)
                    hero.gain_gold(boss.bounty_gold)
                    await self.hero_repo.save(hero)

            guild = await self.guild_repo.get_by_id(cmd.guild_id)
            if guild:
                guild.gain_experience(boss.bounty_guild_xp)
                guild.deposit_gold(boss.bounty_gold)
                await self.guild_repo.save(guild)

            await self.notification_port.notify_boss_defeated(
                guild_id=cmd.guild_id,
                boss_title=boss.title,
                hero_name=hero.name if hero else "A Guilda",
            )

            return BugEventResult(
                mini_boss=boss,
                is_defeated=True,
                bounty_hero_xp=boss.bounty_hero_xp,
                bounty_guild_xp=boss.bounty_guild_xp,
            )

        if boss is None:
            # Caso raro: bug já nasceu resolvido
            boss = MiniBoss.spawn_from_bug(cmd.external_id, cmd.title, cmd.guild_id, cmd.severity)
            boss.is_defeated = True
            await self.boss_repo.save(boss)

        return BugEventResult(mini_boss=boss, is_defeated=boss.is_defeated)
