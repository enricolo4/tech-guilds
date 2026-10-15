from abc import ABC, abstractmethod
from services.common.events import HeroRegisteredEvent


class EventPublisherPort(ABC):
    """Porta Secundária para publicação de eventos de domínio no barramento NATS JetStream."""

    @abstractmethod
    async def publish_hero_registered(self, event: HeroRegisteredEvent) -> None:
        """Publica o evento HeroRegisteredEvent no stream do JetStream."""
        pass
