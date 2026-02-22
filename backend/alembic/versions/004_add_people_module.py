"""新增人脉模块：person_profiles + community_roles 表

Revision ID: 004_add_people_module
Revises: 003_add_content_communities
Create Date: 2026-02-22
"""

import sqlalchemy as sa
from alembic import op

revision = "004_add_people_module"
down_revision = "003_add_content_communities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "person_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("github_handle", sa.String(100), nullable=True, unique=True),
        sa.Column("gitcode_handle", sa.String(100), nullable=True, unique=True),
        sa.Column("email", sa.String(200), nullable=True, unique=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("company", sa.String(200), nullable=True),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("bio", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("source", sa.String(30), nullable=False, server_default="manual"),
        sa.Column(
            "created_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_person_profiles_display_name", "person_profiles", ["display_name"])
    op.create_index("ix_person_profiles_github_handle", "person_profiles", ["github_handle"])
    op.create_index("ix_person_profiles_email", "person_profiles", ["email"])
    op.create_index("ix_person_profiles_company", "person_profiles", ["company"])

    op.create_table(
        "community_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("community_name", sa.String(200), nullable=False),
        sa.Column("project_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("role_label", sa.String(100), nullable=True),
        sa.Column("is_current", sa.Boolean, server_default="1"),
        sa.Column("started_at", sa.Date, nullable=True),
        sa.Column("ended_at", sa.Date, nullable=True),
        sa.Column("source_url", sa.String(500), nullable=True),
        sa.Column(
            "updated_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_community_roles_person_id", "community_roles", ["person_id"])


def downgrade() -> None:
    op.drop_index("ix_community_roles_person_id", "community_roles")
    op.drop_table("community_roles")
    op.drop_index("ix_person_profiles_company", "person_profiles")
    op.drop_index("ix_person_profiles_email", "person_profiles")
    op.drop_index("ix_person_profiles_github_handle", "person_profiles")
    op.drop_index("ix_person_profiles_display_name", "person_profiles")
    op.drop_table("person_profiles")
