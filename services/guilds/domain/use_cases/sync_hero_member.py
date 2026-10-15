from datetime import datetime, timezone

from services.guilds.domain.model.guild_member import GuildMember
from services.guilds.domain.ports.primary.guild_ports import (
    SyncHeroMemberCommand,
    SyncHeroMemberPort,
    SyncHeroMemberResult,
)
from services.guilds.domain.ports.secondary.guild_member_repository import GuildMemberRepository


class SyncHeroMemberUseCase(SyncHeroMemberPort):
    """Caso de uso para sincronizar a projeção do membro quando um herói é registrado ou atualizado."""

    def __init__(self, member_repository: GuildMemberRepository):
        self.member_repository = member_repository

    async def execute(self, cmd: SyncHeroMemberCommand) -> SyncHeroMemberResult:
        existing = await self.member_repository.find_by_hero_id(cmd.hero_id)

        if existing:
            existing.name = cmd.name
            existing.email = cmd.email
            existing.hero_class = cmd.hero_class
            existing.level = cmd.level
            if cmd.avatar_url is not None:
                existing.avatar_url = cmd.avatar_url
            existing.updated_at = datetime.now(timezone.utc)
            saved = await self.member_repository.save(existing)
            return SyncHeroMemberResult(member=saved, is_new=False)

        new_member = GuildMember(
            hero_id=cmd.hero_id,
            name=cmd.name,
            email=cmd.email,
            hero_class=cmd.hero_class,
            avatar_url=cmd.avatar_url,
            level=cmd.level,
            guild_id=None,
        )
        saved = await self.member_repository.save(new_member)
        return SyncHeroMemberResult(member=saved, is_new=True)
