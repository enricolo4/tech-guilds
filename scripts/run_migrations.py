#!/usr/bin/env python3
"""Script unificado de execução de Migrations para todos os microsserviços.

Executa as migrations do Alembic em ordem, aplicando as alterações em cada
schema isolado do PostgreSQL ('registration', 'auth', 'guilds', 'gamification').
"""

import sys
import os
from pathlib import Path
from alembic.config import Config
from alembic import command

# Raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

SERVICES_CONFIG = [
    ("Registration", ROOT_DIR / "services/registration/secondary/postgresql/migrations/alembic.ini"),
    ("Auth", ROOT_DIR / "services/auth/secondary/postgresql/migrations/alembic.ini"),
    ("Guilds", ROOT_DIR / "services/guilds/secondary/postgresql/migrations/alembic.ini"),
    ("Gamification", ROOT_DIR / "services/gamification/secondary/postgresql/migrations/alembic.ini"),
]


def run_migrations():
    print("=" * 60)
    print("🚀 TECH GUILDS - Execução de Migrations dos Microsserviços")
    print("=" * 60)

    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/tech_guilds",
    )
    print(f"📊 Banco de Dados alvo: {db_url}\n")

    for service_name, ini_path in SERVICES_CONFIG:
        if not ini_path.exists():
            print(f"❌ [ERRO] Configuração não encontrada: {ini_path}")
            sys.exit(1)

        print(f"📦 Aplicando migrations para: [{service_name}]...")
        try:
            alembic_cfg = Config(str(ini_path))
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            command.upgrade(alembic_cfg, "head")
            print(f"✅ [{service_name}] Migrations aplicadas com sucesso!\n")
        except Exception as exc:
            print(f"❌ [{service_name}] Falha na migração: {exc}\n")
            # Se o PostgreSQL não estiver rodando localmente (ex: ambiente de teste sem container),
            # apenas avisa sem abortar os testes offline.
            if "ConnectionRefused" in str(exc) or "Cannot connect" in str(exc):
                print(f"⚠️  Dica: Verifique se o container do PostgreSQL está em execução (docker compose up -d).")
            return False

    print("🎉 Todas as migrations foram executadas com sucesso!")
    return True


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
