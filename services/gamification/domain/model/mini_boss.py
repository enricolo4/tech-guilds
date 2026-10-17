from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4


class BossSeverity(str, Enum):
    LOW = "LOW"            # Bug cosmético / P3
    MEDIUM = "MEDIUM"      # Bug funcional normal / P2
    HIGH = "HIGH"          # Bug que afeta fluxo principal / P1
    CRITICAL = "CRITICAL"  # Incidente em produção / Queda / P0


@dataclass
class MiniBoss:
    """Representa um Bug em aberto ou Incidente que ataca a Guilda até ser corrigido."""
    id: UUID = field(default_factory=uuid4)
    tenant_id: str = "default"
    external_id: str = ""       # ex: "BUG-304"
    title: str = ""
    guild_id: UUID = field(default_factory=uuid4)
    severity: BossSeverity = BossSeverity.MEDIUM
    max_health: int = 100
    current_health: int = 100
    is_defeated: bool = False
    bounty_hero_xp: int = 50
    bounty_guild_xp: int = 100
    bounty_gold: int = 30

    @classmethod
    def spawn_from_bug(
        cls,
        external_id: str,
        title: str,
        guild_id: UUID,
        severity: BossSeverity,
        tenant_id: str = "default",
    ) -> "MiniBoss":
        health_map = {
            BossSeverity.LOW: 50,
            BossSeverity.MEDIUM: 100,
            BossSeverity.HIGH: 200,
            BossSeverity.CRITICAL: 400,
        }
        hp = health_map.get(severity, 100)
        return cls(
            tenant_id=tenant_id or "default",
            external_id=external_id,
            title=title,
            guild_id=guild_id,
            severity=severity,
            max_health=hp,
            current_health=hp,
            bounty_hero_xp=hp // 2,
            bounty_guild_xp=hp,
            bounty_gold=hp // 3,
        )

    def take_damage(self, damage: int) -> bool:
        """Aplica dano ao Mini-Boss. Retorna True se o monstro foi derrotado."""
        self.current_health = max(0, self.current_health - damage)
        if self.current_health == 0 and not self.is_defeated:
            self.is_defeated = True
            return True
        return False
