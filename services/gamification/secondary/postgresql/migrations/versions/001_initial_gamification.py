"""initial gamification tables

Revision ID: 001_gamification
Revises: 
Create Date: 2026-10-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# revision identifiers, used by Alembic.
revision = '001_gamification'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 0. Cria o schema gamification se ainda não existir
    op.execute("CREATE SCHEMA IF NOT EXISTS gamification")

    # 1. Tabela hero_progressions
    op.create_table(
        'hero_progressions',
        sa.Column('hero_id', PG_UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('hero_class', sa.String(length=50), nullable=False, server_default='NOVICE'),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('exp', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gold', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('hp', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_hp', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('mana', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('max_mana', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('stats', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('equipped_gear', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('active_buffs', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('skill_cooldowns', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('guild_id', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='gamification',
    )
    op.create_index('ix_gamification_hero_progressions_email', 'hero_progressions', ['email'], schema='gamification')
    op.create_index('ix_gamification_hero_progressions_guild_id', 'hero_progressions', ['guild_id'], schema='gamification')

    # 2. Tabela quests
    op.create_table(
        'quests',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('external_source', sa.String(length=50), nullable=False, server_default='linear'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('guild_id', PG_UUID(as_uuid=True), nullable=False),
        sa.Column('assignee_hero_id', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('adventure_id', PG_UUID(as_uuid=True), nullable=True),
        sa.Column('quest_type', sa.String(length=50), nullable=False, server_default='FEATURE'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='TODO'),
        sa.Column('difficulty', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('is_pair_programming', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='gamification',
    )
    op.create_index('ix_gamification_quests_external_id', 'quests', ['external_id'], unique=True, schema='gamification')
    op.create_index('ix_gamification_quests_guild_id', 'quests', ['guild_id'], schema='gamification')
    op.create_index('ix_gamification_quests_assignee_hero_id', 'quests', ['assignee_hero_id'], schema='gamification')

    # 3. Tabela mini_bosses
    op.create_table(
        'mini_bosses',
        sa.Column('id', PG_UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('guild_id', PG_UUID(as_uuid=True), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False, server_default='MEDIUM'),
        sa.Column('max_health', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('current_health', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_defeated', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('bounty_hero_xp', sa.Integer(), nullable=False, server_default='50'),
        sa.Column('bounty_guild_xp', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('bounty_gold', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='gamification',
    )
    op.create_index('ix_gamification_mini_bosses_external_id', 'mini_bosses', ['external_id'], unique=True, schema='gamification')
    op.create_index('ix_gamification_mini_bosses_guild_id', 'mini_bosses', ['guild_id'], schema='gamification')


def downgrade() -> None:
    op.drop_table('mini_bosses', schema='gamification')
    op.drop_table('quests', schema='gamification')
    op.drop_table('hero_progressions', schema='gamification')
    op.execute("DROP SCHEMA IF EXISTS gamification CASCADE")
