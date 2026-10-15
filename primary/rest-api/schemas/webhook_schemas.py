from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from tech_guilds.domain.model.quest import QuestStatus, QuestDifficulty
from tech_guilds.domain.model.mini_boss import BossSeverity


class WebhookCardEventRequest(BaseModel):
    """Schema normalizado para eventos de cards vindos de Linear, Jira ou GitHub."""
    external_id: str
    external_source: str = "linear"
    title: str
    assignee_email: str
    guild_id: UUID
    new_status: QuestStatus
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False
    adventure_external_id: Optional[str] = None


class WebhookBugEventRequest(BaseModel):
    """Schema normalizado para eventos de bugs/incidentes."""
    external_id: str
    title: str
    guild_id: UUID
    severity: BossSeverity = BossSeverity.MEDIUM
    is_resolved: bool = False
    resolver_email: Optional[str] = None


class WebhookEventResponse(BaseModel):
    success: bool
    event_type: str
    message: str
    reward_hero_xp: Optional[int] = None
    reward_guild_xp: Optional[int] = None
