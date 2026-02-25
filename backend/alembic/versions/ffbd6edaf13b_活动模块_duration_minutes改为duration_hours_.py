"""活动模块：duration_minutes改为duration_hours，移除draft和cancelled状态

Revision ID: ffbd6edaf13b
Revises: 986ddbdad1d7
Create Date: 2026-02-25 18:03:52.645280

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffbd6edaf13b'
down_revision: Union[str, None] = '986ddbdad1d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 数据迁移：将 draft/cancelled 状态更新为 planning
    op.execute(sa.text("UPDATE events SET status = 'planning' WHERE status IN ('draft', 'cancelled')"))

    # 2. 先添加 duration_hours 列
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration_hours', sa.Float(), nullable=True))

    # 3. 将 duration_minutes 换算为 duration_hours（保留 1 位小数）
    op.execute(sa.text(
        "UPDATE events SET duration_hours = ROUND(CAST(duration_minutes AS FLOAT) / 60.0, 1) "
        "WHERE duration_minutes IS NOT NULL"
    ))

    # 4. 移除 duration_minutes 列
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('duration_minutes')


def downgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration_minutes', sa.INTEGER(), nullable=True))

    op.execute(sa.text(
        "UPDATE events SET duration_minutes = CAST(duration_hours * 60 AS INTEGER) "
        "WHERE duration_hours IS NOT NULL"
    ))

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('duration_hours')
