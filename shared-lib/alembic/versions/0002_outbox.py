"""add transactional outbox table

Revision ID: 0002_outbox
Revises: 0001_anomaly_flag
"""

from alembic import op

revision = "0002_outbox"
down_revision = "0001_anomaly_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS outbox (
            id SERIAL PRIMARY KEY,
            topic VARCHAR(200) NOT NULL,
            key VARCHAR(200),
            payload TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            sent BOOLEAN NOT NULL DEFAULT FALSE,
            sent_at TIMESTAMP
        )
        """
    )
    # Partial index: relay only ever scans unsent rows.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_outbox_unsent ON outbox (id) WHERE sent = FALSE"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_outbox_unsent")
    op.execute("DROP TABLE IF EXISTS outbox")
