"""add assignee_ids to checklist_items

Revision ID: a1b2c3d4e5f6
Revises: 7967bee72e83
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7967bee72e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('checklist_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assignee_ids', sa.JSON(), nullable=True))
        batch_op.drop_column('assignee_id')


def downgrade() -> None:
    with op.batch_alter_table('checklist_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assignee_id', sa.Integer(), nullable=True))
        batch_op.drop_column('assignee_ids')
