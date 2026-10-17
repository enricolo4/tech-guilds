import uuid
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from services.registration.domain.model.hero import Hero, HeroClass, HeroStats


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy isolada para o serviço de Registration."""
    pass


class HeroModel(Base):
    """Modelo relacional do Herói armazenado no PostgreSQL no schema 'registration'."""
    __tablename__ = "heroes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_registration_heroes_tenant_email"),
        {"schema": "registration"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, default="default", server_default="default", index=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    hero_class: Mapped[str] = mapped_column(String(50), nullable=False, default="NOVICE")
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_health: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    mana: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_mana: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    strength: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    intelligence: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    constitution: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    perception: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    guild_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    def to_domain(self) -> Hero:
        """Converte o modelo de persistência para o modelo puro de domínio."""
        try:
            h_class = HeroClass(self.hero_class)
        except ValueError:
            h_class = HeroClass.NOVICE

        return Hero(
            id=self.id if isinstance(self.id, uuid.UUID) else uuid.UUID(str(self.id)),
            email=self.email,
            name=self.name,
            tenant_id=self.tenant_id or "default",
            avatar_url=self.avatar_url,
            guild_id=self.guild_id if (self.guild_id is None or isinstance(self.guild_id, uuid.UUID)) else uuid.UUID(str(self.guild_id)),
            hero_class=h_class,
            level=self.level,
            experience=self.experience,
            gold=self.gold,
            health=self.health,
            max_health=self.max_health,
            mana=self.mana,
            max_mana=self.max_mana,
            stats=HeroStats(
                strength=self.strength,
                intelligence=self.intelligence,
                constitution=self.constitution,
                perception=self.perception,
            ),
        )

    @classmethod
    def from_domain(cls, hero: Hero) -> "HeroModel":
        """Cria uma instância do modelo relacional a partir do modelo puro de domínio."""
        class_str = hero.hero_class.value if hasattr(hero.hero_class, "value") else str(hero.hero_class)
        return cls(
            id=hero.id,
            tenant_id=hero.tenant_id or "default",
            email=hero.email,
            name=hero.name,
            avatar_url=hero.avatar_url,
            hero_class=class_str,
            level=hero.level,
            experience=hero.experience,
            gold=hero.gold,
            health=hero.health,
            max_health=hero.max_health,
            mana=hero.mana,
            max_mana=hero.max_mana,
            strength=hero.stats.strength,
            intelligence=hero.stats.intelligence,
            constitution=hero.stats.constitution,
            perception=hero.stats.perception,
            guild_id=hero.guild_id,
        )

