from services.gamification.domain.model.mini_boss import MiniBoss
from services.gamification.domain.ports.primary.process_bug_event_port import (
    ProcessBugEventPort,
    ProcessBugEventCommand,
    ProcessBugEventResult,
)
from services.gamification.domain.ports.secondary.mini_boss_repository import (
    MiniBossRepository,
)
from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)


class ProcessBugEventUseCase(ProcessBugEventPort):
    """Implementação da Porta Primária para processamento de bugs e incidentes (Mini-Bosses)."""

    def __init__(
        self,
        boss_repo: MiniBossRepository,
        hero_progression_repo: HeroProgressionRepository,
    ):
        self.boss_repo = boss_repo
        self.hero_progression_repo = hero_progression_repo

    async def execute(self, cmd: ProcessBugEventCommand) -> ProcessBugEventResult:
        tenant_id = (cmd.tenant_id or "default").strip() or "default"
        boss = await self.boss_repo.get_by_external_id(cmd.external_id, tenant_id=tenant_id)

        # Se o bug foi aberto e o boss ainda não existe -> Spawna o Mini-Boss
        if boss is None and not cmd.is_resolved:
            boss = MiniBoss.spawn_from_bug(
                external_id=cmd.external_id,
                title=cmd.title,
                guild_id=cmd.guild_id,
                severity=cmd.severity,
                tenant_id=tenant_id,
            )
            saved_boss = await self.boss_repo.save(boss)
            return ProcessBugEventResult(mini_boss=saved_boss, is_defeated=False)

        # Se o bug foi resolvido -> Derrota o Mini-Boss e concede a recompensa (Bounty)
        if boss and cmd.is_resolved and not boss.is_defeated:
            boss.take_damage(boss.current_health)
            saved_boss = await self.boss_repo.save(boss)

            filter_tenant = tenant_id if tenant_id != "default" else None
            hero = None
            hero_leveled_up = False
            if cmd.resolver_hero_id:
                hero = await self.hero_progression_repo.get_by_id(cmd.resolver_hero_id, tenant_id=filter_tenant)
            elif cmd.resolver_email:
                hero = await self.hero_progression_repo.get_by_email(cmd.resolver_email, tenant_id=filter_tenant)

            if hero:
                hero_leveled_up = hero.gain_experience(boss.bounty_hero_xp)
                hero.gain_gold(boss.bounty_gold)
                await self.hero_progression_repo.save(hero)

            return ProcessBugEventResult(
                mini_boss=saved_boss,
                is_defeated=True,
                bounty_hero_xp=boss.bounty_hero_xp,
                bounty_guild_xp=boss.bounty_guild_xp,
                bounty_gold=boss.bounty_gold,
                hero_leveled_up=hero_leveled_up,
                hero_progression=hero,
            )

        if boss is None:
            # Bug já nasceu resolvido
            boss = MiniBoss.spawn_from_bug(
                cmd.external_id, cmd.title, cmd.guild_id, cmd.severity, tenant_id=tenant_id
            )
            boss.is_defeated = True
            saved_boss = await self.boss_repo.save(boss)
            return ProcessBugEventResult(
                mini_boss=saved_boss,
                is_defeated=True,
                bounty_hero_xp=boss.bounty_hero_xp,
                bounty_guild_xp=boss.bounty_guild_xp,
                bounty_gold=boss.bounty_gold,
            )

        return ProcessBugEventResult(mini_boss=boss, is_defeated=boss.is_defeated)
