"""Placeholder: community url and channel refactor (already in 001_initial)

Revision ID: 005
Revises: 004
Create Date: 2026-02-09

The url column in communities and channel_configs changes were already
applied in 001_initial. This is a no-op placeholder.
"""

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass  # url column already exists in 001_initial


def downgrade() -> None:
    pass
