"""add_campaign_tasks_table

Revision ID: 4c2c0cc4b1a5
Revises: a1b2c3d4e5f6
Create Date: 2026-02-27 23:12:17.209747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c2c0cc4b1a5'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'campaign_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='not_started'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('assignee_ids', sa.JSON(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_campaign_tasks_campaign_id'), 'campaign_tasks', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_campaign_tasks_id'), 'campaign_tasks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_campaign_tasks_id'), table_name='campaign_tasks')
    op.drop_index(op.f('ix_campaign_tasks_campaign_id'), table_name='campaign_tasks')
    op.drop_table('campaign_tasks')
