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
poetry run dev
```

Check if database works in outpusts!

Access API:
- http://localhost:8000/
- http://localhost:8000/docs

Access DB:
- http://localhost:8081

Other:

Kill process:
```
lsof -ti:8000 | xargs kill -9
```
