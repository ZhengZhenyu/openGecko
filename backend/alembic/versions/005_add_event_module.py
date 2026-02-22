"""新增活动模块：event_templates、checklist_template_items、events、
checklist_items、event_personnel、event_attendees、
feedback_items、issue_links、event_tasks 表

Revision ID: 005_add_event_module
Revises: 004_add_people_module
Create Date: 2026-02-22
"""

import sqlalchemy as sa
from alembic import op

revision = "005_add_event_module"
down_revision = "004_add_people_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_templates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("community_id", sa.Integer, sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, server_default="0"),
        sa.Column("created_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_event_templates_community_id", "event_templates", ["community_id"])

    op.create_table(
        "checklist_template_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("template_id", sa.Integer, sa.ForeignKey("event_templates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.String(10), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_checklist_template_items_template_id", "checklist_template_items", ["template_id"])

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("community_id", sa.Integer, sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False, server_default="offline"),
        sa.Column("template_id", sa.Integer, sa.ForeignKey("event_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("planned_at", sa.DateTime, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("online_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("attendee_count", sa.Integer, nullable=True),
        sa.Column("online_count", sa.Integer, nullable=True),
        sa.Column("offline_count", sa.Integer, nullable=True),
        sa.Column("registration_count", sa.Integer, nullable=True),
        sa.Column("result_summary", sa.Text, nullable=True),
        sa.Column("media_urls", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_events_community_id", "events", ["community_id"])

    op.create_table(
        "checklist_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase", sa.String(10), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("assignee_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_checklist_items_event_id", "checklist_items", ["event_id"])

    op.create_table(
        "event_personnel",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("role_label", sa.String(100), nullable=True),
        sa.Column("assignee_type", sa.String(20), nullable=False),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confirmed", sa.String(20), server_default="pending"),
        sa.Column("time_slot", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_event_personnel_event_id", "event_personnel", ["event_id"])

    op.create_table(
        "event_attendees",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.Integer, sa.ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("checked_in", sa.Boolean, server_default="0"),
        sa.Column("role_at_event", sa.String(100), nullable=True),
        sa.Column("source", sa.String(20), server_default="manual"),
    )
    op.create_index("ix_event_attendees_event_id", "event_attendees", ["event_id"])
    op.create_index("ix_event_attendees_person_id", "event_attendees", ["person_id"])

    op.create_table(
        "feedback_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), server_default="question"),
        sa.Column("raised_by", sa.String(200), nullable=True),
        sa.Column("raised_by_person_id", sa.Integer, sa.ForeignKey("person_profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column("assignee_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_feedback_items_event_id", "feedback_items", ["event_id"])

    op.create_table(
        "issue_links",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("feedback_id", sa.Integer, sa.ForeignKey("feedback_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("repo", sa.String(200), nullable=False),
        sa.Column("issue_number", sa.Integer, nullable=False),
        sa.Column("issue_url", sa.String(500), nullable=False),
        sa.Column("issue_type", sa.String(10), server_default="issue"),
        sa.Column("issue_status", sa.String(10), server_default="open"),
        sa.Column("linked_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("linked_by_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_issue_links_feedback_id", "issue_links", ["feedback_id"])

    op.create_table(
        "event_tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("task_type", sa.String(20), server_default="task"),
        sa.Column("phase", sa.String(10), server_default="pre"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("progress", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="not_started"),
        sa.Column("depends_on", sa.JSON, nullable=True),
        sa.Column("parent_task_id", sa.Integer, sa.ForeignKey("event_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_event_tasks_event_id", "event_tasks", ["event_id"])


def downgrade() -> None:
    op.drop_index("ix_event_tasks_event_id", "event_tasks")
    op.drop_table("event_tasks")
    op.drop_index("ix_issue_links_feedback_id", "issue_links")
    op.drop_table("issue_links")
    op.drop_index("ix_feedback_items_event_id", "feedback_items")
    op.drop_table("feedback_items")
    op.drop_index("ix_event_attendees_person_id", "event_attendees")
    op.drop_index("ix_event_attendees_event_id", "event_attendees")
    op.drop_table("event_attendees")
    op.drop_index("ix_event_personnel_event_id", "event_personnel")
    op.drop_table("event_personnel")
    op.drop_index("ix_checklist_items_event_id", "checklist_items")
    op.drop_table("checklist_items")
    op.drop_index("ix_events_community_id", "events")
    op.drop_table("events")
    op.drop_index("ix_checklist_template_items_template_id", "checklist_template_items")
    op.drop_table("checklist_template_items")
    op.drop_index("ix_event_templates_community_id", "event_templates")
    op.drop_table("event_templates")
