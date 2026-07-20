"""add_hashed_phone

Revision ID: ddc6eb0a7db0
Revises: d0bacb935bd4
Create Date: 2026-07-08 11:20:50.065412

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddc6eb0a7db0'
down_revision: Union[str, None] = 'd0bacb935bd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
