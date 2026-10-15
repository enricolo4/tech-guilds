import pytest
from uuid import uuid4

from services.common.events import HeroRegisteredEvent
from services.gamification.domain.model.quest import (
    QuestStatus,
    QuestDifficulty,
)
from services.gamification.domain.model.mini_boss import BossSeverity
from services.gamification.domain.model.item import (
    Equipment,
    EquipmentSlot,
    create_equipment,
)
from services.gamification.domain.model.hero_progression import (
    HeroProgression,
    HeroProgressionStats,
)
from services.gamification.domain.ports.primary.process_card_event_port import (
    ProcessCardEventCommand,
)
from services.gamification.domain.ports.primary.process_bug_event_port import (
    ProcessBugEventCommand,
)
from services.gamification.domain.ports.primary.cast_skill_port import (
    CastSkillCommand,
)
from services.gamification.domain.ports.primary.equip_item_port import (
    EquipItemCommand,
    UnequipItemCommand,
)
from services.gamification.domain.use_cases.sync_hero_progression import (
    SyncHeroProgressionUseCase,
)
from services.gamification.domain.use_cases.process_card_event import (
    ProcessCardEventUseCase,
)
from services.gamification.domain.use_cases.process_bug_event import (
    ProcessBugEventUseCase,
)
from services.gamification.domain.use_cases.cast_skill import (
    CastSkillUseCase,
)
from services.gamification.domain.use_cases.equip_item import (
    EquipItemUseCase,
)
from services.gamification.primary.nats_consumer.hero_registered_consumer import (
    HeroRegisteredConsumer,
)
from services.gamification.secondary.postgresql.repositories.hero_progression_repository import (
    InMemoryHeroProgressionRepository,
)
from services.gamification.secondary.postgresql.repositories.quest_repository import (
    InMemoryQuestRepository,
)
from services.gamification.secondary.postgresql.repositories.mini_boss_repository import (
    InMemoryMiniBossRepository,
)


@pytest.mark.asyncio
async def test_nats_hero_registered_initializes_hero_progression():
    """1. Testa o consumo do evento NATS 'hero.registered' e inicialização da ficha RPG."""
    hero_repo = InMemoryHeroProgressionRepository()
    use_case = SyncHeroProgressionUseCase(hero_repo)
    consumer = HeroRegisteredConsumer(use_case)

    hero_id = uuid4()
    event = HeroRegisteredEvent(
        hero_id=hero_id,
        email="arthur.pendragon@guild.com",
        name="Arthur Pendragon",
        hero_class="WARRIOR",
        avatar_url="https://avatar.url/arthur.png",
        level=1,
        experience=0,
        gold=10,
    )

    # Simula o recebimento dos bytes no NATS
    payload_bytes = event.to_bytes()
    result = await consumer.process_message_payload(payload_bytes)

    assert result.created is True
    assert result.hero_progression.hero_id == hero_id
    assert result.hero_progression.name == "Arthur Pendragon"
    assert result.hero_progression.email == "arthur.pendragon@guild.com"
    assert result.hero_progression.hero_class == "WARRIOR"
    assert result.hero_progression.level == 1
    assert result.hero_progression.hp == 100
    assert result.hero_progression.mana == 100
    assert result.hero_progression.stats.strength == 10

    # Verifica persistência no repositório
    stored = await hero_repo.get_by_id(hero_id)
    assert stored is not None
    assert stored.name == "Arthur Pendragon"

    # Segunda invocação (idempotência do consumidor): não deve criar duplicata nem resetar ficha
    second_result = await consumer.process_message_payload(payload_bytes)
    assert second_result.created is False
    assert second_result.hero_progression.hero_id == hero_id


@pytest.mark.asyncio
async def test_quest_resolution_awards_xp_and_level_up():
    """2. Testa resolução de quests com recompensa de XP, ganho de ouro e subida de nível."""
    hero_repo = InMemoryHeroProgressionRepository()
    quest_repo = InMemoryQuestRepository()
    card_use_case = ProcessCardEventUseCase(quest_repo, hero_repo)

    hero_id = uuid4()
    guild_id = uuid4()
    hero = HeroProgression(
        hero_id=hero_id,
        name="Merlin",
        email="merlin@guild.com",
        hero_class="MAGE",
        level=1,
        exp=80,  # Próximo nível exige 100
        gold=50,
        guild_id=guild_id,
    )
    await hero_repo.save(hero)

    # 1. Tarefa entra em progresso
    cmd_in_progress = ProcessCardEventCommand(
        external_id="LIN-401",
        external_source="linear",
        title="Refatorar camada de autenticação",
        guild_id=guild_id,
        new_status=QuestStatus.IN_PROGRESS,
        assignee_email="merlin@guild.com",
        difficulty=QuestDifficulty.MEDIUM,
    )
    res_in_progress = await card_use_case.execute(cmd_in_progress)
    assert res_in_progress.reward is None
    assert res_in_progress.hero_leveled_up is False

    # 2. Tarefa concluída (DONE) com Pair Programming
    cmd_done = ProcessCardEventCommand(
        external_id="LIN-401",
        external_source="linear",
        title="Refatorar camada de autenticação",
        guild_id=guild_id,
        new_status=QuestStatus.DONE,
        assignee_email="merlin@guild.com",
        difficulty=QuestDifficulty.MEDIUM,
        is_pair_programming=True,
    )
    res_done = await card_use_case.execute(cmd_done)

    assert res_done.reward is not None
    assert res_done.reward.hero_xp > 0
    assert res_done.reward.hero_gold > 0
    assert res_done.hero_leveled_up is True

    # Verifica herói atualizado
    updated_hero = await hero_repo.get_by_id(hero_id)
    assert updated_hero.level == 2
    assert updated_hero.gold > 50
    # Ao subir de nível, atributos aumentam em 1
    assert updated_hero.stats.strength == 11
    assert updated_hero.stats.intelligence == 11
    assert updated_hero.max_hp == 110


