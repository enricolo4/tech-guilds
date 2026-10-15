import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from services.guilds.secondary.postgresql.database import Base
from services.guilds.secondary.postgresql.models.guid_type import GUID


class GuildModel(Base):
    """Representação relacional de uma Guilda na base de dados (PostgreSQL schema: 'guilds')."""
    __tablename__ = "guilds"
    __table_args__ = {"schema": "guilds"}

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=False, default="")
    level = Column(Integer, nullable=False, default=1)
    experience = Column(Integer, nullable=False, default=0)
    treasury_gold = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    members = relationship(
        "GuildMemberModel",
        back_populates="guild",
        lazy="selectin",
    )
