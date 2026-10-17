from typing import Callable, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth.domain.model.token import Session
from services.auth.domain.ports.secondary.session_repository import SessionRepository
from services.auth.secondary.postgresql.models.session_model import SessionModel


class PostgresSessionRepository(SessionRepository):
    """Implementação PostgreSQL da porta SessionRepository utilizando SQLAlchemy assíncrono."""

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        self._session_factory = session_factory

    async def save(self, session: Session) -> Session:
        async with self._session_factory() as db:
            async with db.begin():
                existing = await db.get(SessionModel, session.id)
                if existing:
                    existing.token = session.token
                    existing.expires_at = session.expires_at
                    existing.is_revoked = session.is_revoked
                    existing.tenant_id = session.tenant_id or "default"
                    await db.flush()
                    return existing.to_domain()
                else:
                    model = SessionModel.from_domain(session)
                    db.add(model)
                    await db.flush()
                    return model.to_domain()

    async def find_by_id(self, session_id: str) -> Session | None:
        async with self._session_factory() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.id == session_id)
            )
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None

    async def revoke(self, session_id: str) -> None:
        async with self._session_factory() as db:
            async with db.begin():
                await db.execute(
                    update(SessionModel)
                    .where(SessionModel.id == session_id)
                    .values(is_revoked=True)
                )

    async def find_by_user_id(self, user_id: str) -> List[Session]:
        async with self._session_factory() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.user_id == user_id)
            )
            models = result.scalars().all()
            return [m.to_domain() for m in models]

    async def find_by_email(self, email: str, tenant_id: str | None = None) -> Session | None:
        async with self._session_factory() as db:
            stmt = select(SessionModel).where(SessionModel.email == email)
            if tenant_id:
                stmt = stmt.where(SessionModel.tenant_id == tenant_id)
            stmt = stmt.order_by(SessionModel.created_at.desc())
            result = await db.execute(stmt)
            model = result.scalars().first()
            return model.to_domain() if model else None


class InMemorySessionRepository(SessionRepository):
    """Implementação em memória da porta SessionRepository para testes e ambientes locais."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    async def save(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return session

    async def find_by_id(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def revoke(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].is_revoked = True

    async def find_by_user_id(self, user_id: str) -> List[Session]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    async def find_by_email(self, email: str, tenant_id: str | None = None) -> Session | None:
        matches = [
            s
            for s in self._sessions.values()
            if s.email == email and (tenant_id is None or s.tenant_id == tenant_id)
        ]
        return matches[-1] if matches else None


