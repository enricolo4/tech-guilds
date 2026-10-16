
from services.guilds.domain.ports.primary.guild_ports import (
    AddMemberCommand,
    AddMemberPort,
    AddMemberResult,
)
from services.guilds.domain.ports.secondary.guild_member_repository import GuildMemberRepository
from services.guilds.domain.ports.secondary.guild_repository import GuildRepository


class AddMemberUseCase(AddMemberPort):
    """Caso de uso para adicionar um herói/membro a uma Guilda."""

    def __init__(
        self,
        guild_repository: GuildRepository,
        member_repository: GuildMemberRepository | None = None,
    ):
        self.guild_repository = guild_repository
        self.member_repository = member_repository

    async def execute(self, cmd: AddMemberCommand) -> AddMemberResult:
        guild = await self.guild_repository.find_by_id(cmd.guild_id)
        if not guild:
            raise ValueError(f"Guilda com ID '{cmd.guild_id}' não encontrada.")

        guild.add_member(cmd.hero_id)
        await self.guild_repository.save(guild)

        if self.member_repository:
            await self.member_repository.update_guild_assignment(
                hero_id=cmd.hero_id,
                guild_id=guild.id,
            )

        return AddMemberResult(
            guild_id=guild.id,
            hero_id=cmd.hero_id,
            success=True,
            message="Membro adicionado à guilda com sucesso.",
        )
