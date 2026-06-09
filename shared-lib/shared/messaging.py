"""Kafka producer and consumer helpers shared by producers and workers."""

import json
import logging
import os
import time
from typing import Callable

from confluent_kafka import Consumer, Producer

logger = logging.getLogger(__name__)

TRANSACTIONS_TOPIC = "transactions.created"

# How many times a handler is retried before the message is parked in the DLQ.
HANDLER_MAX_ATTEMPTS = int(os.getenv("CONSUMER_MAX_ATTEMPTS", "3"))


def _brokers() -> str:
    return os.getenv("KAFKA_BROKERS", "kafka:9092")


def get_producer() -> Producer:
    return Producer({"bootstrap.servers": _brokers()})


def publish(producer: Producer, topic: str, key: str, value: dict) -> None:
    producer.produce(topic, key=key, value=json.dumps(value).encode("utf-8"))
    producer.flush()


def _send_to_dlq(producer: Producer, dlq_topic: str, raw_value: bytes, error: str) -> None:
    """Park a poison message in the dead-letter topic with failure context."""
    envelope = {
        "error": error,
        "failed_at": time.time(),
        "original": raw_value.decode("utf-8", errors="replace"),
    }
    producer.produce(dlq_topic, value=json.dumps(envelope).encode("utf-8"))
    producer.flush()


def consume(topic: str, group_id: str, handler: Callable[[dict], None]) -> None:
    """Blocking consume loop with bounded retries and a dead-letter queue.

    A handler that keeps failing on the same message would otherwise block the
    partition forever (offset never commits → same message redelivered). Here we
    retry up to ``HANDLER_MAX_ATTEMPTS`` times, then route the message to
    ``<topic>.dlq`` and commit so the stream keeps moving.
    """
    consumer = Consumer(
        {
            "bootstrap.servers": _brokers(),
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    dlq_topic = f"{topic}.dlq"
    dlq_producer = get_producer()
    consumer.subscribe([topic])
    logger.info("consuming topic=%s group=%s (dlq=%s)", topic, group_id, dlq_topic)
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("consume error: %s", msg.error())
                continue

            last_error = None
            for attempt in range(1, HANDLER_MAX_ATTEMPTS + 1):
                try:
                    handler(json.loads(msg.value()))
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "handler failed (attempt %d/%d) topic=%s: %s",
                        attempt,
                        HANDLER_MAX_ATTEMPTS,
                        topic,
                        exc,
                    )
                    time.sleep(min(2 ** (attempt - 1), 5))  # backoff: 1s, 2s, 4s…

            if last_error is not None:
                logger.error("routing message to DLQ %s after %d attempts", dlq_topic, HANDLER_MAX_ATTEMPTS)
                try:
                    _send_to_dlq(dlq_producer, dlq_topic, msg.value(), repr(last_error))
                except Exception:
                    logger.exception("failed to write to DLQ; leaving message uncommitted")
                    continue  # don't commit — retry on next poll rather than lose it

            consumer.commit(msg)
    finally:
        consumer.close()
