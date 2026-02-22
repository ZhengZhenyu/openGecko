"""新增 Campaign 运营活动模块

Revision ID: 007_add_campaign_module
Revises: 006_link_committee_member_to_person
Create Date: 2026-02-22
"""
import sqlalchemy as sa
from alembic import op

revision = "007_add_campaign_module"
down_revision = "006_link_committee_member_to_person"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("community_id", sa.Integer, sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("target_count", sa.Integer, nullable=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_campaigns_community_id", "campaigns", ["community_id"])

    op.create_table(
        "campaign_contacts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("added_by", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("last_contacted_at", sa.DateTime, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("assigned_to_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("campaign_id", "person_id", name="uq_campaign_contact"),
    )
    op.create_index("ix_campaign_contacts_campaign_id", "campaign_contacts", ["campaign_id"])
    op.create_index("ix_campaign_contacts_person_id", "campaign_contacts", ["person_id"])

    op.create_table(
        "campaign_activities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("outcome", sa.String(300), nullable=True),
        sa.Column("operator_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_campaign_activities_campaign_id", "campaign_activities", ["campaign_id"])


def downgrade() -> None:
    op.drop_table("campaign_activities")
    op.drop_table("campaign_contacts")
    op.drop_table("campaigns")
