from datetime import datetime, timezone

from services.auth.domain.ports.primary.auth_port import (
    ValidateTokenPort,
    ValidateTokenCommand,
    ValidateTokenResult,
)
from services.auth.domain.ports.secondary.session_repository import SessionRepository
from services.auth.domain.ports.secondary.token_service_port import TokenServicePort


class ValidateSessionUseCase(ValidateTokenPort):
    """Caso de uso para validação de token JWT e sessão de usuário.
    Implementa formalmente a porta primária ValidateTokenPort.
    """

    def __init__(
        self,
        token_service: TokenServicePort,
        session_repository: SessionRepository,
    ):
        self._token_service = token_service
        self._session_repo = session_repository

    async def validate_token(self, command: ValidateTokenCommand) -> ValidateTokenResult:
        if not command.token or not command.token.strip():
            return ValidateTokenResult(is_valid=False, error="Token não fornecido.")

        token = command.token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        try:
            payload = self._token_service.verify_token(token)
        except Exception as e:
            return ValidateTokenResult(is_valid=False, error=f"Token inválido ou expirado: {str(e)}")

        session = await self._session_repo.find_by_id(payload.session_id)
        if not session:
            return ValidateTokenResult(is_valid=False, error="Sessão não encontrada.")

        now = datetime.now(timezone.utc)
        if not session.is_active(now):
            if session.is_revoked:
                return ValidateTokenResult(is_valid=False, error="Sessão revogada.")
            return ValidateTokenResult(is_valid=False, error="Sessão expirada.")

        return ValidateTokenResult(is_valid=True, payload=payload)
