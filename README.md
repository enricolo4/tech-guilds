# Tech Guilds ⚔️

Motor cooperativo de gamificação em RPG retrô para **Squads de Engenharia de Software**, inspirado no Habitica e desenhado especificamente para equipes integradas com **Linear, Jira, GitHub e SSO Corporativo**.

O projeto é estruturado como um **Monorepo Nx Poliglota** composto por uma malha de **Microsserviços Hexagonais em Python 3.14** orientados a eventos via **NATS JetStream**, banco de dados **PostgreSQL 16** com isolamento por schemas, **Frontend Web em React + Vite + Tailwind CSS** e **Aplicativo Mobile em Flutter**.

---

## 🏛️ Topologia de Arquitetura

```mermaid
flowchart TD
    subgraph Clients["Aplicações Clientes (apps/)"]
        Web["apps/web\n(React 18 + Vite + Tailwind CSS)"]
        Mobile["apps/mobile\n(Flutter iOS / Android)"]
    end

    subgraph Nx["Orquestração: Nx Monorepo"]
        NxCLI["Nx CLI & Task Pipeline\n(Smart Caching, Affected & Graph)"]
    end

    subgraph Gateway["API Gateway (Porta 8000)"]
        GW["services/gateway\n(FastAPI Gateway)"]
    end

    subgraph Microservices["Microsserviços Hexagonais (services/)"]
        Reg["services/registration\n(Schema: registration)"]
        Auth["services/auth\n(Schema: auth)"]
        Guilds["services/guilds\n(Schema: guilds)"]
        Gami["services/gamification\n(Schema: gamification)"]
    end

    NATS[("NATS JetStream\nStream: TECH_GUILDS\nPorta 4222")]
    DB[("PostgreSQL 16\nPorta 5433\n4 Schemas Isolados")]

    Web -->|HTTP / REST (Proxy :3000 -> :8000)| GW
    Mobile -->|HTTP / REST| GW

    GW -->|/api/registration| Reg
    GW -->|/api/auth| Auth
    GW -->|/api/guilds| Guilds
    GW -->|/api/gamification| Gami

    Reg -- "tech_guilds.hero.registered" --> NATS
    NATS -->|Sync Projeção Membro| Guilds
    NATS -->|Sync Ficha RPG & Stats| Gami

    Reg -. Schema: registration .-> DB
    Auth -. Schema: auth .-> DB
    Guilds -. Schema: guilds .-> DB
    Gami -. Schema: gamification .-> DB

    NxCLI -. Orquestra .-> Web
    NxCLI -. Orquestra .-> Mobile
    NxCLI -. Orquestra .-> Microservices
```

---

## 📂 Estrutura do Monorepo Nx

```text
tech-guilds/
├── nx.json                     # Configuração global de caching e tarefas do Nx
├── package.json                # Gerenciador raiz do Monorepo e dependências de tooling
├── pyproject.toml              # Dependências Poetry dos microsserviços Python
├── docker-compose.yml          # PostgreSQL 16 (porta 5433) + NATS JetStream 2.10 (porta 4222)
│
├── apps/                       # Aplicações de Interface com o Usuário
│   ├── web/                    # Frontend Web em React 18 + Vite + TypeScript + Tailwind CSS
│   │   ├── src/
│   │   │   ├── pages/          # OnboardingPage.tsx, DashboardPage.tsx
│   │   │   ├── components/     # Header.tsx, Retro UI Components
│   │   │   ├── api/            # client.ts (integração tipada com o Gateway)
│   │   │   └── types.ts        # Tipos TypeScript compartilhados
│   │   ├── project.json        # Alvos do Nx: build, serve, preview
│   │   └── vite.config.ts      # Proxy para http://localhost:8000
│   │
│   └── mobile/                 # Aplicativo Mobile em Flutter (iOS e Android)
│       ├── lib/main.dart       # Ponto de entrada do app Flutter
│       ├── pubspec.yaml        # Dependências Dart/Flutter
│       └── project.json        # Alvos do Nx: serve, build, test
│
├── services/                   # Microsserviços Hexagonais Independentes (Python 3.14)
│   ├── registration/           # Onboarding de heróis via SSO e emissão de eventos NATS
│   ├── auth/                   # Validação de credenciais SSO e emissão de tokens JWT
│   ├── guilds/                 # Gestão de Guildas, Squads, Cofre de Ouro e Projeções
│   ├── gamification/           # Quests (Linear/GitHub), Combate a Mini-Bosses e Loja RPG
│   ├── gateway/                # API Gateway unificado agregando rotas e consumidores
│   └── common/                 # Schemas de eventos e provisionamento NATS JetStream
│
└── scripts/                    # Scripts de infraestrutura e automação
    ├── dev.sh                  # Inicialização em um comando (Docker + Migrations + Gateway)
    ├── run_migrations.py       # Runner de migrations Alembic dos 4 schemas isolados
    └── init-db/                # DDL de provisionamento dos schemas no PostgreSQL
```

---

## 🧩 Os 4 Microsserviços Hexagonais

