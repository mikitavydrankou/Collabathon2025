# Collabathon2025

## Setup

Create `.env` from `.env.example` in root and backend directory.

Start database:
```
docker compose up -d
```

Install dependencies:
```
cd backend
poetry install
```

Run backend:
```
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Check database in outpusts E.g.:
```
INFO:     Waiting for application startup.
Starting FastAPI...
DB connected: PostgreSQL 17.7 (Debian 17.7-3.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
```

Access API:
- http://localhost:8000/
- http://localhost:8000/docs
