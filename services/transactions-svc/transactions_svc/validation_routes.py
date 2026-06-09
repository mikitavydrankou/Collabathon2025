from fastapi import APIRouter, Depends
from shared.database import get_recent_transactions
from shared.models import User
from sqlalchemy.orm import Session

from shared.db import get_db
from .validation_schemas import (
    AmountCheckRequest,
    BankNumberCheckRequest,
    FullnameCheckRequest,
)
from .anomaly import (
    is_amount_valid,
    is_bankNumber_valid,
    is_fullname_valid,
)

router = APIRouter()


@router.post("/validate_amount")
def validate_amount_endpoint(payload: AmountCheckRequest, db=Depends(get_db)):
    result = is_amount_valid(db, payload.user_id, payload.amount)
    return result


@router.post("/validate_bank_number")
def validate_bank_number_endpoint(payload: BankNumberCheckRequest, db=Depends(get_db)):
    result = is_bankNumber_valid(db, payload.user_id, payload.bank_number)
    return result


@router.post("/validate_fullname")
def validate_fullname_endpoint(payload: FullnameCheckRequest, db=Depends(get_db)):
    result = is_fullname_valid(
        db, payload.user_id, payload.bank_number, payload.fullname
    )
    return result


@router.get("/transactions/{user_id}")
def get_user_transactions(user_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get recent transactions for a user"""
    transactions = get_recent_transactions(db, user_id, limit)

    result = []
    for txn in transactions:
        # Get receiver info
        receiver = db.query(User).filter(User.user_id == txn.receiver_id).first()

        result.append(
            {
                "transaction_id": txn.transaction_id,
                "receiver_name": f"{txn.receiver_name} {txn.receiver_surname}",
                "receiver_bank_account": receiver.bank_number if receiver else None,
                "amount": float(txn.amount),  # type: ignore
                "transaction_date": txn.transaction_date_and_time.isoformat(),
                "transaction_type": txn.transaction_type,
                "transaction_text": txn.transaction_text,
                "amount_before": float(txn.amount_before),  # type: ignore
                "amount_after": float(txn.amount_after),  # type: ignore
                "flagged": bool(txn.flagged),
                "flag_reason": txn.flag_reason,
            }
        )

    return {"transactions": result}
