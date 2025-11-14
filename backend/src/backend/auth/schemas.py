from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    name: str
    surname: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    name: str
    surname: str
    balance: float
    bank_number: str
