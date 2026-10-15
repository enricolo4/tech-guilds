from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..entities.quest import Quest, QuestStatus, QuestDifficulty, QuestReward
from ..ports.repositories import (
    HeroRepository,
    GuildRepository,
    QuestRepository,
    AdventureRepository,
)
from ..ports.notification_port import NotificationPort


@dataclass
class ProcessCardEventCommand:
    external_id: str
    external_source: str
    title: str
    assignee_email: str
    guild_id: UUID
    new_status: QuestStatus
    difficulty: QuestDifficulty = QuestDifficulty.MEDIUM
    is_pair_programming: bool = False
    adventure_external_id: Optional[str] = None


@dataclass
class ProcessCardEventResult:
    quest: Quest
    reward: Optional[QuestReward] = None
    hero_leveled_up: bool = False
    guild_leveled_up: bool = False
    adventure_completed: bool = False


class ProcessCardEventUseCase:
    """Caso de uso executado quando um card de tarefa é criado, movido ou concluído no Linear/Jira/GitHub."""
    def __init__(
        self,
        quest_repo: QuestRepository,
        hero_repo: HeroRepository,
        guild_repo: GuildRepository,
        adventure_repo: AdventureRepository,
        notification_port: NotificationPort,
    ):
        self.quest_repo = quest_repo
        self.hero_repo = hero_repo
        self.guild_repo = guild_repo
        self.adventure_repo = adventure_repo
        self.notification_port = notification_port

    async def execute(self, cmd: ProcessCardEventCommand) -> ProcessCardEventResult:
        # 1. Recupera ou cria a Quest pelo external_id (ex: LIN-104)
        quest = await self.quest_repo.get_by_external_id(cmd.external_id)
        if quest is None:
            quest = Quest(
                external_id=cmd.external_id,
                external_source=cmd.external_source,
                title=cmd.title,
                guild_id=cmd.guild_id,
                difficulty=cmd.difficulty,
                is_pair_programming=cmd.is_pair_programming,
            )

        previous_status = quest.status
        quest.status = cmd.new_status
        quest.title = cmd.title
        quest.is_pair_programming = cmd.is_pair_programming

        # 2. Localiza o herói atribuído pelo e-mail corporativo
        hero = await self.hero_repo.get_by_email(cmd.assignee_email)
        if hero:
            quest.assignee_hero_id = hero.id
            if hero.guild_id is None:
                hero.join_guild(cmd.guild_id)

        # 3. Localiza a Guilda
        guild = await self.guild_repo.get_by_id(cmd.guild_id)

        reward: Optional[QuestReward] = None
        hero_leveled_up = False
        guild_leveled_up = False
        adventure_completed = False

        # 4. Se a tarefa foi concluída (e antes não estava concluída) -> Distribui XP e Ouro!
        if cmd.new_status == QuestStatus.DONE and previous_status != QuestStatus.DONE:
            reward = quest.calculate_rewards()

            # Recompensa o Herói
            if hero:
                hero_leveled_up = hero.gain_experience(reward.hero_xp)
                hero.gain_gold(reward.hero_gold)
                await self.hero_repo.save(hero)

                if hero_leveled_up:
                    await self.notification_port.notify_level_up(
                        guild_id=cmd.guild_id,
                        hero_name=hero.name,
                        new_level=hero.level,
                        hero_class=hero.hero_class.value,
                    )

            # Recompensa a Guilda (Squad)
            if guild:
                guild_leveled_up = guild.gain_experience(reward.guild_xp)
                guild.deposit_gold(reward.guild_gold)

                # Se a tarefa fizer parte de uma Aventura (Épico), avança a aventura
                if cmd.adventure_external_id:
                    adventure = await self.adventure_repo.get_by_external_id(cmd.adventure_external_id)
                    if adventure:
                        quest.adventure_id = adventure.id
                        adventure_completed = adventure.register_quest_completion()
                        if adventure_completed:
                            # Vitória total no Épico: bônus massivo para a guilda inteira!
                            guild.gain_experience(adventure.reward_guild_xp)
                            guild.deposit_gold(adventure.reward_guild_gold)
                            await self.notification_port.notify_guild_channel(
                                guild_id=guild.id,
                                title="🏆 Aventura Concluída com Sucesso!",
                                message=f"O Squad finalizou o Épico '{adventure.title}'! +{adventure.reward_guild_xp} XP e +{adventure.reward_guild_gold} Ouro no baú da Guilda!",
                            )
                        await self.adventure_repo.save(adventure)

                await self.guild_repo.save(guild)

            # Notifica conclusão da Quest
            await self.notification_port.notify_guild_channel(
                guild_id=cmd.guild_id,
                title="⚔️ Missão Cumprida!",
                message=f"{hero.name if hero else 'Alguém'} concluiu [{quest.external_id}] '{quest.title}'! +{reward.hero_xp} XP individual e +{reward.guild_xp} XP para a Guilda!",
            )

        await self.quest_repo.save(quest)

        return ProcessCardEventResult(
            quest=quest,
            reward=reward,
            hero_leveled_up=hero_leveled_up,
            guild_leveled_up=guild_leveled_up,
            adventure_completed=adventure_completed,
        )
