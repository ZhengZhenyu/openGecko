"""Placeholder: governance module tables already created in 002 and 003

Revision ID: 004
Revises: 003_add_meetings
Create Date: 2026-02-09

Tables (committees, committee_members, meetings, meeting_reminders) were
already created in 002_add_governance and 003_add_meetings. This revision
is a no-op placeholder to maintain the migration chain.
"""

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003_add_meetings'
branch_labels = None
depends_on = None


def upgrade():
    pass  # Tables already created in 002_add_governance and 003_add_meetings


def downgrade():
    pass  # Nothing to undo
