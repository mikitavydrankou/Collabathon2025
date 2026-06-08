from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, validator


class TransactionBase(BaseModel):
    """Base transaction schema"""

    receiver_name: str = Field(..., min_length=1, max_length=100)
    receiver_surname: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    transaction_text: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction"""

    receiver_bank_number: str = Field(..., min_length=1, max_length=50)

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        # Convert to 2 decimal places
        return round(v, 2)


class TransactionResponse(TransactionBase):
    """Schema for transaction response"""

    transaction_id: int
    sender_id: int
    receiver_id: int
    transaction_date_and_time: datetime
    amount_before: Decimal
    amount_after: Decimal
    transaction_type: str
    transaction_posted: bool
    receiver_bank_account: str

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat(),
        }


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list"""

    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class TransactionDetailResponse(TransactionResponse):
    """Schema for detailed transaction view"""

    sender_name: str
    sender_surname: str
    sender_bank_account: str


class TransactionStats(BaseModel):
    """Schema for transaction statistics"""

    total_sent: Decimal
    total_received: Decimal
    total_transactions: int
    sent_count: int
    received_count: int
    pending_count: int

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }


class TransactionFilter(BaseModel):
    """Schema for filtering transactions"""

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    posted_only: Optional[bool] = None


class CreateTransactionRequest(BaseModel):
    """Request schema for creating a transaction"""

    user_id: int
    receiver_bank_number: str = Field(..., min_length=1)
    receiver_name: str = Field(..., min_length=1, max_length=100)
    receiver_surname: str = Field(..., min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=0)
    transaction_text: Optional[str] = Field(None, max_length=500)

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return round(v, 2)


class CreateTransactionResponse(BaseModel):
    """Response schema for transaction creation"""

    success: bool
    message: str
    transaction_id: Optional[int] = None
    transaction: Optional[TransactionResponse] = None


class TransactionSummary(BaseModel):
    """Schema for transaction summary"""

    user_id: int
    balance: Decimal
    transactions_sent: int
    transactions_received: int
    total_sent: Decimal
    total_received: Decimal
    recent_transactions: list[TransactionResponse]

    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
        }
