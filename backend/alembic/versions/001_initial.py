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
  meetings, meeting_reminders, meeting_assignees, meeting_participants,
  wechat_article_stats, wechat_stats_aggregates
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


    # ------------------------------------------------------------------
    # wechat_article_stats
    # ------------------------------------------------------------------
    op.create_table(
        "wechat_article_stats",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("publish_record_id", sa.Integer(),
                  sa.ForeignKey("publish_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("article_category",
                  sa.Enum("release", "technical", "activity", name="article_category_enum"),
                  nullable=False, server_default="technical"),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("read_count", sa.Integer(), server_default="0"),
        sa.Column("read_user_count", sa.Integer(), server_default="0"),
        sa.Column("read_original_count", sa.Integer(), server_default="0"),
        sa.Column("like_count", sa.Integer(), server_default="0"),
        sa.Column("wow_count", sa.Integer(), server_default="0"),
        sa.Column("share_count", sa.Integer(), server_default="0"),
        sa.Column("comment_count", sa.Integer(), server_default="0"),
        sa.Column("favorite_count", sa.Integer(), server_default="0"),
        sa.Column("forward_count", sa.Integer(), server_default="0"),
        sa.Column("new_follower_count", sa.Integer(), server_default="0"),
        sa.Column("unfollow_count", sa.Integer(), server_default="0"),
        sa.Column("community_id", sa.Integer(),
                  sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("collected_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("publish_record_id", "stat_date", name="uq_article_stat_date"),
    )
    op.create_index("ix_wechat_article_stats_publish_record_id", "wechat_article_stats", ["publish_record_id"])
    op.create_index("ix_wechat_article_stats_stat_date", "wechat_article_stats", ["stat_date"])
    op.create_index("ix_wechat_article_stats_article_category", "wechat_article_stats", ["article_category"])
    op.create_index("ix_wechat_article_stats_community_id", "wechat_article_stats", ["community_id"])
    op.create_index("ix_wechat_stats_category_date", "wechat_article_stats", ["article_category", "stat_date"])
    op.create_index("ix_wechat_stats_community_date", "wechat_article_stats", ["community_id", "stat_date"])

    # ------------------------------------------------------------------
    # wechat_stats_aggregates
    # ------------------------------------------------------------------
    op.create_table(
        "wechat_stats_aggregates",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("community_id", sa.Integer(),
                  sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_type",
                  sa.Enum("daily", "weekly", "monthly", "quarterly",
                          "semi_annual", "annual", name="period_type_enum"),
                  nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("article_category",
                  sa.Enum("release", "technical", "activity", name="article_category_enum"),
                  nullable=True),
        sa.Column("total_articles", sa.Integer(), server_default="0"),
        sa.Column("total_read_count", sa.Integer(), server_default="0"),
        sa.Column("total_read_user_count", sa.Integer(), server_default="0"),
        sa.Column("total_like_count", sa.Integer(), server_default="0"),
        sa.Column("total_wow_count", sa.Integer(), server_default="0"),
        sa.Column("total_share_count", sa.Integer(), server_default="0"),
        sa.Column("total_comment_count", sa.Integer(), server_default="0"),
        sa.Column("total_favorite_count", sa.Integer(), server_default="0"),
        sa.Column("total_forward_count", sa.Integer(), server_default="0"),
        sa.Column("total_new_follower_count", sa.Integer(), server_default="0"),
        sa.Column("avg_read_count", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "community_id", "period_type", "period_start", "article_category",
            name="uq_stats_aggregate",
        ),
    )
    op.create_index("ix_wechat_stats_aggregates_community_id", "wechat_stats_aggregates", ["community_id"])
    op.create_index("ix_wechat_stats_aggregates_period_type", "wechat_stats_aggregates", ["period_type"])
    op.create_index("ix_wechat_stats_aggregates_period_start", "wechat_stats_aggregates", ["period_start"])
    op.create_index("ix_aggregate_period", "wechat_stats_aggregates", ["community_id", "period_type", "period_start"])


def downgrade():
    op.drop_table("wechat_stats_aggregates")
    op.drop_table("wechat_article_stats")
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
