"""v1.0 complete initial schema

This single migration creates the full database schema for openGecko v1.0,
consolidating all previous incremental migrations (001-009).

Revision ID: 001_initial
Revises: None
Create Date: 2026-02-21

Tables:
  users, communities, community_users,
  channel_configs, audit_logs, password_reset_tokens,
  contents, content_collaborators, content_assignees, content_analytics,
  publish_records,
  committees, committee_members,
  meetings, meeting_reminders, meeting_assignees, meeting_participants
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_default_admin", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # ------------------------------------------------------------------
    # communities
    # ------------------------------------------------------------------
    op.create_table(
        "communities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ------------------------------------------------------------------
    # community_users
    # ------------------------------------------------------------------
    op.create_table(
        "community_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # channel_configs
    # ------------------------------------------------------------------
    op.create_table(
        "channel_configs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False, index=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("community_id", "channel", name="uq_community_channel"),
    )

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("community_id", sa.Integer(), nullable=True, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True, index=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # password_reset_tokens
    # ------------------------------------------------------------------
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(200), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # contents
    # ------------------------------------------------------------------
    op.create_table(
        "contents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=True),
        sa.Column("content_html", sa.Text(), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=True),
        sa.Column("source_file", sa.String(500), nullable=True),
        sa.Column("author", sa.String(200), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("cover_image", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=True, server_default="draft"),
        sa.Column("work_status", sa.String(50), nullable=True, server_default="planning", index=True),
        sa.Column("community_id", sa.Integer(), nullable=False, index=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("owner_id", sa.Integer(), nullable=True, index=True),
        sa.Column("scheduled_publish_at", sa.DateTime(), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
    )

    # ------------------------------------------------------------------
    # content_collaborators  (association table)
    # ------------------------------------------------------------------
    op.create_table(
        "content_collaborators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # content_assignees  (responsibility mapping)
    # ------------------------------------------------------------------
    op.create_table(
        "content_assignees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content_id", sa.Integer(), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # publish_records
    # ------------------------------------------------------------------
    op.create_table(
        "publish_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("platform_article_id", sa.String(200), nullable=True),
        sa.Column("platform_url", sa.String(500), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["contents.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # content_analytics
    # ------------------------------------------------------------------
    op.create_table(
        "content_analytics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("publish_record_id", sa.Integer(), nullable=False),
        sa.Column("read_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("like_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("share_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("comment_count", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("collected_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["publish_record_id"], ["publish_records.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # committees
    # ------------------------------------------------------------------
    op.create_table(
        "committees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("meeting_frequency", sa.String(50), nullable=True),
        sa.Column("notification_email", sa.String(200), nullable=True),
        sa.Column("notification_wechat", sa.String(100), nullable=True),
        sa.Column("established_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("community_id", "slug", name="uq_committee_community_slug"),
    )

    # ------------------------------------------------------------------
    # committee_members
    # ------------------------------------------------------------------
    op.create_table(
        "committee_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("committee_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("wechat", sa.String(100), nullable=True),
        sa.Column("organization", sa.String(200), nullable=True),
        sa.Column("gitcode_id", sa.String(100), nullable=True),
        sa.Column("github_id", sa.String(100), nullable=True),
        sa.Column("roles", sa.JSON(), nullable=True),
        sa.Column("term_start", sa.Date(), nullable=True),
        sa.Column("term_end", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["committee_id"], ["committees.id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------
    # meetings
    # ------------------------------------------------------------------
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("committee_id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("duration", sa.Integer(), nullable=True, server_default="120"),
        sa.Column("location_type", sa.String(50), nullable=True),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("work_status", sa.String(50), nullable=True, server_default="planning", index=True),
        sa.Column("agenda", sa.Text(), nullable=True),
        sa.Column("minutes", sa.Text(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("reminder_sent", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("reminder_before_hours", sa.Integer(), nullable=True, server_default="24"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["committee_id"], ["committees.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["community_id"], ["communities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
    )

    # ------------------------------------------------------------------
    # meeting_reminders
    # ------------------------------------------------------------------
    op.create_table(
        "meeting_reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("reminder_type", sa.String(50), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("notification_channels", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_reminder_scheduled_status", "meeting_reminders", ["scheduled_at", "status"])

    # ------------------------------------------------------------------
    # meeting_assignees
    # ------------------------------------------------------------------
    op.create_table(
        "meeting_assignees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), nullable=False, index=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------------
    # meeting_participants
    # ------------------------------------------------------------------
    op.create_table(
        "meeting_participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False, index=True),
        sa.Column("source", sa.String(50), nullable=True, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "email", name="uq_meeting_participant_email"),
    )


def downgrade():
    op.drop_table("meeting_participants")
    op.drop_table("meeting_assignees")
    op.drop_index("idx_reminder_scheduled_status", table_name="meeting_reminders")
    op.drop_table("meeting_reminders")
    op.drop_table("meetings")
    op.drop_table("committee_members")
    op.drop_table("committees")
    op.drop_table("content_analytics")
    op.drop_table("publish_records")
    op.drop_table("content_assignees")
    op.drop_table("content_collaborators")
    op.drop_table("contents")
    op.drop_table("password_reset_tokens")
    op.drop_table("audit_logs")
    op.drop_table("channel_configs")
    op.drop_table("community_users")
    op.drop_table("communities")
    op.drop_table("users")
