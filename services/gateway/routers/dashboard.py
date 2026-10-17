"""Router do Retro RPG Squad Dashboard no API Gateway.

Serve a interface gráfica retrô em pixel art e os endpoints de agregação
de dados (guilda, heróis, mini-boss arena, épico e armory/shop).
"""

from pathlib import Path
from uuid import UUID, uuid4
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse

from services.guilds.primary.rest_api.dependencies.container import (
    get_container as get_guilds_container,
    DependencyContainer as GuildsContainer,
)
from services.gamification.primary.rest_api.dependencies.container import (
    get_gamification_container,
    GamificationContainer,
)
from services.gamification.domain.model.mini_boss import MiniBoss, BossSeverity
from services.gamification.domain.model.quest import Quest, QuestStatus, QuestDifficulty, QuestReward
from services.gamification.domain.ports.primary.sync_hero_progression_port import SyncHeroProgressionCommand

router = APIRouter(prefix="/dashboard", tags=["RPG Dashboard"])

WEB_DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "web_dashboard"
INDEX_HTML_PATH = WEB_DASHBOARD_DIR / "index.html"
ONBOARDING_HTML_PATH = WEB_DASHBOARD_DIR / "onboarding.html"

DEFAULT_SHOP_ITEMS = [
    {
        "id": "shop-1",
        "name": "Keyboard of Infinite Refactoring",
        "type": "weapon",
        "rarity": "rare",
        "price": 120,
        "icon": "⚔️",
        "description": "+15 STR. Eradicates technical debt with zero regressions."
    },
    {
        "id": "shop-2",
        "name": "Staff of Clean Architecture",
        "type": "weapon",
        "rarity": "epic",
        "price": 160,
        "icon": "🪄",
        "description": "+18 INT. Guarantees pure domain boundaries and decoupled ports."
    },
    {
        "id": "shop-3",
        "name": "Shield of 99.99% Uptime",
        "type": "weapon",
        "rarity": "legendary",
        "price": 220,
        "icon": "🛡️",
        "description": "+22 CON. Deflects traffic surges and AWS region outages."
    },
    {
        "id": "shop-4",
        "name": "Cyberpunk Neon Sprite Skin",
        "type": "skin",
        "rarity": "rare",
        "price": 90,
        "icon": "🎨",
        "description": "Cosmetic: Grants your hero a synthwave glowing pixel aura."
    },
    {
        "id": "shop-5",
        "name": "Pizza Feast Squad Buff",
        "type": "perk",
        "rarity": "epic",
        "price": 250,
        "icon": "🍕",
        "description": "Team Perk: +25% XP gain for all squad members during this sprint."
    },
    {
        "id": "shop-6",
        "name": "Cold Brew Elixir of Focus",
        "type": "perk",
        "rarity": "common",
        "price": 80,
        "icon": "☕",
        "description": "Team Perk: Boosts Pair Programming co-op synergy by 15%."
    }
]


