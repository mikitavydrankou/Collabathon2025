from fastapi import APIRouter, Depends
from backend.utils.unusual_behavior import is_fullname_valid, is_bankNumber_valid, is_amount_valid
from backend.utils.schemas import AmountCheckRequest, BankNumberCheckRequest, FullnameCheckRequest
from backend.db import get_db

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
    result = is_fullname_valid(db, payload.user_id, payload.bank_number, payload.fullname)
    return result