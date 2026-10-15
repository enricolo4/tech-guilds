from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from tech_guilds.domain.model.hero import HeroClass


class SSOLoginRequest(BaseModel):
    token: str
    provider: str  # "google", "github", "azure", "microsoft"


class HeroResponse(BaseModel):
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    guild_id: Optional[UUID] = None
    hero_class: HeroClass
    level: int
    experience: int
    experience_to_next_level: int
    gold: int
    health: int
    max_health: int


class SSOLoginResponse(BaseModel):
    hero: HeroResponse
    is_new_player: bool
    access_token: str


class ChangeClassRequest(BaseModel):
    new_class: HeroClass
