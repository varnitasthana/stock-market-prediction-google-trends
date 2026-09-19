"""add artifact_path to model_runs

Revision ID: a1b2c3d4e5f6
Revises: 9f8e7d6c5b4a
Create Date: 2026-09-19 18:40:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | Sequence[str] | None = '9f8e7d6c5b4a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('model_runs', sa.Column('artifact_path', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('model_runs', 'artifact_path')
