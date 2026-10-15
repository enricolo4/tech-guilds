import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    ForeignKey,
    DateTime,
)
from .guild_model import GUID
from ..database import Base


class AdventureModel(Base):
    __tablename__ = "adventures"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    guild_id = Column(GUID, ForeignKey("guilds.id"), nullable=False, index=True)
    total_quests = Column(Integer, default=0, nullable=False)
    completed_quests = Column(Integer, default=0, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    reward_guild_xp = Column(Integer, default=500, nullable=False)
    reward_guild_gold = Column(Integer, default=200, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
