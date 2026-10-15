from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..model.hero import Hero
from ..ports.repositories import HeroRepository, GuildRepository
from ..ports.notification_port import NotificationPort


@dataclass
class ProcessCodeReviewCommand:
    reviewer_email: str
    guild_id: UUID
    pr_number: int
    pr_title: str
    reviewer_name: Optional[str] = None
    xp_amount: int = 50
    gold_amount: int = 15


@dataclass
class ProcessCodeReviewResult:
    hero: Optional[Hero]
    xp_awarded: int
    gold_awarded: int
    hero_leveled_up: bool = False
    message: str = ""


class ProcessCodeReviewUseCase:
    """Caso de uso executado quando uma revisão de código (Code Review) é aprovada.
    Concede a 'Bênção do Guardião' e XP de Code Review para o revisor.
    """
    def __init__(
        self,
        hero_repo: HeroRepository,
        guild_repo: GuildRepository,
        notification_port: NotificationPort,
    ):
        self.hero_repo = hero_repo
        self.guild_repo = guild_repo
        self.notification_port = notification_port

    async def execute(self, cmd: ProcessCodeReviewCommand) -> ProcessCodeReviewResult:
        hero = await self.hero_repo.get_by_email(cmd.reviewer_email)
        if hero is None:
            name = cmd.reviewer_name or cmd.reviewer_email.split("@")[0]
            hero = Hero(
                email=cmd.reviewer_email,
                name=name,
                guild_id=cmd.guild_id,
            )
            await self.hero_repo.save(hero)

        if hero.guild_id is None:
            hero.join_guild(cmd.guild_id)

        # Concede XP de revisão (Bênção do Guardião) e Ouro
        hero_leveled_up = hero.gain_experience(cmd.xp_amount)
        hero.gain_gold(cmd.gold_amount)
        await self.hero_repo.save(hero)

        # Notifica a guilda sobre a Bênção do Guardião
        await self.notification_port.notify_guardian_blessing(
            guild_id=cmd.guild_id,
            hero_name=hero.name,
            xp_gained=cmd.xp_amount,
            pr_title=f"#{cmd.pr_number} {cmd.pr_title}",
        )

        if hero_leveled_up:
            await self.notification_port.notify_level_up(
                guild_id=cmd.guild_id,
                hero_name=hero.name,
                new_level=hero.level,
                hero_class=hero.hero_class.value,
            )

        # Guilda também recebe XP coletivo por incentivar revisões de qualidade
        guild = await self.guild_repo.get_by_id(cmd.guild_id)
        if guild:
            guild.gain_experience(max(10, cmd.xp_amount // 2))
            await self.guild_repo.save(guild)

        msg = (
            f"🛡️ Bênção do Guardião concedida a {hero.name}! "
            f"+{cmd.xp_amount} XP de Code Review e +{cmd.gold_amount} Ouro por aprovar PR #{cmd.pr_number}."
        )

        return ProcessCodeReviewResult(
            hero=hero,
            xp_awarded=cmd.xp_amount,
            gold_awarded=cmd.gold_amount,
            hero_leveled_up=hero_leveled_up,
            message=msg,
        )
