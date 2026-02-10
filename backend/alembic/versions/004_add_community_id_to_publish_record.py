"""add community_id to publish_record

Revision ID: 004_add_community_id
Revises: 003_add_rbac_and_collaborators
Create Date: 2026-02-09

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = 'db476070cb0b'
branch_labels = None
depends_on = None


def upgrade():
    """Add community_id column to publish_records table."""
    # Add community_id column (nullable first for data migration)
    op.add_column(
        'publish_records',
        sa.Column('community_id', sa.Integer(), nullable=True)
    )

    # Migrate existing data: get community_id from related content
    op.execute("""
        UPDATE publish_records
        SET community_id = (
            SELECT community_id
            FROM contents
            WHERE contents.id = publish_records.content_id
        )
        WHERE community_id IS NULL
    """)

    # Now make it NOT NULL
    op.alter_column('publish_records', 'community_id', nullable=False)

    # Note: SQLite doesn't support adding foreign keys via ALTER TABLE
    # Foreign key will be enforced at application level

    # Create index for performance
    op.create_index(
        'ix_publish_records_community_id',
        'publish_records',
        ['community_id']
    )


def downgrade():
    """Remove community_id column from publish_records table."""
    # Drop index
    op.drop_index('ix_publish_records_community_id', table_name='publish_records')

    # Drop column
    op.drop_column('publish_records', 'community_id')
