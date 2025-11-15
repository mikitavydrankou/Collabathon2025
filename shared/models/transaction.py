from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from . import Base


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    receiver_name = Column(String(100), nullable=False)
    receiver_surname = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_date_and_time = Column(DateTime, nullable=False)
    amount_before = Column(Numeric(15, 2), nullable=False)
    amount_after = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False)
    transaction_posted = Column(Boolean, nullable=False, default=False)
    transaction_text = Column(String(500), nullable=True)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_transactions")
    receiver = relationship(
        "User", foreign_keys=[receiver_id], backref="received_transactions"
    )

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, sender={self.sender_id}, receiver={self.receiver_id}, amount={self.amount})>"
