"""Integrated migration: create all models and seed default community/admin

Revision ID: integrated_all_models
Revises: None
Create Date: 2026-02-10

This migration is written to be idempotent for fresh DBs and safe to run
against an empty SQLite database for testing upgrade/downgrade.
"""
from datetime import datetime

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'integrated_all_models'
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(conn, name):
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def upgrade():
    conn = op.get_bind()

    # users
    if not _table_exists(conn, 'users'):
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(100), nullable=False, unique=True),
            sa.Column('email', sa.String(200), nullable=False, unique=True),
            sa.Column('hashed_password', sa.String(200), nullable=False),
            sa.Column('full_name', sa.String(200), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('is_default_admin', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    # communities
    if not _table_exists(conn, 'communities'):
        op.create_table(
            'communities',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('name', sa.String(200), nullable=False, unique=True),
            sa.Column('slug', sa.String(100), nullable=False, unique=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('url', sa.String(500), nullable=True),
            sa.Column('logo_url', sa.String(500), nullable=True),
            sa.Column('settings', sa.JSON(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )

    # association table: community_users
    if not _table_exists(conn, 'community_users'):
        op.create_table(
            'community_users',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('community_id', sa.Integer(), nullable=False),
            sa.Column('role', sa.String(50), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        )

    # contents
    if not _table_exists(conn, 'contents'):
        op.create_table(
            'contents',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('content_markdown', sa.Text(), nullable=True),
            sa.Column('content_html', sa.Text(), nullable=True),
            sa.Column('source_type', sa.String(50), nullable=True),
            sa.Column('source_file', sa.String(500), nullable=True),
            sa.Column('author', sa.String(200), nullable=True),
            sa.Column('tags', sa.JSON(), nullable=True),
            sa.Column('category', sa.String(100), nullable=True),
            sa.Column('cover_image', sa.String(500), nullable=True),
            sa.Column('status', sa.String(50), nullable=True),
            sa.Column('community_id', sa.Integer(), nullable=False),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('scheduled_publish_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='SET NULL'),
        )

    # publish_records
    if not _table_exists(conn, 'publish_records'):
        op.create_table(
            'publish_records',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('content_id', sa.Integer(), nullable=False),
            sa.Column('channel', sa.String(50), nullable=False),
            sa.Column('status', sa.String(50), nullable=True),
            sa.Column('platform_article_id', sa.String(200), nullable=True),
            sa.Column('platform_url', sa.String(500), nullable=True),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        )

    # content_analytics
    if not _table_exists(conn, 'content_analytics'):
        op.create_table(
            'content_analytics',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('publish_record_id', sa.Integer(), nullable=False),
            sa.Column('read_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('like_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('share_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('comment_count', sa.Integer(), nullable=True, server_default='0'),
            sa.Column('collected_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['publish_record_id'], ['publish_records.id'], ondelete='CASCADE'),
        )

    # governance: committees and members
    if not _table_exists(conn, 'committees'):
        op.create_table(
            'committees',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('community_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('slug', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('meeting_frequency', sa.String(50), nullable=True),
            sa.Column('notification_email', sa.String(200), nullable=True),
            sa.Column('notification_wechat', sa.String(100), nullable=True),
            sa.Column('established_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('community_id', 'slug', name='uq_committee_community_slug'),
        )

    if not _table_exists(conn, 'committee_members'):
        op.create_table(
            'committee_members',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('committee_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('email', sa.String(200), nullable=True),
            sa.Column('phone', sa.String(50), nullable=True),
            sa.Column('wechat', sa.String(100), nullable=True),
            sa.Column('organization', sa.String(200), nullable=True),
            sa.Column('roles', sa.JSON(), nullable=True),
            sa.Column('term_start', sa.Date(), nullable=True),
            sa.Column('term_end', sa.Date(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('bio', sa.Text(), nullable=True),
            sa.Column('avatar_url', sa.String(500), nullable=True),
            sa.Column('joined_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['committee_id'], ['committees.id'], ondelete='CASCADE'),
        )

    # meetings
    if not _table_exists(conn, 'meetings'):
        op.create_table(
            'meetings',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('committee_id', sa.Integer(), nullable=False),
            sa.Column('community_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(500), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('scheduled_at', sa.DateTime(), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=True, server_default='120'),
            sa.Column('location_type', sa.String(50), nullable=True),
            sa.Column('location', sa.String(500), nullable=True),
            sa.Column('status', sa.String(50), nullable=True),
            sa.Column('agenda', sa.Text(), nullable=True),
            sa.Column('minutes', sa.Text(), nullable=True),
            sa.Column('attachments', sa.JSON(), nullable=True),
            sa.Column('reminder_sent', sa.Boolean(), nullable=False, server_default=sa.text('0')),
            sa.Column('reminder_before_hours', sa.Integer(), nullable=True, server_default='24'),
            sa.Column('created_by_user_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['committee_id'], ['committees.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        )

    if not _table_exists(conn, 'meeting_reminders'):
        op.create_table(
            'meeting_reminders',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('meeting_id', sa.Integer(), nullable=False),
            sa.Column('reminder_type', sa.String(50), nullable=False),
            sa.Column('scheduled_at', sa.DateTime(), nullable=False),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('notification_channels', sa.JSON(), nullable=True),
            sa.Column('status', sa.String(50), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        )
        op.create_index('idx_reminder_scheduled_status', 'meeting_reminders', ['scheduled_at', 'status'])

    # seed default community and admin
    # insert only if not exists
    users = conn.execute(sa.text("SELECT id FROM users WHERE username = :u OR email = :e"), {"u": "admin", "e": "admin@example.com"}).fetchone()
    if not users:
        now = datetime.utcnow()
        # create community first
        res = conn.execute(
            sa.text(
                "INSERT INTO communities (name, slug, description, is_active, created_at, updated_at) VALUES (:n, :s, :d, :a, :c, :u)"
            ),
            {
                "n": "Default Community",
                "s": "default",
                "d": "Auto-created default community",
                "a": 1,
                "c": now,
                "u": now,
            },
        )
        # fetch community id
        community_row = conn.execute(sa.text("SELECT id FROM communities WHERE slug = :s"), {"s": "default"}).fetchone()
        community_id = community_row[0] if community_row else None

        # insert admin user
        hashed = 'changeme'  # placeholder; app should reset this
        conn.execute(
            sa.text(
                "INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser, is_default_admin, created_at) VALUES (:u, :e, :p, :f, :a, :s, :d, :c)"
            ),
            {"u": "admin", "e": "admin@example.com", "p": hashed, "f": "Default Admin", "a": 1, "s": 1, "d": 1, "c": now},
        )

        user_row = conn.execute(sa.text("SELECT id FROM users WHERE username = :u"), {"u": "admin"}).fetchone()
        user_id = user_row[0] if user_row else None

        # link admin to default community
        if community_id and user_id:
            conn.execute(
                sa.text(
                    "INSERT INTO community_users (user_id, community_id, role, joined_at) VALUES (:uid, :cid, :r, :j)"
                ),
                {"uid": user_id, "cid": community_id, "r": "admin", "j": now},
            )


def downgrade():
    conn = op.get_bind()
    # remove seeded admin and community
    try:
        conn.execute(sa.text("DELETE FROM community_users WHERE user_id IN (SELECT id FROM users WHERE username = :u)"), {"u": "admin"})
        conn.execute(sa.text("DELETE FROM users WHERE username = :u"), {"u": "admin"})
        conn.execute(sa.text("DELETE FROM communities WHERE slug = :s"), {"s": "default"})
    except Exception:
        pass

    # drop tables in reverse order if exist
    for t in [
        'meeting_reminders',
        'meetings',
        'committee_members',
        'committees',
        'content_analytics',
        'publish_records',
        'contents',
        'community_users',
        'communities',
        'users',
    ]:
        if _table_exists(conn, t):
            op.drop_table(t)
