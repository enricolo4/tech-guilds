#!/usr/bin/env bash
set -e

# Cores para terminal
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}    🛡️  TECH GUILDS - AMBIENTE DE DESENVOLVIMENTO  ⚔️     ${NC}"
echo -e "${CYAN}======================================================${NC}"

# 1. Verifica/sobe infraestrutura Docker (PostgreSQL + NATS JetStream)
echo -e "\n${YELLOW}[1/4] Subindo infraestrutura Docker (Postgres + NATS JetStream)...${NC}"
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose up -d
    echo -e "${GREEN}✓ Containers ativos com sucesso via docker-compose.${NC}"
elif docker compose version >/dev/null 2>&1; then
    docker compose up -d
    echo -e "${GREEN}✓ Containers ativos com sucesso via docker compose.${NC}"
else
    echo -e "${RED}⚠️ Docker Compose não encontrado no PATH. Certifique-se de que o Postgres e o NATS estão rodando localmente.${NC}"
fi

# 2. Aguarda PostgreSQL e NATS estarem prontos
echo -e "\n${YELLOW}[2/4] Aguardando serviços de infraestrutura estarem saudáveis...${NC}"
sleep 2

# 3. Executa as Migrations dos Schemas
echo -e "\n${YELLOW}[3/4] Executando Migrations dos 4 Schemas isolados...${NC}"
if command -v poetry >/dev/null 2>&1; then
    poetry run python scripts/run_migrations.py || true
else
    python3 scripts/run_migrations.py || true
fi

# 4. Inicia o API Gateway e o Dashboard
echo -e "\n${YELLOW}[4/4] Inicializando API Gateway, Microsserviços e Dashboard RPG...${NC}"
echo -e "${GREEN}🎮 Dashboard disponível em: http://localhost:8000/dashboard${NC}"
echo -e "${GREEN}📚 Documentação Swagger em: http://localhost:8000/docs${NC}"
echo -e "${GREEN}⚡ NATS JetStream ativo em: nats://localhost:4222 (Monitoring: http://localhost:8222)${NC}\n"

if command -v poetry >/dev/null 2>&1; then
    poetry run uvicorn services.gateway.main:app --host 0.0.0.0 --port 8000 --reload
else
    python3 -m uvicorn services.gateway.main:app --host 0.0.0.0 --port 8000 --reload
fi
