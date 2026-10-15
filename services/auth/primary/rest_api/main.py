from fastapi import FastAPI
from services.auth.primary.rest_api.controllers.auth_controller import router as auth_router


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI do microsserviço de autenticação."""
    app = FastAPI(
        title="Auth Microservice",
        description="Microsserviço de autenticação corporativa via SSO e emissão de JWT para Tech Guilds",
        version="1.0.0",
    )
    app.include_router(auth_router)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "auth"}

    return app


app = create_app()
