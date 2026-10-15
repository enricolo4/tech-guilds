from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional
from .hero import HeroClass


class SkillTargetType(str, Enum):
    BOSS = "BOSS"
    HERO = "HERO"
    GUILD = "GUILD"


@dataclass
class Skill:
    """Habilidade especial de classe conjurada por um Herói consumindo mana."""
    id: str
    name: str
    description: str
    hero_class: HeroClass
    mana_cost: int = 25
    cooldown_turns: int = 1
    target_type: SkillTargetType = SkillTargetType.BOSS
    base_power: int = 50


# Habilidades canônicas inspiradas em papéis de tecnologia e Habitica
BRUTAL_REFACTOR = Skill(
    id="BRUTAL_REFACTOR",
    name="Brutal Refactor",
    description="Ferreiro / Backend desfere um ataque arquitetural devastador, causando alto dano a Mini-Bosses.",
    hero_class=HeroClass.WARRIOR_BACKEND,
    mana_cost=30,
    cooldown_turns=1,
    target_type=SkillTargetType.BOSS,
    base_power=60,
)

SCRIPT_AUTOMATION = Skill(
    id="SCRIPT_AUTOMATION",
    name="Script Automation",
    description="Ilusionista / Frontend cria scripts para automatizar tarefas repetitivas, multiplicando o ganho de EXP.",
    hero_class=HeroClass.MAGE_FRONTEND,
    mana_cost=25,
    cooldown_turns=1,
    target_type=SkillTargetType.HERO,
    base_power=2,  # Multiplicador de EXP (ex: 2.0x)
)

CICD_SHIELD = Skill(
    id="CICD_SHIELD",
    name="CI/CD Shield",
    description="Guardião / DevOps ergue pipelines blindados que reduzem drasticamente o dano sofrido por todo o Squad.",
    hero_class=HeroClass.PALADIN_DEVOPS,
    mana_cost=35,
    cooldown_turns=2,
    target_type=SkillTargetType.GUILD,
    base_power=50,  # 50% de redução de dano coletivo
)

EDGE_CASE_STRIKE = Skill(
    id="EDGE_CASE_STRIKE",
    name="Edge Case Strike",
    description="Caçador de Sombras / QA encontra a brecha crítica em testes de borda e atinge o Bug com dano crítico fatal.",
    hero_class=HeroClass.RANGER_QA,
    mana_cost=25,
    cooldown_turns=1,
    target_type=SkillTargetType.BOSS,
    base_power=80,  # Dano crítico ampliado por Percepção
)

SPRINT_RALLY = Skill(
    id="SPRINT_RALLY",
    name="Sprint Rally",
    description="Estrategista / Tech Lead alinha o objetivo da sprint e inspira o time, concedendo bônus de EXP para todo o Squad.",
    hero_class=HeroClass.TACTICIAN_TL,
    mana_cost=40,
    cooldown_turns=2,
    target_type=SkillTargetType.GUILD,
    base_power=150,  # EXP coletiva concedida
)

SKILL_REGISTRY: Dict[str, Skill] = {
    "BRUTAL_REFACTOR": BRUTAL_REFACTOR,
    "SCRIPT_AUTOMATION": SCRIPT_AUTOMATION,
    "CICD_SHIELD": CICD_SHIELD,
    "EDGE_CASE_STRIKE": EDGE_CASE_STRIKE,
    "SPRINT_RALLY": SPRINT_RALLY,
}

CLASS_SKILLS: Dict[HeroClass, Skill] = {
    HeroClass.WARRIOR_BACKEND: BRUTAL_REFACTOR,
    HeroClass.MAGE_FRONTEND: SCRIPT_AUTOMATION,
    HeroClass.PALADIN_DEVOPS: CICD_SHIELD,
    HeroClass.RANGER_QA: EDGE_CASE_STRIKE,
    HeroClass.TACTICIAN_TL: SPRINT_RALLY,
}


def get_skill(skill_id_or_name: str) -> Optional[Skill]:
    """Recupera habilidade pelo ID ou nome em formato normalizado."""
    key = skill_id_or_name.strip().upper().replace(" ", "_").replace("-", "_")
    return SKILL_REGISTRY.get(key)
