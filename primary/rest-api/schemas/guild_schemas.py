from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from .auth_schemas import HeroResponse


class CreateGuildRequest(BaseModel):
    name: str
    description: str = ""


class GuildDetailsResponse(BaseModel):
    id: UUID
    name: str
    description: str
    level: int
    experience: int
    experience_to_next_level: int
    treasury_gold: int
    members: List[HeroResponse] = []
    active_adventure_title: Optional[str] = None
    active_boss_count: int = 0
