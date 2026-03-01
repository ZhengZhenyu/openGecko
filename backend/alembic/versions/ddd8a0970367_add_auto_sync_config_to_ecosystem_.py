"""add auto_sync config to ecosystem_projects

Revision ID: ddd8a0970367
Revises: b1c2d3e4f5a6
Create Date: 2026-03-01 16:31:06.338286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddd8a0970367'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('ecosystem_projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('auto_sync_enabled', sa.Boolean(), nullable=False, server_default='1'))
        batch_op.add_column(sa.Column('sync_interval_hours', sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('ecosystem_projects', schema=None) as batch_op:
        batch_op.drop_column('sync_interval_hours')
        batch_op.drop_column('auto_sync_enabled')
