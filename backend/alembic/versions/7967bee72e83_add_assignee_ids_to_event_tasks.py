"""add assignee_ids to event_tasks

Revision ID: 7967bee72e83
Revises: 74ae746f13e6
Create Date: 2026-02-26 17:01:18.743787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7967bee72e83'
down_revision: Union[str, None] = '74ae746f13e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('event_tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assignee_ids', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('event_tasks', schema=None) as batch_op:
        batch_op.drop_column('assignee_ids')
