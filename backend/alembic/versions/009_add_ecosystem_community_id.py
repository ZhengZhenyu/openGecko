"""Ecosystem projects 增加 community_id 多租户字段

Revision ID: 009_add_ecosystem_community_id
Revises: 008_add_ecosystem_module
Create Date: 2026-02-22
"""
import sqlalchemy as sa
from alembic import op

revision = "009_add_ecosystem_community_id"
down_revision = "008_add_ecosystem_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite 不支持 ADD COLUMN NOT NULL without default，用 batch 模式
    with op.batch_alter_table("ecosystem_projects") as batch_op:
        batch_op.add_column(
            sa.Column(
                "community_id",
                sa.Integer,
                nullable=True,   # 已有数据兼容；新记录由 API 层强制填写
            )
        )
        batch_op.create_index("ix_ecosystem_projects_community_id", ["community_id"])
        batch_op.create_foreign_key(
            "fk_ecosystem_projects_community_id",
            "communities",
            ["community_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("ecosystem_projects") as batch_op:
        batch_op.drop_constraint("fk_ecosystem_projects_community_id", type_="foreignkey")
        batch_op.drop_index("ix_ecosystem_projects_community_id")
        batch_op.drop_column("community_id")
