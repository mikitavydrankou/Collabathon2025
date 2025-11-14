# Collabathon2025

## Setup

1. Create `.env` from `.env.example` in root and backend directory.

2. Start database:
```
docker compose up -d
```

3. Install poetry dependencies (backend):
```
cd backend
poetry install
```

4. Run backend:
```
poetry run dev
```

5. Check if database works via http://localhost:8000/health

---

Access API:
- http://localhost:8000/
- http://localhost:8000/docs

Access DB:
- http://localhost:8080

---

Other:

Kill process:
```
lsof -ti:8000 | xargs kill -9
```
