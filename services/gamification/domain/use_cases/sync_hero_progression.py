from services.gamification.domain.model.hero_progression import (
    HeroProgression,
    HeroProgressionStats,
)
from services.gamification.domain.ports.primary.sync_hero_progression_port import (
    SyncHeroProgressionPort,
    SyncHeroProgressionCommand,
    SyncHeroProgressionResult,
)
from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)


class SyncHeroProgressionUseCase(SyncHeroProgressionPort):
    """Implementação da Porta Primária para sincronização da ficha RPG do herói."""

    def __init__(self, hero_progression_repo: HeroProgressionRepository):
        self.hero_progression_repo = hero_progression_repo

    async def execute(self, cmd: SyncHeroProgressionCommand) -> SyncHeroProgressionResult:
        tenant_id = (cmd.tenant_id or "default").strip() or "default"
        existing = await self.hero_progression_repo.get_by_id(cmd.hero_id)
        if existing:
            # Atualiza informações de cadastro sem resetar progresso de jogo
            existing.name = cmd.name
            if cmd.email:
                existing.email = cmd.email
            if cmd.hero_class and existing.hero_class == "NOVICE":
                existing.hero_class = cmd.hero_class
            if cmd.guild_id:
                existing.guild_id = cmd.guild_id
            existing.tenant_id = tenant_id
            saved = await self.hero_progression_repo.save(existing)
            return SyncHeroProgressionResult(hero_progression=saved, created=False)

        # Inicializa nova ficha de RPG
        new_hero = HeroProgression(
            hero_id=cmd.hero_id,
            name=cmd.name,
            email=cmd.email,
            hero_class=cmd.hero_class or "NOVICE",
            level=cmd.level,
            exp=cmd.experience,
            gold=cmd.gold,
            guild_id=cmd.guild_id,
            stats=HeroProgressionStats(),
            tenant_id=tenant_id,
        )
        saved = await self.hero_progression_repo.save(new_hero)
        return SyncHeroProgressionResult(hero_progression=saved, created=True)
