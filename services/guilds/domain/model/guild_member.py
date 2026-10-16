from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class GuildMember:
    """Projeção de herói mantida no contexto de Guildas (CQRS / Read Model sincronizado via NATS)."""
    hero_id: UUID
    name: str
    email: str
    hero_class: str
    guild_id: UUID | None = None
    level: int = 1
    avatar_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def assign_to_guild(self, guild_id: UUID) -> None:
        self.guild_id = guild_id
        self.updated_at = datetime.now(timezone.utc)

    def leave_guild(self) -> None:
        self.guild_id = None
        self.updated_at = datetime.now(timezone.utc)
