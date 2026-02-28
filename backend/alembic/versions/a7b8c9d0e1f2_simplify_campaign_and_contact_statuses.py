"""simplify_campaign_and_contact_statuses

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-02-28 12:00:00.000000

Campaign 状态简化：
  draft    → active
  archived → completed

Contact 状态简化（3 种 → 新 3 种）：
  pending               → pending   (不变)
  contacted_no_response → contacted
  completed             → contacted (已联系过)
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Campaign status migration
    op.execute("UPDATE campaigns SET status = 'active' WHERE status = 'draft'")
    op.execute("UPDATE campaigns SET status = 'completed' WHERE status = 'archived'")

    # Contact status migration
    op.execute(
        "UPDATE campaign_contacts SET status = 'contacted' "
        "WHERE status = 'contacted_no_response'"
    )
    op.execute(
        "UPDATE campaign_contacts SET status = 'contacted' "
        "WHERE status = 'completed'"
    )


def downgrade() -> None:
    # Reverse contact status (best-effort, no way to distinguish)
    op.execute(
        "UPDATE campaign_contacts SET status = 'contacted_no_response' "
        "WHERE status = 'contacted'"
    )
    # Reverse campaign status (keep as active, can't restore archived)
    op.execute("UPDATE campaigns SET status = 'draft' WHERE status = 'active'")
