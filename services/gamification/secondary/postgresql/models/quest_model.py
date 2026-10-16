import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
)
from services.gamification.secondary.postgresql.database import Base, GUID


class QuestModel(Base):
    __tablename__ = "quests"
    __table_args__ = {"schema": "gamification"}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    external_source = Column(String(50), default="linear", nullable=False)
    title = Column(String(255), nullable=False)
    guild_id = Column(GUID, nullable=False, index=True)
    assignee_hero_id = Column(GUID, nullable=True, index=True)
    adventure_id = Column(GUID, nullable=True, index=True)
    quest_type = Column(String(50), default="FEATURE", nullable=False)
    status = Column(String(50), default="TODO", nullable=False)
    difficulty = Column(String(50), default="MEDIUM", nullable=False)
    is_pair_programming = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
