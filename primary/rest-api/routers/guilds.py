from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.entities.hero import Hero
from ..dependencies.container import DependencyContainer, get_container
from ..dependencies.auth import get_current_hero
from ..schemas.guild_schemas import CreateGuildRequest, GuildDetailsResponse
from .auth import _to_hero_response

router = APIRouter(prefix="/guilds", tags=["Guildas & Squads"])


@router.post("", response_model=GuildDetailsResponse, status_code=status.HTTP_201_CREATED)
async def create_guild(
    req: CreateGuildRequest,
    hero: Hero = Depends(get_current_hero),
    container: DependencyContainer = Depends(get_container),
):
    """Cria uma nova Guilda para o Squad de tecnologia e associa o criador como membro."""
    existing = await container.guild_repo.get_by_name(req.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe uma Guilda com o nome '{req.name}'.",
        )

    guild = Guild(
        name=req.name,
        description=req.description,
        member_ids=[hero.id],
    )
    saved_guild = await container.guild_repo.save(guild)

    # Associa o herói criador à guilda
    hero.join_guild(saved_guild.id)
    await container.hero_repo.save(hero)

    return GuildDetailsResponse(
        id=saved_guild.id,
        name=saved_guild.name,
        description=saved_guild.description,
        level=saved_guild.level,
        experience=saved_guild.experience,
        experience_to_next_level=saved_guild.experience_to_next_level,
        treasury_gold=saved_guild.treasury_gold,
        members=[_to_hero_response(hero)],
        active_adventure_title=None,
        active_boss_count=0,
    )


@router.get("/{guild_id}", response_model=GuildDetailsResponse)
async def get_guild_details(
    guild_id: UUID,
    container: DependencyContainer = Depends(get_container),
):
    """Retorna detalhes completos do Squad: nível, membros, épicos ativos e mini-bosses em combate."""
    guild = await container.guild_repo.get_by_id(guild_id)
    if guild is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guilda não encontrada.",
        )

    members = await container.hero_repo.list_by_guild(guild.id)
    active_adv = await container.adventure_repo.get_active_by_guild(guild.id)
    active_bosses = await container.boss_repo.list_active_by_guild(guild.id)

    return GuildDetailsResponse(
        id=guild.id,
        name=guild.name,
        description=guild.description,
        level=guild.level,
        experience=guild.experience,
        experience_to_next_level=guild.experience_to_next_level,
        treasury_gold=guild.treasury_gold,
        members=[_to_hero_response(m) for m in members],
        active_adventure_title=active_adv.title if active_adv else None,
        active_boss_count=len(active_bosses),
    )


@router.post("/{guild_id}/join", response_model=GuildDetailsResponse)
async def join_guild(
    guild_id: UUID,
    hero: Hero = Depends(get_current_hero),
    container: DependencyContainer = Depends(get_container),
):
    """Entra em uma Guilda existente."""
    guild = await container.guild_repo.get_by_id(guild_id)
    if guild is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guilda não encontrada.",
        )

    guild.add_member(hero.id)
    await container.guild_repo.save(guild)

    hero.join_guild(guild.id)
    await container.hero_repo.save(hero)

    members = await container.hero_repo.list_by_guild(guild.id)
    active_adv = await container.adventure_repo.get_active_by_guild(guild.id)
    active_bosses = await container.boss_repo.list_active_by_guild(guild.id)

    return GuildDetailsResponse(
        id=guild.id,
        name=guild.name,
        description=guild.description,
        level=guild.level,
        experience=guild.experience,
        experience_to_next_level=guild.experience_to_next_level,
        treasury_gold=guild.treasury_gold,
        members=[_to_hero_response(m) for m in members],
        active_adventure_title=active_adv.title if active_adv else None,
        active_boss_count=len(active_bosses),
    )
