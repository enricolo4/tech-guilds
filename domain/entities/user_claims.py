from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserClaims:
    """Dados de identidade autenticados retornados pelos provedores de SSO corporativos."""
    email: str
    name: str
    provider: str  # 'google', 'github', 'azure', 'microsoft'
    provider_user_id: str
    avatar_url: Optional[str] = None
