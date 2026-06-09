import logging
import os

from shared.messaging import TRANSACTIONS_TOPIC, consume
from shared.models import SessionLocal, Transaction
from shared.tracing import init_tracing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomaly_worker")

AMOUNT_THRESHOLD = float(os.getenv("ANOMALY_AMOUNT_THRESHOLD", "10000"))


def _flag_transaction(transaction_id: int, reason: str) -> None:
    db = SessionLocal()
    try:
        tx = (
            db.query(Transaction)
            .filter(Transaction.transaction_id == transaction_id)
            .first()
        )
        if tx is not None:
            tx.flagged = True
            tx.flag_reason = reason
            db.commit()
    finally:
        db.close()


def handle(event: dict) -> None:
    amount = float(event.get("amount") or 0)
    transaction_id = event.get("transaction_id")
    if amount >= AMOUNT_THRESHOLD:
        reason = f"Amount {amount:.2f} exceeds threshold {AMOUNT_THRESHOLD:.2f}"
        _flag_transaction(transaction_id, reason)
        logger.warning("flagged transaction %s: %s", transaction_id, reason)
    else:
        logger.info("transaction %s within range (amount=%.2f)", transaction_id, amount)


def main() -> None:
    init_tracing("anomaly-worker")
    consume(TRANSACTIONS_TOPIC, "anomaly", handle)


if __name__ == "__main__":
    main()
