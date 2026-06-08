"""Kafka producer and consumer helpers shared by producers and workers."""

import json
import logging
import os
from typing import Callable

from confluent_kafka import Consumer, Producer

logger = logging.getLogger(__name__)

TRANSACTIONS_TOPIC = "transactions.created"


def _brokers() -> str:
    return os.getenv("KAFKA_BROKERS", "kafka:9092")


def get_producer() -> Producer:
    return Producer({"bootstrap.servers": _brokers()})


def publish(producer: Producer, topic: str, key: str, value: dict) -> None:
    producer.produce(topic, key=key, value=json.dumps(value).encode("utf-8"))
    producer.flush()


def consume(topic: str, group_id: str, handler: Callable[[dict], None]) -> None:
    """Run a blocking consume loop, dispatching each decoded message to handler."""
    consumer = Consumer(
        {
            "bootstrap.servers": _brokers(),
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([topic])
    logger.info("consuming topic=%s group=%s", topic, group_id)
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                logger.error("consume error: %s", msg.error())
                continue
            try:
                handler(json.loads(msg.value()))
                consumer.commit(msg)
            except Exception:
                logger.exception("handler failed; message not committed")
    finally:
        consumer.close()
