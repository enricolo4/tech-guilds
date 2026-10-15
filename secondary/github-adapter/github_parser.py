import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from tech_guilds.domain.model.quest import (
    QuestDifficulty,
    QuestStatus,
    QuestType,
)
from tech_guilds.domain.model.mini_boss import BossSeverity
from tech_guilds.domain.use_cases.process_card_event import ProcessCardEventCommand
from tech_guilds.domain.use_cases.process_bug_event import BugEventCommand
from tech_guilds.domain.use_cases.process_code_review import ProcessCodeReviewCommand


@dataclass
class GitHubWebhookEvent:
    """Representa um evento normalizado recebido do webhook do GitHub."""
    event_type: str                   # "pull_request", "pull_request_review", "issues"
    action: str                       # "opened", "closed", "submitted", etc.
    identifier: str                   # "GH-PR-10" ou "GH-ISSUE-42"
    title: str
    description: str = ""
    # Pull Request & Issue fields
    status: QuestStatus = QuestStatus.TODO
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_bug: bool = False
    severity: BossSeverity = BossSeverity.MEDIUM
    author_login: Optional[str] = None
    author_email: Optional[str] = None
    is_merged: bool = False
    is_pair_programming: bool = False
    adventure_external_id: Optional[str] = None
    # Code Review fields
    is_review_approved: bool = False
    reviewer_login: Optional[str] = None
    reviewer_email: Optional[str] = None
    review_state: Optional[str] = None
    pr_number: Optional[int] = None
    # Bug / MiniBoss fields
    is_resolved: bool = False
    resolver_email: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


