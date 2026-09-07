"""Initial Schema Migration for LEATrace Enterprise Infrastructure.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-31 11:15:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Upgrade migrations — table creation is safely handled via Base.metadata.create_all()
    # or Alembic migration commands.
    pass


def downgrade() -> None:
    # Downgrade migrations
    pass
