from abc import ABC, abstractmethod
from ...model.hero import Hero
from dataclasses import dataclass


@dataclass
class AuthenticateHeroResult:
    hero: Hero
    is_new_player: bool


class AuthenticateHeroPort(ABC):
    """Porta Primária (Driving/Input Port) para autenticação e provisionamento de heróis."""
    @abstractmethod
    async def execute(self, token: str, provider: str) -> AuthenticateHeroResult:
        pass
