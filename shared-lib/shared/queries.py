"""Shared DB query helpers — used by mcp_server and any service that needs them."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from shared.models import Transaction, User


def get_user_balance(db: Session, user_id: int) -> Optional[Decimal]:
    user = db.query(User).filter(User.user_id == user_id).first()
    return user.balance if user else None


def get_recent_transactions(db: Session, user_id: int, limit: int = 10) -> List[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .order_by(Transaction.transaction_date_and_time.desc())
        .limit(limit)
        .all()
    )


def get_time_based_transactions(db: Session, user_id: int) -> List[Tuple[Transaction, str]]:
    now = datetime.now()
    results: List[Tuple[Transaction, str]] = []

    def _near(target: datetime, window: timedelta, label: str) -> None:
        tx = (
            db.query(Transaction)
            .filter(Transaction.sender_id == user_id)
            .filter(Transaction.transaction_posted == True)
            .filter(Transaction.transaction_date_and_time >= target - window)
            .filter(Transaction.transaction_date_and_time <= target + window)
            .order_by(Transaction.transaction_date_and_time.desc())
            .first()
        )
        if tx:
            results.append((tx, label))

    _near(now - timedelta(days=365), timedelta(days=7), "about a year ago")
    _near(now - timedelta(days=30), timedelta(days=3), "about a month ago")
    _near(now - timedelta(days=7), timedelta(days=1), "about a week ago")
    return results


def filter_transactions(
    db: Session,
    user_id: int,
    recipient_name: Optional[str] = None,
    recipient_bank_account: Optional[str] = None,
    amount: Optional[Decimal] = None,
    title: Optional[str] = None,
    limit: int = 10,
) -> List[Transaction]:
    query = (
        db.query(Transaction)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
    )

    if recipient_name:
        parts = recipient_name.strip().lower().split()
        name_filters = []
        for p in parts:
            name_filters.append(Transaction.receiver_name.ilike(f"%{p}%"))
            name_filters.append(Transaction.receiver_surname.ilike(f"%{p}%"))
        query = query.filter(or_(*name_filters))

    if recipient_bank_account:
        query = query.join(User, Transaction.receiver_id == User.user_id).filter(
            User.bank_number == recipient_bank_account
        )

    if amount is not None:
        query = query.filter(Transaction.amount == amount)

    if title:
        query = query.filter(Transaction.transaction_text.ilike(f"%{title}%"))

    return query.order_by(Transaction.transaction_date_and_time.desc()).limit(limit).all()


def get_recipient_patterns(db: Session, user_id: int) -> Dict[str, Dict[str, int]]:
    """Map recipient full-name → {bank_account: count}. Single query, no N+1."""
    rows = (
        db.query(Transaction, User)
        .join(User, Transaction.receiver_id == User.user_id)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .all()
    )
    patterns: Dict[str, Dict[str, int]] = {}
    for tx, receiver in rows:
        name = f"{tx.receiver_name} {tx.receiver_surname}"
        acct = receiver.bank_number
        patterns.setdefault(name, {})
        patterns[name][acct] = patterns[name].get(acct, 0) + 1
    return patterns


def get_account_patterns(db: Session, user_id: int) -> Dict[str, Dict[str, int]]:
    """Map bank_account → {recipient full-name: count}. Single query, no N+1."""
    rows = (
        db.query(Transaction, User)
        .join(User, Transaction.receiver_id == User.user_id)
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_posted == True)
        .all()
    )
    patterns: Dict[str, Dict[str, int]] = {}
    for tx, receiver in rows:
        name = f"{tx.receiver_name} {tx.receiver_surname}"
        acct = receiver.bank_number
        patterns.setdefault(acct, {})
        patterns[acct][name] = patterns[acct].get(name, 0) + 1
    return patterns
