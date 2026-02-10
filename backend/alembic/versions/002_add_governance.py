"""Add governance module tables (committees and members)

Revision ID: 002_add_governance
Revises: 001_initial
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_governance'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade():
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


def downgrade():
    op.drop_table('committee_members')
    op.drop_table('committees')
