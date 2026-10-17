from abc import ABC, abstractmethod
from dataclasses import dataclass
from services.registration.domain.model.hero import Hero


@dataclass
class RegisterHeroCommand:
    """Comando de entrada para cadastro ou onboarding de um novo herói."""
    email: str | None = None
    name: str | None = None
    hero_class: str | None = "NOVICE"
    avatar_url: str | None = None
    sso_token: str | None = None
    sso_provider: str | None = None
    tenant_id: str | None = None


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
