from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class SkillTargetType(str, Enum):
    BOSS = "BOSS"
    HERO = "HERO"
    GUILD = "GUILD"


@dataclass
class SkillEffect:
    """Representa o efeito mecânico de uma habilidade."""
    effect_type: str  # "DAMAGE", "EXP_MULTIPLIER", "DAMAGE_REDUCTION", "SQUAD_EXP_BUFF"
    power: float
    description: str = ""


@dataclass
class Skill:
    """Habilidade especial de classe conjurada por um Herói consumindo mana."""
    id: str
    name: str
    description: str
    hero_class: str
    mana_cost: int = 25
    cooldown_turns: int = 1
    target_type: SkillTargetType = SkillTargetType.BOSS
    base_power: int = 50
    effect: Optional[SkillEffect] = None


# Habilidades canônicas inspiradas em papéis de tecnologia e Habitica
BRUTAL_REFACTOR = Skill(
    id="BRUTAL_REFACTOR",
    name="Brutal Refactor",
    description="Ferreiro / Backend desfere um ataque arquitetural devastador, causando alto dano a Mini-Bosses.",
    hero_class="WARRIOR",
    mana_cost=30,
    cooldown_turns=1,
    target_type=SkillTargetType.BOSS,
    base_power=60,
    effect=SkillEffect(effect_type="DAMAGE", power=60.0, description="Dano direto massivo em Mini-Bosses"),
)

SCRIPT_AUTOMATION = Skill(
    id="SCRIPT_AUTOMATION",
    name="Script Automation",
    description="Ilusionista / Frontend cria scripts para automatizar tarefas repetitivas, multiplicando o ganho de EXP.",
    hero_class="MAGE",
    mana_cost=25,
    cooldown_turns=1,
    target_type=SkillTargetType.HERO,
    base_power=2,
    effect=SkillEffect(effect_type="EXP_MULTIPLIER", power=2.0, description="Multiplicador temporário de EXP individual"),
)

CICD_SHIELD = Skill(
    id="CICD_SHIELD",
    name="CI/CD Shield",
    description="Guardião / DevOps ergue pipelines blindados que reduzem drasticamente o dano sofrido por todo o Squad.",
    hero_class="PALADIN",
    mana_cost=35,
    cooldown_turns=2,
    target_type=SkillTargetType.GUILD,
    base_power=50,
    effect=SkillEffect(effect_type="DAMAGE_REDUCTION", power=0.5, description="Redução de dano coletivo do Squad"),
)

EDGE_CASE_STRIKE = Skill(
    id="EDGE_CASE_STRIKE",
    name="Edge Case Strike",
    description="Caçador de Sombras / QA encontra a brecha crítica em testes de borda e atinge o Bug com dano crítico fatal.",
    hero_class="RANGER",
    mana_cost=25,
    cooldown_turns=1,
    target_type=SkillTargetType.BOSS,
    base_power=80,
    effect=SkillEffect(effect_type="DAMAGE", power=80.0, description="Dano crítico ampliado em Mini-Bosses"),
)

SPRINT_RALLY = Skill(
    id="SPRINT_RALLY",
    name="Sprint Rally",
    description="Estrategista / Tech Lead alinha o objetivo da sprint e inspira o time, concedendo bônus de EXP para todo o Squad.",
    hero_class="TACTICIAN",
    mana_cost=40,
    cooldown_turns=2,
    target_type=SkillTargetType.GUILD,
    base_power=150,
    effect=SkillEffect(effect_type="SQUAD_EXP_BUFF", power=150.0, description="Bônus de EXP concedido para todo o Squad"),
)

SKILL_REGISTRY: Dict[str, Skill] = {
    "BRUTAL_REFACTOR": BRUTAL_REFACTOR,
    "SCRIPT_AUTOMATION": SCRIPT_AUTOMATION,
    "CICD_SHIELD": CICD_SHIELD,
    "EDGE_CASE_STRIKE": EDGE_CASE_STRIKE,
    "SPRINT_RALLY": SPRINT_RALLY,
}


def get_skill(skill_id_or_name: str) -> Optional[Skill]:
    """Recupera habilidade pelo ID ou nome em formato normalizado."""
    key = skill_id_or_name.strip().upper().replace(" ", "_").replace("-", "_")
    return SKILL_REGISTRY.get(key)
