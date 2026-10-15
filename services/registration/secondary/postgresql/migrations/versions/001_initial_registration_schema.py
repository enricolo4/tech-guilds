"""Initial registration schema

Revision ID: 001_initial_registration
Revises: 
Create Date: 2026-10-15 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_registration'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criação isolada do schema 'registration'
    op.execute("CREATE SCHEMA IF NOT EXISTS registration")

    op.create_table(
        'heroes',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('avatar_url', sa.String(length=1024), nullable=True),
        sa.Column('hero_class', sa.String(length=50), nullable=False, server_default='NOVICE'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('experience', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gold', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('health', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_health', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('mana', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_mana', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('strength', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('intelligence', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('constitution', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('perception', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('guild_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='registration',
    )
    op.create_index(
        op.f('ix_registration_heroes_email'),
        'heroes',
        ['email'],
        unique=True,
        schema='registration',
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_registration_heroes_email'), table_name='heroes', schema='registration')
    op.drop_table('heroes', schema='registration')
    op.execute("DROP SCHEMA IF EXISTS registration CASCADE")
