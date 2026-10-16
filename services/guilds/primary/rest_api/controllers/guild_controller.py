from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.guilds.domain.ports.primary.guild_ports import (
    AddMemberCommand,
    AddMemberPort,
    CreateGuildCommand,
    CreateGuildPort,
)
from services.guilds.domain.ports.secondary.guild_member_repository import GuildMemberRepository
from services.guilds.domain.ports.secondary.guild_repository import GuildRepository
from services.guilds.primary.rest_api.dependencies.container import (
    get_add_member_port,
    get_create_guild_port,
    get_guild_member_repository,
    get_guild_repository,
)

router = APIRouter(prefix="/guilds", tags=["Guilds"])


# Pydantic Schemas
class CreateGuildRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Nome da guilda / squad")
    description: str = Field(default="", description="Descrição do squad ou time")
    creator_hero_id: Optional[UUID] = Field(default=None, description="ID do herói criador/líder")


class AddMemberRequest(BaseModel):
    hero_id: UUID = Field(..., description="ID do herói a ser adicionado")


class GuildMemberResponse(BaseModel):
    hero_id: UUID
    name: str
    email: str
    hero_class: str
    guild_id: Optional[UUID]
    level: int
    avatar_url: Optional[str]


class GuildResponse(BaseModel):
    id: UUID
    name: str
    description: str
    level: int
    experience: int
    treasury_gold: int
    member_ids: List[UUID]


@router.post("", response_model=GuildResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=GuildResponse, status_code=status.HTTP_201_CREATED)
async def create_guild(
    req: CreateGuildRequest,
    port: CreateGuildPort = Depends(get_create_guild_port),
):
    """Cria uma nova guilda através da porta primária CreateGuildPort."""
    try:
        cmd = CreateGuildCommand(
            name=req.name,
            description=req.description,
            creator_hero_id=req.creator_hero_id,
        )
        result = await port.execute(cmd)
        g = result.guild
        return GuildResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            level=g.level,
            experience=g.experience,
            treasury_gold=g.treasury_gold,
            member_ids=g.member_ids,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get("", response_model=List[GuildResponse], include_in_schema=False)
@router.get("/", response_model=List[GuildResponse])
async def list_guilds(
    limit: int = 100,
    offset: int = 0,
    repo: GuildRepository = Depends(get_guild_repository),
):
    """Lista todas as guildas cadastradas."""
    guilds = await repo.list_all(limit=limit, offset=offset)
    return [
        GuildResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            level=g.level,
            experience=g.experience,
            treasury_gold=g.treasury_gold,
            member_ids=g.member_ids,
        )
        for g in guilds
    ]


@router.get("/{guild_id}", response_model=GuildResponse)
async def get_guild(
    guild_id: UUID,
    repo: GuildRepository = Depends(get_guild_repository),
):
    """Recupera detalhes de uma guilda pelo identificador."""
    guild = await repo.find_by_id(guild_id)
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guilda '{guild_id}' não encontrada.",
        )
    return GuildResponse(
        id=guild.id,
        name=guild.name,
        description=guild.description,
        level=guild.level,
        experience=guild.experience,
        treasury_gold=guild.treasury_gold,
        member_ids=guild.member_ids,
    )


@router.post("/{guild_id}/members", status_code=status.HTTP_200_OK)
async def add_member(
    guild_id: UUID,
    req: AddMemberRequest,
    port: AddMemberPort = Depends(get_add_member_port),
):
    """Adiciona um herói como membro de uma guilda através da porta primária AddMemberPort."""
    try:
        cmd = AddMemberCommand(guild_id=guild_id, hero_id=req.hero_id)
        result = await port.execute(cmd)
        return {
            "success": result.success,
            "message": result.message,
            "guild_id": str(result.guild_id),
            "hero_id": str(result.hero_id),
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get("/{guild_id}/members", response_model=List[GuildMemberResponse])
async def list_guild_members(
    guild_id: UUID,
    member_repo: GuildMemberRepository = Depends(get_guild_member_repository),
    guild_repo: GuildRepository = Depends(get_guild_repository),
):
    """Lista as projeções de membros de uma guilda."""
    guild = await guild_repo.find_by_id(guild_id)
    if not guild:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Guilda '{guild_id}' não encontrada.",
        )
    members = await member_repo.find_by_guild_id(guild_id)
    return [
        GuildMemberResponse(
            hero_id=m.hero_id,
            name=m.name,
            email=m.email,
            hero_class=m.hero_class,
            guild_id=m.guild_id,
            level=m.level,
            avatar_url=m.avatar_url,
        )
        for m in members
    ]


@router.get("/heroes/{hero_id}", response_model=GuildMemberResponse)
async def get_hero_guild_membership(
    hero_id: UUID,
    member_repo: GuildMemberRepository = Depends(get_guild_member_repository),
):
    """Retorna a guilda e projeção de membro de um herói."""
    member = await member_repo.find_by_hero_id(hero_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Herói '{hero_id}' não encontrado nas guildas.",
        )
    return GuildMemberResponse(
        hero_id=member.hero_id,
        name=member.name,
        email=member.email,
        hero_class=member.hero_class,
        guild_id=member.guild_id,
        level=member.level,
        avatar_url=member.avatar_url,
    )
