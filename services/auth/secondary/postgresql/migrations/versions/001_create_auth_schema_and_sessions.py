"""create auth schema and sessions

Revision ID: 001_auth_sessions
Revises: 
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_auth_sessions'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('provider_user_id', sa.String(length=128), nullable=False),
        sa.Column('token', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id'),
        schema='auth',
    )
    op.create_index('ix_auth_sessions_user_id', 'sessions', ['user_id'], unique=False, schema='auth')
    op.create_index('ix_auth_sessions_email', 'sessions', ['email'], unique=False, schema='auth')


def downgrade() -> None:
    op.drop_index('ix_auth_sessions_email', table_name='sessions', schema='auth')
    op.drop_index('ix_auth_sessions_user_id', table_name='sessions', schema='auth')
    op.drop_table('sessions', schema='auth')
