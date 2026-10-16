import logging
from typing import List
import os

try:
    import nats
    from nats.js import JetStreamContext
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    JetStreamContext = object

from services.common.events import (
    NATS_STREAM_TECH_GUILDS,
    NATS_SUBJECT_HERO_REGISTERED,
    HeroRegisteredEvent,
)
from services.registration.domain.ports.secondary.event_publisher_port import EventPublisherPort

logger = logging.getLogger(__name__)


class InMemoryEventPublisher(EventPublisherPort):
    """Implementação em memória da porta EventPublisherPort para testes rápidos e isolados."""

    def __init__(self):
        self.published_events: List[HeroRegisteredEvent] = []

    async def publish_hero_registered(self, event: HeroRegisteredEvent) -> None:
        self.published_events.append(event)
        logger.info(f"[InMemory] Evento publicado: {event}")

    def clear(self) -> None:
        self.published_events.clear()


class NatsJetStreamPublisher(EventPublisherPort):
    """Implementação resiliente de EventPublisherPort via nats-py JetStream.
    Possui fallback automático para memória/log se o cluster NATS não estiver acessível.
    """

    def __init__(
        self,
        nats_url: str | None = None,
        stream_name: str = NATS_STREAM_TECH_GUILDS,
        fallback_mode: bool = False,
    ):
        self.nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
        self.stream_name = stream_name
        self.fallback_mode = fallback_mode
        self._nc = None
        self._js: JetStreamContext | None = None
        self.published_events: List[HeroRegisteredEvent] = []

    async def connect(self) -> bool:
        """Tenta conectar ao broker NATS e inicializar o contexto JetStream."""
        if not NATS_AVAILABLE or self.fallback_mode:
            logger.warning("NATS não disponível ou fallback_mode ativado. Operando em modo in-memory.")
            return False

        try:
            self._nc = await nats.connect(self.nats_url, connect_timeout=2)
            self._js = self._nc.jetstream()

            # Assegura existência do Stream
            try:
                await self._js.add_stream(
                    name=self.stream_name,
                    subjects=["tech_guilds.>"],
                )
            except Exception:
                # Stream pode já existir
                pass

            logger.info(f"Conectado ao NATS JetStream em {self.nats_url}")
            return True
        except Exception as e:
            logger.warning(f"Falha ao conectar no NATS ({e}). Ativando fallback resiliente.")
            self._js = None
            return False

    async def close(self) -> None:
        """Encerra a conexão com o NATS."""
        if self._nc and not self._nc.is_closed:
            await self._nc.drain()
            await self._nc.close()

    async def publish_hero_registered(self, event: HeroRegisteredEvent) -> None:
        """Publica o HeroRegisteredEvent no subject NATS JetStream ou no buffer de fallback."""
        self.published_events.append(event)

        if self._js is not None:
            try:
                ack = await self._js.publish(
                    subject=NATS_SUBJECT_HERO_REGISTERED,
                    payload=event.to_bytes(),
                )
                logger.info(f"Evento {NATS_SUBJECT_HERO_REGISTERED} publicado com sucesso no NATS (seq: {ack.seq})")
                return
            except Exception as e:
                logger.error(f"Erro ao publicar no JetStream ({e}). Evento mantido no buffer de fallback.")
                return

        logger.info(f"[Fallback NATS] Evento {NATS_SUBJECT_HERO_REGISTERED} armazenado em buffer local: {event.hero_id}")
