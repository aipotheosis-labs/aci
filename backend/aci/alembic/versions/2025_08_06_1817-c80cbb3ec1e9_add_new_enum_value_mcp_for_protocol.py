"""add new enum value MCP for protocol

Revision ID: c80cbb3ec1e9
Revises: 0d328a61b91f
Create Date: 2025-08-06 18:17:49.583763+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c80cbb3ec1e9'
down_revision: Union[str, None] = '0d328a61b91f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE protocol ADD VALUE 'MCP'")


def downgrade() -> None:
    pass
