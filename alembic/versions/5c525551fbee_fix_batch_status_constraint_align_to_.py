"""fix_batch_status_constraint_align_to_service_values

Revision ID: 5c525551fbee
Revises: 41ceddbc66f3
Create Date: 2026-04-06

Fixes the chk_batch_status CheckConstraint to match the actual values written
by dispatch_service.py: 'pending', 'dispatched', 'cancelled'.

The previous constraint incorrectly listed 'draft', 'consolidated', 'confirmed',
'shipped' — none of which are ever written by the service layer.
No data migration required: existing rows should only contain 'pending',
'dispatched', or 'cancelled'.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c525551fbee'
down_revision: Union[str, Sequence[str], None] = '41ceddbc66f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace the misaligned batch status constraint with the correct values."""
    with op.batch_alter_table('dispatch_batch', schema=None) as batch_op:
        # Drop the incorrect constraint from the previous migration
        batch_op.drop_constraint('chk_batch_status', type_='check')
        # Add the correct constraint matching BatchStatus constants
        batch_op.create_check_constraint(
            'chk_batch_status',
            "status IN ('pending', 'dispatched', 'cancelled')"
        )


def downgrade() -> None:
    """Restore the prior (misaligned) constraint."""
    with op.batch_alter_table('dispatch_batch', schema=None) as batch_op:
        batch_op.drop_constraint('chk_batch_status', type_='check')
        batch_op.create_check_constraint(
            'chk_batch_status',
            "status IN ('draft', 'consolidated', 'confirmed', 'shipped', 'cancelled')"
        )
