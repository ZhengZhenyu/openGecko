"""Add RBAC roles and content collaborators

Revision ID: 003
Revises: db476070cb0b
Create Date: 2026-02-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = 'db476070cb0b'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch mode for SQLite compatibility when altering existing tables
    with op.batch_alter_table('contents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_contents_owner_id'), ['owner_id'], unique=False)
        batch_op.create_foreign_key('fk_contents_owner_id', 'users', ['owner_id'], ['id'], ondelete='SET NULL')
    
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
    
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('contents', schema=None) as batch_op:
        batch_op.drop_constraint('fk_contents_owner_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_contents_owner_id'))
        batch_op.drop_column('owner_id')
