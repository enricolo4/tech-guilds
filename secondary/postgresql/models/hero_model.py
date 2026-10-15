import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    JSON,
)
from .guild_model import GUID
from ..database import Base


class HeroModel(Base):
    __tablename__ = "heroes"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    guild_id = Column(GUID, ForeignKey("guilds.id"), nullable=True, index=True)
    hero_class = Column(String(50), default="NOVICE", nullable=False)
    level = Column(Integer, default=1, nullable=False)
    experience = Column(Integer, default=0, nullable=False)
    gold = Column(Integer, default=0, nullable=False)
    health = Column(Integer, default=100, nullable=False)
    max_health = Column(Integer, default=100, nullable=False)
    mana = Column(Integer, default=100, nullable=False)
    max_mana = Column(Integer, default=100, nullable=False)

    # Atributos de RPG
    strength = Column(Integer, default=10, nullable=False)
    intelligence = Column(Integer, default=10, nullable=False)
    constitution = Column(Integer, default=10, nullable=False)
    perception = Column(Integer, default=10, nullable=False)

    # Inventário e Customizações
    equipped_gear = Column(JSON, default=dict, nullable=True)
    unlocked_skins = Column(JSON, default=list, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
