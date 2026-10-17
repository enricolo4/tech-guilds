from services.guilds.domain.model.guild import Guild, SquadLevel, Treasury
from services.guilds.domain.ports.primary.guild_ports import (
    CreateGuildCommand,
    CreateGuildPort,
    CreateGuildResult,
)
from services.guilds.domain.ports.secondary.guild_member_repository import GuildMemberRepository
from services.guilds.domain.ports.secondary.guild_repository import GuildRepository


class CreateGuildUseCase(CreateGuildPort):
    """Caso de uso para criação de novas guildas / squads tecnológicos."""

    def __init__(
        self,
        guild_repository: GuildRepository,
        member_repository: GuildMemberRepository | None = None,
    ):
        self.guild_repository = guild_repository
        self.member_repository = member_repository

    async def execute(self, cmd: CreateGuildCommand) -> CreateGuildResult:
        stripped_name = cmd.name.strip()
        if not stripped_name:
            raise ValueError("O nome da guilda não pode ser vazio.")

        tenant_id = (cmd.tenant_id or "default").strip() or "default"

        existing = await self.guild_repository.find_by_name(stripped_name, tenant_id=tenant_id)
        if existing:
            raise ValueError(f"Já existe uma guilda com o nome '{stripped_name}' nesta organização.")

        guild = Guild(
            name=stripped_name,
            description=cmd.description.strip(),
            tenant_id=tenant_id,
            squad_level=SquadLevel(level=1, experience=0),
            treasury=Treasury(gold=0),
        )

        if cmd.creator_hero_id:
            guild.add_member(cmd.creator_hero_id)

        saved_guild = await self.guild_repository.save(guild)

        if cmd.creator_hero_id and self.member_repository:
            await self.member_repository.update_guild_assignment(
                hero_id=cmd.creator_hero_id,
                guild_id=saved_guild.id,
            )

        return CreateGuildResult(
            guild=saved_guild,
            success=True,
            message=f"Guilda '{saved_guild.name}' criada com sucesso.",
        )

