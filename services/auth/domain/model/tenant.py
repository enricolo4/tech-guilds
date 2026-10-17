from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Tenant:
    """Representa uma Organização / Empresa cliente (Tenant) na plataforma SaaS Tech Guilds."""
    id: str  # Slug ou identificador único (ex: 'o2inc.com', 'nubank', 'default')
    name: str
    domain: str | None = None
    plan: str = "enterprise"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
