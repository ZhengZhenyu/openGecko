"""add insights fields to contributors and ecosystem snapshots table

Revision ID: be19f0609e7e
Revises: ddd8a0970367
Create Date: 2026-03-01 17:26:18.492361

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'be19f0609e7e'
down_revision: Union[str, None] = 'ddd8a0970367'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ecosystem_snapshots（如果已被 create_all 自动建出则跳过）---
    bind = op.get_bind()
    inspector = inspect(bind)
    if 'ecosystem_snapshots' not in inspector.get_table_names():
        op.create_table(
            'ecosystem_snapshots',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('project_id', sa.Integer(), nullable=False),
            sa.Column('snapshot_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('stars', sa.Integer(), nullable=True),
            sa.Column('forks', sa.Integer(), nullable=True),
            sa.Column('open_issues', sa.Integer(), nullable=True),
            sa.Column('open_prs', sa.Integer(), nullable=True),
            sa.Column('commits_30d', sa.Integer(), nullable=True),
            sa.Column('pr_merged_30d', sa.Integer(), nullable=True),
            sa.Column('active_contributors_30d', sa.Integer(), nullable=True),
            sa.Column('new_contributors_30d', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['project_id'], ['ecosystem_projects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        with op.batch_alter_table('ecosystem_snapshots', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_ecosystem_snapshots_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_ecosystem_snapshots_project_id'), ['project_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_ecosystem_snapshots_snapshot_at'), ['snapshot_at'], unique=False)

    # --- ecosystem_contributors 新增 4 个情报分析列 ---
    with op.batch_alter_table('ecosystem_contributors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('review_count_90d', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('company', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('first_contributed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('ecosystem_contributors', schema=None) as batch_op:
        batch_op.drop_column('first_contributed_at')
        batch_op.drop_column('location')
        batch_op.drop_column('company')
        batch_op.drop_column('review_count_90d')

    bind = op.get_bind()
    inspector = inspect(bind)
    if 'ecosystem_snapshots' in inspector.get_table_names():
        with op.batch_alter_table('ecosystem_snapshots', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_ecosystem_snapshots_snapshot_at'))
            batch_op.drop_index(batch_op.f('ix_ecosystem_snapshots_project_id'))
            batch_op.drop_index(batch_op.f('ix_ecosystem_snapshots_id'))
        op.drop_table('ecosystem_snapshots')
