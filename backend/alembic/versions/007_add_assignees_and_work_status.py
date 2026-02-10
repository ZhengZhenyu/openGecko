"""add assignees and work status

Revision ID: 007_add_assignees
Revises: 006_add_member_contact_fields
Create Date: 2026-02-10 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '007_add_assignees'
down_revision = '006_add_member_contact_fields'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 为 contents 表添加 work_status 字段（工作状态）
    # 保留原有的 status 字段用于发布流程
    with op.batch_alter_table('contents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('work_status', sa.String(50), nullable=True, server_default='planning'))
        batch_op.create_index('ix_contents_work_status', ['work_status'])
    
    # 默认将所有现有内容的 work_status 设置为 'planning'
    op.execute("UPDATE contents SET work_status = 'planning' WHERE work_status IS NULL")
    
    # 2. 创建内容责任人关联表
    op.create_table(
        'content_assignees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('assigned_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_content_assignees_content_id', 'content_assignees', ['content_id'])
    op.create_index('ix_content_assignees_user_id', 'content_assignees', ['user_id'])
    
    # 为所有现有内容添加创建者作为默认责任人
    op.execute("""
        INSERT INTO content_assignees (content_id, user_id, assigned_by_user_id)
        SELECT id, created_by_user_id, created_by_user_id
        FROM contents
        WHERE created_by_user_id IS NOT NULL
    """)
    
    # 3. 创建会议责任人关联表
    op.create_table(
        'meeting_assignees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('meeting_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('assigned_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['meeting_id'], ['meetings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_meeting_assignees_meeting_id', 'meeting_assignees', ['meeting_id'])
    op.create_index('ix_meeting_assignees_user_id', 'meeting_assignees', ['user_id'])
    
    # 为所有现有会议添加创建者作为默认责任人
    op.execute("""
        INSERT INTO meeting_assignees (meeting_id, user_id, assigned_by_user_id)
        SELECT id, created_by_user_id, created_by_user_id
        FROM meetings
        WHERE created_by_user_id IS NOT NULL
    """)
    
    # 4. 为 meetings 表添加 work_status 字段
    with op.batch_alter_table('meetings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('work_status', sa.String(50), nullable=True, server_default='planning'))
        batch_op.create_index('ix_meetings_work_status', ['work_status'])
    
    # 根据现有的 status 字段设置 work_status
    op.execute("""
        UPDATE meetings 
        SET work_status = CASE 
            WHEN status = 'scheduled' THEN 'planning'
            WHEN status = 'in_progress' THEN 'in_progress'
            WHEN status = 'completed' THEN 'completed'
            WHEN status = 'cancelled' THEN 'completed'
            ELSE 'planning'
        END
    """)


def downgrade():
    # 删除会议相关
    with op.batch_alter_table('meetings', schema=None) as batch_op:
        batch_op.drop_index('ix_meetings_work_status')
        batch_op.drop_column('work_status')
    
    op.drop_index('ix_meeting_assignees_user_id', 'meeting_assignees')
    op.drop_index('ix_meeting_assignees_meeting_id', 'meeting_assignees')
    op.drop_table('meeting_assignees')
    
    # 删除内容相关
    op.drop_index('ix_content_assignees_user_id', 'content_assignees')
    op.drop_index('ix_content_assignees_content_id', 'content_assignees')
    op.drop_table('content_assignees')
    
    with op.batch_alter_table('contents', schema=None) as batch_op:
        batch_op.drop_index('ix_contents_work_status')
        batch_op.drop_column('work_status')
