from pathlib import Path
from uuid import UUID
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse

from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.entities.hero import HeroClass
from ..dependencies.container import DependencyContainer, get_container

router = APIRouter(prefix="/dashboard", tags=["RPG Dashboard"])

WEB_DASHBOARD_DIR = Path(__file__).resolve().parent.parent.parent / "web_dashboard"
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
                "name": "Valkyrie SRE",
                "email": "valkyrie@techguilds.io",
                "hero_class": "PALADIN",
                "hero_class_label": "Paladin (DevOps)",
                "level": 6,
                "experience": 310,
                "experience_to_next_level": 550,
                "health": 160,
                "max_health": 160,
                "health_percent": 100.0,
                "mana": 75,
                "max_mana": 80,
                "gold": 450,
                "stats": {
                    "strength": 15,
                    "intelligence": 16,
                    "constitution": 28,
                    "perception": 14
                },
                "equipped_items": {
                    "weapon": "Hammer of Kubernetes",
                    "armor": "Aegis of 99.99% Uptime",
                    "accessory": "Helm of Prometheus"
                },
                "status": "ON-CALL",
                "avatar_url": "https://api.dicebear.com/7.x/pixel-art/svg?seed=Valkyrie"
            },
            {
                "id": "00000000-0000-0000-0000-000000000104",
                "name": "Hawkeye QA",
                "email": "hawkeye@techguilds.io",
                "hero_class": "RANGER",
                "hero_class_label": "Ranger (QA)",
                "level": 4,
                "experience": 150,
                "experience_to_next_level": 380,
                "health": 110,
                "max_health": 110,
                "health_percent": 100.0,
                "mana": 60,
                "max_mana": 70,
                "gold": 210,
                "stats": {
                    "strength": 12,
                    "intelligence": 15,
                    "constitution": 14,
                    "perception": 26
                },
                "equipped_items": {
                    "weapon": "Crossbow of Edge Cases",
                    "armor": "Cloak of Cypress",
                    "accessory": "Scope of Jest"
                },
                "status": "REVIEWING",
                "avatar_url": "https://api.dicebear.com/7.x/pixel-art/svg?seed=Hawkeye"
            }
        ],
        "active_boss": {
            "id": "00000000-0000-0000-0000-000000000201",
            "external_id": "BUG-404",
            "title": "Memory Leak Hydra of Production",
            "severity": "CRITICAL",
            "max_health": 400,
            "current_health": 260,
            "health_percent": 65.0,
            "is_defeated": False,
            "bounty_hero_xp": 200,
            "bounty_guild_xp": 400,
            "bounty_gold": 130,
            "avatar": "👾"
        },
        "active_adventure": {
            "id": "00000000-0000-0000-0000-000000000301",
            "external_id": "EPIC-90",
            "title": "Project Chronos: Multi-Cloud SSO Migration",
            "total_quests": 12,
            "completed_quests": 8,
            "progress_percentage": 66.7,
            "is_completed": False,
            "reward_guild_xp": 1200,
            "reward_guild_gold": 500
        },
        "quests": [
            {
                "id": "00000000-0000-0000-0000-000000000401",
                "external_id": "LIN-101",
                "external_source": "linear",
                "title": "Provisionar cluster multi-region no EKS",
                "status": "DONE",
                "difficulty": "HARD",
                "quest_type": "CHORE",
                "assignee_name": "Valkyrie SRE",
                "is_pair_programming": True,
                "rewards": {
                    "hero_xp": 156,
                    "hero_gold": 52,
                    "guild_xp": 60,
                    "guild_gold": 20
                }
            },
            {
                "id": "00000000-0000-0000-0000-000000000402",
                "external_id": "LIN-102",
                "external_source": "linear",
                "title": "Implementar handshake OIDC com Okta e Azure AD",
                "status": "IN_REVIEW",
                "difficulty": "MEDIUM",
                "quest_type": "FEATURE",
                "assignee_name": "Conan The Backend",
                "is_pair_programming": False,
                "rewards": {
                    "hero_xp": 75,
                    "hero_gold": 25,
                    "guild_xp": 37,
                    "guild_gold": 12
                }
            },
            {
                "id": "00000000-0000-0000-0000-000000000403",
                "external_id": "LIN-103",
                "external_source": "linear",
                "title": "Desenvolver Dashboard Retro em Alpine.js",
                "status": "IN_PROGRESS",
                "difficulty": "HARD",
                "quest_type": "FEATURE",
                "assignee_name": "Gandalf Dev",
                "is_pair_programming": True,
                "rewards": {
                    "hero_xp": 156,
                    "hero_gold": 52,
                    "guild_xp": 60,
                    "guild_gold": 20
                }
            },
            {
                "id": "00000000-0000-0000-0000-000000000404",
                "external_id": "LIN-104",
                "external_source": "linear",
                "title": "Configurar suite de testes de integração com Testcontainers",
                "status": "TODO",
                "difficulty": "MEDIUM",
                "quest_type": "IMPROVEMENT",
                "assignee_name": "Hawkeye QA",
                "is_pair_programming": False,
                "rewards": {
                    "hero_xp": 75,
                    "hero_gold": 25,
                    "guild_xp": 37,
                    "guild_gold": 12
                }
            }
        ],
        "shop_items": DEFAULT_SHOP_ITEMS,
        "combat_log": [
            {
                "timestamp": "14:28:10",
                "message": "Gandalf Dev executed 'Alpine State Reactive Magic'! Mini-boss took 45 damage!",
                "type": "damage"
            },
            {
                "timestamp": "14:25:30",
                "message": "Conan The Backend added composite index on Postgres! Query speed +300%.",
                "type": "defense"
            },
            {
                "timestamp": "14:20:00",
                "message": "Valkyrie SRE resolved 'LIN-101' (+60 Squad XP, +20 Squad Gold)!",
                "type": "loot"
            },
            {
                "timestamp": "14:15:12",
                "message": "Mini-boss 'Memory Leak Hydra' triggered OOM-Killed error!",
                "type": "boss"
            }
        ]
    }


