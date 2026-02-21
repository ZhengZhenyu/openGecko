"""make committee member email and organization nullable

Revision ID: 009_make_member_email_org_nullable
Revises: 008_add_meeting_participants
Create Date: 2026-02-14 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "009_make_member_email_org_nullable"
down_revision = "008_add_meeting_participants"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite requires batch mode for column alterations
    with op.batch_alter_table("committee_members") as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=200),
            nullable=True,
        )
        batch_op.alter_column(
            "organization",
            existing_type=sa.String(length=200),
            nullable=True,
        )


def downgrade():
    with op.batch_alter_table("committee_members") as batch_op:
        batch_op.alter_column(
            "organization",
            existing_type=sa.String(length=200),
            nullable=False,
        )
        batch_op.alter_column(
            "email",
            existing_type=sa.String(length=200),
            nullable=False,
        )
