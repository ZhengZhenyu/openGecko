"""add event_communities many_to_many

Revision ID: 7e70abbef6ae
Revises: 003_data_migrations
Create Date: 2026-02-24 20:21:52.592608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '7e70abbef6ae'
down_revision: Union[str, None] = '003_data_migrations'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'event_communities',
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id', 'community_id'),
    )


def downgrade() -> None:
    op.drop_table('event_communities')
