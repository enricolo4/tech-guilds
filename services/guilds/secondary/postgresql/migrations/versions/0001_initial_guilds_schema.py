"""Initial guilds schema: guilds.guilds and guilds.members

Revision ID: 0001_initial_guilds
Revises: None
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_guilds"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Garante a existência do schema 'guilds'
    op.execute("CREATE SCHEMA IF NOT EXISTS guilds")

    # 2. Criação da tabela guilds.guilds
    op.create_table(
        "guilds",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("experience", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("treasury_gold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        schema="guilds",
    )
    op.create_index(
        "ix_guilds_guilds_name",
        "guilds",
        ["name"],
        unique=True,
        schema="guilds",
    )

    # 3. Criação da tabela guilds.members
    op.create_table(
        "members",
        sa.Column("hero_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hero_class", sa.String(length=50), nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("guild_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["guild_id"],
            ["guilds.guilds.id"],
            ondelete="SET NULL",
        ),
        schema="guilds",
    )
    op.create_index(
        "ix_guilds_members_guild_id",
        "members",
        ["guild_id"],
        unique=False,
        schema="guilds",
    )


def downgrade() -> None:
    op.drop_index("ix_guilds_members_guild_id", table_name="members", schema="guilds")
    op.drop_table("members", schema="guilds")
    op.drop_index("ix_guilds_guilds_name", table_name="guilds", schema="guilds")
    op.drop_table("guilds", schema="guilds")
    op.execute("DROP SCHEMA IF EXISTS guilds CASCADE")
