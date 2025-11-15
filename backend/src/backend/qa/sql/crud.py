from backend.models import Transaction, User
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy import func
from datetime import datetime, timedelta

## Crud operations:
## 1. Get total expenses for a user for X days
## 2. Get total income for a user for X days
## 3. Get number of transactions for a user for X days
## 4. Get last n transactions for a user
## 5. Get most frequent transaction receiver for a user
## 6. Get Largest single expense
## 7. Monthly spending trend

def get_total_expenses(db: Session, user_id: int, days: int) -> float:
    """
    Get the total expenses for a user.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user.
        days (int): Number of days to look back.
    
    Returns:
        float: Total expenses amount.
    """
    filtered_date = func.now() - func.make_interval(0, 0, 0, days, 0, 0, 0)
    total = db.query(func.sum(Transaction.amount))\
        .filter(Transaction.sender_id == user_id)\
        .filter(Transaction.transaction_date_and_time >= filtered_date)\
        .scalar()
    return float(total or 0.0)

def get_total_income(db: Session, user_id: int, days: int) -> float:
    """
    Get the total income for a user.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user.
        days (int): Number of days to look back.

    Returns:
        float: Total income amount.
    """
    filtered_date = func.now() - func.make_interval(0, 0, 0, days, 0, 0, 0)
    total = db.query(func.sum(Transaction.amount))\
        .filter(Transaction.receiver_id == user_id)\
        .filter(Transaction.transaction_date_and_time >= filtered_date)\
        .scalar()
    return float(total or 0.0)

def get_transaction_count(db: Session, user_id: int, days: int) -> int:
    """
    Get the number of transactions for a user.
    Args:
        db (Session): Database session.
        user_id (int): ID of the user.
        days (int): Number of days to look back.

    Returns:
        int: Number of transactions.
    """
    filtered_date = func.now() - func.make_interval(0, 0, 0, days, 0, 0, 0)
    count = db.query(func.count(Transaction.transaction_id))\
        .filter(or_(Transaction.sender_id == user_id, Transaction.receiver_id == user_id))\
        .filter(Transaction.transaction_date_and_time >= filtered_date)\
        .scalar()
    return count or 0

def get_last_n_transactions(db: Session, user_id: int, n: int) -> list[Transaction]:
    """
    Get the last n transactions for a user.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user.
        n (int): Number of transactions to retrieve.

    Returns:
        list[Transaction]: List of last n transactions.
    """
    transactions = (
        db.query(Transaction)
        .filter(
            or_(Transaction.sender_id == user_id, Transaction.receiver_id == user_id)
        )
        .order_by(Transaction.transaction_date_and_time.desc())
        .limit(n)
        .all()
    )
    transactions_json = []
    for tx in transactions:
        transactions_json.append({
            "receiver_name": f"{tx.receiver.name} {tx.receiver.surname}",
            "amount": float(tx.amount),
            "transaction_date": tx.transaction_date_and_time.isoformat(),
            "transaction_type": tx.transaction_type,
            "transaction_text": tx.transaction_text,
            "amount_before": float(tx.amount_before),
            "amount_after": float(tx.amount_after),
        })
    return transactions_json

def get_most_frequent_receiver(db: Session, user_id: int) -> int | None:
    """
    Get the most frequent transaction receiver for a user.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user.

    Returns:
        int | None: User ID of the most frequent receiver or None if no transactions exist.
    """
    result = (
        db.query(Transaction.receiver_id, func.count(Transaction.receiver_id).label("count"))
        .filter(Transaction.sender_id == user_id)
        .group_by(Transaction.receiver_id)
        .order_by(func.count(Transaction.receiver_id).desc())
        .first()
    )

    def get_fullname_by_id(user_id: int) -> str | None:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            return f"{user.name} {user.surname}"
        return None

    return get_fullname_by_id(result.receiver_id) if result else None

def get_largest_expense(db: Session, user_id: int) -> float:
    """
    Get the largest single expense for a user.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user.

    Returns:
        float: Largest expense amount.
    """
    largest = db.query(func.max(Transaction.amount))\
        .filter(Transaction.sender_id == user_id)\
        .scalar()
    return float(largest or 0.0)

def get_monthly_trend(db: Session, user_id: int, months_back: int = 6) -> list[dict]:
    """
    Get monthly spending trend for the last `months_back` months.

    Args:
        db (Session): Database session.
        user_id (int): ID of the user.
        months_back (int): Number of months to include in the trend (default 6).

    Returns:
        list[dict]: List of dicts: {'month': 'YYYY-MM', 'total_spent': float}
    """
    now = datetime.now()
    start_month = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    for _ in range(months_back - 1):
        start_month = (start_month - timedelta(days=1)).replace(day=1)

    # Query grouped by month
    results = (
        db.query(
            func.date_trunc('month', Transaction.transaction_date_and_time).label('month'),
            func.sum(Transaction.amount).label('total_spent')
        )
        .filter(Transaction.sender_id == user_id)
        .filter(Transaction.transaction_date_and_time >= start_month)
        .group_by(func.date_trunc('month', Transaction.transaction_date_and_time))
        .order_by(func.date_trunc('month', Transaction.transaction_date_and_time))
        .all()
    )

    trend = [
        {
            'month': result.month.strftime('%Y-%m'),
            'total_spent': float(result.total_spent)
        }
        for result in results
    ]
    return trend

## TESTING THE FUNCTIONS
##from backend.models import SessionLocal
##db = SessionLocal()

##functions = [
##    get_total_expenses,
##    get_total_income,
##    get_transaction_count,
##    get_last_n_transactions,
##    get_most_frequent_receiver,
##    get_largest_expense,
##    get_monthly_trend,
##]

# print("Testing CRUD functions:")
# for f in functions:
#    print(f"Function: {f.__name__}")
#    if f == get_total_expenses:
#        print(f(db, user_id=1, days=400))
#    elif f == get_total_income:
#        print(f(db, user_id=1, days=400))
#    elif f == get_transaction_count:
#        print(f(db, user_id=1, days=400))
#    elif f == get_last_n_transactions:
#        print(f(db, user_id=1, n=5))
#    elif f == get_most_frequent_receiver:
#        print(f(db, user_id=1))
#    elif f == get_largest_expense:
#        print(f(db, user_id=1))
#    elif f == get_monthly_trend:
#        print(f(db, user_id=1, months_back=15))
#    print("-" * 40)

# db.close()