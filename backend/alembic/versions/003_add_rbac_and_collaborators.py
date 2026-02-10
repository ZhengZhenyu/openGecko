"""Add RBAC roles and content collaborators

Revision ID: 003
Revises: 002
Create Date: 2026-02-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '993d1f15fe95'
branch_labels = None
depends_on = None


def upgrade():
    # Add owner_id column to contents table
    op.add_column('contents', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_contents_owner_id'), 'contents', ['owner_id'], unique=False)
    # Note: SQLite doesn't support adding foreign keys via ALTER TABLE
    # Foreign key will be enforced at application level

    # Create content_collaborators table
    op.create_table('content_collaborators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('added_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['content_id'], ['contents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Update existing contents to set owner_id = created_by_user_id
    op.execute("UPDATE contents SET owner_id = created_by_user_id WHERE created_by_user_id IS NOT NULL")


def downgrade():
    # Drop content_collaborators table
    op.drop_table('content_collaborators')

    # Remove owner_id column from contents table
    op.drop_index(op.f('ix_contents_owner_id'), table_name='contents')
    op.drop_column('contents', 'owner_id')
