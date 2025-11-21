# Banking Money Transfer MCP Server

Production-ready FastAPI service providing three tools for LLM-driven money transfer assistance.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 System Architecture                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Frontend (Future)  ──────►  Backend/Agents       │
│     Port: TBD                   Port: 8000         │
│                                    │                │
│                                    │                │
│                                    ▼                │
│                              MCP Server             │
│                               Port: 8001            │
│                                    │                │
│                                    ▼                │
│                              PostgreSQL             │
│                               Port: 5433            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Services

1. **PostgreSQL** (port 5433) - Database
2. **MCP Server** (port 8001) - FastAPI exposing 3 tools as REST endpoints
3. **Backend/Agents** (port 8000) - Future: FastAPI with agents that call MCP tools
4. **Frontend** (future) - Will call backend

## Quick Start

### With Docker (Recommended)

```bash
# Start all services (db + mcp)
docker compose up -d

# Check MCP server health
curl http://localhost:8001/health

# View API docs
open http://localhost:8001/docs
```

### Local Development

```bash
# Ensure database is running
docker compose up -d db

# Install dependencies
cd backend
poetry install

# Run MCP server locally
poetry run mcp
```

## API Endpoints

### 1. POST /tools/first-suggestion

Get up to 5 transactions with temporal context for LLM analysis.

**Request**:
```json
{
  "user_id": 1
}
```

**Response**:
```json
{
  "transactions": [
    {
      "recipient_name": "Kate Davis",
      "bank_account": "4276987654321098",
      "amount": 5000.00,
      "title": "Payment for services",
      "transaction_date": "2025-01-15T10:30:00",
      "temporal_label": "1_month_ago"
    },
    {
      "recipient_name": "Mike Wilson",
      "bank_account": "4276555511112222",
      "amount": 7500.00,
      "title": "Project investment",
      "transaction_date": "2025-01-28T11:00:00",
      "temporal_label": "recent"
    }
  ],
  "user_balance": 50000.00,
  "total_transactions_count": 5
}
```

**Behavior**:
- Returns **max 5 transactions**: 1 from ~1 year ago, 1 from ~1 month ago, 1 from ~1 week ago, 2 recent
- temporal_label: `"1_year_ago"` | `"1_month_ago"` | `"1_week_ago"` | `"recent"`
- LLM decides which to suggest based on temporal patterns

**cURL Example**:
```bash
curl -X POST http://localhost:8001/tools/first-suggestion \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

---

### 2. POST /tools/filter-suggestion

Filter past transactions by partial name/amount/title.

**Request**:
```json
{
  "user_id": 1,
  "recipient_name": "Kate",
  "amount": 5000.00,
  "title": "services"
}
```

**Response**:
```json
{
  "matched_transactions": [
    {
      "recipient_name": "Kate Davis",
      "bank_account": "4276987654321098",
      "amount": 5000.00,
      "title": "Payment for services",
      "transaction_date": "2025-01-15T10:30:00",
      "temporal_label": null
    }
  ],
  "filters_applied": {
    "recipient_name": "Kate",
    "amount": 5000.00,
    "title": "services"
  },
  "match_count": 1
}
```

**Behavior**:
- All filters optional
- `recipient_name`: case-insensitive partial match
- `amount`: exact match
- `title`: case-insensitive partial match
- Returns up to 10 matches

**cURL Example**:
```bash
curl -X POST http://localhost:8001/tools/filter-suggestion \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "recipient_name": "Kate"}'
```

---

### 3. POST /tools/final-check

Validate transaction and return OK or list of problems.

**Request**:
```json
{
  "user_id": 1,
  "recipient_name": "Kate Davis",
  "bank_account": "4276987654321098",
  "amount": 100.00,
  "title": "Coffee money"
}
```

**Response (OK)**:
```json
{
  "is_ok": true,
  "problems": [],
  "user_balance": 50000.00,
  "amount_to_send": 100.00
}
```

**Response (Problems)**:
```json
{
  "is_ok": false,
  "problems": [
    "Insufficient balance: trying to send 60000.00 but only have 50000.00",
    "Warning: 'Kate Davis' usually uses account 4276111122223333 (used 5 times before)"
  ],
  "user_balance": 50000.00,
  "amount_to_send": 60000.00
}
```

**Validation Checks**:
1. All required fields present
2. Amount is positive
3. Amount doesn't exceed user balance
4. Bank account length is 10-34 characters
5. Historical consistency (name-account pairing)

**cURL Example**:
```bash
curl -X POST http://localhost:8001/tools/final-check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 1,
    "recipient_name": "Kate Davis",
    "bank_account": "4276987654321098",
    "amount": 100.00,
    "title": "Coffee"
  }'
