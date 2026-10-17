import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    UniqueConstraint,
)
from services.gamification.secondary.postgresql.database import Base, GUID


class MiniBossModel(Base):
    __tablename__ = "mini_bosses"
    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id", name="uq_gamification_mini_bosses_tenant_external_id"),
        {"schema": "gamification"},
    )

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    external_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    guild_id = Column(GUID, nullable=False, index=True)
    severity = Column(String(50), default="MEDIUM", nullable=False)
    max_health = Column(Integer, default=100, nullable=False)
    current_health = Column(Integer, default=100, nullable=False)
    is_defeated = Column(Boolean, default=False, nullable=False)
    bounty_hero_xp = Column(Integer, default=50, nullable=False)
    bounty_guild_xp = Column(Integer, default=100, nullable=False)
    bounty_gold = Column(Integer, default=30, nullable=False)
    tenant_id = Column(String(120), default="default", nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
