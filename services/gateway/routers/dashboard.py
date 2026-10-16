"""Router do Retro RPG Squad Dashboard no API Gateway.

Serve a interface gráfica retrô em pixel art e os endpoints de agregação
de dados (guilda, heróis, mini-boss arena, épico e armory/shop).
"""

from pathlib import Path
from uuid import UUID
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse

from services.guilds.primary.rest_api.dependencies.container import (
    get_container as get_guilds_container,
    DependencyContainer as GuildsContainer,
)
from services.gamification.primary.rest_api.dependencies.container import (
    get_in_memory_container as get_gamification_container,
    GamificationContainer,
)

router = APIRouter(prefix="/dashboard", tags=["RPG Dashboard"])

WEB_DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "web_dashboard"
INDEX_HTML_PATH = WEB_DASHBOARD_DIR / "index.html"

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
            "active_boss_count": 1
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

    # Membros da guilda
    members = await guilds_container.member_repository.list_by_guild(guild.id)
    heroes_data = []
    for m in members:
        heroes_data.append({
            "id": str(m.hero_id),
            "name": m.name,
            "email": m.email,
            "hero_class": m.hero_class,
            "hero_class_label": _class_label(m.hero_class),
            "level": 1,
            "experience": 0,
            "experience_to_next_level": 100,
            "health": 100,
            "max_health": 100,
            "health_percent": 100.0,
            "mana": 50,
            "max_mana": 50,
            "gold": 0,
            "stats": {"strength": 10, "intelligence": 10, "constitution": 10, "perception": 10},
            "equipped_items": _default_gear(m.hero_class),
            "status": "CODING",
            "avatar_url": f"https://api.dicebear.com/7.x/pixel-art/svg?seed={m.name}"
        })

    # Bosses e Quests
    bosses = await gamification_container.mini_boss_repo.list_active()
    active_boss_data = None
    if bosses:
        boss = bosses[0]
        b_max = max(1, boss.max_health)
        active_boss_data = {
            "id": str(boss.id),
            "external_id": boss.external_id,
            "title": boss.title,
            "severity": boss.severity.value,
            "max_health": boss.max_health,
            "current_health": boss.current_health,
            "health_percent": round((boss.current_health / b_max) * 100.0, 1),
            "is_defeated": boss.is_defeated,
            "bounty_hero_xp": boss.bounty_hero_xp,
            "bounty_guild_xp": boss.bounty_guild_xp,
            "bounty_gold": boss.bounty_gold,
            "avatar": "👾" if boss.severity.value in ("CRITICAL", "HIGH") else "🐛",
        }

    quests = await gamification_container.quest_repo.list_active()
    quests_data = []
    for q in quests:
        quests_data.append({
            "id": str(q.id),
            "external_id": q.external_id,
            "external_source": "SYSTEM",
            "title": q.title,
            "status": q.status.value,
            "difficulty": q.difficulty.value,
            "quest_type": "TASK",
            "assignee_name": None,
            "is_pair_programming": False,
            "rewards": {
                "hero_xp": q.reward.hero_xp,
                "hero_gold": q.reward.hero_gold,
                "guild_xp": q.reward.guild_xp,
                "guild_gold": q.reward.guild_gold,
            }
        })

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
            "active_adventure_title": None,
            "active_boss_count": len(bosses),
        },
        "heroes": heroes_data,
        "active_boss": active_boss_data,
        "active_adventure": None,
        "quests": quests_data,
        "shop_items": DEFAULT_SHOP_ITEMS,
        "combat_log": [
            {
                "timestamp": "12:00:00",
                "message": f"Guilda '{guild.name}' conectada com sucesso ao RPG Dashboard!",
                "type": "loot",
            }
        ],
    }
