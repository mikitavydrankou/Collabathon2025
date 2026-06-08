from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from shared.models import Transaction, User
from .schemas import (
    CreateTransactionRequest,
    TransactionFilter,
    TransactionStats,
)


class TransactionService:
    """Service for handling transaction operations"""

    @staticmethod
    def create_transaction(
        db: Session,
        sender_id: int,
        receiver_bank_number: str,
        receiver_name: str,
        receiver_surname: str,
        amount: Decimal,
        transaction_text: Optional[str] = None,
    ) -> tuple[bool, str, Optional[Transaction]]:
        """
        Create a new transaction between users

        Returns:
            tuple: (success: bool, message: str, transaction: Optional[Transaction])
        """
        try:
            # Find sender
            sender = db.query(User).filter(User.user_id == sender_id).first()
            if not sender:
                return False, "Sender not found", None

            # Find receiver by bank number
            receiver = (
                db.query(User).filter(User.bank_number == receiver_bank_number).first()
            )
            if not receiver:
                return False, "Receiver bank account not found", None

            # Verify receiver name matches
            if (
                receiver.name.lower() != receiver_name.lower()
                or receiver.surname.lower() != receiver_surname.lower()
            ):
                return (
                    False,
                    f"Receiver name mismatch. Expected: {receiver.name} {receiver.surname}",
                    None,
                )

            # Check if sender has sufficient balance
            if sender.balance < amount:
                return (
                    False,
                    f"Insufficient funds. Available: {sender.balance} PLN, Required: {amount} PLN",
                    None,
                )

            # Calculate balances
            amount_before = sender.balance
            amount_after = amount_before - amount

            # Create transaction
            transaction = Transaction(
                sender_id=sender.user_id,
                receiver_id=receiver.user_id,
                receiver_name=receiver.name,
                receiver_surname=receiver.surname,
                amount=amount,
                transaction_date_and_time=datetime.now(),
                amount_before=amount_before,
                amount_after=amount_after,
                transaction_type="transfer",
                transaction_posted=True,
                transaction_text=transaction_text
                or f"Transfer to {receiver.name} {receiver.surname}",
            )

            # Update sender balance
            sender.balance = amount_after

            # Update receiver balance
            receiver.balance += amount

            # Save to database
            db.add(transaction)
            db.commit()
            db.refresh(transaction)

            return True, "Transaction completed successfully", transaction

        except Exception as e:
            db.rollback()
            return False, f"Transaction failed: {str(e)}", None

    @staticmethod
    def get_user_transactions(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        filters: Optional[TransactionFilter] = None,
    ) -> list[dict]:
        """
        Get all transactions for a user (both sent and received)

        Returns:
            List of transaction dictionaries with additional computed fields
        """
        query = db.query(Transaction).filter(
            or_(Transaction.sender_id == user_id, Transaction.receiver_id == user_id)
        )

        # Apply filters if provided
        if filters:
            if filters.start_date:
                query = query.filter(
                    Transaction.transaction_date_and_time >= filters.start_date
                )
            if filters.end_date:
                query = query.filter(
                    Transaction.transaction_date_and_time <= filters.end_date
                )
            if filters.min_amount:
                query = query.filter(Transaction.amount >= filters.min_amount)
            if filters.max_amount:
                query = query.filter(Transaction.amount <= filters.max_amount)
            if filters.transaction_type:
                query = query.filter(
                    Transaction.transaction_type == filters.transaction_type
                )
            if filters.posted_only is not None:
                query = query.filter(
                    Transaction.transaction_posted == filters.posted_only
                )

        # Order by date descending
        query = query.order_by(desc(Transaction.transaction_date_and_time))

        # Apply pagination
        total_count = query.count()
        results = query.limit(limit).offset(offset).all()

        # Format results
        transactions = []
        for transaction in results:
            # Determine if this is a sent or received transaction
            is_sent = transaction.sender_id == user_id

            # Get the appropriate user details and bank number
            if is_sent:
                # For sent transactions, show receiver info
                receiver = (
                    db.query(User)
                    .filter(User.user_id == transaction.receiver_id)
                    .first()
                )
                account_number = receiver.bank_number if receiver else "Unknown"
                display_name = transaction.receiver_name
                display_surname = transaction.receiver_surname
            else:
                # For received transactions, show sender info
                sender = (
                    db.query(User).filter(User.user_id == transaction.sender_id).first()
                )
                account_number = sender.bank_number if sender else "Unknown"
                display_name = sender.name if sender else "Unknown"
                display_surname = sender.surname if sender else ""

            transaction_dict = {
                "transaction_id": transaction.transaction_id,
                "receiver_name": display_name,
                "receiver_surname": display_surname,
                "receiver_bank_account": account_number,
                "amount": float(transaction.amount),
                "transaction_date": transaction.transaction_date_and_time.isoformat(),
                "transaction_type": transaction.transaction_type,
                "transaction_text": transaction.transaction_text,
                "amount_before": float(transaction.amount_before),
                "amount_after": float(transaction.amount_after),
                "is_sent": is_sent,
                "transaction_posted": transaction.transaction_posted,
            }
            transactions.append(transaction_dict)

        return transactions

    @staticmethod
    def get_transaction_by_id(
        db: Session, transaction_id: int, user_id: int
    ) -> Optional[dict]:
        """
        Get a specific transaction by ID
        Only returns if user is sender or receiver
        """
        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id == transaction_id,
                or_(
                    Transaction.sender_id == user_id,
                    Transaction.receiver_id == user_id,
                ),
            )
            .first()
        )

        if not transaction:
            return None

        # Get sender and receiver details
        sender = db.query(User).filter(User.user_id == transaction.sender_id).first()
        receiver = (
            db.query(User).filter(User.user_id == transaction.receiver_id).first()
        )

        if not sender or not receiver:
            return None

        is_sent = transaction.sender_id == user_id

        return {
            "transaction_id": transaction.transaction_id,
            "sender_id": transaction.sender_id,
            "sender_name": sender.name,
            "sender_surname": sender.surname,
            "sender_bank_account": sender.bank_number,
            "receiver_id": transaction.receiver_id,
            "receiver_name": transaction.receiver_name,
            "receiver_surname": transaction.receiver_surname,
            "receiver_bank_account": receiver.bank_number,
            "amount": float(transaction.amount),
            "transaction_date": transaction.transaction_date_and_time.isoformat(),
            "transaction_type": transaction.transaction_type,
            "transaction_text": transaction.transaction_text,
            "amount_before": float(transaction.amount_before),
            "amount_after": float(transaction.amount_after),
            "is_sent": is_sent,
            "transaction_posted": transaction.transaction_posted,
        }

    @staticmethod
    def get_transaction_stats(db: Session, user_id: int) -> TransactionStats:
        """Get transaction statistics for a user"""
        sent_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.sender_id == user_id, Transaction.transaction_posted == True
            )
            .all()
        )

        received_transactions = (
            db.query(Transaction)
            .filter(
                Transaction.receiver_id == user_id,
                Transaction.transaction_posted == True,
            )
            .all()
        )

        pending_count = (
            db.query(Transaction)
            .filter(
                Transaction.sender_id == user_id,
                Transaction.transaction_posted == False,
            )
            .count()
        )

        total_sent = sum(t.amount for t in sent_transactions)
        total_received = sum(t.amount for t in received_transactions)

        return TransactionStats(
            total_sent=total_sent,
            total_received=total_received,
            total_transactions=len(sent_transactions) + len(received_transactions),
            sent_count=len(sent_transactions),
            received_count=len(received_transactions),
            pending_count=pending_count,
        )

    @staticmethod
    def cancel_transaction(
        db: Session, transaction_id: int, user_id: int
    ) -> tuple[bool, str]:
        """
        Cancel a pending transaction
        Only sender can cancel and only if not posted
        """
        transaction = (
            db.query(Transaction)
            .filter(
                Transaction.transaction_id == transaction_id,
                Transaction.sender_id == user_id,
            )
            .first()
        )

        if not transaction:
            return False, "Transaction not found or you don't have permission"

        if transaction.transaction_posted:
            return False, "Cannot cancel a posted transaction"

        try:
            # Restore sender's balance
            sender = (
                db.query(User).filter(User.user_id == transaction.sender_id).first()
            )
            if sender:
                sender.balance = transaction.amount_before

            db.delete(transaction)
            db.commit()
            return True, "Transaction cancelled successfully"
        except Exception as e:
            db.rollback()
            return False, f"Failed to cancel transaction: {str(e)}"

    @staticmethod
    def get_recent_receivers(db: Session, user_id: int, limit: int = 10) -> list[dict]:
        """Get recent transaction receivers for quick transfers"""
        transactions = (
            db.query(Transaction)
            .filter(Transaction.sender_id == user_id)
            .order_by(desc(Transaction.transaction_date_and_time))
            .limit(limit * 2)  # Get more to deduplicate
            .all()
        )

        # Deduplicate by receiver
        seen_receivers = set()
        recent_receivers = []

        for t in transactions:
            receiver_key = (t.receiver_id, t.receiver_name, t.receiver_surname)
            if receiver_key not in seen_receivers:
                receiver = db.query(User).filter(User.user_id == t.receiver_id).first()
                if receiver:
                    recent_receivers.append(
                        {
                            "receiver_id": t.receiver_id,
                            "receiver_name": t.receiver_name,
                            "receiver_surname": t.receiver_surname,
                            "receiver_bank_account": receiver.bank_number,
                            "last_transaction_date": t.transaction_date_and_time.isoformat(),
                            "last_amount": float(t.amount),
                        }
                    )
                    seen_receivers.add(receiver_key)

            if len(recent_receivers) >= limit:
                break

        return recent_receivers

    @staticmethod
    def verify_receiver(
        db: Session, bank_number: str, name: str, surname: str
    ) -> tuple[bool, Optional[str]]:
        """
        Verify if receiver details match the bank account

        Returns:
            tuple: (is_valid: bool, message: Optional[str])
        """
        receiver = db.query(User).filter(User.bank_number == bank_number).first()

        if not receiver:
            return False, "Bank account not found"

        if (
            receiver.name.lower() == name.lower()
            and receiver.surname.lower() == surname.lower()
        ):
            return True, None

        return (
            False,
            f"Name mismatch. Account holder: {receiver.name} {receiver.surname}",
        )