def _class_label(hero_class: HeroClass) -> str:
    mapping = {
        HeroClass.WARRIOR_BACKEND: "Warrior (Backend)",
        HeroClass.MAGE_FRONTEND: "Mage (Frontend)",
        HeroClass.PALADIN_DEVOPS: "Paladin (DevOps)",
        HeroClass.RANGER_QA: "Ranger (QA)",
        HeroClass.TACTICIAN_TL: "Tactician (Tech Lead)",
        HeroClass.NOVICE: "Novice"
    }
    return mapping.get(hero_class, hero_class.value)


def _default_gear(hero_class: HeroClass) -> Dict[str, str]:
    if hero_class == HeroClass.WARRIOR_BACKEND:
        return {"weapon": "Blade of Postgres Indices", "armor": "Chainmail of ACID", "accessory": "Pendant of Low Latency"}
    elif hero_class == HeroClass.MAGE_FRONTEND:
        return {"weapon": "Staff of Tailwind CSS", "armor": "Robe of Pixel Perfection", "accessory": "Ring of Zero Console Errors"}
    elif hero_class == HeroClass.PALADIN_DEVOPS:
        return {"weapon": "Hammer of Kubernetes", "armor": "Aegis of 99.99% Uptime", "accessory": "Helm of Prometheus"}
    elif hero_class == HeroClass.RANGER_QA:
        return {"weapon": "Crossbow of Edge Cases", "armor": "Cloak of Cypress", "accessory": "Scope of Jest"}
    elif hero_class == HeroClass.TACTICIAN_TL:
        return {"weapon": "Scepter of Roadmaps", "armor": "Tunic of Alignment", "accessory": "Orb of 1-on-1s"}
    return {"weapon": "Standard Keyboard", "armor": "Hoodie of Warmth", "accessory": "Coffee Mug"}


@router.get("", response_class=HTMLResponse)
async def serve_dashboard():
    """Entrega a página HTML do Dashboard Retro RPG para Squads de Tecnologia."""
    if not INDEX_HTML_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Arquivo do dashboard HTML não encontrado."
        )
    return HTMLResponse(content=INDEX_HTML_PATH.read_text(encoding="utf-8"))


