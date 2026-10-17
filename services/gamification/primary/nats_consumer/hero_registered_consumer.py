import json
import logging
from typing import Any, Union

from services.common.events import (
    HeroRegisteredEvent,
    NATS_SUBJECT_HERO_REGISTERED,
    NATS_STREAM_TECH_GUILDS,
)
from services.gamification.domain.ports.primary.sync_hero_progression_port import (
    SyncHeroProgressionPort,
    SyncHeroProgressionCommand,
    SyncHeroProgressionResult,
)

logger = logging.getLogger(__name__)


class HeroRegisteredConsumer:
    """Consumidor NATS JetStream que escuta o evento 'tech_guilds.hero.registered'
    e invoca o caso de uso SyncHeroProgressionPort para inicializar a ficha de RPG do herói
    na tabela gamification.hero_progressions.
    """

    def __init__(self, sync_hero_progression_port: SyncHeroProgressionPort):
        self.sync_hero_progression_port = sync_hero_progression_port

    async def process_event(self, event: HeroRegisteredEvent) -> SyncHeroProgressionResult:
        """Processa diretamente uma instância de HeroRegisteredEvent."""
        logger.info(f"Consumindo HeroRegisteredEvent para hero_id={event.hero_id}, nome={event.name}")
        cmd = SyncHeroProgressionCommand(
            hero_id=event.hero_id,
            name=event.name,
            email=event.email,
            hero_class=event.hero_class,
            level=event.level,
            experience=event.experience,
            gold=event.gold,
            tenant_id=getattr(event, "tenant_id", "default") or "default",
        )
        result = await self.sync_hero_progression_port.execute(cmd)
        logger.info(
            f"Ficha RPG sincronizada para {event.name} (hero_id={event.hero_id}, criada={result.created})"
        )
        return result

    async def process_message_payload(self, data: Union[bytes, str]) -> SyncHeroProgressionResult:
        """Desserializa payload JSON/Bytes e invoca process_event."""
        if isinstance(data, bytes):
            event = HeroRegisteredEvent.from_bytes(data)
        else:
            event = HeroRegisteredEvent.from_json(data)
        return await self.process_event(event)

    async def handle_nats_message(self, msg: Any) -> SyncHeroProgressionResult:
        """Handler compatível com callbacks de mensagens NATS / JetStream."""
        try:
            result = await self.process_message_payload(msg.data)
            if hasattr(msg, "ack") and callable(msg.ack):
                await msg.ack()
            return result
        except Exception as e:
            logger.error(f"Erro ao processar mensagem NATS hero.registered: {e}", exc_info=True)
            if hasattr(msg, "nak") and callable(msg.nak):
                await msg.nak()
            raise

    async def start_consumer(
        self,
        js: Any,
        durable_name: str = "gamification_hero_registered_consumer",
        stream: str = NATS_STREAM_TECH_GUILDS,
        subject: str = NATS_SUBJECT_HERO_REGISTERED,
    ) -> Any:
        """Inicia inscrição persistente (durable) no JetStream para processar registros de heróis."""
        logger.info(
            f"Subscrevendo NATS JetStream: stream={stream}, subject={subject}, durable={durable_name}"
        )
        sub = await js.subscribe(
            subject=subject,
            stream=stream,
            durable=durable_name,
            cb=self.handle_nats_message,
            manual_ack=True,
        )
        return sub
