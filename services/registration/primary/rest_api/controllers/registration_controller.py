from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.registration.domain.model.hero import Hero
from services.registration.domain.ports.primary.register_hero_port import (
    RegisterHeroCommand,
    RegisterHeroPort,
)
from services.registration.domain.ports.secondary.hero_repository import HeroRepository
from services.registration.primary.rest_api.dependencies.container import (
    get_register_hero_port,
    get_hero_repository,
)

router = APIRouter(prefix="/registration", tags=["Registration"])


class RegisterHeroRequest(BaseModel):
    email: Optional[str] = Field(None, description="Email corporativo do herói")
    name: Optional[str] = Field(None, description="Nome ou apelido do herói")
    hero_class: Optional[str] = Field("NOVICE", description="Classe inicial (NOVICE, WARRIOR, MAGE, PALADIN, RANGER, TACTICIAN)")
    avatar_url: Optional[str] = Field(None, description="URL do avatar")
    sso_token: Optional[str] = Field(None, description="Token JWT do provedor SSO")
    sso_provider: Optional[str] = Field(None, description="Provedor SSO (google, github, azure, microsoft)")


class HeroStatsResponse(BaseModel):
    strength: int
    intelligence: int
    constitution: int
    perception: int


class HeroResponse(BaseModel):
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str]
    hero_class: str
    level: int
    experience: int
    gold: int
    health: int
    max_health: int
    mana: int
    max_mana: int
    stats: HeroStatsResponse

    @classmethod
    def from_domain(cls, hero: Hero) -> "HeroResponse":
        return cls(
            id=hero.id,
            email=hero.email,
            name=hero.name,
            avatar_url=hero.avatar_url,
            hero_class=hero.hero_class.value if hasattr(hero.hero_class, "value") else str(hero.hero_class),
            level=hero.level,
            experience=hero.experience,
            gold=hero.gold,
            health=hero.health,
            max_health=hero.max_health,
            mana=hero.mana,
            max_mana=hero.max_mana,
            stats=HeroStatsResponse(
                strength=hero.stats.strength,
                intelligence=hero.stats.intelligence,
                constitution=hero.stats.constitution,
                perception=hero.stats.perception,
            ),
        )


class RegisterHeroResponse(BaseModel):
    hero: HeroResponse
    is_new_registration: bool
    message: str


@router.post(
    "/register",
    response_model=RegisterHeroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra ou realiza onboarding de um herói",
)
@router.post(
    "/heroes",
    response_model=RegisterHeroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra ou realiza onboarding de um herói (alias)",
)
async def register_hero(
    request: RegisterHeroRequest,
    port: RegisterHeroPort = Depends(get_register_hero_port),
):
    command = RegisterHeroCommand(
        email=request.email,
        name=request.name,
        hero_class=request.hero_class,
        avatar_url=request.avatar_url,
        sso_token=request.sso_token,
        sso_provider=request.sso_provider,
    )
    try:
        result = await port.register(command)
        return RegisterHeroResponse(
            hero=HeroResponse.from_domain(result.hero),
            is_new_registration=result.is_new_registration,
            message=result.message,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/heroes/by-email/{email}",
    response_model=HeroResponse,
    summary="Busca dados cadastrais de um herói por e-mail",
)
async def get_hero_by_email(
    email: str,
    repo: HeroRepository = Depends(get_hero_repository),
):
    hero = await repo.get_by_email(email)
    if hero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Herói com email '{email}' não encontrado",
        )
    return HeroResponse.from_domain(hero)


@router.get(
    "/heroes/{hero_id}",
    response_model=HeroResponse,
    summary="Busca dados cadastrais de um herói por UUID",
)
async def get_hero_by_id(
    hero_id: UUID,
    repo: HeroRepository = Depends(get_hero_repository),
):
    hero = await repo.get_by_id(hero_id)
    if hero is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Herói com ID {hero_id} não encontrado",
        )
    return HeroResponse.from_domain(hero)


@router.get(
    "/heroes",
    response_model=List[HeroResponse],
    summary="Lista todos os heróis cadastrados",
)
async def list_heroes(
    repo: HeroRepository = Depends(get_hero_repository),
):
    heroes = await repo.list_all()
    return [HeroResponse.from_domain(h) for h in heroes]


@router.get("/health", summary="Health check do microsserviço de Registration")
async def health_check():
    return {"status": "ok", "service": "registration"}
