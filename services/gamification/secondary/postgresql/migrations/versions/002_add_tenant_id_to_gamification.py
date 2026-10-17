"""Add tenant_id to gamification tables

Revision ID: 002_add_tenant_id_to_gamification
Revises: 001_initial_gamification
Create Date: 2026-10-17 03:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_add_tenant_id_to_gamification"
down_revision: Union[str, None] = "001_initial_gamification"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # hero_progressions
    op.add_column(
        "hero_progressions",
        sa.Column("tenant_id", sa.String(length=120), server_default="default", nullable=False),
        schema="gamification",
    )
    op.create_index(
        "ix_gamification_hero_progressions_tenant_id",
        "hero_progressions",
        ["tenant_id"],
        unique=False,
        schema="gamification",
    )

    # quests
    op.add_column(
        "quests",
        sa.Column("tenant_id", sa.String(length=120), server_default="default", nullable=False),
        schema="gamification",
    )
    op.create_index(
        "ix_gamification_quests_tenant_id",
        "quests",
        ["tenant_id"],
        unique=False,
        schema="gamification",
    )
    op.create_unique_constraint(
        "uq_gamification_quests_tenant_external_id",
        "quests",
        ["tenant_id", "external_id"],
        schema="gamification",
    )

    # mini_bosses
    op.add_column(
        "mini_bosses",
        sa.Column("tenant_id", sa.String(length=120), server_default="default", nullable=False),
        schema="gamification",
    )
    op.create_index(
        "ix_gamification_mini_bosses_tenant_id",
        "mini_bosses",
        ["tenant_id"],
        unique=False,
        schema="gamification",
    )
    op.create_unique_constraint(
        "uq_gamification_mini_bosses_tenant_external_id",
        "mini_bosses",
        ["tenant_id", "external_id"],
        schema="gamification",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_gamification_mini_bosses_tenant_external_id",
        "mini_bosses",
        schema="gamification",
        type_="unique",
    )
    op.drop_index("ix_gamification_mini_bosses_tenant_id", table_name="mini_bosses", schema="gamification")
    op.drop_column("mini_bosses", "tenant_id", schema="gamification")

    op.drop_constraint(
        "uq_gamification_quests_tenant_external_id",
        "quests",
        schema="gamification",
        type_="unique",
    )
    op.drop_index("ix_gamification_quests_tenant_id", table_name="quests", schema="gamification")
    op.drop_column("quests", "tenant_id", schema="gamification")

    op.drop_index(
        "ix_gamification_hero_progressions_tenant_id",
        table_name="hero_progressions",
        schema="gamification",
    )
    op.drop_column("hero_progressions", "tenant_id", schema="gamification")
