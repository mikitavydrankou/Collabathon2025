from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from shared.db import get_db
from shared.models import User
from shared.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    verify_password,
)

from .schemas import LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_request.username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    if not verify_password(login_request.password, str(user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = create_access_token(
        data={"sub": str(user.username)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=int(user.user_id),  # type: ignore
        username=str(user.username),  # type: ignore
        name=str(user.name),  # type: ignore
        surname=str(user.surname),  # type: ignore
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        user_id=int(current_user.user_id),  # type: ignore
        username=str(current_user.username),  # type: ignore
        name=str(current_user.name),  # type: ignore
        surname=str(current_user.surname),  # type: ignore
        balance=float(current_user.balance),  # type: ignore
        bank_number=str(current_user.bank_number),  # type: ignore
    )


@router.get("/user/{user_id}/balance")
def get_user_balance(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "user_id": int(user.user_id),  # type: ignore
        "balance": float(user.balance),  # type: ignore
    }
