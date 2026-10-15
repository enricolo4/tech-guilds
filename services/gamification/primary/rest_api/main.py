import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.common.nats_client import get_nats_jetstream, close_nats
from services.gamification.primary.rest_api.controllers.gamification_controller import router as gamification_router
from services.gamification.primary.rest_api.dependencies.container import get_in_memory_container
from services.gamification.primary.nats_consumer.hero_registered_consumer import HeroRegisteredConsumer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida da aplicação: inicializa e finaliza o consumidor NATS JetStream."""
    nc, js = await get_nats_jetstream()
    consumer = None

    if js:
        try:
            container = get_in_memory_container()
            consumer = HeroRegisteredConsumer(
                sync_hero_progression_port=container.sync_hero_progression
            )
            sub = await consumer.start_consumer(js=js)
            app.state.nats_consumer = consumer
            app.state.nats_subscription = sub
            app.state.nats_nc = nc
            logger.info("Consumidor NATS JetStream de Gamification iniciado com sucesso.")
        except Exception as exc:
            logger.warning("Falha ao iniciar consumidor NATS em Gamification: %s", exc)

    yield

    if nc:
        await close_nats(nc)


def create_app() -> FastAPI:
    """Fábrica de aplicação FastAPI para o microsserviço de Gamificação."""
    app = FastAPI(
        title="Tech Guilds - Gamification Microservice",
        description="Microsserviço de RPG, Quests, Combate a Mini-Bosses e Skills",
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

    app.include_router(gamification_router)

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "ok", "service": "gamification"}

    return app


app = create_app()
