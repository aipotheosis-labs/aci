"""add monthly quota and period start fields

Revision ID: 23b947f44d83
Revises: 068b47f44d83
Create Date: 2025-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23b947f44d83'
down_revision: Union[str, None] = '068b47f44d83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add monthly quota fields to projects table
    op.add_column('projects', sa.Column('api_quota_monthly_used', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('projects', sa.Column('api_quota_last_reset', sa.DateTime(), nullable=False, server_default=sa.text('now()')))

    # Add current_period_start to subscriptions table
    op.add_column('subscriptions', sa.Column('current_period_start', sa.DateTime(), nullable=True))

    # Update existing subscriptions to have current_period_start = current_period_end - interval
    # This is a reasonable default for existing subscriptions
    op.execute("""
        UPDATE subscriptions
        SET current_period_start = CASE
            WHEN interval = 'MONTH' THEN current_period_end - INTERVAL '1 month'
            WHEN interval = 'YEAR' THEN current_period_end - INTERVAL '1 year'
            ELSE current_period_end - INTERVAL '1 month'
        END
        WHERE current_period_start IS NULL
    """)

    # Make current_period_start non-nullable after setting defaults
    op.alter_column('subscriptions', 'current_period_start', nullable=False)


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('projects', 'api_quota_last_reset')
    op.drop_column('projects', 'api_quota_monthly_used')
    op.drop_column('subscriptions', 'current_period_start')
