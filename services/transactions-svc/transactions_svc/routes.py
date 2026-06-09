import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from shared.models import SessionLocal, User
from .schemas import (
    CreateTransactionRequest,
    CreateTransactionResponse,
    TransactionDetailResponse,
    TransactionFilter,
    TransactionListResponse,
    TransactionStats,
)
from .services import TransactionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/create", response_model=CreateTransactionResponse)
async def create_transaction(
    request: CreateTransactionRequest,
    db: Session = Depends(get_db),
):
    """
    Create a new transaction between users

    - **user_id**: ID of the sender
    - **receiver_bank_number**: Bank account number of the receiver
    - **receiver_name**: First name of the receiver
    - **receiver_surname**: Last name of the receiver
    - **amount**: Amount to transfer (must be > 0)
    - **transaction_text**: Optional description/reference text
    """
    success, message, transaction = TransactionService.create_transaction(
        db=db,
        sender_id=request.user_id,
        receiver_bank_number=request.receiver_bank_number,
        receiver_name=request.receiver_name,
        receiver_surname=request.receiver_surname,
        amount=request.amount,
        transaction_text=request.transaction_text,
    )

    if not success:
        return CreateTransactionResponse(
            success=False,
            message=message,
            transaction_id=None,
            transaction=None,
        )

    # Format transaction response as dict
    transaction_dict = {
        "transaction_id": int(transaction.transaction_id),
        "sender_id": int(transaction.sender_id),
        "receiver_id": int(transaction.receiver_id),
        "receiver_name": str(transaction.receiver_name),
        "receiver_surname": str(transaction.receiver_surname),
        "amount": float(transaction.amount),
        "transaction_date_and_time": transaction.transaction_date_and_time.isoformat(),
        "amount_before": float(transaction.amount_before),
        "amount_after": float(transaction.amount_after),
        "transaction_type": str(transaction.transaction_type),
        "transaction_posted": bool(transaction.transaction_posted),
        "transaction_text": str(transaction.transaction_text)
        if transaction.transaction_text
        else None,
        "receiver_bank_account": request.receiver_bank_number,
    }

    return {
        "success": True,
        "message": message,
        "transaction_id": int(transaction.transaction_id),
        "transaction": transaction_dict,
    }


@router.get("/{user_id}")
async def get_user_transactions(
    user_id: int,
    limit: int = Query(
        50, ge=1, le=100, description="Number of transactions to return"
    ),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    start_date: Optional[str] = Query(
        None, description="Filter by start date (ISO format)"
    ),
    end_date: Optional[str] = Query(
        None, description="Filter by end date (ISO format)"
    ),
    min_amount: Optional[float] = Query(
        None, ge=0, description="Minimum transaction amount"
    ),
    max_amount: Optional[float] = Query(
        None, ge=0, description="Maximum transaction amount"
    ),
    transaction_type: Optional[str] = Query(
        None, description="Filter by transaction type"
    ),
    posted_only: Optional[bool] = Query(
        None, description="Show only posted transactions"
    ),
    db: Session = Depends(get_db),
):
    """
    Get all transactions for a user (both sent and received)

    Returns paginated list of transactions with filtering options
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Build filters
    from datetime import datetime as dt

    start_dt = dt.fromisoformat(start_date) if start_date else None
    end_dt = dt.fromisoformat(end_date) if end_date else None

    filters = TransactionFilter(
        start_date=start_dt,
        end_date=end_dt,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        transaction_type=transaction_type,
        posted_only=posted_only,
    )

    # Get transactions
    transactions = TransactionService.get_user_transactions(
        db=db,
        user_id=user_id,
        limit=limit,
        offset=offset,
        filters=filters,
    )

    # Count total (for pagination)
    total = len(transactions) if not offset else offset + len(transactions)
    has_more = len(transactions) == limit

    return {
        "transactions": transactions,
        "total": total,
        "page": offset // limit + 1 if limit > 0 else 1,
        "page_size": len(transactions),
        "has_more": has_more,
    }


@router.get("/{user_id}/stats")
async def get_transaction_stats(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Get transaction statistics for a user

    Returns:
    - Total amount sent
    - Total amount received
    - Transaction counts
    - Pending transactions count
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stats = TransactionService.get_transaction_stats(db=db, user_id=user_id)
    return {
        "total_sent": float(stats.total_sent),
        "total_received": float(stats.total_received),
        "total_transactions": stats.total_transactions,
        "sent_count": stats.sent_count,
        "received_count": stats.received_count,
        "pending_count": stats.pending_count,
    }


@router.get("/{user_id}/recent-receivers")
async def get_recent_receivers(
    user_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of receivers to return"),
    db: Session = Depends(get_db),
):
    """
    Get list of recent transaction receivers for quick transfers

    Returns deduplicated list of people the user has sent money to recently
    """
    # Verify user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    receivers = TransactionService.get_recent_receivers(
        db=db,
        user_id=user_id,
        limit=limit,
    )

    return {
        "user_id": user_id,
        "recent_receivers": receivers,
        "count": len(receivers),
    }


@router.get("/{user_id}/{transaction_id}")
async def get_transaction_detail(
    user_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific transaction

    User must be either sender or receiver
    """
    transaction = TransactionService.get_transaction_by_id(
        db=db,
        transaction_id=transaction_id,
        user_id=user_id,
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found or you don't have permission to view it",
        )

    return transaction


@router.delete("/{user_id}/{transaction_id}")
async def cancel_transaction(
    user_id: int,
    transaction_id: int,
    db: Session = Depends(get_db),
):
    """
    Cancel a pending transaction

    Only the sender can cancel, and only if the transaction hasn't been posted
    """
    success, message = TransactionService.cancel_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=user_id,
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@router.post("/verify-receiver")
async def verify_receiver(
    bank_number: str = Query(..., description="Bank account number"),
    name: str = Query(..., description="Receiver first name"),
    surname: str = Query(..., description="Receiver last name"),
    db: Session = Depends(get_db),
):
    """
    Verify if receiver details match the bank account

    Returns validation result with appropriate message
    """
    is_valid, message = TransactionService.verify_receiver(
        db=db,
        bank_number=bank_number,
        name=name,
        surname=surname,
    )

    return {
        "valid": is_valid,
        "message": message if message else "Receiver details verified successfully",
        "bank_number": bank_number,
    }
