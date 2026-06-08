import numpy as np
from sqlalchemy import or_
from sqlalchemy.orm import Session

from shared.models import SessionLocal, Transaction, User

## Take all historical transactions for a specific user


def filter_by_user(db: Session, user_id: int):
    return (
        db.query(Transaction)
        .filter(
            or_(Transaction.sender_id == user_id, Transaction.receiver_id == user_id)
        )
        .order_by(Transaction.transaction_date_and_time.desc())
        .all()
    )


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
    receiver_ids = [
        tx.receiver_id for tx in user_transactions if tx.receiver_id != user_id
    ]

    # Get previous receivers with their bank numbers
    previous_receivers = db.query(User).filter(User.user_id.in_(receiver_ids)).all()

    if not previous_receivers:
        return {
            "valid": True,
            "suggestion": None,
            "receiver_name": None,
            "error_position": None,
        }

    def equal_or_similar(bn1, bn2):
        bn1, bn2 = bn1.strip(), bn2.strip()
        if bn1 == bn2:
            return {"match": "exact", "error_position": None}
        if len(bn1) != len(bn2):
            return {"match": False, "error_position": None}
        differences = sum(c1 != c2 for c1, c2 in zip(bn1, bn2))
        if differences <= 3:
            # Find the position of the first difference
            error_position = next(
                i for i, (c1, c2) in enumerate(zip(bn1, bn2)) if c1 != c2
            )
            return {"match": "similar", "error_position": error_position}
        return {"match": False, "error_position": None}

    for receiver in previous_receivers:
        if not receiver.bank_number:
            continue

        res = equal_or_similar(receiver.bank_number, bank_number)
        if res["match"] == "exact":
            return {
                "valid": True,
                "suggestion": None,
                "receiver_name": None,
                "error_position": None,
            }

        elif res["match"] == "similar":
            # Get receiver's full name
            receiver_full_name = f"{receiver.name} {receiver.surname}".strip()
            return {
                "valid": False,
                "suggestion": receiver.bank_number,
                "receiver_name": receiver_full_name,
                "error_position": res["error_position"],
            }

    return {
        "valid": True,
        "suggestion": None,
        "receiver_name": None,
        "error_position": None,
    }


## Full name validation


def is_fullname_valid(
    db: Session, sender_user_id: int, receiver_bank_number: str, fullname: str
):
    """
    Validates if a given full name matches historical receiver names
    for the specified receiver bank number.
    """

    # 1. Find receiver user by bank number
    receiver_user = (
        db.query(User).filter(User.bank_number == receiver_bank_number).first()
    )

    # If bank number not found → new receiver → valid
    if not receiver_user:
        return {"valid": True, "suggestion": None}

    # 2. Get previous transactions between same sender → receiver
    user_transactions = (
        db.query(Transaction)
        .filter(
            Transaction.sender_id == sender_user_id,
            Transaction.receiver_id == receiver_user.user_id,
        )
        .all()
    )

    # No previous transactions → new receiver → valid
    if not user_transactions:
        return {"valid": True, "suggestion": None}

    # 3. Extract previous first and last names
    previous_firstnames = [
        tx.receiver_name.strip() for tx in user_transactions if tx.receiver_name
    ]
    previous_lastnames = [
        tx.receiver_surname.strip() for tx in user_transactions if tx.receiver_surname
    ]

    # 4. Split the input
    parts = fullname.split()
    if len(parts) < 2:
        return {
            "valid": False,
            "suggestion": f"{previous_firstnames[0]} {previous_lastnames[0]}",
        }

    first_name, last_name = parts[0].strip(), " ".join(parts[1:]).strip()

    # Helper to normalize comparison
    def norm(s):
        return s.strip().lower()

    # 5. Check normal order: First Last
    normal_first_ok = any(norm(fn) == norm(first_name) for fn in previous_firstnames)
    normal_last_ok = any(norm(ln) == norm(last_name) for ln in previous_lastnames)

    # 6. Check swapped order: Last First
    swapped_first_ok = any(norm(fn) == norm(last_name) for fn in previous_firstnames)
    swapped_last_ok = any(norm(ln) == norm(first_name) for ln in previous_lastnames)

    # 7. If either normal matches OR swapped matches → OK
    normal_valid = normal_first_ok and normal_last_ok
    swapped_valid = swapped_first_ok and swapped_last_ok

    if normal_valid or swapped_valid:
        return {"valid": True, "suggestion": None}

    # 8. If invalid → suggest correct name
    suggestion = f"{previous_firstnames[0]} {previous_lastnames[0]}"

    return {"valid": False, "suggestion": suggestion}


# if __name__ == "__main__":
#    # Initialize database and seed if needed
#    from shared.db import init_db
#    from backend.seed import seed_database
#
#    print("Initializing database...")
#    init_db()
#    seed_database()

# Test the function
#    db = SessionLocal()
#    try:
#        result = is_bankNumber_valid(db, 1, "4276555311412423")
#        print(f"Result: {result}")
#    finally:
#        db.close()
