import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
)
from .guild_model import GUID
from ..database import Base


class ItemModel(Base):
    __tablename__ = "items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="", nullable=False)
    price = Column(Integer, default=0, nullable=False)
    item_type = Column(String(50), default="EQUIPMENT", nullable=False)
    slot = Column(String(50), nullable=True)

    # Bônus de Atributos de RPG
    bonus_strength = Column(Integer, default=0, nullable=False)
    bonus_intelligence = Column(Integer, default=0, nullable=False)
    bonus_constitution = Column(Integer, default=0, nullable=False)
    bonus_perception = Column(Integer, default=0, nullable=False)

    required_level = Column(Integer, default=1, nullable=False)
    allowed_class = Column(String(50), nullable=True)

    owner_hero_id = Column(GUID, ForeignKey("heroes.id"), nullable=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
