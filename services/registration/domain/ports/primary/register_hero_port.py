from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from services.registration.domain.model.hero import Hero


@dataclass
class RegisterHeroCommand:
    """Comando de entrada para cadastro ou onboarding de um novo herói."""
    email: Optional[str] = None
    name: Optional[str] = None
    hero_class: Optional[str] = "NOVICE"
    avatar_url: Optional[str] = None
    sso_token: Optional[str] = None
    sso_provider: Optional[str] = None


@dataclass
class RegisterHeroResult:
    """Resultado do processo de cadastro de um herói."""
    hero: Hero
    is_new_registration: bool = True
    message: str = "Hero registered successfully"


class RegisterHeroPort(ABC):
    """Porta Primária (Driving Port) para o caso de uso de cadastro de herói."""

    @abstractmethod
    async def register(self, command: RegisterHeroCommand) -> RegisterHeroResult:
        """Executa o cadastro/onboarding de um novo herói."""
        pass
