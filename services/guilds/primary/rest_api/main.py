import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common.nats_client import get_nats_jetstream, close_nats
from services.guilds.primary.rest_api.controllers.guild_controller import router as guild_router
from services.guilds.primary.rest_api.dependencies.container import get_sync_hero_member_port
from services.guilds.primary.nats_consumer.hero_registered_consumer import HeroRegisteredConsumer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicação: inicializa e finaliza o consumidor NATS JetStream."""
    nc, js = await get_nats_jetstream()
    consumer = None

    if js:
        try:
            sync_port = get_sync_hero_member_port()
            consumer = HeroRegisteredConsumer(
                sync_port=sync_port,
                nats_client=nc,
                jetstream=js,
            )
            await consumer.start()
            app.state.nats_consumer = consumer
            app.state.nats_nc = nc
            logger.info("Consumidor NATS JetStream de Guilds iniciado com sucesso.")
        except Exception as exc:
            logger.warning("Falha ao iniciar consumidor NATS em Guilds: %s", exc)

    yield

    if consumer:
        await consumer.stop()
    if nc:
        await close_nats(nc)


def create_app() -> FastAPI:
    """Factory para o aplicativo FastAPI do microsserviço de Guildas."""
    app = FastAPI(
        title="Guilds & Squads Microservice",
        description="Microsserviço de gerenciamento de Guildas, Squads e Projeções de Membros",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(guild_router)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "service": "guilds"}

    return app


app = create_app()
