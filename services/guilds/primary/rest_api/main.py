from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.guilds.primary.rest_api.controllers.guild_controller import router as guild_router


def create_app() -> FastAPI:
    """Factory para o aplicativo FastAPI do microsserviço de Guildas."""
    app = FastAPI(
        title="Guilds & Squads Microservice",
        description="Microsserviço de gerenciamento de Guildas, Squads e Projeções de Membros",
        version="0.1.0",
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
