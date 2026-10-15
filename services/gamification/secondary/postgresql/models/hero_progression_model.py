import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    JSON,
)
from services.gamification.secondary.postgresql.database import Base, GUID


class HeroProgressionModel(Base):
    __tablename__ = "hero_progressions"
    __table_args__ = {"schema": "gamification"}

    hero_id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True, index=True)
    hero_class = Column(String(50), default="NOVICE", nullable=False)
    level = Column(Integer, default=1, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    gold = Column(Integer, default=0, nullable=False)
    hp = Column(Integer, default=100, nullable=False)
    max_hp = Column(Integer, default=100, nullable=False)
    mana = Column(Integer, default=100, nullable=False)
    max_mana = Column(Integer, default=100, nullable=False)
    stats = Column(JSON, default=dict, nullable=False)
    equipped_gear = Column(JSON, default=dict, nullable=False)
    active_buffs = Column(JSON, default=dict, nullable=False)
    skill_cooldowns = Column(JSON, default=dict, nullable=False)
    guild_id = Column(GUID, nullable=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
