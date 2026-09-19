"""add phase 9 model training columns

Revision ID: 9f8e7d6c5b4a
Revises: 6723a170031f
Create Date: 2026-09-19 16:50:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9f8e7d6c5b4a'
down_revision: str | Sequence[str] | None = '6723a170031f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('model_runs', sa.Column('task_type', sa.String(length=50), nullable=False, server_default='classification'))
    op.add_column('model_runs', sa.Column('target_name', sa.String(length=100), nullable=False, server_default='next_day_direction'))
    op.add_column('model_runs', sa.Column('test_start_date', sa.Date(), nullable=True))
    op.add_column('model_runs', sa.Column('test_end_date', sa.Date(), nullable=True))
    op.add_column('model_runs', sa.Column('parameters', sa.String(), nullable=True))
    op.add_column('model_runs', sa.Column('random_state', sa.Integer(), nullable=True))
    op.add_column('model_runs', sa.Column('feature_count', sa.Integer(), nullable=True))
    op.alter_column('model_runs', 'metrics', existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    op.drop_column('model_runs', 'feature_count')
    op.drop_column('model_runs', 'random_state')
    op.drop_column('model_runs', 'parameters')
    op.drop_column('model_runs', 'test_end_date')
    op.drop_column('model_runs', 'test_start_date')
    op.drop_column('model_runs', 'target_name')
    op.drop_column('model_runs', 'task_type')
