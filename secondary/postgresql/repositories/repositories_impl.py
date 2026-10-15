from typing import Dict, List, Optional
from uuid import UUID
from tech_guilds.domain.entities.hero import Hero
from tech_guilds.domain.entities.guild import Guild
from tech_guilds.domain.entities.quest import Quest
from tech_guilds.domain.entities.adventure import Adventure
from tech_guilds.domain.entities.mini_boss import MiniBoss
from tech_guilds.domain.ports.repositories import (
    HeroRepository,
    GuildRepository,
    QuestRepository,
    AdventureRepository,
    MiniBossRepository,
)


class InMemoryHeroRepository(HeroRepository):
    def __init__(self):
        self._store: Dict[UUID, Hero] = {}

    async def get_by_id(self, hero_id: UUID) -> Optional[Hero]:
        return self._store.get(hero_id)

    async def get_by_email(self, email: str) -> Optional[Hero]:
        email_clean = email.strip().lower()
        for hero in self._store.values():
            if hero.email.strip().lower() == email_clean:
                return hero
        return None

    async def save(self, hero: Hero) -> Hero:
        self._store[hero.id] = hero
        return hero

    async def list_by_guild(self, guild_id: UUID) -> List[Hero]:
        return [h for h in self._store.values() if h.guild_id == guild_id]


class InMemoryGuildRepository(GuildRepository):
    def __init__(self):
        self._store: Dict[UUID, Guild] = {}

    async def get_by_id(self, guild_id: UUID) -> Optional[Guild]:
        return self._store.get(guild_id)

    async def get_by_name(self, name: str) -> Optional[Guild]:
        name_clean = name.strip().lower()
        for guild in self._store.values():
            if guild.name.strip().lower() == name_clean:
                return guild
        return None

    async def save(self, guild: Guild) -> Guild:
        self._store[guild.id] = guild
        return guild

    async def list_all(self) -> List[Guild]:
        return list(self._store.values())


class InMemoryQuestRepository(QuestRepository):
    def __init__(self):
        self._store: Dict[UUID, Quest] = {}

    async def get_by_id(self, quest_id: UUID) -> Optional[Quest]:
        return self._store.get(quest_id)

    async def get_by_external_id(self, external_id: str) -> Optional[Quest]:
        for quest in self._store.values():
            if quest.external_id == external_id:
                return quest
        return None

    async def save(self, quest: Quest) -> Quest:
        self._store[quest.id] = quest
        return quest

    async def list_by_adventure(self, adventure_id: UUID) -> List[Quest]:
        return [q for q in self._store.values() if q.adventure_id == adventure_id]

    async def list_by_guild(self, guild_id: UUID) -> List[Quest]:
        return [q for q in self._store.values() if q.guild_id == guild_id]


class InMemoryAdventureRepository(AdventureRepository):
    def __init__(self):
        self._store: Dict[UUID, Adventure] = {}

    async def get_by_id(self, adventure_id: UUID) -> Optional[Adventure]:
        return self._store.get(adventure_id)

    async def get_by_external_id(self, external_id: str) -> Optional[Adventure]:
        for adv in self._store.values():
            if adv.external_id == external_id:
                return adv
        return None

    async def save(self, adventure: Adventure) -> Adventure:
        self._store[adventure.id] = adventure
        return adventure

    async def get_active_by_guild(self, guild_id: UUID) -> Optional[Adventure]:
        for adv in self._store.values():
            if adv.guild_id == guild_id and not adv.is_completed:
                return adv
        return None


class InMemoryMiniBossRepository(MiniBossRepository):
    def __init__(self):
        self._store: Dict[UUID, MiniBoss] = {}

    async def get_by_id(self, boss_id: UUID) -> Optional[MiniBoss]:
        return self._store.get(boss_id)

    async def get_by_external_id(self, external_id: str) -> Optional[MiniBoss]:
        for boss in self._store.values():
            if boss.external_id == external_id:
                return boss
        return None

    async def save(self, boss: MiniBoss) -> MiniBoss:
        self._store[boss.id] = boss
        return boss

    async def list_active_by_guild(self, guild_id: UUID) -> List[MiniBoss]:
        return [b for b in self._store.values() if b.guild_id == guild_id and not b.is_defeated]
