"""为 meetings 表添加 online_url 字段，支持线上线下混合会议

Revision ID: 011_add_meeting_online_url
Revises: 010_make_community_id_nullable
Create Date: 2026-02-23
"""
import sqlalchemy as sa
from alembic import op

revision = "011_add_meeting_online_url"
down_revision = "010_make_community_id_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("meetings") as batch_op:
        batch_op.add_column(
            sa.Column("online_url", sa.String(500), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("meetings") as batch_op:
        batch_op.drop_column("online_url")
