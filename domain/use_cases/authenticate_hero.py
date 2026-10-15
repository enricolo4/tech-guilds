from ..model.hero import Hero, HeroClass
from ..ports.primary.auth_port import AuthenticateHeroPort, AuthenticateHeroResult
from ..ports.secondary.repositories import HeroRepository
from ..ports.secondary.sso_port import SSOIdentityPort


class AuthenticateHeroUseCase(AuthenticateHeroPort):
    """Implementação da Porta Primária para login via SSO corporativo (Google, GitHub, Azure, Microsoft).
    Se o desenvolvedor estiver entrando pela primeira vez, cria o personagem automaticamente no Nível 1.
    """
    def __init__(self, sso_port: SSOIdentityPort, hero_repo: HeroRepository):
        self.sso_port = sso_port
        self.hero_repo = hero_repo

    async def execute(self, token: str, provider: str) -> AuthenticateHeroResult:
        claims = await self.sso_port.verify_token(token=token, provider=provider)
        hero = await self.hero_repo.get_by_email(claims.email)

        if hero is None:
            # Auto-provisionamento no primeiro login corporativo
            hero = Hero(
                email=claims.email,
                name=claims.name or claims.email.split("@")[0],
                avatar_url=claims.avatar_url,
                hero_class=HeroClass.NOVICE,
                level=1,
                health=100,
                max_health=100,
            )
            saved_hero = await self.hero_repo.save(hero)
            return AuthenticateHeroResult(hero=saved_hero, is_new_player=True)

        # Atualiza nome e avatar caso tenham mudado no SSO
        updated = False
        if claims.name and hero.name != claims.name:
            hero.name = claims.name
            updated = True
        if claims.avatar_url and hero.avatar_url != claims.avatar_url:
            hero.avatar_url = claims.avatar_url
            updated = True

        if updated:
            hero = await self.hero_repo.save(hero)

        return AuthenticateHeroResult(hero=hero, is_new_player=False)
