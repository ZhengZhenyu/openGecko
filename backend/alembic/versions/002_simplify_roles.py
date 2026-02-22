"""简化权限模型：移除 community_admin 角色

将所有 community_users.role = 'community_admin' 统一降级为 'user'。
新权限体系：superuser / admin / user（三层，无 community_admin）

Revision ID: 002_simplify_roles
Revises: 001_initial
Create Date: 2026-02-22
"""

from alembic import op

revision = "002_simplify_roles"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "UPDATE community_users SET role = 'user' WHERE role = 'community_admin'"
    )


def downgrade() -> None:
    # 无法恢复：降级后无法区分哪些 user 原本是 community_admin
    pass