@router.get("/data/{guild_id}")
async def get_dashboard_data(
    guild_id: str,
    container: DependencyContainer = Depends(get_container),
):
    """Retorna o payload completo do dashboard (guilda, heróis, boss, épico, quests, armory) em uma única chamada rápida."""
    # Suporte para rota de demonstração / testes rápidos
    if guild_id.lower() == "demo":
        return _get_demo_payload()

    try:
        guild_uuid = UUID(guild_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID da guilda deve ser um UUID válido ou 'demo'."
        )

    guild = await container.guild_repo.get_by_id(guild_uuid)
    if guild is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guilda não encontrada."
        )

    # Coleta de dados agregados
    heroes = await container.hero_repo.list_by_guild(guild.id)
    active_adv = await container.adventure_repo.get_active_by_guild(guild.id)
    active_bosses = await container.boss_repo.list_active_by_guild(guild.id)
    quests = await container.quest_repo.list_by_guild(guild.id)

    if not quests and active_adv:
        quests = await container.quest_repo.list_by_adventure(active_adv.id)

    # Mapeamento dos heróis
    hero_map = {h.id: h for h in heroes}
    heroes_data = []
    for h in heroes:
        h_max = max(1, h.max_health)
        heroes_data.append({
            "id": str(h.id),
            "name": h.name,
            "email": h.email,
            "hero_class": h.hero_class.value,
            "hero_class_label": _class_label(h.hero_class),
            "level": h.level,
            "experience": h.experience,
            "experience_to_next_level": h.experience_to_next_level,
            "health": h.health,
            "max_health": h.max_health,
            "health_percent": round((h.health / h_max) * 100.0, 1),
            "mana": 80,
            "max_mana": 100,
            "gold": h.gold,
            "stats": {
                "strength": h.stats.strength,
                "intelligence": h.stats.intelligence,
                "constitution": h.stats.constitution,
                "perception": h.stats.perception,
            },
            "equipped_items": _default_gear(h.hero_class),
            "status": "CODING",
            "avatar_url": h.avatar_url or f"https://api.dicebear.com/7.x/pixel-art/svg?seed={h.name}"
        })

    # Mini-Boss ativo
    active_boss_data = None
    if active_bosses:
        boss = active_bosses[0]
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

    # Aventura / Épico ativo
    active_adv_data = None
    if active_adv:
        active_adv_data = {
            "id": str(active_adv.id),
            "external_id": active_adv.external_id,
            "title": active_adv.title,
            "total_quests": active_adv.total_quests,
            "completed_quests": active_adv.completed_quests,
            "progress_percentage": round(active_adv.progress_percentage, 1),
            "is_completed": active_adv.is_completed,
            "reward_guild_xp": active_adv.reward_guild_xp,
            "reward_guild_gold": active_adv.reward_guild_gold,
        }

    # Quests / Tarefas do Board
    quests_data = []
    for q in quests:
        reward = q.calculate_rewards()
        assignee_name = hero_map[q.assignee_hero_id].name if q.assignee_hero_id in hero_map else None
        quests_data.append({
            "id": str(q.id),
            "external_id": q.external_id,
            "external_source": q.external_source,
            "title": q.title,
            "status": q.status.value,
            "difficulty": q.difficulty.value,
            "quest_type": q.quest_type.value,
            "assignee_hero_id": str(q.assignee_hero_id) if q.assignee_hero_id else None,
            "assignee_name": assignee_name,
            "is_pair_programming": q.is_pair_programming,
            "rewards": {
                "hero_xp": reward.hero_xp,
                "hero_gold": reward.hero_gold,
                "guild_xp": reward.guild_xp,
                "guild_gold": reward.guild_gold,
            }
        })

    # Cálculo da porcentagem de EXP da guilda
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
            "active_members_count": len(heroes),
            "active_adventure_title": active_adv.title if active_adv else None,
            "active_boss_count": len(active_bosses),
        },
        "heroes": heroes_data,
        "active_boss": active_boss_data,
        "active_adventure": active_adv_data,
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
