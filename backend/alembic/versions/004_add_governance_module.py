"""Add governance module tables: committees, committee_members, meetings, meeting_reminders

Revision ID: 004
Revises: 003
Create Date: 2026-02-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # 创建委员会表
    op.create_table(
        'committees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), server_default=''),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('meeting_frequency', sa.String(50), nullable=True),
        sa.Column('notification_email', sa.String(200), nullable=True),
        sa.Column('notification_wechat', sa.String(100), nullable=True),
        sa.Column('established_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('community_id', 'slug', name='uq_committee_community_slug'),
    )
    op.create_index(op.f('ix_committees_id'), 'committees', ['id'], unique=False)
    op.create_index(op.f('ix_committees_community_id'), 'committees', ['community_id'], unique=False)

    # 创建委员会成员表
    op.create_table(
        'committee_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('committee_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('wechat', sa.String(100), nullable=True),
        sa.Column('organization', sa.String(200), nullable=True),
        sa.Column('roles', sa.JSON(), nullable=True),
        sa.Column('term_start', sa.Date(), nullable=True),
        sa.Column('term_end', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1'),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['committee_id'], ['committees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_committee_members_id'), 'committee_members', ['id'], unique=False)
    op.create_index(op.f('ix_committee_members_committee_id'), 'committee_members', ['committee_id'], unique=False)
    op.create_index(op.f('ix_committee_members_email'), 'committee_members', ['email'], unique=False)

    # 创建会议表
    op.create_table(
        'meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('committee_id', sa.Integer(), nullable=False),
        sa.Column('community_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('duration', sa.Integer(), server_default='120'),
        sa.Column('location_type', sa.String(50), nullable=True),
        sa.Column('location', sa.String(500), nullable=True),
        sa.Column('status', sa.String(50), server_default='scheduled'),
        sa.Column('agenda', sa.Text(), nullable=True),
        sa.Column('minutes', sa.Text(), nullable=True),
        sa.Column('attachments', sa.JSON(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), server_default='0'),
        sa.Column('reminder_before_hours', sa.Integer(), server_default='24'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['committee_id'], ['committees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_meetings_id'), 'meetings', ['id'], unique=False)
    op.create_index(op.f('ix_meetings_committee_id'), 'meetings', ['committee_id'], unique=False)
    op.create_index(op.f('ix_meetings_community_id'), 'meetings', ['community_id'], unique=False)
    op.create_index(op.f('ix_meetings_scheduled_at'), 'meetings', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_meetings_status'), 'meetings', ['status'], unique=False)

    # 创建会议提醒记录表
    op.create_table(
        'meeting_reminders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('reminder_type', sa.String(50), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('notification_channels', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_meeting_reminders_id'), 'meeting_reminders', ['id'], unique=False)
    op.create_index(op.f('ix_meeting_reminders_meeting_id'), 'meeting_reminders', ['meeting_id'], unique=False)
    op.create_index('idx_reminder_scheduled_status', 'meeting_reminders', ['scheduled_at', 'status'], unique=False)


def downgrade():
    op.drop_table('meeting_reminders')
    op.drop_table('meetings')
    op.drop_table('committee_members')
    op.drop_table('committees')
