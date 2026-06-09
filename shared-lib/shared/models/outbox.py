from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from . import Base


class OutboxEvent(Base):
    """Transactional outbox row.

    Written in the same DB transaction as the business change, then relayed to
    Kafka by a separate process. Guarantees DB-write and event-publish are
    atomic (no dual-write loss) without distributed transactions.
    """

    __tablename__ = "outbox"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(200), nullable=False)
    key = Column(String(200), nullable=True)
    payload = Column(Text, nullable=False)  # JSON-encoded event body
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent = Column(Boolean, nullable=False, default=False)
    sent_at = Column(DateTime, nullable=True)
