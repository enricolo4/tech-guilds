from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from services.auth.domain.model.token import Session


class Base(DeclarativeBase):
    """Base declarativa isolada para o serviço de autenticação."""
    pass


class SessionModel(Base):
    """Modelo ORM SQLAlchemy da tabela auth.sessions."""
    __tablename__ = "sessions"
    __table_args__ = {"schema": "auth"}

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    token: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def to_domain(self) -> Session:
        return Session(
            id=self.id,
            user_id=self.user_id,
            email=self.email,
            provider=self.provider,
            provider_user_id=self.provider_user_id,
            created_at=self.created_at,
            expires_at=self.expires_at,
            token=self.token,
            is_revoked=self.is_revoked,
        )

    @classmethod
    def from_domain(cls, session: Session) -> "SessionModel":
        return cls(
            id=session.id,
            user_id=session.user_id,
            email=session.email,
            provider=session.provider,
            provider_user_id=session.provider_user_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            token=session.token,
            is_revoked=session.is_revoked,
        )