def _get_demo_payload() -> Dict[str, Any]:
    """Retorna os dados ricos do esquadrão de demonstração para exibição instantânea."""
    return {
        "guild": {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "The Byte Crusaders",
            "description": "Core Backend, DevOps & Frontend Elite Vanguard",
            "level": 4,
            "experience": 420,
            "experience_to_next_level": 650,
            "experience_percent": 64.6,
            "treasury_gold": 1480,
            "active_members_count": 4,
            "active_adventure_title": "Project Chronos: Multi-Cloud SSO Migration",
            "active_boss_count": 1,
            "tenant_id": "default"
        },
        "heroes": [
            {
                "id": "00000000-0000-0000-0000-000000000101",
                "name": "Gandalf Dev",
                "email": "gandalf@techguilds.io",
                "hero_class": "MAGE",
                "hero_class_label": "Mage (Frontend)",
                "level": 5,
                "experience": 190,
                "experience_to_next_level": 350,
                "health": 120,
                "max_health": 120,
                "health_percent": 100.0,
                "mana": 90,
                "max_mana": 100,
                "gold": 320,
                "stats": {
                    "strength": 11,
                    "intelligence": 25,
                    "constitution": 13,
                    "perception": 15
                },
                "equipped_items": {
                    "weapon": "Staff of Tailwind CSS",
                    "armor": "Robe of Pixel Perfection",
                    "accessory": "Ring of Zero Bugs"
                },
                "status": "CODING",
                "avatar_url": "https://api.dicebear.com/7.x/pixel-art/svg?seed=Gandalf"
            },
            {
                "id": "00000000-0000-0000-0000-000000000102",
                "name": "Conan The Backend",
                "email": "conan@techguilds.io",
                "hero_class": "WARRIOR",
                "hero_class_label": "Warrior (Backend)",
                "level": 4,
                "experience": 210,
                "experience_to_next_level": 400,
                "health": 140,
                "max_health": 140,
                "health_percent": 100.0,
                "mana": 40,
                "max_mana": 60,
                "gold": 280,
                "stats": {
                    "strength": 24,
                    "intelligence": 12,
                    "constitution": 20,
                    "perception": 10
                },
                "equipped_items": {
                    "weapon": "Blade of Postgres Indices",
                    "armor": "Chainmail of ACID",
                    "accessory": "Pendant of Low Latency"
                },
                "status": "PAIRING",
                "avatar_url": "https://api.dicebear.com/7.x/pixel-art/svg?seed=Conan"
            },
            {
                "id": "00000000-0000-0000-0000-000000000103",
                "name": "Legolas QA",
                "email": "legolas@techguilds.io",
                "hero_class": "RANGER",
                "hero_class_label": "Ranger (QA)",
                "level": 3,
                "experience": 150,
                "experience_to_next_level": 300,
                "health": 95,
                "max_health": 100,
                "health_percent": 95.0,
                "mana": 60,
                "max_mana": 70,
                "gold": 190,
                "stats": {
                    "strength": 12,
                    "intelligence": 16,
                    "constitution": 14,
                    "perception": 24
                },
                "equipped_items": {
                    "weapon": "Bow of Cypress End-to-End",
                    "armor": "Tunic of Edge Cases",
                    "accessory": "Quiver of Assertions"
                },
                "status": "TESTING",
                "avatar_url": "https://api.dicebear.com/7.x/pixel-art/svg?seed=Legolas"
            },
            {
                "id": "00000000-0000-0000-0000-000000000104",
                "name": "Uther DevOps",
                "email": "uther@techguilds.io",
                "hero_class": "PALADIN",
                "hero_class_label": "Paladin (DevOps)",
                "level": 4,
                "experience": 280,
                "experience_to_next_level": 400,
                "health": 160,
                "max_health": 160,
                "health_percent": 100.0,
                "mana": 75,
                "max_mana": 80,
                "gold": 410,
                "stats": {
                    "strength": 18,
                    "intelligence": 14,
                    "constitution": 24,
                    "perception": 12
                },
                "equipped_items": {
                    "weapon": "Hammer of Kubernetes Clusters",
                    "armor": "Aegis of Zero Downtime",
                    "accessory": "Talisman of CI/CD"
                },
                "status": "DEPLOYING",
                "avatar_url": "https://api.dicebear.com/7.x/pixel-art/svg?seed=Uther"
            }
        ],
        "active_boss": {
            "id": "00000000-0000-0000-0000-000000000201",
            "external_id": "BUG-904",
            "title": "Lord Memory Leak: Zombie Threads in Production",
            "severity": "CRITICAL",
            "max_health": 250,
            "current_health": 85,
            "health_percent": 34.0,
            "is_defeated": False,
            "bounty_hero_xp": 180,
            "bounty_guild_xp": 350,
            "bounty_gold": 220,
            "avatar": "👾"
        },
        "active_adventure": {
            "id": "00000000-0000-0000-0000-000000000301",
            "external_id": "EPIC-42",
            "title": "Sprint 34: Enterprise Multi-Region Migration",
            "total_quests": 12,
            "completed_quests": 8,
            "progress_percentage": 66.7,
            "is_completed": False,
            "reward_guild_xp": 800,
            "reward_guild_gold": 500
        },
        "quests": [
            {
                "id": "00000000-0000-0000-0000-000000000401",
                "external_id": "TG-101",
                "external_source": "LINEAR",
                "title": "Implementar rate limiter resiliente com Redis Sentinel",
                "status": "DONE",
                "difficulty": "HARD",
                "quest_type": "FEATURE",
                "assignee_name": "Conan The Backend",
                "is_pair_programming": True,
                "rewards": {
                    "hero_xp": 90,
                    "hero_gold": 60,
                    "guild_xp": 120,
                    "guild_gold": 80
                }
            },
            {
                "id": "00000000-0000-0000-0000-000000000402",
                "external_id": "TG-102",
                "external_source": "GITHUB",
                "title": "Migrar componentes de checkout para Tailwind e WebSockets",
                "status": "IN_PROGRESS",
                "difficulty": "MEDIUM",
                "quest_type": "FEATURE",
                "assignee_name": "Gandalf Dev",
                "is_pair_programming": False,
                "rewards": {
                    "hero_xp": 50,
                    "hero_gold": 30,
                    "guild_xp": 70,
                    "guild_gold": 40
                }
            },
            {
                "id": "00000000-0000-0000-0000-000000000403",
                "external_id": "TG-103",
                "external_source": "LINEAR",
                "title": "Configurar suite de testes de integração com Testcontainers",
                "status": "IN_REVIEW",
                "difficulty": "MEDIUM",
                "quest_type": "TEST",
                "assignee_name": "Legolas QA",
                "is_pair_programming": True,
                "rewards": {
                    "hero_xp": 60,
                    "hero_gold": 40,
                    "guild_xp": 80,
                    "guild_gold": 50
                }
            },
            {
                "id": "00000000-0000-0000-0000-000000000404",
                "external_id": "TG-104",
                "external_source": "GITHUB",
                "title": "Criar pipeline de deploy canary no cluster EKS",
                "status": "TODO",
                "difficulty": "EPIC",
                "quest_type": "DEVOPS",
                "assignee_name": "Uther DevOps",
                "is_pair_programming": False,
                "rewards": {
                    "hero_xp": 120,
                    "hero_gold": 90,
                    "guild_xp": 180,
                    "guild_gold": 120
                }
            }
        ],
        "shop_items": DEFAULT_SHOP_ITEMS,
        "combat_log": [
            {
                "timestamp": "10:14:22",
                "message": "Gandalf Dev lançou 'Script de Automação'! Multiplicador de XP ativo.",
                "type": "skill"
            },
            {
                "timestamp": "10:28:40",
                "message": "Conan The Backend desferiu 'Refatoração Brutal' causando 65 de dano no Lord Memory Leak!",
                "type": "combat"
            },
            {
                "timestamp": "11:05:12",
                "message": "Uther DevOps ativou 'Escudo de CI/CD' protegendo o esquadrão contra bugs críticos.",
                "type": "buff"
            },
            {
                "timestamp": "11:42:01",
                "message": "Quest TG-101 concluída! +120 Guild XP depositados no cofre.",
                "type": "loot"
            }
        ]
    }


