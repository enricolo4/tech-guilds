# 🛡️ Tech Guilds — Microsserviços Hexagonais

Malha de microsserviços em **Python 3.14** construídos sob **Arquitetura Hexagonal Pura (Ports & Adapters)** e orientados a eventos via **NATS JetStream**, com persistência no **PostgreSQL 16** através de schemas isolados.

---

## 🏛️ Diretrizes de Domínio Puro

Cada microsserviço dentro de `services/` segue rigorosamente:
- `domain/model/`: Dataclasses de domínio puro. **Sem entidades**, sem frameworks (zero SQLAlchemy, zero Pydantic).
- `domain/ports/primary/`: Portas Primárias de entrada. Todo caso de uso implementa formalmente uma interface de Primary Port.
- `domain/ports/secondary/`: Portas Secundárias de saída para persistência e mensageria.
- `domain/use_cases/`: Casos de uso segregados implementando sua respectiva Primary Port.
- `primary/`: REST API com FastAPI (controllers injetam Primary Ports via Depends) e ouvintes NATS.
- `secondary/`: Adaptadores PostgreSQL (SQLAlchemy models com `__table_args__ = {"schema": "..."}`), NATS JetStream publishers e SSO.
- `secondary/postgresql/migrations/`: Versionamento Alembic dedicado ao schema exclusivo do serviço (`version_table_schema`).

---

## 📦 Lista de Microsserviços

### 1. Registration (`services/registration`)
- **Schema:** `registration`
- **Tabelas:** `registration.heroes`
- **Use Cases:** `RegisterHeroUseCase` (implementa `RegisterHeroPort`).
- **Eventos:** Publica `HeroRegisteredEvent` no subject `tech_guilds.hero.registered`.

### 2. Auth (`services/auth`)
- **Schema:** `auth`
- **Tabelas:** `auth.sessions`
- **Use Cases:** `AuthenticateSSOUseCase`, `ValidateSessionUseCase`.
- **Segurança:** Emissão e validação de tokens JWT (HS256) e adaptador multi-provedor SSO (Google, GitHub, Azure).

### 3. Guilds (`services/guilds`)
- **Schema:** `guilds`
- **Tabelas:** `guilds.guilds`, `guilds.members`
- **Use Cases:** `CreateGuildUseCase`, `AddMemberUseCase`, `SyncHeroMemberUseCase`.
- **Eventos:** Consome `tech_guilds.hero.registered` para criar/atualizar a projeção do membro em `guilds.members`.

### 4. Gamification (`services/gamification`)
- **Schema:** `gamification`
- **Tabelas:** `gamification.hero_progressions`, `gamification.mini_bosses`, `gamification.quests`
- **Use Cases:** `ProcessCardEventUseCase`, `ProcessBugEventUseCase`, `CastSkillUseCase`, `EquipItemUseCase`, `SyncHeroProgressionUseCase`.
- **Eventos:** Consome `tech_guilds.hero.registered` para inicializar os atributos RPG e barra de HP/Mana do herói em `gamification.hero_progressions`.

### 5. API Gateway (`services/gateway`)
- Ponto de entrada unificado agregando os roteadores FastAPI:
  - `/api/registration/*`
  - `/api/auth/*`
  - `/api/guilds/*`
  - `/api/gamification/*`
  - `/dashboard/data/*`
- Inicializa os ouvintes NATS JetStream em background via ciclo de vida `lifespan`.

---

## 🧪 Testes dos Microsserviços

```bash
# Executar testes de todos os microsserviços via Nx
npx nx run-many -t test

# Ou via Poetry diretamente:
TESTING=true poetry run pytest services/ -v
```
