from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.models.user import User
from backend.models.transaction import Transaction
from backend.models import SessionLocal
import numpy as np

db = SessionLocal()

## Take all historical transactions for a specific user

def filter_by_user(db: Session, user_id: int):
    return (
        db.query(Transaction).filter(or_(Transaction.sender_id == user_id,
                                         Transaction.receiver_id == user_id)
                                         ).order_by(Transaction.transaction_date_and_time.desc()).all())

## Amount validation

def is_amount_valid(db: Session, user_id: int, amount: float):
    user = db.get(User, user_id)
    if not user:
        raise ValueError(f"User with id {user_id} does not exist.")

    user_transactions = filter_by_user(db, user_id)
    
    amounts = np.array([tx.amount for tx in user_transactions], dtype=float)

    q1 = np.percentile(amounts, 25)
    q3 = np.percentile(amounts, 75)
    IQR = q3 - q1

    lower_bound = q1 - 3 * IQR
    upper_bound = q3 + 3 * IQR

    if amount < lower_bound or amount > upper_bound:
        return {"valid": False, "suggestion": None}
    else:
        return {"valid": True, "suggestion": None}

## Bank number validation

def is_bankNumber_valid(db: Session, user_id: int, bank_number: str):
    user = db.get(User, user_id)
    if not user:
        raise ValueError(f"User with id {user_id} does not exist.")

    user_transactions = filter_by_user(db, user_id)
    receiver_ids = [tx.receiver_id for tx in user_transactions if tx.receiver_id != user_id]

    previous_bank_numbers = db.query(User.bank_number).filter(User.user_id.in_(receiver_ids)).all()
    previous_bank_numbers = [bn[0] for bn in previous_bank_numbers if bn[0] is not None]

    if not previous_bank_numbers:
        return {"valid": True, "suggestion": None}

    def equal_or_similar(bn1, bn2):
        bn1, bn2 = bn1.strip(), bn2.strip()
        if bn1 == bn2:
            return "exact"
        if len(bn1) != len(bn2):
            return False
        differences = sum(c1 != c2 for c1, c2 in zip(bn1, bn2))
        if differences <= 3:
            return "similar"
        return False

    for bn in previous_bank_numbers:
        res = equal_or_similar(bn, bank_number)
        if res == "exact":
            return {"valid": True, "suggestion": None}
            
        elif res == "similar":
            return {"valid": False, "suggestion": bn}
        
    return {"valid": True, "suggestion": None}

## First name validation

def is_name_valid(db: Session, sender_user_id: int, receiver_bank_number: str, name: str):
    receiver_user = db.query(User).filter(User.bank_number == receiver_bank_number).first()

    if not receiver_user:
        return {"valid": True, "suggestion": None}

    user_transactions = db.query(Transaction)\
        .filter(Transaction.sender_id == sender_user_id,
                Transaction.receiver_id == receiver_user.user_id)\
        .all()

    if not user_transactions:
        return {"valid": True, "suggestion": None}

    previous_names = [tx.receiver_name for tx in user_transactions if tx.receiver_name]

    for prev_name in previous_names:
        if prev_name.strip().lower() == name.strip().lower():
            return {"valid": True, "suggestion": None}

    return {"valid": False, "suggestion": previous_names[0]}

## Surname validation

def is_surname_valid(db: Session, sender_user_id: int, receiver_bank_number: str, surname: str):
    receiver_user = db.query(User).filter(User.bank_number == receiver_bank_number).first()

    if not receiver_user:
        return {"valid": True, "suggestion": None}

    user_transactions = db.query(Transaction)\
        .filter(Transaction.sender_id == sender_user_id,
                Transaction.receiver_id == receiver_user.user_id)\
        .all()

    if not user_transactions:
        return {"valid": True, "suggestion": None}

    previous_surnames = [tx.receiver_surname for tx in user_transactions if tx.receiver_surname]
    
    for prev_surname in previous_surnames:
        if prev_surname.strip().lower() == surname.strip().lower():
            return {"valid": True, "suggestion": None}

    return {"valid": False, "suggestion": previous_surnames[0]}