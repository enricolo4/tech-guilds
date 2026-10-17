from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from services.auth.domain.model.token import TokenPayload
from services.auth.domain.ports.secondary.token_service_port import TokenServicePort


class JoseJWTService(TokenServicePort):
    """Adaptador secundário para emissão e validação de tokens JWT utilizando python-jose."""

    def __init__(
        self,
        secret_key: str = "auth-super-secret-key-change-in-production-1234567890",
        algorithm: str = "HS256",
        default_expires_in: int = 3600,
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._default_expires_in = default_expires_in

    def issue_token(self, payload: TokenPayload, expires_in_seconds: int | None = None) -> str:
        ttl = expires_in_seconds or self._default_expires_in
        now = datetime.now(timezone.utc)
        exp = int((now + timedelta(seconds=ttl)).timestamp())
        iat = int(now.timestamp())

        claims = {
            "sub": payload.sub,
            "email": payload.email,
            "name": payload.name,
            "provider": payload.provider,
            "session_id": payload.session_id,
            "tenant_id": payload.tenant_id,
            "roles": payload.roles,
            "exp": exp,
            "iat": iat,
        }
        return jwt.encode(claims, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        try:
            claims = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            return TokenPayload(
                sub=claims["sub"],
                email=claims["email"],
                name=claims["name"],
                provider=claims["provider"],
                session_id=claims["session_id"],
                tenant_id=claims.get("tenant_id", "default"),
                roles=claims.get("roles", []),
                exp=claims.get("exp"),
                iat=claims.get("iat"),
            )
        except JWTError as e:
            raise ValueError(f"Assinatura do JWT inválida ou expirada: {str(e)}") from e

