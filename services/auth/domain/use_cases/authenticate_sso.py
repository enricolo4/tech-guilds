import uuid
from datetime import datetime, timedelta, timezone

from services.common.tenant import resolve_tenant_id, resolve_organization_name
from services.auth.domain.model.token import AuthToken, Session, TokenPayload
from services.auth.domain.model.user_claims import UserClaims
from services.auth.domain.ports.primary.auth_port import (
    AuthenticateUserPort,
    LoginDirectCommand,
    LoginSSOCommand,
    LoginSSOResult,
    RegisterAccountCommand,
)
from services.auth.domain.ports.secondary.session_repository import SessionRepository
from services.auth.domain.ports.secondary.sso_port import SSOIdentityPort
from services.auth.domain.ports.secondary.token_service_port import TokenServicePort


class AuthenticateSSOUseCase(AuthenticateUserPort):
    """Caso de uso de autenticação via SSO corporativo e contas diretas multi-tenant.
    Implementa formalmente a porta primária AuthenticateUserPort.
    """

    def __init__(
        self,
        sso_port: SSOIdentityPort,
        session_repository: SessionRepository,
        token_service: TokenServicePort,
        token_ttl_seconds: int = 3600,
        session_ttl_days: int = 7,
    ):
        self._sso_port = sso_port
        self._session_repo = session_repository
        self._token_service = token_service
        self._token_ttl_seconds = token_ttl_seconds
        self._session_ttl_days = session_ttl_days

    async def login_sso(self, command: LoginSSOCommand) -> LoginSSOResult:
        raw_claims = await self._sso_port.verify_token(command.token, command.provider)
        tenant_id = resolve_tenant_id(
            email=raw_claims.email,
            explicit_tenant_id=command.tenant_id or (raw_claims.tenant_id if raw_claims.tenant_id != "default" else None),
        )
        org_name = resolve_organization_name(tenant_id, explicit_name=raw_claims.organization_name)

        claims = UserClaims(
            email=raw_claims.email,
            name=raw_claims.name,
            provider=raw_claims.provider,
            provider_user_id=raw_claims.provider_user_id,
            avatar_url=raw_claims.avatar_url,
            tenant_id=tenant_id,
            organization_name=org_name,
        )

        now = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())
        session_expires_at = now + timedelta(days=self._session_ttl_days)

        payload = TokenPayload(
            sub=claims.provider_user_id,
            email=claims.email,
            name=claims.name,
            provider=claims.provider,
            session_id=session_id,
            tenant_id=tenant_id,
            roles=["player"],
        )
        token_str = self._token_service.issue_token(payload, expires_in_seconds=self._token_ttl_seconds)

        session = Session(
            id=session_id,
            user_id=claims.provider_user_id,
            email=claims.email,
            provider=claims.provider,
            provider_user_id=claims.provider_user_id,
            tenant_id=tenant_id,
            created_at=now,
            expires_at=session_expires_at,
            token=token_str,
            is_revoked=False,
        )
        await self._session_repo.save(session)

        auth_token = AuthToken(
            access_token=token_str,
            token_type="bearer",
            expires_in=self._token_ttl_seconds,
        )

        return LoginSSOResult(
            auth_token=auth_token,
            user=claims,
            session_id=session_id,
            tenant_id=tenant_id,
        )

    async def register_account(self, command: RegisterAccountCommand) -> LoginSSOResult:
        """Cria uma conta real para o usuário, salvando a sessão e emitindo o token JWT."""
        email = command.email.strip().lower()
        name = command.name.strip()
        if not email or "@" not in email:
            raise ValueError("E-mail corporativo inválido.")
        if not name:
            raise ValueError("Nome é obrigatório.")

        tenant_id = resolve_tenant_id(
            email=email,
            explicit_tenant_id=command.tenant_id,
            organization_name=command.organization_name,
        )
        org_name = resolve_organization_name(tenant_id, explicit_name=command.organization_name)

        user_id = str(uuid.uuid4())
        claims = UserClaims(
            email=email,
            name=name,
            provider="direct",
            provider_user_id=user_id,
            avatar_url=command.avatar_url or f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}",
            tenant_id=tenant_id,
            organization_name=org_name,
        )

        now = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())
        session_expires_at = now + timedelta(days=self._session_ttl_days)

        payload = TokenPayload(
            sub=user_id,
            email=email,
            name=name,
            provider="direct",
            session_id=session_id,
            tenant_id=tenant_id,
            roles=["player"],
        )
        token_str = self._token_service.issue_token(payload, expires_in_seconds=self._token_ttl_seconds)

        session = Session(
            id=session_id,
            user_id=user_id,
            email=email,
            provider="direct",
            provider_user_id=user_id,
            tenant_id=tenant_id,
            created_at=now,
            expires_at=session_expires_at,
            token=token_str,
            is_revoked=False,
        )
        await self._session_repo.save(session)

        return LoginSSOResult(
            auth_token=AuthToken(
                access_token=token_str,
                token_type="bearer",
                expires_in=self._token_ttl_seconds,
            ),
            user=claims,
            session_id=session_id,
            tenant_id=tenant_id,
        )

    async def login_direct(self, command: LoginDirectCommand) -> LoginSSOResult:
        """Autentica o usuário diretamente com seu e-mail corporativo."""
        email = command.email.strip().lower()
        if not email or "@" not in email:
            raise ValueError("E-mail corporativo inválido.")

        existing_session = await self._session_repo.find_by_email(email, tenant_id=command.tenant_id)
        name = email.split("@")[0].capitalize()
        user_id = existing_session.user_id if existing_session else str(uuid.uuid4())
        tenant_id = (
            command.tenant_id
            or (existing_session.tenant_id if existing_session and existing_session.tenant_id != "default" else None)
            or resolve_tenant_id(email=email)
        )
        org_name = resolve_organization_name(tenant_id)

        now = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())
        session_expires_at = now + timedelta(days=self._session_ttl_days)

        claims = UserClaims(
            email=email,
            name=name,
            provider="direct",
            provider_user_id=user_id,
            avatar_url=f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}",
            tenant_id=tenant_id,
            organization_name=org_name,
        )

        payload = TokenPayload(
            sub=user_id,
            email=email,
            name=name,
            provider="direct",
            session_id=session_id,
            tenant_id=tenant_id,
            roles=["player"],
        )
        token_str = self._token_service.issue_token(payload, expires_in_seconds=self._token_ttl_seconds)

        session = Session(
            id=session_id,
            user_id=user_id,
            email=email,
            provider="direct",
            provider_user_id=user_id,
            tenant_id=tenant_id,
            created_at=now,
            expires_at=session_expires_at,
            token=token_str,
            is_revoked=False,
        )
        await self._session_repo.save(session)

        return LoginSSOResult(
            auth_token=AuthToken(
                access_token=token_str,
                token_type="bearer",
                expires_in=self._token_ttl_seconds,
            ),
            user=claims,
            session_id=session_id,
            tenant_id=tenant_id,
        )

