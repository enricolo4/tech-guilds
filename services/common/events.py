import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

NATS_STREAM_TECH_GUILDS = "TECH_GUILDS"
NATS_SUBJECT_HERO_REGISTERED = "tech_guilds.hero.registered"


@dataclass
class HeroRegisteredEvent:
    """Evento disparado no NATS JetStream quando o cadastro/onboarding de um herói é concluído."""
    hero_id: UUID
    email: str
    name: str
    hero_class: str
    avatar_url: str | None = None
    level: int = 1
    experience: int = 0
    gold: int = 0
    occurred_at: str | None = None

    def __post_init__(self):
        if self.occurred_at is None:
            self.occurred_at = datetime.now(timezone.utc).isoformat()
        if isinstance(self.hero_id, str):
            self.hero_id = UUID(self.hero_id)

    def to_json(self) -> str:
        data = asdict(self)
        data["hero_id"] = str(self.hero_id)
        return json.dumps(data)

    def to_bytes(self) -> bytes:
        return self.to_json().encode("utf-8")

    @classmethod
    def from_json(cls, json_str: str) -> "HeroRegisteredEvent":
        raw = json.loads(json_str)
        return cls(
            hero_id=UUID(raw["hero_id"]),
            email=raw["email"],
            name=raw["name"],
            hero_class=raw["hero_class"],
            avatar_url=raw.get("avatar_url"),
            level=raw.get("level", 1),
            experience=raw.get("experience", 0),
            gold=raw.get("gold", 0),
            occurred_at=raw.get("occurred_at"),
        )

    @classmethod
    def from_bytes(cls, b: bytes) -> "HeroRegisteredEvent":
        return cls.from_json(b.decode("utf-8"))
