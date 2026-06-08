import logging
import os

from shared.messaging import TRANSACTIONS_TOPIC, consume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("anomaly_worker")

AMOUNT_THRESHOLD = float(os.getenv("ANOMALY_AMOUNT_THRESHOLD", "10000"))


def handle(event: dict) -> None:
    amount = float(event.get("amount") or 0)
    transaction_id = event.get("transaction_id")
    if amount >= AMOUNT_THRESHOLD:
        logger.warning(
            "anomaly: transaction %s amount=%.2f exceeds threshold %.2f",
            transaction_id,
            amount,
            AMOUNT_THRESHOLD,
        )
    else:
        logger.info("transaction %s within range (amount=%.2f)", transaction_id, amount)


def main() -> None:
    consume(TRANSACTIONS_TOPIC, "anomaly", handle)


if __name__ == "__main__":
    main()
