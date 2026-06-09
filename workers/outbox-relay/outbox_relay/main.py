"""Transactional outbox relay.

Polls the ``outbox`` table for unsent rows and publishes them to Kafka, then
marks them sent. Because business rows and outbox rows are written in the same
DB transaction, an event is durable the moment the transfer commits — this
relay just delivers it (at-least-once; consumers are idempotent).
"""

import json
import logging
import os
import time

from sqlalchemy import inspect

from shared.messaging import get_producer
from shared.models import OutboxEvent, SessionLocal, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbox_relay")

BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "100"))
POLL_INTERVAL = float(os.getenv("OUTBOX_POLL_INTERVAL", "1.0"))


def _wait_for_table(timeout: float = 60.0) -> None:
    """Block until the outbox table exists (a service applies the migration).

    Avoids noisy UndefinedTable errors when the relay wins the startup race
    against the service that runs migrations.
    """
    deadline = time.time() + timeout
    while True:
        try:
            if inspect(engine).has_table(OutboxEvent.__tablename__):
                return
        except Exception:
            pass  # DB not reachable yet
        if time.time() >= deadline:
            logger.warning("outbox table still missing after %.0fs; starting anyway", timeout)
            return
        logger.info("waiting for outbox table…")
        time.sleep(2.0)


def _relay_once(producer) -> int:
    """Publish one batch of unsent outbox rows. Returns count delivered."""
    db = SessionLocal()
    try:
        rows = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.sent.is_(False))
            .order_by(OutboxEvent.id)
            .limit(BATCH_SIZE)
            .all()
        )
        if not rows:
            return 0

        for row in rows:
            producer.produce(
                row.topic,
                key=(row.key.encode("utf-8") if row.key else None),
                value=row.payload.encode("utf-8"),
            )
        producer.flush()  # one flush per batch, not per message

        from datetime import datetime

        for row in rows:
            row.sent = True
            row.sent_at = datetime.utcnow()
        db.commit()
        logger.info("relayed %d outbox event(s)", len(rows))
        return len(rows)
    except Exception:
        db.rollback()
        logger.exception("outbox relay batch failed")
        return 0
    finally:
        db.close()


def main() -> None:
    _wait_for_table()
    producer = get_producer()
    logger.info("outbox relay started (batch=%d, interval=%.1fs)", BATCH_SIZE, POLL_INTERVAL)
    while True:
        delivered = _relay_once(producer)
        # Only sleep when idle; drain backlog fast when there's work.
        if delivered == 0:
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
