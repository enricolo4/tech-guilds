from fastapi import APIRouter, Depends, HTTPException, status
from tech_guilds.domain.entities.hero import Hero
from ..dependencies.container import DependencyContainer, get_container
from ..dependencies.auth import get_current_hero
from ..schemas.auth_schemas import (
    SSOLoginRequest,
    SSOLoginResponse,
    HeroResponse,
    ChangeClassRequest,
)

router = APIRouter(prefix="", tags=["Auth & Heróis"])


def _to_hero_response(hero: Hero) -> HeroResponse:
    return HeroResponse(
        id=hero.id,
        email=hero.email,
        name=hero.name,
        avatar_url=hero.avatar_url,
        guild_id=hero.guild_id,
        hero_class=hero.hero_class,
        level=hero.level,
        experience=hero.experience,
        experience_to_next_level=hero.experience_to_next_level,
        gold=hero.gold,
        health=hero.health,
        max_health=hero.max_health,
    )


@router.post("/auth/sso/login", response_model=SSOLoginResponse, status_code=status.HTTP_200_OK)
async def login_with_sso(
    req: SSOLoginRequest,
    container: DependencyContainer = Depends(get_container),
):
    """Efetua login via SSO corporativo (Google, GitHub, Azure, Microsoft).
    Auto-provisiona o personagem no Nível 1 caso seja o primeiro acesso do desenvolvedor.
    """
    try:
        result = await container.auth_use_case.execute(token=req.token, provider=req.provider)
        hero = result.hero
        return SSOLoginResponse(
            hero=_to_hero_response(hero),
            is_new_player=result.is_new_player,
            access_token=hero.email,  # Retorna credencial de sessão
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/heroes/me", response_model=HeroResponse)
async def get_my_profile(hero: Hero = Depends(get_current_hero)):
    """Retorna os dados do personagem autenticado atualmente."""
    return _to_hero_response(hero)


@router.post("/heroes/me/class", response_model=HeroResponse)
async def change_hero_class(
    req: ChangeClassRequest,
    hero: Hero = Depends(get_current_hero),
    container: DependencyContainer = Depends(get_container),
):
    """Permite ao desenvolvedor escolher ou trocar sua classe de RPG (Warrior, Mage, Paladin, Ranger, Tactician)."""
    hero.assign_class(req.new_class)
    saved_hero = await container.hero_repo.save(hero)
    return _to_hero_response(saved_hero)
