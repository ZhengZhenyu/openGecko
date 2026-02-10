"""Add meetings and meeting_reminders tables

Revision ID: 003_add_meetings
Revises: 002_add_governance
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_meetings'
down_revision = '002_add_governance'
branch_labels = None
depends_on = None


def upgrade():
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

    # optional composite index for reminders
    op.create_index('idx_reminder_scheduled_status', 'meeting_reminders', ['scheduled_at', 'status'])


def downgrade():
    op.drop_index('idx_reminder_scheduled_status', table_name='meeting_reminders')
    op.drop_table('meeting_reminders')
    op.drop_table('meetings')
