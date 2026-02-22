"""CommitteeMember 关联 PersonProfile

Revision ID: 006_link_committee_member_to_person
Revises: 005_add_event_module
Create Date: 2026-02-22
"""

import sqlalchemy as sa
from alembic import op

revision = "006_link_committee_member_to_person"
down_revision = "005_add_event_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("committee_members") as batch_op:
        batch_op.add_column(
            sa.Column("person_id", sa.Integer, nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_committee_members_person_id",
            "person_profiles",
            ["person_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_committee_members_person_id", ["person_id"])


def downgrade() -> None:
    with op.batch_alter_table("committee_members") as batch_op:
        batch_op.drop_index("ix_committee_members_person_id")
        batch_op.drop_column("person_id")
