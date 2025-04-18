"""add new protocol enum value

Revision ID: 70dd635d80d4
Revises: 6482e8fa201e
Create Date: 2025-03-08 19:22:45.910952+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70dd635d80d4'
down_revision: Union[str, None] = '6482e8fa201e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create a new temporary enum type with the new value
    op.execute("ALTER TYPE protocol ADD VALUE 'CONNECTOR'")

    # Note: PostgreSQL allows adding values to enum types directly with the command above.
    # If you were using a different database, you might need a more complex migration.


def downgrade() -> None:
    # Unfortunately, PostgreSQL doesn't provide a direct way to remove enum values
    # The only way would be to create a new type without the value and migrate data
    # This is complex and potentially dangerous, so it's often left as a no-op
    pass
