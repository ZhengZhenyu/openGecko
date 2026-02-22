"""新增 Ecosystem 生态洞察模块

Revision ID: 008_add_ecosystem_module
Revises: 007_add_campaign_module
Create Date: 2026-02-22
"""
import sqlalchemy as sa
from alembic import op

revision = "008_add_ecosystem_module"
down_revision = "007_add_campaign_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ecosystem_projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("org_name", sa.String(200), nullable=False),
        sa.Column("repo_name", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="1"),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column("added_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "ecosystem_contributors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("ecosystem_projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_handle", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("commit_count_90d", sa.Integer, nullable=True),
        sa.Column("pr_count_90d", sa.Integer, nullable=True),
        sa.Column("star_count", sa.Integer, nullable=True),
        sa.Column("followers", sa.Integer, nullable=True),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_synced_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "github_handle", name="uq_eco_contributor"),
    )
    op.create_index("ix_ecosystem_contributors_project_id", "ecosystem_contributors", ["project_id"])
    op.create_index("ix_ecosystem_contributors_github_handle", "ecosystem_contributors", ["github_handle"])
    op.create_index("ix_ecosystem_contributors_person_id", "ecosystem_contributors", ["person_id"])


def downgrade() -> None:
    op.drop_table("ecosystem_contributors")
    op.drop_table("ecosystem_projects")
