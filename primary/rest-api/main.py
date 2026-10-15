from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routers.auth import router as auth_router
from .routers.webhooks import router as webhooks_router
from .routers.guilds import router as guilds_router
from .routers.dashboard import router as dashboard_router

app = FastAPI(
    title="Tech Guilds API",
    description="Motor cooperativo de gamificação em RPG para Squads de Tecnologia integrado com Linear, Jira, GitHub e SSO Corporativo.",
    version="1.0.0",
)

# Configuração de CORS para permitir dashboards e extensões internas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montagem de Arquivos Estáticos do Dashboard Retro RPG
STATIC_DIR = Path(__file__).resolve().parent.parent / "web_dashboard" / "static"
if STATIC_DIR.exists():
    app.mount("/dashboard/static", StaticFiles(directory=str(STATIC_DIR)), name="dashboard_static")
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Registro de Rotas
app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(guilds_router)
app.include_router(dashboard_router)


@app.get("/health", tags=["Status"])
async def health_check():
    return {
        "status": "healthy",
        "service": "tech-guilds",
        "version": "1.0.0",
    }
