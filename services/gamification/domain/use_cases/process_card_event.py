
from services.gamification.domain.model.quest import (
    Quest,
    QuestStatus,
    QuestReward,
)
from services.gamification.domain.ports.primary.process_card_event_port import (
    ProcessCardEventPort,
    ProcessCardEventCommand,
    ProcessCardEventResult,
)
from services.gamification.domain.ports.secondary.quest_repository import QuestRepository
from services.gamification.domain.ports.secondary.hero_progression_repository import (
    HeroProgressionRepository,
)


class ProcessCardEventUseCase(ProcessCardEventPort):
    """Implementação da Porta Primária para processamento de eventos de cards e tarefas."""

    def __init__(
        self,
        quest_repo: QuestRepository,
        hero_progression_repo: HeroProgressionRepository,
    ):
        self.quest_repo = quest_repo
        self.hero_progression_repo = hero_progression_repo

    async def execute(self, cmd: ProcessCardEventCommand) -> ProcessCardEventResult:
        tenant_id = (cmd.tenant_id or "default").strip() or "default"
        quest = await self.quest_repo.get_by_external_id(cmd.external_id, tenant_id=tenant_id)
        if quest is None:
            quest = Quest(
                external_id=cmd.external_id,
                external_source=cmd.external_source,
                title=cmd.title,
                guild_id=cmd.guild_id,
                difficulty=cmd.difficulty,
                is_pair_programming=cmd.is_pair_programming,
                adventure_id=cmd.adventure_id,
                tenant_id=tenant_id,
            )

        previous_status = quest.status
        quest.status = cmd.new_status
        quest.title = cmd.title
        quest.is_pair_programming = cmd.is_pair_programming
        quest.tenant_id = tenant_id
        if cmd.adventure_id:
            quest.adventure_id = cmd.adventure_id

        # Localiza o herói associado por ID ou e-mail dentro do tenant
        filter_tenant = tenant_id if tenant_id != "default" else None
        hero = None
        if cmd.assignee_hero_id:
            hero = await self.hero_progression_repo.get_by_id(cmd.assignee_hero_id, tenant_id=filter_tenant)
        elif cmd.assignee_email:
            hero = await self.hero_progression_repo.get_by_email(cmd.assignee_email, tenant_id=filter_tenant)

        if hero:
            quest.assignee_hero_id = hero.hero_id
            if tenant_id == "default" and hero.tenant_id:
                quest.tenant_id = hero.tenant_id
            if hero.guild_id is None:
                hero.guild_id = cmd.guild_id

        reward: QuestReward | None = None
        hero_leveled_up = False

        # Se a tarefa foi concluída -> Distribui XP e Ouro
        if cmd.new_status == QuestStatus.DONE and previous_status != QuestStatus.DONE:
            reward = quest.calculate_rewards()
            if hero:
                hero_leveled_up = hero.gain_experience(reward.hero_xp)
                hero.gain_gold(reward.hero_gold)
                await self.hero_progression_repo.save(hero)

        saved_quest = await self.quest_repo.save(quest)

        return ProcessCardEventResult(
            quest=saved_quest,
            reward=reward,
            hero_leveled_up=hero_leveled_up,
            hero_progression=hero,
        )