@pytest.mark.asyncio
async def test_mini_boss_combat_and_bounty():
    """3. Testa combate a mini-bosses (bugs), aplicação de dano e concessão de bounty."""
    hero_repo = InMemoryHeroProgressionRepository()
    boss_repo = InMemoryMiniBossRepository()
    bug_use_case = ProcessBugEventUseCase(boss_repo, hero_repo)
    skill_use_case = CastSkillUseCase(hero_repo, boss_repo)

    guild_id = uuid4()
    hero_id = uuid4()
    hero = HeroProgression(
        hero_id=hero_id,
        name="Lancelot",
        email="lancelot@guild.com",
        hero_class="WARRIOR",
        level=2,
        exp=0,
        gold=20,
        mana=100,
        guild_id=guild_id,
    )
    await hero_repo.save(hero)

    # 1. Bug reportado -> Spawna Mini-Boss
    spawn_cmd = ProcessBugEventCommand(
        external_id="BUG-999",
        title="NPE crítico no checkout de pagamentos",
        guild_id=guild_id,
        severity=BossSeverity.HIGH,
        is_resolved=False,
    )
    spawn_res = await bug_use_case.execute(spawn_cmd)
    assert spawn_res.is_defeated is False
    assert spawn_res.mini_boss.max_health == 200
    assert spawn_res.mini_boss.current_health == 200

    boss_id = spawn_res.mini_boss.id

    # 2. Guerreiro conjura habilidade 'BRUTAL_REFACTOR' contra o Mini-Boss
    cast_cmd = CastSkillCommand(
        hero_id=hero_id,
        skill_id="BRUTAL_REFACTOR",
        target_boss_id=boss_id,
    )
    cast_res = await skill_use_case.execute(cast_cmd)
    assert cast_res.success is True
    assert cast_res.damage_dealt > 0
    assert cast_res.hero.mana < 100  # Consumiu mana

    boss_after_attack = await boss_repo.get_by_id(boss_id)
    assert boss_after_attack.current_health < 200

    # 3. Bug marcado como resolvido -> Mini-Boss é derrotado e recompensa concedida
    resolve_cmd = ProcessBugEventCommand(
        external_id="BUG-999",
        title="NPE crítico no checkout de pagamentos",
        guild_id=guild_id,
        severity=BossSeverity.HIGH,
        is_resolved=True,
        resolver_hero_id=hero_id,
    )
    resolve_res = await bug_use_case.execute(resolve_cmd)
    assert resolve_res.is_defeated is True
    assert resolve_res.bounty_hero_xp > 0
    assert resolve_res.bounty_gold > 0

    hero_rewarded = await hero_repo.get_by_id(hero_id)
    assert hero_rewarded.exp >= resolve_res.bounty_hero_xp
    assert hero_rewarded.gold > 20


@pytest.mark.asyncio
async def test_equipment_lifecycle():
    """4. Testa equipar e desequipar itens e bônus de atributos."""
    hero_repo = InMemoryHeroProgressionRepository()
    equip_use_case = EquipItemUseCase(hero_repo)

    hero_id = uuid4()
    hero = HeroProgression(
        hero_id=hero_id,
        name="Robin",
        email="robin@guild.com",
        hero_class="RANGER",
        level=2,
    )
    await hero_repo.save(hero)

    bow = create_equipment(
        name="Arco Longo Élfico",
        description="Aumenta percepção e força",
        slot=EquipmentSlot.WEAPON,
        strength=4,
        perception=8,
        required_level=1,
    )

    # Equipa a arma
    equip_res = await equip_use_case.execute(EquipItemCommand(hero_id=hero_id, equipment=bow))
    assert equip_res.hero.stats.strength == 14
    assert equip_res.hero.stats.perception == 18
    assert "WEAPON" in equip_res.hero.equipped_gear

    # Desequipa a arma
    unequip_res = await equip_use_case.unequip(UnequipItemCommand(hero_id=hero_id, slot=EquipmentSlot.WEAPON))
    assert unequip_res.hero.stats.strength == 10
    assert unequip_res.hero.stats.perception == 10
    assert "WEAPON" not in unequip_res.hero.equipped_gear
