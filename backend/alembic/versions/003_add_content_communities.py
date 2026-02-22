"""新增 content_communities 关联表，迁移现有 community_id 数据

第一步（本文件）：创建关联表，将 contents.community_id 迁移进新表（is_primary=True）
第二步（009_remove_content_community_id.py）：迁移验证无误后移除旧 community_id 列

Revision ID: 003_add_content_communities
Revises: 002_simplify_roles
Create Date: 2026-02-22
"""

import sqlalchemy as sa
from alembic import op

revision = "003_add_content_communities"
down_revision = "002_simplify_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 唯一约束直接内联到 create_table，兼容 SQLite（不支持 ALTER ADD CONSTRAINT）
    op.create_table(
        "content_communities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "content_id",
            sa.Integer,
            sa.ForeignKey("contents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "community_id",
            sa.Integer,
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("is_primary", sa.Boolean, server_default="1"),
        sa.Column("linked_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "linked_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("content_id", "community_id", name="uq_content_community"),
    )
    # 迁移现有数据：将 contents.community_id 作为主社区写入新关联表
    op.execute("""
        INSERT INTO content_communities (content_id, community_id, is_primary)
        SELECT id, community_id, 1
        FROM contents
        WHERE community_id IS NOT NULL
    """)


def downgrade() -> None:
    op.drop_table("content_communities")
