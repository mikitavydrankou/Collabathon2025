from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import router as auth_router
from sqlalchemy.orm import Session


from backend.db import init_db, test_connection
from backend.seed import seed_database
from backend.utils.unusual_behavior import is_fullname_valid, is_bankNumber_valid, is_amount_valid
from backend.db import get_db
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.on_event("startup")
def startup():
    print("Starting FastAPI...")
    try:
        init_db()
        print("✓ Database initialized")
        seed_database()
    except Exception as e:
        print(f"✗ DB init failed: {e}")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"database": test_connection()}


@app.post("/validate_amount")
def validate_amount_endpoint(payload: AmountCheckRequest, db=Depends(get_db)):
    result = is_amount_valid(db, payload.user_id, payload.amount)
    return result

@app.post("/validate_bank_number")
def validate_bank_number_endpoint(payload: BankNumberCheckRequest, db=Depends(get_db)):
    result = is_bankNumber_valid(db, payload.user_id, payload.bank_number)
    return result

@app.post("/validate_fullname")
def validate_fullname_endpoint(payload: FullnameCheckRequest, db=Depends(get_db)):
    result = is_fullname_valid(db, payload.user_id, payload.bank_number, payload.fullname)
    return result

def start():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


def dev():
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
