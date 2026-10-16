from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
import uuid


@dataclass(frozen=True)
class TokenPayload:
    """Payload contido no JWT emitido pelo serviço de autenticação."""
    sub: str
    email: str
    name: str
    provider: str
    session_id: str
    roles: List[str] = field(default_factory=list)
    exp: int | None = None
    iat: int | None = None


@dataclass(frozen=True)
class AuthToken:
    """Representação do token de autenticação retornado ao cliente."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_token: str | None = None


@dataclass
class Session:
    """Sessão de usuário ativa persistida."""
    id: str
    user_id: str
    email: str
    provider: str
    provider_user_id: str
    created_at: datetime
    expires_at: datetime
    token: str | None = None
    is_revoked: bool = False

    def is_active(self, current_time: datetime | None = None) -> bool:
        """Verifica se a sessão está válida e não revogada."""
        if self.is_revoked:
            return False
        now = current_time or datetime.now(timezone.utc)
        if self.expires_at.tzinfo is None and now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        elif self.expires_at.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return self.expires_at > now

    def revoke(self) -> None:
        """Revoga a sessão."""
        self.is_revoked = True
