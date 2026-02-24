"""合并新增模块的所有 Schema 变更

将原 003~011 的 DDL 操作合并为单一迁移，以最终状态直接建表，消除中间的
ALTER TABLE（如 community_id NOT NULL → nullable、单独 ADD COLUMN 等）。

包含变更：
- contents.community_id 改为 nullable（原 010）
- content_communities 关联表（原 003）
- person_profiles + community_roles（原 004）
- committee_members.person_id FK（原 006）
- 活动模块：event_templates / events / 相关子表，community_id 直接 nullable（原 005+010）
- 运营活动模块：campaigns / 相关子表，community_id 直接 nullable（原 007+010）
- 生态洞察模块：ecosystem_projects（含 community_id）/ ecosystem_contributors（原 008+009）
- meetings.online_url 字段（原 011）

Revision ID: 002_schema_additions
Revises: 001_initial
Create Date: 2026-02-24
"""

import sqlalchemy as sa
from alembic import op

revision = "002_schema_additions"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. contents.community_id → nullable ────────────────────────────────────
    with op.batch_alter_table("contents") as batch_op:
        batch_op.alter_column("community_id", existing_type=sa.Integer(), nullable=True)

    # ── 2. content_communities 关联表 ──────────────────────────────────────────
    op.create_table(
        "content_communities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "content_id",
            sa.Integer,
            sa.ForeignKey("contents.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "community_id",
            sa.Integer,
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("is_primary", sa.Boolean, server_default="1"),
        sa.Column("linked_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "linked_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("content_id", "community_id", name="uq_content_community"),
    )

    # ── 3. 人脉模块：person_profiles + community_roles ─────────────────────────
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

    # ── 4. committee_members.person_id FK（依赖 person_profiles） ──────────────
    with op.batch_alter_table("committee_members") as batch_op:
        batch_op.add_column(sa.Column("person_id", sa.Integer, nullable=True))
        batch_op.create_foreign_key(
            "fk_committee_members_person_id",
            "person_profiles",
            ["person_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_committee_members_person_id", ["person_id"])

    # ── 5. 活动模块（community_id 直接 nullable，无需后续 ALTER） ──────────────
    op.create_table(
        "event_templates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "community_id",
            sa.Integer,
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=True,   # nullable from the start (replaces 010 ALTER)
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_public", sa.Boolean, server_default="0"),
        sa.Column(
            "created_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_event_templates_community_id", "event_templates", ["community_id"])

    op.create_table(
        "checklist_template_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "template_id",
            sa.Integer,
            sa.ForeignKey("event_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phase", sa.String(10), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index(
        "ix_checklist_template_items_template_id",
        "checklist_template_items",
        ["template_id"],
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "community_id",
            sa.Integer,
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=True,   # nullable from the start
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False, server_default="offline"),
        sa.Column(
            "template_id",
            sa.Integer,
            sa.ForeignKey("event_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("planned_at", sa.DateTime, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
        sa.Column("location", sa.String(300), nullable=True),
        sa.Column("online_url", sa.String(500), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("cover_image_url", sa.String(500), nullable=True),
        sa.Column(
            "owner_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phase", sa.String(10), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column(
            "assignee_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_checklist_items_event_id", "checklist_items", ["event_id"])

    op.create_table(
        "event_personnel",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("role_label", sa.String(100), nullable=True),
        sa.Column("assignee_type", sa.String(20), nullable=False),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confirmed", sa.String(20), server_default="pending"),
        sa.Column("time_slot", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_event_personnel_event_id", "event_personnel", ["event_id"])

    op.create_table(
        "event_attendees",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("checked_in", sa.Boolean, server_default="0"),
        sa.Column("role_at_event", sa.String(100), nullable=True),
        sa.Column("source", sa.String(20), server_default="manual"),
    )
    op.create_index("ix_event_attendees_event_id", "event_attendees", ["event_id"])
    op.create_index("ix_event_attendees_person_id", "event_attendees", ["person_id"])

    op.create_table(
        "feedback_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", sa.String(50), server_default="question"),
        sa.Column("raised_by", sa.String(200), nullable=True),
        sa.Column(
            "raised_by_person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), server_default="open"),
        sa.Column(
            "assignee_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_feedback_items_event_id", "feedback_items", ["event_id"])

    op.create_table(
        "issue_links",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "feedback_id",
            sa.Integer,
            sa.ForeignKey("feedback_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("repo", sa.String(200), nullable=False),
        sa.Column("issue_number", sa.Integer, nullable=False),
        sa.Column("issue_url", sa.String(500), nullable=False),
        sa.Column("issue_type", sa.String(10), server_default="issue"),
        sa.Column("issue_status", sa.String(10), server_default="open"),
        sa.Column("linked_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "linked_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_issue_links_feedback_id", "issue_links", ["feedback_id"])

    op.create_table(
        "event_tasks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "event_id",
            sa.Integer,
            sa.ForeignKey("events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("task_type", sa.String(20), server_default="task"),
        sa.Column("phase", sa.String(10), server_default="pre"),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("progress", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="not_started"),
        sa.Column("depends_on", sa.JSON, nullable=True),
        sa.Column(
            "parent_task_id",
            sa.Integer,
            sa.ForeignKey("event_tasks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("order", sa.Integer, server_default="0"),
    )
    op.create_index("ix_event_tasks_event_id", "event_tasks", ["event_id"])

    # ── 6. 运营活动模块（community_id 直接 nullable） ──────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "community_id",
            sa.Integer,
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=True,   # nullable from the start
        ),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("target_count", sa.Integer, nullable=True),
        sa.Column(
            "owner_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_campaigns_community_id", "campaigns", ["community_id"])

    op.create_table(
        "campaign_contacts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "campaign_id",
            sa.Integer,
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("channel", sa.String(50), nullable=True),
        sa.Column("added_by", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("last_contacted_at", sa.DateTime, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "assigned_to_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.UniqueConstraint("campaign_id", "person_id", name="uq_campaign_contact"),
    )
    op.create_index("ix_campaign_contacts_campaign_id", "campaign_contacts", ["campaign_id"])
    op.create_index("ix_campaign_contacts_person_id", "campaign_contacts", ["person_id"])

    op.create_table(
        "campaign_activities",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "campaign_id",
            sa.Integer,
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=True),
        sa.Column("outcome", sa.String(300), nullable=True),
        sa.Column(
            "operator_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_campaign_activities_campaign_id", "campaign_activities", ["campaign_id"])

    # ── 7. 生态洞察模块（ecosystem + community_id 合并建表） ───────────────────
    op.create_table(
        "ecosystem_projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "community_id",
            sa.Integer,
            sa.ForeignKey("communities.id", ondelete="CASCADE"),
            nullable=True,   # merged 009 ADD COLUMN + 010 nullable adjustment
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("platform", sa.String(30), nullable=False),
        sa.Column("org_name", sa.String(200), nullable=False),
        sa.Column("repo_name", sa.String(200), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="1"),
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column(
            "added_by_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_ecosystem_projects_community_id", "ecosystem_projects", ["community_id"])

    op.create_table(
        "ecosystem_contributors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "project_id",
            sa.Integer,
            sa.ForeignKey("ecosystem_projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("github_handle", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("commit_count_90d", sa.Integer, nullable=True),
        sa.Column("pr_count_90d", sa.Integer, nullable=True),
        sa.Column("star_count", sa.Integer, nullable=True),
        sa.Column("followers", sa.Integer, nullable=True),
        sa.Column(
            "person_id",
            sa.Integer,
            sa.ForeignKey("person_profiles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_synced_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "github_handle", name="uq_eco_contributor"),
    )
    op.create_index(
        "ix_ecosystem_contributors_project_id",
        "ecosystem_contributors",
        ["project_id"],
    )
    op.create_index(
        "ix_ecosystem_contributors_github_handle",
        "ecosystem_contributors",
        ["github_handle"],
    )
    op.create_index(
        "ix_ecosystem_contributors_person_id",
        "ecosystem_contributors",
        ["person_id"],
    )

    # ── 8. meetings.online_url ─────────────────────────────────────────────────
    with op.batch_alter_table("meetings") as batch_op:
        batch_op.add_column(sa.Column("online_url", sa.String(500), nullable=True))


def downgrade() -> None:
    # 逆序撤销，依赖关系安全
    with op.batch_alter_table("meetings") as batch_op:
        batch_op.drop_column("online_url")

    op.drop_index("ix_ecosystem_contributors_person_id", "ecosystem_contributors")
    op.drop_index("ix_ecosystem_contributors_github_handle", "ecosystem_contributors")
    op.drop_index("ix_ecosystem_contributors_project_id", "ecosystem_contributors")
    op.drop_table("ecosystem_contributors")
    op.drop_index("ix_ecosystem_projects_community_id", "ecosystem_projects")
    op.drop_table("ecosystem_projects")

    op.drop_index("ix_campaign_activities_campaign_id", "campaign_activities")
    op.drop_table("campaign_activities")
    op.drop_index("ix_campaign_contacts_person_id", "campaign_contacts")
    op.drop_index("ix_campaign_contacts_campaign_id", "campaign_contacts")
    op.drop_table("campaign_contacts")
    op.drop_index("ix_campaigns_community_id", "campaigns")
    op.drop_table("campaigns")

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

    with op.batch_alter_table("committee_members") as batch_op:
        batch_op.drop_index("ix_committee_members_person_id")
        batch_op.drop_column("person_id")

    op.drop_index("ix_community_roles_person_id", "community_roles")
    op.drop_table("community_roles")
    op.drop_index("ix_person_profiles_company", "person_profiles")
    op.drop_index("ix_person_profiles_email", "person_profiles")
    op.drop_index("ix_person_profiles_github_handle", "person_profiles")
    op.drop_index("ix_person_profiles_display_name", "person_profiles")
    op.drop_table("person_profiles")

    op.drop_table("content_communities")

    with op.batch_alter_table("contents") as batch_op:
        batch_op.alter_column("community_id", existing_type=sa.Integer(), nullable=False)
