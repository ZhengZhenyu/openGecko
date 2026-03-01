"""update_campaign_contact_status_values

Revision ID: f1a2b3c4d5e6
Revises: 4c2c0cc4b1a5
Create Date: 2026-02-28 10:00:00.000000

将联系人状态从 5 种迁移到 3 种（向后兼容）：
  pending           → pending          (未变)
  contacted         → contacted_no_response
  responded         → contacted_no_response
  converted         → completed
  declined          → completed
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "4c2c0cc4b1a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE campaign_contacts
        SET status = CASE
            WHEN status = 'contacted' THEN 'contacted_no_response'
            WHEN status = 'responded' THEN 'contacted_no_response'
            WHEN status = 'converted' THEN 'completed'
            WHEN status = 'declined'  THEN 'completed'
            ELSE status
        END
    """)


def downgrade() -> None:
    """回滚（不完全可逆，将新值映射回最相近的旧值）"""
    op.execute("""
        UPDATE campaign_contacts
        SET status = CASE
            WHEN status = 'contacted_no_response' THEN 'contacted'
            WHEN status = 'completed'             THEN 'converted'
            ELSE status
        END
    """)
