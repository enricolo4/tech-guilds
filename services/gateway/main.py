import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Common NATS
from services.common.nats_client import get_nats_jetstream, close_nats

# Microservices Controllers
from services.registration.primary.rest_api.controllers.registration_controller import router as registration_router
from services.auth.primary.rest_api.controllers.auth_controller import router as auth_router
from services.guilds.primary.rest_api.controllers.guild_controller import router as guild_router
from services.gamification.primary.rest_api.controllers.gamification_controller import router as gamification_router

# Consumers & Ports
from services.guilds.primary.nats_consumer.hero_registered_consumer import HeroRegisteredConsumer as GuildsConsumer
from services.guilds.domain.ports.primary.guild_ports import SyncHeroMemberPort, SyncHeroMemberCommand, SyncHeroMemberResult
from services.guilds.domain.use_cases.sync_hero_member import SyncHeroMemberUseCase
from services.guilds.secondary.postgresql.database import async_session_maker as guilds_session_maker
from services.guilds.secondary.postgresql.repositories.postgres_guild_repository import PostgresGuildMemberRepository
from services.guilds.primary.rest_api.dependencies.container import get_sync_hero_member_port

from services.gamification.primary.nats_consumer.hero_registered_consumer import HeroRegisteredConsumer as GamificationConsumer
from services.gamification.domain.ports.primary.sync_hero_progression_port import SyncHeroProgressionPort, SyncHeroProgressionCommand, SyncHeroProgressionResult
from services.gamification.domain.use_cases.sync_hero_progression import SyncHeroProgressionUseCase
from services.gamification.secondary.postgresql.database import async_session_maker as gamification_session_maker
from services.gamification.secondary.postgresql.repositories.hero_progression_repository import PostgresHeroProgressionRepository
from services.gamification.primary.rest_api.dependencies.container import get_in_memory_container

# Dashboard router local do Gateway
from services.gateway.routers.dashboard import router as dashboard_router

logger = logging.getLogger("gateway")

WEB_DASHBOARD_DIR = Path(__file__).resolve().parent / "web_dashboard"


class PostgresGatewayGuildsSyncPort(SyncHeroMemberPort):
    async def execute(self, cmd: SyncHeroMemberCommand) -> SyncHeroMemberResult:
        async with guilds_session_maker() as session:
            repo = PostgresGuildMemberRepository(session)
            uc = SyncHeroMemberUseCase(repo)
            result = await uc.execute(cmd)
            await session.commit()
            return result


class PostgresGatewayGamificationSyncPort(SyncHeroProgressionPort):
    async def execute(self, cmd: SyncHeroProgressionCommand) -> SyncHeroProgressionResult:
        async with gamification_session_maker() as session:
            repo = PostgresHeroProgressionRepository(session)
            uc = SyncHeroProgressionUseCase(repo)
            result = await uc.execute(cmd)
            await session.commit()
            return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida do API Gateway: inicializa conexão NATS JetStream e consumidores dos serviços."""
    logger.info("Iniciando API Gateway do Tech Guilds...")
    nc, js = await get_nats_jetstream()
    guilds_sub = None
    gamification_sub = None

    if js:
        # Inicia consumidor de Guilds com persistência no PostgreSQL
        try:
            guilds_sync_port = (
                PostgresGatewayGuildsSyncPort()
                if os.getenv("TESTING", "false").lower() != "true"
                else get_sync_hero_member_port()
            )
            guilds_consumer = GuildsConsumer(
                sync_port=guilds_sync_port,
                nats_client=nc,
                jetstream=js,
            )
            guilds_sub = await guilds_consumer.start()
            app.state.guilds_consumer = guilds_consumer
            logger.info("Consumidor NATS de Guilds ativado no Gateway (PostgreSQL).")
        except Exception as exc:
            logger.warning("Não foi possível iniciar consumidor de Guilds: %s", exc)

        # Inicia consumidor de Gamification com persistência no PostgreSQL
        try:
            gamification_sync_port = (
                PostgresGatewayGamificationSyncPort()
                if os.getenv("TESTING", "false").lower() != "true"
                else get_in_memory_container().sync_hero_progression
            )
            gamification_consumer = GamificationConsumer(
                sync_hero_progression_port=gamification_sync_port
            )
            gamification_sub = await gamification_consumer.start_consumer(js=js)
            app.state.gamification_consumer = gamification_consumer
            logger.info("Consumidor NATS de Gamification ativado no Gateway (PostgreSQL).")
        except Exception as exc:
            logger.warning("Não foi possível iniciar consumidor de Gamification: %s", exc)

    yield

    logger.info("Encerrando API Gateway e conexões NATS...")
    if guilds_sub and hasattr(guilds_sub, "unsubscribe"):
        await guilds_sub.unsubscribe()
    if gamification_sub and hasattr(gamification_sub, "unsubscribe"):
        await gamification_sub.unsubscribe()
    if nc:
        await close_nats(nc)


def create_gateway_app() -> FastAPI:
    """Cria e configura o API Gateway unificado."""
    app = FastAPI(
        title="Tech Guilds - API Gateway",
        description="Portal unificado de microsserviços, orquestração NATS JetStream e Dashboard RPG",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 1. Rota raiz redireciona para o Dashboard
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/dashboard")

    # Rota direta para Onboarding
    @app.get("/onboarding", include_in_schema=False)
    async def onboarding_view():
        return FileResponse(WEB_DASHBOARD_DIR / "onboarding.html")

    # 2. Healthcheck global
    @app.get("/health", tags=["Infraestrutura"])
    async def global_health():
        return {
            "status": "healthy",
            "gateway": "online",
            "services": ["registration", "auth", "guilds", "gamification"],
        }

    # 3. Mapeamento de rotas dos microsserviços
    app.include_router(registration_router, prefix="/api")
    app.include_router(auth_router, prefix="/api")
    app.include_router(guild_router, prefix="/api")
    app.include_router(gamification_router, prefix="/api")
    app.include_router(dashboard_router)

    # 4. Servir arquivos estáticos (CSS, imagens retrô e pixel art)
    static_dir = WEB_DASHBOARD_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app


app = create_gateway_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=port, reload=True)
