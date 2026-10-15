import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from tech_guilds.domain.entities.quest import (
    QuestDifficulty,
    QuestStatus,
    QuestType,
)
from tech_guilds.domain.entities.mini_boss import BossSeverity
from tech_guilds.domain.use_cases.process_card_event import ProcessCardEventCommand
from tech_guilds.domain.use_cases.process_bug_event import BugEventCommand


@dataclass
class LinearWebhookEvent:
    """Representa um evento normalizado recebido do webhook do Linear."""
    action: str                        # "create", "update", "remove"
    type: str                          # "Issue", "Project", "Cycle", etc.
    issue_id: str                      # Linear UUID
    identifier: str                    # "ENG-101" ou fallback para issue_id
    title: str
    description: str = ""
    status: QuestStatus = QuestStatus.TODO
    state_name: str = "Todo"
    is_bug: bool = False
    quest_type: QuestType = QuestType.FEATURE
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    severity: BossSeverity = BossSeverity.MEDIUM
    assignee_name: Optional[str] = None
    assignee_email: Optional[str] = None
    cycle_number: Optional[int] = None
    cycle_name: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    is_pair_programming: bool = False
    is_resolved: bool = False
    labels: List[str] = field(default_factory=list)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


class LinearWebhookParser:
    """Parser para decodificar e normalizar payloads de webhooks do Linear."""

    @classmethod
    def parse(cls, payload: Dict[str, Any]) -> LinearWebhookEvent:
        action = payload.get("action", "update")
        entity_type = payload.get("type", "Issue")
        data = payload.get("data", {})

        # Identificadores
        issue_id = str(data.get("id", ""))
        identifier = data.get("identifier") or issue_id or "LIN-000"
        title = data.get("title", "Sem título")
        description = data.get("description", "") or ""

        # Extração de Labels
        raw_labels = data.get("labels", [])
        label_names: List[str] = []
        for lab in raw_labels:
            if isinstance(lab, dict):
                name = lab.get("name", "")
                if name:
                    label_names.append(name)
            elif isinstance(lab, str):
                label_names.append(lab)

        # Determina se é Bug ou Feature/Improvement/Chore
        is_bug = any("bug" in name.lower() for name in label_names) or title.strip().lower().startswith("[bug]")
        quest_type = QuestType.FEATURE
        if is_bug:
            quest_type = QuestType.FEATURE  # Em Quests, bugs podem ser tratados como MiniBoss
        elif any("chore" in name.lower() or "ops" in name.lower() for name in label_names):
            quest_type = QuestType.CHORE
        elif any("improv" in name.lower() or "refactor" in name.lower() for name in label_names):
            quest_type = QuestType.IMPROVEMENT

        # Mapeamento de Estado (Linear State)
        raw_state = data.get("state", {})
        if isinstance(raw_state, dict):
            state_name = raw_state.get("name", "Todo")
            state_type = raw_state.get("type", "unstarted").lower()
        else:
            state_name = str(raw_state)
            state_type = ""

        status = cls._map_state(state_name, state_type)
        is_resolved = status == QuestStatus.DONE

        # Mapeamento de Estimativa / Dificuldade
        estimate = data.get("estimate")
        priority = data.get("priority", 0)  # 0: No priority, 1: Urgent, 2: High, 3: Medium, 4: Low
        difficulty = cls._map_difficulty(estimate, priority)
        severity = cls._map_severity(priority, label_names)

        # Responsável (Assignee)
        raw_assignee = data.get("assignee")
        assignee_name = None
        assignee_email = None
        if isinstance(raw_assignee, dict):
            assignee_name = raw_assignee.get("name")
            assignee_email = raw_assignee.get("email")
        elif isinstance(raw_assignee, str):
            assignee_name = raw_assignee

        # Cycle (Sprint)
        raw_cycle = data.get("cycle")
        cycle_number = None
        cycle_name = None
        if isinstance(raw_cycle, dict):
            cycle_number = raw_cycle.get("number")
            cycle_name = raw_cycle.get("name") or (f"Cycle {cycle_number}" if cycle_number else None)

        # Project (Épico / Aventura)
        raw_project = data.get("project")
        project_id = None
        project_name = None
        if isinstance(raw_project, dict):
            project_id = raw_project.get("id")
            project_name = raw_project.get("name")
        elif isinstance(raw_project, str):
            project_id = raw_project

        # Detecção de Pair Programming
        is_pair = (
            any("pair" in name.lower() or "coop" in name.lower() for name in label_names)
            or bool(re.search(r"\b(pair\s+programming|co-op|pareamento)\b", description, re.IGNORECASE))
        )

        return LinearWebhookEvent(
            action=action,
            type=entity_type,
            issue_id=issue_id,
            identifier=identifier,
            title=title,
            description=description,
            status=status,
            state_name=state_name,
            is_bug=is_bug,
            quest_type=quest_type,
            difficulty=difficulty,
            severity=severity,
            assignee_name=assignee_name,
            assignee_email=assignee_email,
            cycle_number=cycle_number,
            cycle_name=cycle_name,
            project_id=project_id,
            project_name=project_name,
            is_pair_programming=is_pair,
            is_resolved=is_resolved,
            labels=label_names,
            raw_payload=payload,
        )

    @staticmethod
    def _map_state(state_name: str, state_type: str) -> QuestStatus:
        name_lower = state_name.lower()
        if "progress" in name_lower or "started" in name_lower or state_type == "started":
            return QuestStatus.IN_PROGRESS
        if "review" in name_lower or "pr" in name_lower or "homolog" in name_lower:
            return QuestStatus.IN_REVIEW
        if "done" in name_lower or "completed" in name_lower or "closed" in name_lower or state_type == "completed":
            return QuestStatus.DONE
        if "cancel" in name_lower or state_type == "canceled":
            return QuestStatus.CANCELLED
        return QuestStatus.TODO

    @staticmethod
    def _map_difficulty(estimate: Optional[int], priority: int) -> QuestDifficulty:
        if estimate is not None:
            if estimate <= 1:
                return QuestDifficulty.TRIVIAL
            elif estimate == 2:
                return QuestDifficulty.EASY
            elif estimate <= 5:
                return QuestDifficulty.MEDIUM
            else:
                return QuestDifficulty.HARD

        # Fallback para prioridade do Linear (1=Urgent, 2=High, 3=Medium, 4=Low)
        if priority == 1:
            return QuestDifficulty.HARD
        elif priority == 2:
            return QuestDifficulty.MEDIUM
        elif priority == 3:
            return QuestDifficulty.EASY
        elif priority == 4:
            return QuestDifficulty.TRIVIAL

        return QuestDifficulty.MEDIUM

    @staticmethod
    def _map_severity(priority: int, labels: List[str]) -> BossSeverity:
        lower_labels = [l.lower() for l in labels]
        if priority == 1 or any("critical" in l or "p0" in l or "sev0" in l for l in lower_labels):
            return BossSeverity.CRITICAL
        if priority == 2 or any("high" in l or "p1" in l or "sev1" in l for l in lower_labels):
            return BossSeverity.HIGH
        if priority == 3 or any("medium" in l or "p2" in l or "sev2" in l for l in lower_labels):
            return BossSeverity.MEDIUM
        return BossSeverity.LOW

    @classmethod
    def to_card_command(cls, event: LinearWebhookEvent, guild_id: UUID) -> ProcessCardEventCommand:
        """Converte o evento Linear em um comando de domínio para processamento de Quest."""
        return ProcessCardEventCommand(
            external_id=event.identifier,
            external_source="linear",
            title=event.title,
            assignee_email=event.assignee_email or "unassigned@company.local",
            guild_id=guild_id,
            new_status=event.status,
            difficulty=event.difficulty,
            is_pair_programming=event.is_pair_programming,
            adventure_external_id=event.project_name or event.project_id,
        )

    @classmethod
    def to_bug_command(cls, event: LinearWebhookEvent, guild_id: UUID) -> BugEventCommand:
        """Converte o evento Linear em um comando de domínio para geração/derrota de MiniBoss."""
        return BugEventCommand(
            external_id=event.identifier,
            title=event.title,
            guild_id=guild_id,
            severity=event.severity,
            is_resolved=event.is_resolved or event.status == QuestStatus.DONE,
            resolver_email=event.assignee_email,
        )
