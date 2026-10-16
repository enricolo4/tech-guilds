from typing import Dict, List
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.guilds.domain.model.guild import Guild, SquadLevel, Treasury
from services.guilds.domain.model.guild_member import GuildMember
from services.guilds.domain.ports.secondary.guild_member_repository import GuildMemberRepository
from services.guilds.domain.ports.secondary.guild_repository import GuildRepository
from services.guilds.secondary.postgresql.models.guild_member_model import GuildMemberModel
from services.guilds.secondary.postgresql.models.guild_model import GuildModel


def _map_guild_model_to_domain(model: GuildModel) -> Guild:
    member_ids = [m.hero_id for m in model.members] if model.members else []
    return Guild(
        id=model.id,
        name=model.name,
        description=model.description or "",
        squad_level=SquadLevel(level=model.level, experience=model.experience),
        treasury=Treasury(gold=model.treasury_gold),
        member_ids=member_ids,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _map_member_model_to_domain(model: GuildMemberModel) -> GuildMember:
    return GuildMember(
        hero_id=model.hero_id,
        name=model.name,
        email=model.email,
        hero_class=model.hero_class,
        guild_id=model.guild_id,
        level=model.level,
        avatar_url=model.avatar_url,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class PostgresGuildRepository(GuildRepository):
    """Implementação PostgreSQL da porta GuildRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, guild: Guild) -> Guild:
        stmt = (
            select(GuildModel)
            .where(GuildModel.id == guild.id)
            .options(selectinload(GuildModel.members))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = GuildModel(
                id=guild.id,
                name=guild.name,
                description=guild.description,
                level=guild.level,
                experience=guild.experience,
                treasury_gold=guild.treasury_gold,
                created_at=guild.created_at,
                updated_at=guild.updated_at,
            )
            self.session.add(model)
        else:
            model.name = guild.name
            model.description = guild.description
            model.level = guild.level
            model.experience = guild.experience
            model.treasury_gold = guild.treasury_gold
            model.updated_at = guild.updated_at

        await self.session.flush()
        await self.session.refresh(model, ["members"])
        return _map_guild_model_to_domain(model)

    async def find_by_id(self, guild_id: UUID) -> Guild | None:
        stmt = (
            select(GuildModel)
            .where(GuildModel.id == guild_id)
            .options(selectinload(GuildModel.members))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return _map_guild_model_to_domain(model) if model else None

    async def get_by_id(self, guild_id: UUID) -> Guild | None:
        return await self.find_by_id(guild_id)

    async def find_by_name(self, name: str) -> Guild | None:
        stmt = (
            select(GuildModel)
            .where(GuildModel.name == name)
            .options(selectinload(GuildModel.members))
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return _map_guild_model_to_domain(model) if model else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Guild]:
        stmt = (
            select(GuildModel)
            .options(selectinload(GuildModel.members))
            .order_by(GuildModel.name)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [_map_guild_model_to_domain(m) for m in models]

    async def delete(self, guild_id: UUID) -> bool:
        stmt = delete(GuildModel).where(GuildModel.id == guild_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0


class PostgresGuildMemberRepository(GuildMemberRepository):
    """Implementação PostgreSQL da porta GuildMemberRepository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, member: GuildMember) -> GuildMember:
        stmt = select(GuildMemberModel).where(GuildMemberModel.hero_id == member.hero_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            model = GuildMemberModel(
                hero_id=member.hero_id,
                name=member.name,
                email=member.email,
                hero_class=member.hero_class,
                avatar_url=member.avatar_url,
                level=member.level,
                guild_id=member.guild_id,
                created_at=member.created_at,
                updated_at=member.updated_at,
            )
            self.session.add(model)
        else:
            model.name = member.name
            model.email = member.email
            model.hero_class = member.hero_class
            model.avatar_url = member.avatar_url
            model.level = member.level
            model.guild_id = member.guild_id
            model.updated_at = member.updated_at

        await self.session.flush()
        await self.session.refresh(model)
        return _map_member_model_to_domain(model)

    async def find_by_hero_id(self, hero_id: UUID) -> GuildMember | None:
        stmt = select(GuildMemberModel).where(GuildMemberModel.hero_id == hero_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            try:
                from sqlalchemy import text
                hero_stmt = text("SELECT name, email, hero_class, avatar_url FROM registration.heroes WHERE id = :hid")
                res = await self.session.execute(hero_stmt, {"hid": hero_id})
                row = res.first()
                if row:
                    model = GuildMemberModel(
                        hero_id=hero_id,
                        name=row[0],
                        email=row[1],
                        hero_class=row[2] or "NOVICE",
                        avatar_url=row[3],
                        level=1,
                        guild_id=None,
                    )
                    self.session.add(model)
                    await self.session.flush()
                    await self.session.refresh(model)
            except Exception:
                pass
        return _map_member_model_to_domain(model) if model else None

    async def find_by_guild_id(self, guild_id: UUID) -> List[GuildMember]:
        stmt = (
            select(GuildMemberModel)
            .where(GuildMemberModel.guild_id == guild_id)
            .order_by(GuildMemberModel.name)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [_map_member_model_to_domain(m) for m in models]

    async def list_by_guild(self, guild_id: UUID) -> List[GuildMember]:
        return await self.find_by_guild_id(guild_id)

    async def update_guild_assignment(self, hero_id: UUID, guild_id: UUID | None) -> GuildMember | None:
        stmt = select(GuildMemberModel).where(GuildMemberModel.hero_id == hero_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            name = f"Hero {str(hero_id)[:8]}"
            email = f"hero-{str(hero_id)[:8]}@guild.local"
            hero_class = "WARRIOR"
            avatar_url = None
            try:
                from sqlalchemy import text
                hero_stmt = text("SELECT name, email, hero_class, avatar_url FROM registration.heroes WHERE id = :hid")
                res = await self.session.execute(hero_stmt, {"hid": hero_id})
                row = res.first()
                if row:
                    name = row[0] or name
                    email = row[1] or email
                    hero_class = row[2] or hero_class
                    avatar_url = row[3]
            except Exception:
                pass

            model = GuildMemberModel(
                hero_id=hero_id,
                name=name,
                email=email,
                hero_class=hero_class,
                avatar_url=avatar_url,
                level=1,
                guild_id=guild_id,
            )
            self.session.add(model)
        else:
            model.guild_id = guild_id
        await self.session.flush()
        await self.session.refresh(model)
        return _map_member_model_to_domain(model)

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[GuildMember]:
        stmt = select(GuildMemberModel).order_by(GuildMemberModel.name).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [_map_member_model_to_domain(m) for m in models]


class InMemoryGuildRepository(GuildRepository):
    """Implementação em memória da porta GuildRepository para testes isolados."""

    def __init__(self):
        self._guilds: Dict[UUID, Guild] = {}

    async def save(self, guild: Guild) -> Guild:
        self._guilds[guild.id] = guild
        return guild

    async def find_by_id(self, guild_id: UUID) -> Guild | None:
        return self._guilds.get(guild_id)

    async def get_by_id(self, guild_id: UUID) -> Guild | None:
        return await self.find_by_id(guild_id)

    async def find_by_name(self, name: str) -> Guild | None:
        for g in self._guilds.values():
            if g.name.lower() == name.lower():
                return g
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Guild]:
        items = list(self._guilds.values())
        return items[offset : offset + limit]

    async def delete(self, guild_id: UUID) -> bool:
        return self._guilds.pop(guild_id, None) is not None


class InMemoryGuildMemberRepository(GuildMemberRepository):
    """Implementação em memória da porta GuildMemberRepository para testes isolados."""

    def __init__(self):
        self._members: Dict[UUID, GuildMember] = {}

    async def save(self, member: GuildMember) -> GuildMember:
        self._members[member.hero_id] = member
        return member

    async def find_by_hero_id(self, hero_id: UUID) -> GuildMember | None:
        return self._members.get(hero_id)

    async def find_by_guild_id(self, guild_id: UUID) -> List[GuildMember]:
        return [m for m in self._members.values() if m.guild_id == guild_id]

    async def list_by_guild(self, guild_id: UUID) -> List[GuildMember]:
        return await self.find_by_guild_id(guild_id)

    async def update_guild_assignment(self, hero_id: UUID, guild_id: UUID | None) -> GuildMember | None:
        member = self._members.get(hero_id)
        if member:
            member.guild_id = guild_id
            return member
        return None

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[GuildMember]:
        items = list(self._members.values())
        return items[offset : offset + limit]
