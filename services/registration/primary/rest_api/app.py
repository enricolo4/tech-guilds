from fastapi import FastAPI
from services.registration.primary.rest_api.controllers.registration_controller import router as registration_router


def create_app() -> FastAPI:
    """Fábrica de aplicação FastAPI para o microsserviço de Registration."""
    app = FastAPI(
        title="Tech Guilds - Registration Service",
        description="Microsserviço de Cadastro, Onboarding e Emissão de Eventos de Heróis",
        version="0.1.0",
    )
    app.include_router(registration_router)
    return app


app = create_app()
