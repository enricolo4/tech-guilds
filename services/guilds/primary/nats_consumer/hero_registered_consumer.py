import inspect
import logging
from typing import Any

from services.common.events import (
    NATS_STREAM_TECH_GUILDS,
    NATS_SUBJECT_HERO_REGISTERED,
    HeroRegisteredEvent,
)
from services.guilds.domain.ports.primary.guild_ports import (
    SyncHeroMemberCommand,
    SyncHeroMemberPort,
    SyncHeroMemberResult,
)

logger = logging.getLogger(__name__)


class HeroRegisteredConsumer:
    """Consumidor NATS JetStream para o evento 'tech_guilds.hero.registered'.
    
    Responsável por capturar o evento de cadastro/onboarding de um herói, desserializá-lo
    e acionar a porta primária SyncHeroMemberPort para manter atualizada a projeção
    de membros na tabela/schema de 'guilds'.
    """

    def __init__(
        self,
        sync_port: SyncHeroMemberPort,
        nats_client: Any | None = None,
        jetstream: Any | None = None,
    ):
        self.sync_port = sync_port
        self.nc = nats_client
        self.js = jetstream
        self.subscription = None

    async def handle_message(self, msg: Any) -> SyncHeroMemberResult:
        """Processa a mensagem recebida pelo NATS JetStream."""
        try:
            data = msg.data
            if isinstance(data, (bytes, bytearray)):
                event = HeroRegisteredEvent.from_bytes(data)
            elif isinstance(data, str):
                event = HeroRegisteredEvent.from_json(data)
            elif isinstance(data, dict):
                import json
                event = HeroRegisteredEvent.from_json(json.dumps(data))
            else:
                raise ValueError(f"Formato de dados desconhecido: {type(data)}")

            cmd = SyncHeroMemberCommand(
                hero_id=event.hero_id,
                name=event.name,
                email=event.email,
                hero_class=event.hero_class,
                avatar_url=event.avatar_url,
                level=event.level,
                occurred_at=event.occurred_at,
            )

            result = await self.sync_port.execute(cmd)

            if hasattr(msg, "ack"):
                ack_func = getattr(msg, "ack")
                if inspect.iscoroutinefunction(ack_func):
                    await ack_func()
                else:
                    ack_func()

            logger.info(
                "Projeção do membro %s (%s) sincronizada com sucesso. Novo: %s",
                result.member.name,
                result.member.hero_id,
                result.is_new,
            )
            return result

        except Exception as exc:
            logger.error("Erro ao processar mensagem do evento HeroRegistered: %s", exc, exc_info=True)
            if hasattr(msg, "nak"):
                nak_func = getattr(msg, "nak")
                if inspect.iscoroutinefunction(nak_func):
                    await nak_func()
                else:
                    nak_func()
            raise exc

    async def start(
        self,
        subject: str = NATS_SUBJECT_HERO_REGISTERED,
        durable: str = "guilds-hero-registered-consumer",
        stream: str = NATS_STREAM_TECH_GUILDS,
    ) -> Any:
        """Inicia a inscrição no NATS JetStream para consumo do tópico de heróis registrados."""
        if not self.js:
            raise RuntimeError("Instância de NATS JetStream não configurada.")

        self.subscription = await self.js.subscribe(
            subject=subject,
            durable=durable,
            cb=self.handle_message,
            stream=stream,
        )
        logger.info("Inscrição NATS JetStream ativa em '%s' (durable=%s)", subject, durable)
        return self.subscription

    async def stop(self) -> None:
        """Cancela a inscrição ativa."""
        if self.subscription:
            await self.subscription.unsubscribe()
            self.subscription = None
