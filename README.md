# Tech Guilds ⚔️

Motor cooperativo de gamificação em RPG retrô para **Squads de Tecnologia**, inspirado no Habitica e desenhado especificamente para equipes de engenharia de software integradas com **Linear, Jira, GitHub e SSO Corporativo**.

---

## 🏛️ Arquitetura Hexagonal (Ports & Adapters)

O projeto segue rigorosamente o padrão estabelecido em [`ARCHITECTURE_SKILL.md`](../docs/ARCHITECTURE_SKILL.md):

```text
tech-guilds/
├── domain/                                  # 100% puro, sem frameworks externos
│   ├── model/
│   │   ├── hero.py                          # Desenvolvedor (Classe, Stats, Nível, EXP, HP)
│   │   ├── guild.py                         # Squad de Engenharia (Nível, Baú de Ouro, Membros)
│   │   ├── quest.py                         # Cards de Tarefas (Feature, Débito, Chores)
│   │   ├── adventure.py                     # Épicos / Milestones com recompensa coletiva
│   │   ├── mini_boss.py                     # Bugs / Incidentes que atacam a guilda
│   │   └── user_claims.py                   # Dados de identidade do SSO
│   ├── ports/                               # Interfaces abstratas puras (ABCs)
│   │   ├── repositories.py                  # HeroRepository, GuildRepository, etc.
│   │   ├── sso_port.py                      # Validação de tokens de identidade corporativa
│   │   └── notification_port.py             # Alertas nos canais da guilda
│   └── use_cases/                           # Regras de orquestração do negócio
│       ├── authenticate_hero.py             # Login SSO com auto-provisionamento no Nível 1
│       ├── process_card_event.py            # Evento de card (recompensas, co-op, épicos)
│       └── process_bug_event.py             # Ciclo de vida dos Mini-Bosses (Bugs/Incidentes)
│
├── primary/                                 # Adaptadores de entrada (Driving)
│   └── rest_api/                            # FastAPI
│       ├── main.py                          # Ponto de entrada da aplicação HTTP
│       ├── dependencies/                    # Injeção de dependências tipada e autenticação
│       ├── routers/
│       │   ├── auth.py                      # /auth/sso/login, /heroes/me, /heroes/me/class
│       │   ├── webhooks.py                  # /webhooks/cards, /webhooks/bugs
│       │   └── guilds.py                    # /guilds, /guilds/{id}, /guilds/{id}/join
│       └── schemas/                         # DTOs de entrada e saída (Pydantic v2)
│
└── secondary/                               # Adaptadores de saída (Driven)
    ├── postgresql/                          # Repositórios de persistência
    ├── sso_adapter/                         # Validação multi-provedor (Google, GitHub, Azure/Microsoft)
    ├── slack_adapter/                       # Notificador do Slack / Discord da guilda
    └── linear_adapter/                      # Cliente de integração direta com API do Linear
```

---

## 🎮 Mecânicas Principais

1. **Auto-provisionamento via SSO Corporativo:**
   * O desenvolvedor faz login com sua conta do **Google Workspace**, **GitHub Enterprise** ou **Azure AD / Microsoft Entra**.
   * No primeiro login, seu Herói é gerado automaticamente no **Nível 1 (Classe Novice)**.
2. **Classes de Engenharia:**
   * 🔨 **Ferreiro (Warrior / Backend):** Bônus de Força e dano em Mini-Bosses.
   * 🎨 **Ilusionista (Mage / Frontend):** Foco em Inteligência e ganho acelerado de EXP.
   * 🛡️ **Guardião (Paladin / DevOps & SRE):** Bônus de Constituição e proteção contra incidentes.
   * 🏹 **Caçador de Sombras (Ranger / QA):** Acertos críticos e busca de recompensas.
   * 📜 **Estrategista (Tactician / Tech Lead & PM):** Buffs táticos para todo o Squad.
3. **Cards & Épicos:**
   * Cards concluídos no Linear ou Jira rendem EXP e Ouro para o Herói e para a Guilda.
   * **Buff de Pair Programming:** Tarefas realizadas em dupla ganham **+30% de bônus de EXP**.
   * Ao finalizar todas as tarefas de um **Épico (Aventura)**, a Guilda inteira recebe um bônus massivo coletivo.
4. **Bugs como Mini-Bosses:**
   * Quando um bug P0/P1 é aberto, um **Mini-Boss** surge no canal do Squad atacando a equipe.
   * Quando o bug é corrigido, o Mini-Boss é derrotado e a recompensa (*Bounty*) é creditada para o herói e para a guilda.

---

## 🚀 Gerenciamento com Poetry

O projeto utiliza o **Poetry** para empacotamento e gestão de dependências.

### 1. Instalação do Ambiente Virtual e Dependências
```bash
cd tech-guilds
poetry install
```

### 2. Executando os Testes Automatizados
```bash
poetry run pytest tests -v
```

### 3. Subindo o Servidor FastAPI Localmente
```bash
poetry run uvicorn primary.rest_api.main:app --reload --port 8000
```
* **Swagger UI interativo:** `http://localhost:8000/docs`
* **Health Check:** `http://localhost:8000/health`