class GitHubWebhookParser:
    """Parser para normalizar payloads de webhooks do GitHub (PR, Review, Issues)."""

    @classmethod
    def parse(cls, payload: Dict[str, Any], event_header: Optional[str] = None) -> GitHubWebhookEvent:
        # Tenta identificar o tipo de evento através do cabeçalho ou das chaves do payload
        event_type = event_header or cls._infer_event_type(payload)
        action = payload.get("action", "")

        if event_type == "pull_request":
            return cls._parse_pull_request(payload, action)
        elif event_type == "pull_request_review":
            return cls._parse_pull_request_review(payload, action)
        elif event_type == "issues":
            return cls._parse_issue(payload, action)
        else:
            # Fallback genérico para outros eventos
            return GitHubWebhookEvent(
                event_type=event_type,
                action=action,
                identifier=f"GH-GENERIC-{payload.get('number', '0')}",
                title=payload.get("title", "GitHub Event"),
                raw_payload=payload,
            )

    @staticmethod
    def _infer_event_type(payload: Dict[str, Any]) -> str:
        if "review" in payload:
            return "pull_request_review"
        if "pull_request" in payload:
            return "pull_request"
        if "issue" in payload:
            return "issues"
        return "unknown"

    @classmethod
    def _parse_pull_request(cls, payload: Dict[str, Any], action: str) -> GitHubWebhookEvent:
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number") or payload.get("number", 0)
        title = pr.get("title", f"PR #{pr_number}")
        body = pr.get("body", "") or ""
        merged = pr.get("merged", False)

        user = pr.get("user", {})
        author_login = user.get("login")
        author_email = user.get("email") or (f"{author_login}@company.local" if author_login else "dev@company.local")

        # Labels
        labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in pr.get("labels", [])]

        # Milestone como Épico / Aventura
        milestone = pr.get("milestone")
        adv_id = milestone.get("title") if isinstance(milestone, dict) else None

        # Status do Card
        if action == "closed" and merged:
            status = QuestStatus.DONE
        elif action in ("opened", "reopened", "synchronize"):
            status = QuestStatus.IN_REVIEW
        elif action == "closed" and not merged:
            status = QuestStatus.CANCELLED
        else:
            status = QuestStatus.IN_PROGRESS

        # Pair Programming detection
        is_pair = (
            any("pair" in l.lower() or "coop" in l.lower() for l in labels)
            or bool(re.search(r"\b(co-authored-by|pair\s+programming|pareamento)\b", body, re.IGNORECASE))
        )

        # Dificuldade baseada no número de alterações (linhas alteradas)
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        total_changes = additions + deletions
        if total_changes < 50:
            difficulty = QuestDifficulty.TRIVIAL
        elif total_changes < 200:
            difficulty = QuestDifficulty.EASY
        elif total_changes < 600:
            difficulty = QuestDifficulty.MEDIUM
        else:
            difficulty = QuestDifficulty.HARD

        return GitHubWebhookEvent(
            event_type="pull_request",
            action=action,
            identifier=f"GH-PR-{pr_number}",
            title=title,
            description=body,
            status=status,
            difficulty=difficulty,
            author_login=author_login,
            author_email=author_email,
            is_merged=merged,
            is_pair_programming=is_pair,
            adventure_external_id=adv_id,
            pr_number=pr_number,
            labels=labels,
            raw_payload=payload,
        )

    @classmethod
    def _parse_pull_request_review(cls, payload: Dict[str, Any], action: str) -> GitHubWebhookEvent:
        review = payload.get("review", {})
        pr = payload.get("pull_request", {})
        pr_number = pr.get("number") or payload.get("number", 0)
        pr_title = pr.get("title", f"PR #{pr_number}")

        review_state = (review.get("state") or "").lower()
        is_approved = review_state == "approved"

        reviewer = review.get("user", {})
        reviewer_login = reviewer.get("login")
        reviewer_email = reviewer.get("email") or (f"{reviewer_login}@company.local" if reviewer_login else "guardian@company.local")

        return GitHubWebhookEvent(
            event_type="pull_request_review",
            action=action,
            identifier=f"GH-REVIEW-{pr_number}-{review.get('id', '0')}",
            title=f"Review no PR #{pr_number}: {pr_title}",
            description=review.get("body", "") or "",
            is_review_approved=is_approved,
            reviewer_login=reviewer_login,
            reviewer_email=reviewer_email,
            review_state=review_state,
            pr_number=pr_number,
            raw_payload=payload,
        )

    @classmethod
    def _parse_issue(cls, payload: Dict[str, Any], action: str) -> GitHubWebhookEvent:
        issue = payload.get("issue", {})
        issue_number = issue.get("number") or payload.get("number", 0)
        title = issue.get("title", f"Issue #{issue_number}")
        body = issue.get("body", "") or ""
        state = issue.get("state", "open")

        user = issue.get("user", {})
        author_login = user.get("login")
        author_email = user.get("email") or (f"{author_login}@company.local" if author_login else "dev@company.local")

        # Labels
        labels = [l.get("name", "") if isinstance(l, dict) else str(l) for l in issue.get("labels", [])]
        is_bug = any("bug" in l.lower() for l in labels) or title.strip().lower().startswith("[bug]")

        # Severidade
        severity = cls._map_issue_severity(labels)

        # Resolver (quem fechou ou responsável)
        closed_by = issue.get("closed_by") or {}
        assignee = issue.get("assignee") or {}
        resolver_email = (
            closed_by.get("email")
            or (f"{closed_by.get('login')}@company.local" if closed_by.get("login") else None)
            or assignee.get("email")
            or (f"{assignee.get('login')}@company.local" if assignee.get("login") else author_email)
        )

        is_resolved = action == "closed" or state == "closed"
        status = QuestStatus.DONE if is_resolved else QuestStatus.TODO

        # Milestone
        milestone = issue.get("milestone")
        adv_id = milestone.get("title") if isinstance(milestone, dict) else None

        return GitHubWebhookEvent(
            event_type="issues",
            action=action,
            identifier=f"GH-{issue_number}",
            title=title,
            description=body,
            status=status,
            is_bug=is_bug,
            severity=severity,
            author_login=author_login,
            author_email=author_email,
            is_resolved=is_resolved,
            resolver_email=resolver_email,
            adventure_external_id=adv_id,
            labels=labels,
            raw_payload=payload,
        )

    @staticmethod
    def _map_issue_severity(labels: List[str]) -> BossSeverity:
        lower = [l.lower() for l in labels]
        if any("critical" in l or "p0" in l or "sev0" in l or "blocker" in l for l in lower):
            return BossSeverity.CRITICAL
        if any("high" in l or "p1" in l or "sev1" in l for l in lower):
            return BossSeverity.HIGH
        if any("medium" in l or "p2" in l or "sev2" in l for l in lower):
            return BossSeverity.MEDIUM
        return BossSeverity.LOW

    @classmethod
    def to_card_command(cls, event: GitHubWebhookEvent, guild_id: UUID) -> ProcessCardEventCommand:
        """Converte evento GitHub em comando de Quest para o domínio."""
        return ProcessCardEventCommand(
            external_id=event.identifier,
            external_source="github",
            title=event.title,
            assignee_email=event.author_email or "dev@company.local",
            guild_id=guild_id,
            new_status=event.status,
            difficulty=event.difficulty,
            is_pair_programming=event.is_pair_programming,
            adventure_external_id=event.adventure_external_id,
        )

    @classmethod
    def to_bug_command(cls, event: GitHubWebhookEvent, guild_id: UUID) -> BugEventCommand:
        """Converte evento de Issue Bug em comando de MiniBoss para o domínio."""
        return BugEventCommand(
            external_id=event.identifier,
            title=event.title,
            guild_id=guild_id,
            severity=event.severity,
            is_resolved=event.is_resolved,
            resolver_email=event.resolver_email,
        )

    @classmethod
    def to_code_review_command(
        cls,
        event: GitHubWebhookEvent,
        guild_id: UUID,
        xp_amount: int = 50,
    ) -> ProcessCodeReviewCommand:
        """Converte aprovação de PR Review em comando para conceder a Bênção do Guardião."""
        return ProcessCodeReviewCommand(
            reviewer_email=event.reviewer_email or "guardian@company.local",
            reviewer_name=event.reviewer_login,
            guild_id=guild_id,
            pr_number=event.pr_number or 0,
            pr_title=event.title,
            xp_amount=xp_amount,
        )
