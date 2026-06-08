import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import router as auth_router
from backend.chatbot.routes import router as chatbot_router
from backend.db import init_db, test_connection
from backend.qa.routes import router as qa_router
from backend.seed import seed_database
from backend.transactions.routes import router as transactions_router
from backend.utils.routes import router as utils_router

app = FastAPI()

# CORS origins from env (comma-separated). Wildcard "*" is invalid together with
# credentials, so credentials are only enabled for explicit origins.
_cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials="*" not in _cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chatbot_router)
app.include_router(qa_router)
app.include_router(transactions_router)
app.include_router(utils_router)


@app.on_event("startup")
def startup():
    print("Starting FastAPI...")
    try:
        init_db()
        print("✓ Database initialized")
        if os.getenv("SEED_ON_START", "false").lower() in ("1", "true", "yes"):
            seed_database()
        else:
            print("⏭ SEED_ON_START not set — skipping seed")
    except Exception as e:
        print(f"✗ DB init failed: {e}")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"database": test_connection()}


def start():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


def dev():
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
