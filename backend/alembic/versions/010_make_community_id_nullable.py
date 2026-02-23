"""将 events / event_templates / contents / campaigns 的 community_id 改为可选（nullable）

架构重构：从「社区隔离」改为「社区关联」模式
- 活动、内容、运营活动、生态洞察可独立存在，通过 community_id 属性可选关联到社区
- 委员会、会议仍保持强社区绑定

Revision ID: 010_make_community_id_nullable
Revises: 009_add_ecosystem_community_id
Create Date: 2026-02-23
"""
import sqlalchemy as sa
from alembic import op

revision = "010_make_community_id_nullable"
down_revision = "009_add_ecosystem_community_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # events.community_id: NOT NULL → nullable
    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    # event_templates.community_id: NOT NULL → nullable
    with op.batch_alter_table("event_templates") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    # contents.community_id: NOT NULL → nullable
    with op.batch_alter_table("contents") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    # campaigns.community_id: NOT NULL → nullable
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=True,
        )

    # ecosystem_projects.community_id was already added as nullable in 009,
    # but model shows nullable=False. No DDL change needed here since SQLite
    # already has it nullable; the model fix is done in the ORM layer.


def downgrade() -> None:
    # Note: downgrade may fail if there are rows with NULL community_id
    with op.batch_alter_table("campaigns") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("contents") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("event_templates") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("events") as batch_op:
        batch_op.alter_column(
            "community_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
