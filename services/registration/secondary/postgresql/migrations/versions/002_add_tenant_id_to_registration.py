"""add tenant_id to registration.heroes

Revision ID: 002_registration_tenant_id
Revises: 001_initial_registration
Create Date: 2026-10-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_registration_tenant_id"
down_revision: Union[str, None] = "001_initial_registration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "heroes",
        sa.Column("tenant_id", sa.String(length=128), nullable=False, server_default="default"),
        schema="registration",
    )
    op.create_index("ix_registration_heroes_tenant_id", "heroes", ["tenant_id"], unique=False, schema="registration")
    op.drop_index(op.f("ix_registration_heroes_email"), table_name="heroes", schema="registration")
    op.create_index("ix_registration_heroes_email", "heroes", ["email"], unique=False, schema="registration")
    op.create_unique_constraint(
        "uq_registration_heroes_tenant_email",
        "heroes",
        ["tenant_id", "email"],
        schema="registration",
    )


def downgrade() -> None:
    op.drop_constraint("uq_registration_heroes_tenant_email", "heroes", type_="unique", schema="registration")
    op.drop_index("ix_registration_heroes_email", table_name="heroes", schema="registration")
    op.create_index(op.f("ix_registration_heroes_email"), "heroes", ["email"], unique=True, schema="registration")
    op.drop_index("ix_registration_heroes_tenant_id", table_name="heroes", schema="registration")
    op.drop_column("heroes", "tenant_id", schema="registration")
