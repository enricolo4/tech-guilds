from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID


class NotificationPort(ABC):
    """Porta para emitir alertas e mensagens nos canais da Guilda (Slack ou Discord)."""
    @abstractmethod
    async def notify_guild_channel(self, guild_id: UUID, message: str, title: Optional[str] = None) -> None:
        pass

    @abstractmethod
    async def notify_boss_spawned(self, guild_id: UUID, boss_title: str, severity: str, bug_id: str) -> None:
        pass

    @abstractmethod
    async def notify_boss_defeated(self, guild_id: UUID, boss_title: str, hero_name: str) -> None:
        pass

    @abstractmethod
    async def notify_level_up(self, guild_id: UUID, hero_name: str, new_level: int, hero_class: str) -> None:
        pass

    async def notify_guardian_blessing(self, guild_id: UUID, hero_name: str, xp_gained: int, pr_title: str) -> None:
        """Notifica concessão de Bênção do Guardião por aprovação em Code Review."""
        await self.notify_guild_channel(
            guild_id=guild_id,
            title="🛡️ Bênção do Guardião Concedida!",
            message=f"{hero_name} aprovou o PR '{pr_title}' e recebeu +{xp_gained} XP de Code Review!",
        )
