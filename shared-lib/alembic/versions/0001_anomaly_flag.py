"""add anomaly flag columns to transactions

Revision ID: 0001_anomaly_flag
Revises:
"""

from alembic import op

revision = "0001_anomaly_flag"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS flagged BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS flag_reason VARCHAR(200)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS flag_reason")
    op.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS flagged")
