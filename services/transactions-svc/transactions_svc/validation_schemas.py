from pydantic import BaseModel, Field

class AmountCheckRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)

class BankNumberCheckRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    bank_number: str = Field(..., min_length=8, max_length=34)

class FullnameCheckRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    bank_number: str = Field(..., min_length=8, max_length=34)
    fullname: str = Field(..., min_length=1, max_length=100)