def _class_label(hero_class: str) -> str:
    labels = {
        "WARRIOR_BACKEND": "Warrior (Backend)",
        "WARRIOR": "Warrior (Backend)",
        "MAGE_FRONTEND": "Mage (Frontend)",
        "MAGE": "Mage (Frontend)",
        "PALADIN_DEVOPS": "Paladin (DevOps)",
        "PALADIN": "Paladin (DevOps)",
        "RANGER_QA": "Ranger (QA)",
        "RANGER": "Ranger (QA)",
        "TACTICIAN_TL": "Tactician (Tech Lead)",
        "TACTICIAN": "Tactician (Tech Lead)",
        "NOVICE": "Novice"
    }
    return labels.get(hero_class, "Novice")


def _default_gear(hero_class: str) -> Dict[str, str]:
    if "WARRIOR" in hero_class:
        return {
            "weapon": "Blade of Postgres Indices",
            "armor": "Chainmail of ACID Compliance",
            "accessory": "Pendant of Low Latency",
        }
    elif "MAGE" in hero_class:
        return {
            "weapon": "Staff of Tailwind CSS",
            "armor": "Robe of Pixel Perfection",
            "accessory": "Ring of Zero React Re-renders",
        }
    elif "PALADIN" in hero_class:
        return {
            "weapon": "Mace of Kubernetes Orchestration",
            "armor": "Shield of CI/CD Pipeline",
            "accessory": "Relic of 99.99% Uptime",
        }
    elif "RANGER" in hero_class:
        return {
            "weapon": "Bow of Cypress End-to-End",
            "armor": "Tunic of Edge Case Detection",
            "accessory": "Quiver of Jest Mocks",
        }
    elif "TACTICIAN" in hero_class:
        return {
            "weapon": "Tome of Clean Architecture",
            "armor": "Cloak of Sprint Velocity",
            "accessory": "Signet Ring of Unblocked PRs",
        }
    return {
        "weapon": "Wooden Keyboard",
        "armor": "Cotton T-shirt",
        "accessory": "Plastic ID Badge",
    }


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Entrega a página HTML do Retro RPG Squad Dashboard."""
    if not INDEX_HTML_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Arquivo do dashboard HTML não encontrado."
        )
    return HTMLResponse(content=INDEX_HTML_PATH.read_text(encoding="utf-8"))


@router.get("/onboarding", response_class=HTMLResponse)
async def serve_onboarding():
    """Entrega a página HTML de Onboarding de Herói e Criação de Squad."""
    if not ONBOARDING_HTML_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Arquivo de onboarding HTML não encontrado."
        )
    return HTMLResponse(content=ONBOARDING_HTML_PATH.read_text(encoding="utf-8"))


@router.get("/static/css/retro.css")
async def serve_retro_css():
    """Serve o arquivo CSS retro para estilização em pixel art."""
    css_path = WEB_DASHBOARD_DIR / "static" / "css" / "retro.css"
    if not css_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo retro.css não encontrado."
        )
    return FileResponse(css_path, media_type="text/css")


@router.get("/data/demo")
async def get_demo_dashboard_data():
    """Retorna os dados ricos do esquadrão de demonstração para testes instantâneos da UI."""
    return _get_demo_payload()


@router.get("/data/{guild_id}")
async def get_dashboard_data(
    guild_id: str,
    guilds_container: GuildsContainer = Depends(get_guilds_container),
    gamification_container: GamificationContainer = Depends(get_gamification_container),
):
    """Retorna o payload completo do dashboard (guilda, membros, quests, shop) em uma única chamada."""
    if guild_id.lower() == "demo":
        return _get_demo_payload()

    try:
        guild_uuid = UUID(guild_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID da guilda deve ser um UUID válido ou 'demo'."
        )

    guild = await guilds_container.guild_repository.get_by_id(guild_uuid)
    if guild is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guilda não encontrada."
        )

    guild_tenant = getattr(guild, "tenant_id", "default") or "default"

    # Membros da guilda
    members = await guilds_container.member_repository.find_by_guild_id(guild.id)
    heroes_data = []
    for m in members:
        # Busca a ficha de RPG real no microsserviço de gamificação
        hero_prog = await gamification_container.hero_repo.get_by_id(m.hero_id)
        if hero_prog is None:
            try:
                sync_res = await gamification_container.sync_hero_progression.execute(
                    SyncHeroProgressionCommand(
                        hero_id=m.hero_id,
                        name=m.name,
                        email=m.email,
                        hero_class=m.hero_class,
                        level=m.level,
                        tenant_id=guild_tenant,
                    )
                )
                hero_prog = sync_res.hero_progression
            except Exception:
                hero_prog = None

        h_level = hero_prog.level if hero_prog else m.level
        h_exp = hero_prog.exp if hero_prog else 0
        h_exp_next = hero_prog.experience_to_next_level if hero_prog else 100
        h_hp = hero_prog.hp if hero_prog else 100
        h_max_hp = hero_prog.max_hp if hero_prog else 100
        h_mana = hero_prog.mana if hero_prog else 50
        h_max_mana = hero_prog.max_mana if hero_prog else 50
        h_gold = hero_prog.gold if hero_prog else 0
        h_stats = (
            hero_prog.stats.to_dict()
            if hero_prog and hasattr(hero_prog.stats, "to_dict")
            else {"strength": 12, "intelligence": 12, "constitution": 12, "perception": 12}
        )

        heroes_data.append({
            "id": str(m.hero_id),
            "name": m.name,
            "email": m.email,
            "hero_class": m.hero_class,
            "hero_class_label": _class_label(m.hero_class),
            "level": h_level,
            "experience": h_exp,
            "experience_to_next_level": h_exp_next,
            "health": h_hp,
            "max_health": h_max_hp,
            "health_percent": round((h_hp / max(1, h_max_hp)) * 100.0, 1),
            "mana": h_mana,
            "max_mana": h_max_mana,
            "gold": h_gold,
            "stats": h_stats,
            "equipped_items": _default_gear(m.hero_class),
            "status": "CODING",
            "avatar_url": m.avatar_url or f"https://api.dicebear.com/7.x/adventurer/svg?seed={m.name}"
        })

    # Bosses e Quests
    bosses = await gamification_container.boss_repo.list_active_by_guild(guild.id)
    quests = await gamification_container.quest_repo.list_by_guild(guild.id)

    # Se a guilda ainda não possui tarefas ou mini-bosses no banco, gera o starter pack
    if not quests and not bosses:
        starter_boss = MiniBoss(
            id=uuid4(),
            external_id=f"BUG-{str(guild.id)[:4].upper()}",
            title="Lord Memory Leak: Zombie Threads in Production",
            severity=BossSeverity.CRITICAL,
            max_health=200,
            current_health=200,
            is_defeated=False,
            bounty_hero_xp=150,
            bounty_guild_xp=300,
            bounty_gold=180,
            guild_id=guild.id,
            tenant_id=guild_tenant,
        )
        await gamification_container.boss_repo.save(starter_boss)
        bosses = [starter_boss]

        starter_quests = [
            Quest(
                id=uuid4(),
                external_id=f"TG-{str(guild.id)[:3].upper()}-101",
                external_source="LINEAR",
                title="Configurar autenticação corporativa via SSO & JWT",
                guild_id=guild.id,
                status=QuestStatus.DONE,
                difficulty=QuestDifficulty.HARD,
                is_pair_programming=True,
                tenant_id=guild_tenant,
            ),
            Quest(
                id=uuid4(),
                external_id=f"TG-{str(guild.id)[:3].upper()}-102",
                external_source="GITHUB",
                title="Construir componentes interativos do Dashboard em React & Tailwind",
                guild_id=guild.id,
                status=QuestStatus.IN_PROGRESS,
                difficulty=QuestDifficulty.MEDIUM,
                is_pair_programming=False,
                tenant_id=guild_tenant,
            ),
            Quest(
                id=uuid4(),
                external_id=f"TG-{str(guild.id)[:3].upper()}-103",
                external_source="LINEAR",
                title="Implementar persistência nos schemas PostgreSQL e mensageria NATS",
                guild_id=guild.id,
                status=QuestStatus.TODO,
                difficulty=QuestDifficulty.MEDIUM,
                is_pair_programming=True,
                tenant_id=guild_tenant,
            ),
            Quest(
                id=uuid4(),
                external_id=f"TG-{str(guild.id)[:3].upper()}-104",
                external_source="GITHUB",
                title="Criar suíte de testes de integração com Testcontainers",
                guild_id=guild.id,
                status=QuestStatus.TODO,
                difficulty=QuestDifficulty.HARD,
                is_pair_programming=False,
                tenant_id=guild_tenant,
            ),
        ]
        for q in starter_quests:
            await gamification_container.quest_repo.save(q)
        quests = starter_quests

    active_boss_data = None
    if bosses:
        boss = bosses[0]
        b_max = max(1, boss.max_health)
        active_boss_data = {
            "id": str(boss.id),
            "external_id": boss.external_id,
            "title": boss.title,
            "severity": boss.severity.value if hasattr(boss.severity, "value") else str(boss.severity),
            "max_health": boss.max_health,
            "current_health": boss.current_health,
            "health_percent": round((boss.current_health / b_max) * 100.0, 1),
            "is_defeated": boss.is_defeated,
            "bounty_hero_xp": boss.bounty_hero_xp,
            "bounty_guild_xp": boss.bounty_guild_xp,
            "bounty_gold": boss.bounty_gold,
            "avatar": "👾" if str(boss.severity) in ("CRITICAL", "HIGH") else "🐛",
        }

    quests_data = []
    for q in quests:
        rew = q.calculate_rewards()
        quests_data.append({
            "id": str(q.id),
            "external_id": q.external_id,
            "external_source": q.external_source,
            "title": q.title,
            "status": q.status.value if hasattr(q.status, "value") else str(q.status),
            "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
            "quest_type": "TASK",
            "assignee_name": None,
            "is_pair_programming": q.is_pair_programming,
            "rewards": {
                "hero_xp": rew.hero_xp,
                "hero_gold": rew.hero_gold,
                "guild_xp": rew.guild_xp,
                "guild_gold": rew.guild_gold,
            }
        })

    total_q = len(quests)
    done_q = sum(1 for q in quests if (q.status.value if hasattr(q.status, "value") else str(q.status)) == "DONE")
    progress_pct = round((done_q / max(1, total_q)) * 100.0, 1)

    active_adventure_data = {
        "id": str(guild.id),
        "external_id": f"SPRINT-{guild.level}",
        "title": f"Sprint Ciclo {guild.level}: Conquista de Infraestrutura & Features",
        "total_quests": total_q,
        "completed_quests": done_q,
        "progress_percentage": progress_pct,
        "is_completed": done_q == total_q and total_q > 0,
        "reward_guild_xp": 500,
        "reward_guild_gold": 300,
    }

    g_exp_next = max(1, guild.experience_to_next_level)
    exp_percent = round(min(100.0, (guild.experience / g_exp_next) * 100.0), 1)

    return {
        "guild": {
            "id": str(guild.id),
            "name": guild.name,
            "description": guild.description,
            "level": guild.level,
            "experience": guild.experience,
            "experience_to_next_level": guild.experience_to_next_level,
            "experience_percent": exp_percent,
            "treasury_gold": guild.treasury_gold,
            "active_members_count": len(members),
            "active_adventure_title": active_adventure_data["title"],
            "active_boss_count": len([b for b in bosses if not b.is_defeated]),
            "tenant_id": guild_tenant,
        },
        "heroes": heroes_data,
        "active_boss": active_boss_data,
        "active_adventure": active_adventure_data,
        "quests": quests_data,
        "shop_items": DEFAULT_SHOP_ITEMS,
        "combat_log": [
            {
                "timestamp": "Agora",
                "message": f"Guilda '{guild.name}' sincronizada com o banco PostgreSQL e NATS JetStream!",
                "type": "loot",
            }
        ],
    }
