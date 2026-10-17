"""add tenant_id to guilds.guilds and guilds.members

Revision ID: 0002_guilds_tenant_id
Revises: 0001_initial_guilds
Create Date: 2026-10-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "0002_guilds_tenant_id"
down_revision: Union[str, None] = "0001_initial_guilds"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "guilds",
        sa.Column("tenant_id", sa.String(length=128), nullable=False, server_default="default"),
        schema="guilds",
    )
    op.create_index("ix_guilds_guilds_tenant_id", "guilds", ["tenant_id"], unique=False, schema="guilds")
    op.drop_index("ix_guilds_guilds_name", table_name="guilds", schema="guilds")
    op.create_index("ix_guilds_guilds_name", "guilds", ["name"], unique=False, schema="guilds")
    op.create_unique_constraint(
        "uq_guilds_tenant_name",
        "guilds",
        ["tenant_id", "name"],
        schema="guilds",
    )

    op.add_column(
        "members",
        sa.Column("tenant_id", sa.String(length=128), nullable=False, server_default="default"),
        schema="guilds",
    )
    op.create_index("ix_guilds_members_tenant_id", "members", ["tenant_id"], unique=False, schema="guilds")


def downgrade() -> None:
    op.drop_index("ix_guilds_members_tenant_id", table_name="members", schema="guilds")
    op.drop_column("members", "tenant_id", schema="guilds")

    op.drop_constraint("uq_guilds_tenant_name", "guilds", type_="unique", schema="guilds")
    op.drop_index("ix_guilds_guilds_name", table_name="guilds", schema="guilds")
    op.create_index("ix_guilds_guilds_name", "guilds", ["name"], unique=True, schema="guilds")
    op.drop_index("ix_guilds_guilds_tenant_id", table_name="guilds", schema="guilds")
    op.drop_column("guilds", "tenant_id", schema="guilds")
