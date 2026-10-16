from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from services.auth.domain.ports.primary.auth_port import (
    AuthenticateUserPort,
    LoginSSOCommand,
    ValidateTokenCommand,
    ValidateTokenPort,
)
from services.auth.primary.rest_api.dependencies.container import (
    get_auth_port,
    get_validate_token_port,
)


class RegisterAccountRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Nome do usuário/herói")
    email: str = Field(..., description="E-mail corporativo")
    password: str | None = Field(None, description="Senha do usuário (opcional para auth simplificada)")
    avatar_url: str | None = Field(None, description="URL do avatar")


class LoginDirectRequest(BaseModel):
    email: str = Field(..., description="E-mail corporativo")
    password: str | None = Field(None, description="Senha do usuário")


class LoginSSORequest(BaseModel):
    token: str = Field(..., description="Token de ID ou acesso fornecido pelo provedor SSO")
    provider: str = Field(..., description="Nome do provedor (google, github, azure, microsoft)")


class UserClaimsResponse(BaseModel):
    email: str
    name: str
    provider: str
    provider_user_id: str
    avatar_url: str | None = None


class LoginSSOResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: str
    user: UserClaimsResponse


class ValidateTokenRequest(BaseModel):
    token: str | None = Field(None, description="Token JWT para validação")


class ValidateTokenResponse(BaseModel):
    is_valid: bool
    user_id: str | None = None
    email: str | None = None
    name: str | None = None
    roles: List[str] = []
    session_id: str | None = None
    error: str | None = None


router = APIRouter(prefix="/auth", tags=["Autenticação & Sessões"])


@router.post("/register", response_model=LoginSSOResponse, status_code=status.HTTP_201_CREATED)
async def register_account(
    request: RegisterAccountRequest,
    auth_port: AuthenticateUserPort = Depends(get_auth_port),
):
    """Cria uma conta real para o usuário, emitindo o token JWT e iniciando a sessão."""
    try:
        from services.auth.domain.ports.primary.auth_port import RegisterAccountCommand
        command = RegisterAccountCommand(
            name=request.name,
            email=request.email,
            password=request.password,
            avatar_url=request.avatar_url,
        )
        result = await auth_port.register_account(command)
        return LoginSSOResponse(
            access_token=result.auth_token.access_token,
            token_type=result.auth_token.token_type,
            expires_in=result.auth_token.expires_in,
            session_id=result.session_id,
            user=UserClaimsResponse(
                email=result.user.email,
                name=result.user.name,
                provider=result.user.provider,
                provider_user_id=result.user.provider_user_id,
                avatar_url=result.user.avatar_url,
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=LoginSSOResponse, status_code=status.HTTP_200_OK)
async def login_direct(
    request: LoginDirectRequest,
    auth_port: AuthenticateUserPort = Depends(get_auth_port),
):
    """Autentica o usuário diretamente com seu e-mail corporativo."""
    try:
        from services.auth.domain.ports.primary.auth_port import LoginDirectCommand
        command = LoginDirectCommand(
            email=request.email,
            password=request.password,
        )
        result = await auth_port.login_direct(command)
        return LoginSSOResponse(
            access_token=result.auth_token.access_token,
            token_type=result.auth_token.token_type,
            expires_in=result.auth_token.expires_in,
            session_id=result.session_id,
            user=UserClaimsResponse(
                email=result.user.email,
                name=result.user.name,
                provider=result.user.provider,
                provider_user_id=result.user.provider_user_id,
                avatar_url=result.user.avatar_url,
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login/sso", response_model=LoginSSOResponse, status_code=status.HTTP_200_OK)
@router.post("/sso/login", response_model=LoginSSOResponse, status_code=status.HTTP_200_OK)
async def login_sso(
    request: LoginSSORequest,
    auth_port: AuthenticateUserPort = Depends(get_auth_port),
):
    """Autentica o usuário via provedor corporativo SSO e emite o token JWT de sessão."""
    try:
        command = LoginSSOCommand(token=request.token, provider=request.provider)
        result = await auth_port.login_sso(command)
        return LoginSSOResponse(
            access_token=result.auth_token.access_token,
            token_type=result.auth_token.token_type,
            expires_in=result.auth_token.expires_in,
            session_id=result.session_id,
            user=UserClaimsResponse(
                email=result.user.email,
                name=result.user.name,
                provider=result.user.provider,
                provider_user_id=result.user.provider_user_id,
                avatar_url=result.user.avatar_url,
            ),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno de autenticação: {str(e)}",
        )


@router.post("/validate", response_model=ValidateTokenResponse, status_code=status.HTTP_200_OK)
async def validate_token(
    request: ValidateTokenRequest | None = None,
    authorization: str | None = Header(None),
    validate_token_port: ValidateTokenPort = Depends(get_validate_token_port),
):
    """Valida a integridade criptográfica do JWT e se a sessão continua ativa no repositório."""
    token = None
    if request and request.token:
        token = request.token
    elif authorization:
        token = authorization

    if not token:
        return ValidateTokenResponse(
            is_valid=False,
            error="Token não fornecido no corpo ou header Authorization.",
        )

    command = ValidateTokenCommand(token=token)
    result = await validate_token_port.validate_token(command)

    if not result.is_valid:
        return ValidateTokenResponse(
            is_valid=False,
            error=result.error,
        )

    payload = result.payload
    return ValidateTokenResponse(
        is_valid=True,
        user_id=payload.sub if payload else None,
        email=payload.email if payload else None,
        name=payload.name if payload else None,
        roles=payload.roles if payload else [],
        session_id=payload.session_id if payload else None,
    )
