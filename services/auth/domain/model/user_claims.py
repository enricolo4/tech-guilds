from dataclasses import dataclass


@dataclass(frozen=True)
class UserClaims:
    """Dados de identidade autenticados retornados pelos provedores de SSO corporativos."""
    email: str
    name: str
    provider: str  # 'google', 'github', 'azure', 'microsoft', 'direct'
    provider_user_id: str
    avatar_url: str | None = None
    tenant_id: str = "default"
    organization_name: str | None = None

