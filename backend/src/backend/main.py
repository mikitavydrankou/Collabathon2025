import os

from dotenv import load_dotenv
from fastapi import FastAPI

from backend.db import check

load_dotenv()

app = FastAPI()


@app.on_event("startup")
def startup():
    print("Starting FastAPI...")
    try:
        version = check()
        print(f"DB connected: {version}")
    except Exception as e:
        print(f"DB connection failed: {e}")


@app.get("/")
def root():
    print("GET /")
    return {"status": "ok"}


@app.get("/health")
def health():
    print("GET /health")
    return {"database": os.getenv("DATABASE_NAME")}


def start():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
