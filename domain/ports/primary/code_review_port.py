from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from ...model.hero import Hero


@dataclass
class ProcessCodeReviewCommand:
    reviewer_email: str
    guild_id: UUID
    pr_number: int
    pr_title: str
    reviewer_name: Optional[str] = None
    xp_amount: int = 50
    gold_amount: int = 15


# Alias for backward compatibility
CodeReviewCommand = ProcessCodeReviewCommand


@dataclass
class ProcessCodeReviewResult:
    hero: Optional[Hero]
    xp_awarded: int
    gold_awarded: int
    hero_leveled_up: bool = False
    message: str = ""


# Alias for backward compatibility
CodeReviewResult = ProcessCodeReviewResult


class ProcessCodeReviewPort(ABC):
    """Porta Primária (Driving/Input Port) para revisões de código (Bênção do Guardião)."""

    @abstractmethod
    async def execute(self, cmd: ProcessCodeReviewCommand) -> ProcessCodeReviewResult:
        pass
