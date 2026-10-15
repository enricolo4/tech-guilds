from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from services.guilds.secondary.postgresql.database import Base
from services.guilds.secondary.postgresql.models.guid_type import GUID


class GuildMemberModel(Base):
    """Projeção de membros (heróis) vinculados ao contexto de Guildas (PostgreSQL schema: 'guilds')."""
    __tablename__ = "members"
    __table_args__ = {"schema": "guilds"}

    hero_id = Column(GUID, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    hero_class = Column(String(50), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    level = Column(Integer, nullable=False, default=1)
    guild_id = Column(
        GUID,
        ForeignKey("guilds.guilds.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
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

    guild = relationship(
        "GuildModel",
        back_populates="members",
    )
