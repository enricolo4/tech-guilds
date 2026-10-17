"""add tenant_id to auth.sessions

Revision ID: 002_auth_tenant_id
Revises: 001_auth_sessions
Create Date: 2026-10-16 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "002_auth_tenant_id"
down_revision: Union[str, None] = "001_auth_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("tenant_id", sa.String(length=128), nullable=False, server_default="default"),
        schema="auth",
    )
    op.create_index("ix_auth_sessions_tenant_id", "sessions", ["tenant_id"], unique=False, schema="auth")


def downgrade() -> None:
    op.drop_index("ix_auth_sessions_tenant_id", table_name="sessions", schema="auth")
    op.drop_column("sessions", "tenant_id", schema="auth")
