import os

from dotenv import load_dotenv
from fastapi import FastAPI

from backend.db import init_db, test_connection

load_dotenv()

app = FastAPI()


@app.on_event("startup")
def startup():
    print("Starting FastAPI...")
    try:
        init_db()
        print("✓ Database initialized")
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
