from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4


@dataclass
class SquadLevel:
    """Nível e progressão de experiência do Squad/Guilda."""
    level: int = 1
    experience: int = 0

    @property
    def experience_to_next_level(self) -> int:
        """Cálculo de progressão de nível da Guilda."""
        return int(500 * (self.level ** 1.4))

    def gain_experience(self, amount: int, multiplier: float = 1.0) -> bool:
        """Adiciona EXP coletiva ao Squad. Retorna True se o squad subiu de nível."""
        leveled_up = False
        self.experience += int(amount * multiplier)
        while self.experience >= self.experience_to_next_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            leveled_up = True
        return leveled_up


@dataclass
class Treasury:
    """Tesouro e economia coletiva da Guilda."""
    gold: int = 0

    def deposit(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("O valor do depósito deve ser positivo.")
        self.gold += amount

    def spend(self, amount: int) -> bool:
        """Gasta ouro do tesouro da Guilda. Retorna True se o saldo for suficiente."""
        if amount <= 0:
            raise ValueError("O valor do gasto deve ser positivo.")
        if self.gold < amount:
            return False
        self.gold -= amount
        return True


@dataclass
class Guild:
    """Entidade de domínio representando um Squad ou time de engenharia organizado como Guilda."""
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    squad_level: SquadLevel = field(default_factory=SquadLevel)
    treasury: Treasury = field(default_factory=Treasury)
    member_ids: List[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def level(self) -> int:
        return self.squad_level.level

    @property
    def experience(self) -> int:
        return self.squad_level.experience

    @property
    def experience_to_next_level(self) -> int:
        return self.squad_level.experience_to_next_level

    @property
    def treasury_gold(self) -> int:
        return self.treasury.gold

    def gain_experience(self, amount: int, multiplier: float = 1.0) -> bool:
        leveled_up = self.squad_level.gain_experience(amount, multiplier)
        self.updated_at = datetime.now(timezone.utc)
        return leveled_up

    def deposit_gold(self, amount: int) -> None:
        self.treasury.deposit(amount)
        self.updated_at = datetime.now(timezone.utc)

    def spend_gold(self, amount: int) -> bool:
        success = self.treasury.spend(amount)
        if success:
            self.updated_at = datetime.now(timezone.utc)
        return success

    def add_member(self, hero_id: UUID) -> None:
        if hero_id not in self.member_ids:
            self.member_ids.append(hero_id)
            self.updated_at = datetime.now(timezone.utc)

    def remove_member(self, hero_id: UUID) -> None:
        if hero_id in self.member_ids:
            self.member_ids.remove(hero_id)
            self.updated_at = datetime.now(timezone.utc)
