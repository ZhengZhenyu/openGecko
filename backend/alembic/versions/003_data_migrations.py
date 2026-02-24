"""数据迁移：角色简化 + content_communities 数据回填

合并原 002（简化权限角色）和 003（内容社区关联数据迁移）的数据操作。
对全新安装的数据库这两个操作均为空操作（无行可更新/迁移）。

Revision ID: 003_data_migrations
Revises: 002_schema_additions
Create Date: 2026-02-24
"""

from alembic import op

revision = "003_data_migrations"
down_revision = "002_schema_additions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 简化权限角色：community_admin 降为 user
    op.execute("UPDATE community_users SET role = 'user' WHERE role = 'community_admin'")

    # 2. 将 contents.community_id 现有数据回填到 content_communities 关联表
    op.execute("""
        INSERT INTO content_communities (content_id, community_id, is_primary)
        SELECT id, community_id, 1
        FROM contents
        WHERE community_id IS NOT NULL
    """)


def downgrade() -> None:
    # 删除回填数据（仅删除 is_primary=1 且来源于迁移的行）
    # 注意：角色简化不可逆（无法区分哪些 user 原本是 community_admin）
    op.execute("DELETE FROM content_communities WHERE is_primary = 1")
