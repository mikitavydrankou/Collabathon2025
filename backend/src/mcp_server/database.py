"""
Database connection and query utilities for MCP server.

Reuses the existing database configuration from the backend.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import and_, create_engine, or_
from sqlalchemy.orm import Session, sessionmaker

from backend.models import Transaction, User

load_dotenv()

# Database connection configuration (reuses existing env vars)
DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5433')}/{os.getenv('DATABASE_NAME')}"

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)


def get_db() -> Session:
    """Create a new database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def get_user_balance(db: Session, user_id: int) -> Optional[Decimal]:
    """Get the current balance for a user."""
    user = db.query(User).filter(User.user_id == user_id).first()
    return user.balance if user else None


def get_recent_transactions(
    db: Session, user_id: int, limit: int = 10
) -> List[Transaction]:
    """
    Get the most recent transactions for a user.

    Args:
        db: Database session
        user_id: ID of the user
        limit: Maximum number of transactions to return

    Returns:
        List of transactions, most recent first
    """
    return (
        db.query(Transaction)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .order_by(Transaction.transaction_date_and_time.desc())
        .limit(limit)
        .all()
    )


def get_time_based_transactions(
    db: Session, user_id: int
) -> List[Tuple[Transaction, str]]:
    """
    Get transactions from specific time periods (1 year, 1 month, 1 week ago).

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        List of tuples (transaction, time_label)
    """
    now = datetime.now()
    one_year_ago = now - timedelta(days=365)
    one_month_ago = now - timedelta(days=30)
    one_week_ago = now - timedelta(days=7)

    results: List[Tuple[Transaction, str]] = []

    # Get transaction from ~1 year ago (within 7 days of the date)
    year_transaction = (
        db.query(Transaction)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .filter(Transaction.transaction_date_and_time >= one_year_ago - timedelta(days=7))
        .filter(Transaction.transaction_date_and_time <= one_year_ago + timedelta(days=7))
        .order_by(Transaction.transaction_date_and_time.desc())
        .first()
    )
    if year_transaction:
        results.append((year_transaction, "about a year ago"))

    # Get transaction from ~1 month ago (within 3 days)
    month_transaction = (
        db.query(Transaction)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .filter(
            Transaction.transaction_date_and_time >= one_month_ago - timedelta(days=3)
        )
        .filter(
            Transaction.transaction_date_and_time <= one_month_ago + timedelta(days=3)
        )
        .order_by(Transaction.transaction_date_and_time.desc())
        .first()
    )
    if month_transaction:
        results.append((month_transaction, "about a month ago"))

    # Get transaction from ~1 week ago (within 1 day)
    week_transaction = (
        db.query(Transaction)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .filter(Transaction.transaction_date_and_time >= one_week_ago - timedelta(days=1))
        .filter(Transaction.transaction_date_and_time <= one_week_ago + timedelta(days=1))
        .order_by(Transaction.transaction_date_and_time.desc())
        .first()
    )
    if week_transaction:
        results.append((week_transaction, "about a week ago"))

    return results


def filter_transactions(
    db: Session,
    user_id: int,
    recipient_name: Optional[str] = None,
    amount: Optional[Decimal] = None,
    title: Optional[str] = None,
    limit: int = 10,
) -> List[Transaction]:
    """
    Filter transactions based on provided criteria.

    Args:
        db: Database session
        user_id: ID of the user
        recipient_name: Partial or full recipient name
        amount: Transaction amount to match (exact)
        title: Partial or full payment title
        limit: Maximum number of results

    Returns:
        List of matching transactions, most recent first
    """
    query = db.query(Transaction).filter(Transaction.sender_id == user_id).filter(
        Transaction.transaction_posted == True
    )

    if recipient_name:
        # Search in both first and last name
        name_parts = recipient_name.strip().lower().split()
        name_filters = []
        for part in name_parts:
            name_filters.append(Transaction.receiver_name.ilike(f"%{part}%"))
            name_filters.append(Transaction.receiver_surname.ilike(f"%{part}%"))
        query = query.filter(or_(*name_filters))

    if amount is not None:
        query = query.filter(Transaction.amount == amount)

    if title:
        query = query.filter(Transaction.transaction_text.ilike(f"%{title}%"))

    return query.order_by(Transaction.transaction_date_and_time.desc()).limit(limit).all()


def get_recipient_patterns(
    db: Session, user_id: int
) -> Dict[str, Dict[str, int]]:
    """
    Analyze past transactions to find common recipient name -> account patterns.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Dict mapping recipient names to their most common bank accounts with counts
        Format: {
            "John Smith": {"4276123456789012": 5, "4276987654321098": 1},
            ...
        }
    """
    transactions = (
        db.query(Transaction)
        .join(User, Transaction.receiver_id == User.user_id)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .all()
    )

    patterns: Dict[str, Dict[str, int]] = {}

    for transaction in transactions:
        # Get the full name
        full_name = f"{transaction.receiver_name} {transaction.receiver_surname}"

        # Get the receiver's bank account from the User table
        receiver = (
            db.query(User).filter(User.user_id == transaction.receiver_id).first()
        )
        if receiver:
            bank_account = receiver.bank_number

            if full_name not in patterns:
                patterns[full_name] = {}

            if bank_account not in patterns[full_name]:
                patterns[full_name][bank_account] = 0

            patterns[full_name][bank_account] += 1

    return patterns


def get_account_patterns(
    db: Session, user_id: int
) -> Dict[str, Dict[str, int]]:
    """
    Analyze past transactions to find common account -> recipient name patterns.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Dict mapping bank accounts to their most common recipient names with counts
        Format: {
            "4276123456789012": {"John Smith": 5},
            ...
        }
    """
    transactions = (
        db.query(Transaction)
        .join(User, Transaction.receiver_id == User.user_id)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .all()
    )

    patterns: Dict[str, Dict[str, int]] = {}

    for transaction in transactions:
        full_name = f"{transaction.receiver_name} {transaction.receiver_surname}"

        # Get the receiver's bank account
        receiver = (
            db.query(User).filter(User.user_id == transaction.receiver_id).first()
        )
        if receiver:
            bank_account = receiver.bank_number

            if bank_account not in patterns:
                patterns[bank_account] = {}

            if full_name not in patterns[bank_account]:
                patterns[bank_account][full_name] = 0

            patterns[bank_account][full_name] += 1

    return patterns
