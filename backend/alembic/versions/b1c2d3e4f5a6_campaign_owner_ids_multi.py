"""campaign_owner_ids_multi

Revision ID: b1c2d3e4f5a6
Revises: a7b8c9d0e1f2
Create Date: 2026-02-28 14:00:00.000000

将 campaigns.owner_id（单 FK）替换为 owner_ids（JSON 数组），支持多责任人。
"""
import json
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 新增 owner_ids JSON 列（默认空 JSON 数组字符串）
    op.add_column("campaigns", sa.Column("owner_ids", sa.JSON(), nullable=True))

    # 2. 将现有 owner_id 值迁移到 owner_ids（包装成单元素数组）
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, owner_id FROM campaigns")).fetchall()
    for row in rows:
        oids = json.dumps([row[1]]) if row[1] is not None else json.dumps([])
        conn.execute(
            sa.text("UPDATE campaigns SET owner_ids = :oids WHERE id = :id"),
            {"oids": oids, "id": row[0]},
        )

    # 3. 删除旧列（SQLite 需要 batch mode）
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.drop_column("owner_id")


def downgrade() -> None:
    # 1. 恢复 owner_id 列
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))

    # 2. 把 owner_ids 第一个元素写回 owner_id
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, owner_ids FROM campaigns")).fetchall()
    for row in rows:
        try:
            ids = json.loads(row[1]) if row[1] else []
            first = ids[0] if ids else None
        except Exception:
            first = None
        conn.execute(
            sa.text("UPDATE campaigns SET owner_id = :oid WHERE id = :id"),
            {"oid": first, "id": row[0]},
        )

    # 3. 删除 owner_ids 列
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.drop_column("owner_ids")