```

---

### Health Check

**GET /health**

```bash
curl http://localhost:8001/health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "service": "mcp-server"
}
```

---

## Using from Backend Agents

Your backend agents (future port 8000) will call these endpoints:

```python
import httpx

async def get_suggestions_for_user(user_id: int):
    """Call MCP server from backend agent."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://mcp:8001/tools/first-suggestion",  # Use 'mcp' in Docker
            json={"user_id": user_id}
        )
        return response.json()

async def validate_transaction(user_id: int, recipient_name: str,
                                bank_account: str, amount: float, title: str):
    """Validate transaction before processing."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://mcp:8001/tools/final-check",
            json={
                "user_id": user_id,
                "recipient_name": recipient_name,
                "bank_account": bank_account,
                "amount": amount,
                "title": title
            }
        )
        result = response.json()

        if result["is_ok"]:
            return "✅ Transaction validated"
        else:
            return f"❌ Problems: {', '.join(result['problems'])}"
```

## Project Structure

```
backend/
├── src/
│   ├── backend/           # Future: FastAPI agents (port 8000)
│   └── mcp_server/        # MCP FastAPI server (port 8001)
│       ├── __init__.py
│       ├── app.py         # FastAPI application
│       ├── tools.py       # Tool implementations
│       ├── database.py    # Database queries
│       ├── schemas.py     # Pydantic schemas
│       └── README.md      # This file
├── pyproject.toml
└── Dockerfile.mcp
```

## Environment Variables

Uses existing `.env` file:
```env
DATABASE_NAME=your_database_name
DATABASE_USERNAME=your_username
DATABASE_PASSWORD=your_password
DB_HOST=localhost          # 'db' in Docker
DB_PORT=5433              # 5432 in Docker
```

## Docker Compose Configuration

```yaml
services:
  db:
    image: postgres:17
    ports:
      - "5432:5432"

  mcp:
    build:
      context: ./backend
      dockerfile: Dockerfile.mcp
    ports:
      - "8001:8001"
    depends_on:
      - db
```

## Testing

```bash
cd backend
poetry run pytest tests/test_tools.py -v
```

## Development Workflow

### 1. Start services
```bash
docker compose up -d
```

### 2. Seed database (first time)
```bash
cd backend
poetry run python -c "from backend.seed import seed_database; seed_database()"
```

### 3. Access services
- MCP API: http://localhost:8001
- MCP Docs: http://localhost:8001/docs
- DB Admin: http://localhost:8080
- Health Check: http://localhost:8001/health

### 4. Test endpoints
```bash
# Test first-suggestion
curl -X POST http://localhost:8001/tools/first-suggestion \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'

# Test filter-suggestion
curl -X POST http://localhost:8001/tools/filter-suggestion \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "recipient_name": "Kate"}'

# Test final-check
curl -X POST http://localhost:8001/tools/final-check \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"recipient_name":"Kate Davis","bank_account":"4276987654321098","amount":100.00,"title":"Test"}'
```

## Ports Summary

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5433 | localhost:5433 |
| PGWeb (DB Admin) | 8080 | http://localhost:8080 |
| MCP Server | 8001 | http://localhost:8001 |
| Backend (Future) | 8000 | http://localhost:8000 |
| Frontend (Future) | TBD | TBD |

## Design Philosophy

1. **Microservices**: Each service runs independently with clear responsibilities
2. **LLM-First**: MCP returns structured data, not UI messages
3. **REST API**: HTTP endpoints for easy integration from any backend
4. **Docker-Native**: All services containerized and orchestrated
5. **Type-Safe**: Full Pydantic validation on all endpoints

## Troubleshooting

**MCP server won't start**:
```bash
# Check logs
docker compose logs mcp

# Rebuild
docker compose build mcp
docker compose up -d mcp
```

**Database connection issues**:
```bash
# Check database is running
docker compose ps db

# Test health endpoint
curl http://localhost:8001/health
```

**Port conflicts**:
- Ensure ports 5433, 8001, 8080 are available
- Modify `docker-compose.yml` if needed

## Next Steps

1. **Backend/Agents** (port 8000): Implement FastAPI with LLM agents that call MCP tools
2. **Frontend**: Build UI that calls backend agents
3. **Authentication**: Add auth middleware to MCP and backend
4. **Rate Limiting**: Add rate limiting to MCP endpoints

## License

Internal use for Collabathon2025 project.
