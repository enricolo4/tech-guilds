import os
import logging
from typing import Tuple, Any

logger = logging.getLogger(__name__)

DEFAULT_NATS_URL = "nats://localhost:4222"
STREAM_NAME = "TECH_GUILDS"
STREAM_SUBJECTS = ["tech_guilds.*"]


async def get_nats_jetstream(
    nats_url: str | None = None,
    stream_name: str = STREAM_NAME,
    subjects: list | None = None,
) -> Tuple[Any | None, Any | None]:
    """Conecta ao NATS JetStream e assegura a existência do stream principal.
    
    Se o servidor NATS não estiver acessível, retorna (None, None) de forma rápida e resiliente,
    permitindo que a aplicação e os testes funcionem sem bloqueio.
    """
    url = nats_url or os.getenv("NATS_URL", DEFAULT_NATS_URL)
    stream_subs = subjects or STREAM_SUBJECTS

    is_testing = os.getenv("TESTING", "false").lower() == "true" or "pytest" in os.environ.get("_", "")
    timeout = 0.5 if is_testing else 2.0
    max_reconnect = 1 if is_testing else 3

    try:
        import nats
        nc = await nats.connect(
            url,
            connect_timeout=timeout,
            reconnect_time_wait=0.2,
            max_reconnect_attempts=max_reconnect,
            allow_reconnect=not is_testing,
        )
        js = nc.jetstream()

        # Garante a existência do Stream no JetStream
        try:
            await js.stream_info(stream_name)
        except Exception:
            try:
                await js.add_stream(name=stream_name, subjects=stream_subs)
            except Exception as e:
                logger.warning("Não foi possível criar stream '%s': %s", stream_name, e)

        return nc, js
    except Exception as exc:
        logger.info(
            "NATS JetStream não conectado em '%s' (%s). Modo autônomo/fallback ativo.",
            url,
            exc,
        )
        return None, None


async def close_nats(nc: Any | None) -> None:
    """Fecha a conexão com o servidor NATS de forma graciosa."""
    if nc and hasattr(nc, "is_closed") and not nc.is_closed:
        try:
            await nc.drain()
            await nc.close()
        except Exception as exc:
            logger.debug("Erro ao fechar conexão NATS: %s", exc)