Cada microsserviço dentro de `services/` implementa **Arquitetura Hexagonal pura**:
- `domain/model/`: Entidades e modelos puros do domínio (dataclasses sem frameworks).
- `domain/ports/primary/`: Interfaces formais que todo caso de uso implementa obrigatoriamente.
- `domain/ports/secondary/`: Interfaces para persistência e mensageria.
- `domain/use_cases/`: Implementação da lógica de negócio.
- `primary/`: Controladores REST via FastAPI e Consumidores NATS JetStream.
- `secondary/`: Repositórios PostgreSQL (SQLAlchemy) e Publicadores NATS JetStream.
- `secondary/postgresql/migrations/`: Versionamento Alembic dedicado ao schema do serviço.

| Microsserviço | Responsabilidade | Schema PostgreSQL | Eventos Produzidos | Eventos Consumidos |
|---|---|---|---|---|
| **Registration** | Onboarding de heróis, seleção de classe e identidade | `registration` | `hero.registered` | - |
| **Auth** | Login SSO corporativo e validação de tokens JWT | `auth` | - | - |
| **Guilds** | Squads, cofres compartilhados e projeção de membros | `guilds` | `guild.created` | `hero.registered` |
| **Gamification** | Quests (Linear/GitHub), Combate a Mini-Bosses e Loja RPG | `gamification` | `quest.completed` | `hero.registered` |

---

## ⚡ Barramento de Eventos (NATS JetStream)

- **Stream Central:** `TECH_GUILDS`
- **Tópico Principal:** `tech_guilds.hero.registered`
- **Fluxo:** Quando um herói conclui seu cadastro no serviço de **Registration**, o evento `HeroRegisteredEvent` é emitido. Os serviços de **Guilds** e **Gamification** escutam o evento em background e atualizam seus respectivos schemas em tempo real.

---

## 🗄️ Isolamento de Banco de Dados

- **PostgreSQL 16 Alpine** mapeado na porta externa **`5433`** (evitando conflitos com instâncias locais).
- 4 schemas independentes:
  - `registration.heroes`
  - `auth.sessions`
  - `guilds.guilds` e `guilds.members`
  - `gamification.hero_progressions`, `gamification.mini_bosses`, `gamification.quests`
- Runner unificado em [`scripts/run_migrations.py`](scripts/run_migrations.py).

---

## 🎮 Mecânicas do Jogo

1. **Classes de Tecnologia:**
   - ⚔️ **Warrior (Backend Developer):** Foco em integridade ACID e dano contra incidentes de banco de dados. (*Blade of Postgres Indices*).
   - 🪄 **Mage (Frontend Developer):** Mestre de UI/UX, componentes reativos e Tailwind. (*Staff of Tailwind CSS*).
   - 🛡️ **Paladin (DevOps / SRE):** Guardião do 99.99% Uptime e esteiras de CI/CD. (*Hammer of Kubernetes*).
   - 🏹 **Ranger (QA / Software Tester):** Caçador implacável de bugs em produção e testes E2E. (*Bow of Cypress End-to-End*).
   - 📜 **Tactician (Tech Lead):** Desbloqueio de squad, arquitetura limpa e buffs de sprint. (*Tome of Clean Architecture*).
   - 🐣 **Novice (Iniciante / Trainee):** Aprendiz flexível pronto para escolher qualquer especialização.
2. **Quests via Webhooks:**
   - Cards finalizados no **Linear** ou **GitHub** creditam EXP e Ouro para o herói e para o cofre do esquadrão.
   - Tarefas em **Pair Programming** ganham **+30% de bônus cooperativo**.
3. **Mini-Bosses (Incidentes em Produção):**
   - Bugs críticos abertos no Linear ou GitHub invocam um Mini-Boss com HP escalonado pela severidade (P0/P1).
   - Ao resolver o bug e mergear o PR, o Boss é derrotado gerando recompensas coletivas para a guilda.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- **Docker** e **Docker Compose**
- **Python 3.14** e **Poetry**
- **Node.js 20+** e **npm**

### 1. Inicialização Rápida de Infraestrutura e Backend
```bash
# Executa containers, roda as migrations e sobe o Gateway
./scripts/dev.sh
```

Ou passo a passo:
```bash
# Subir PostgreSQL (porta 5433) e NATS JetStream (porta 4222)
docker compose up -d  # ou docker-compose up -d

# Executar as migrações dos 4 schemas
poetry run python scripts/run_migrations.py

# Iniciar o API Gateway (porta 8000)
npx nx serve gateway
```

### 2. Iniciar o Frontend Web em React
Em outro terminal:
```bash
# Inicia a aplicação React com Vite (porta 3000)
npx nx serve web
```

---

## 🛠️ Comandos do Monorepo Nx

```bash
# Executar todos os testes do monorepo em paralelo (com cache inteligente)
npx nx run-many -t test

# Executar testes apenas do microsserviço de cadastro
npx nx test registration

# Gerar build de produção do frontend React
npx nx build web

# Visualizar o grafo interativo de arquitetura e dependências
npx nx graph
```

---

## 🌐 URLs de Acesso

| Serviço | URL | Descrição |
|---|---|---|
| **Frontend Web (React)** | [http://localhost:3000](http://localhost:3000) | Interface moderna em React (Onboarding & Squad Dashboard) |
| **API Gateway (FastAPI)** | [http://localhost:8000](http://localhost:8000) | Gateway unificado agregando os 4 microsserviços |
| **Swagger UI Interativo** | [http://localhost:8000/docs](http://localhost:8000/docs) | Documentação de todos os endpoints REST |
| **NATS JetStream Monitoring** | [http://localhost:8222](http://localhost:8222) | Painel HTTP oficial de métricas do NATS |
