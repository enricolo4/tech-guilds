from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from tech_guilds.domain.model.hero import Hero
from .container import DependencyContainer, get_container

security = HTTPBearer()


async def get_current_hero(
    credentials: HTTPAuthorizationCredentials = Security(security),
    container: DependencyContainer = Depends(get_container),
) -> Hero:
    """Extrai o Bearer token do header e localiza o Hero correspondente."""
    token = credentials.credentials
    # Para fins de autenticação interna simples no MVP, o token carrega o e-mail ou o UUID
    hero = await container.hero_repo.get_by_email(token)
    if hero is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial ou token corporativo inválido. Efetue login via SSO.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return hero
