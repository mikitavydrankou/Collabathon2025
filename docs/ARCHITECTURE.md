# Architecture

EasyFocus Assistant is a multi-service app: a Next.js frontend, a FastAPI backend
that orchestrates the AI agents, an MCP tool server, and PostgreSQL — all wired
together with Docker Compose.

```
┌────────────┐      ┌─────────────────────────────┐      ┌────────────┐
│  Frontend  │─────▶│           Backend           │─────▶│ PostgreSQL │
│  Next.js   │ HTTP │  FastAPI · LangChain agents │ SQL  │     17     │
│  :3000     │◀─────│  :8000                      │◀─────│  :5432     │
└────────────┘      └──────────────┬──────────────┘      └─────┬──────┘
                                   │ MCP                       │
                                   ▼                           │
                            ┌────────────┐                     │
                            │ MCP Server │─────────────────────┘
                            │  :8001     │
                            └────────────┘   pgweb :8080 (DB admin UI)
```

## Services

| Service    | Port   | Role                                                     |
| ---------- | ------ | -------------------------------------------------------- |
| `frontend` | `3000` | Next.js 16 UI (React 18, Tailwind, shadcn/ui)            |
| `backend`  | `8000` | FastAPI — auth, chatbot, QA agents, transactions         |
| `mcp`      | `8001` | Model Context Protocol tool server                       |
| `db`       | `5432` | PostgreSQL 17 (persisted in `postgres_data` volume)      |
| `pgweb`    | `8080` | Web DB admin UI                                          |

## Backend

Core Python FastAPI application handling AI orchestration, authentication, and data processing.

```
backend/src/backend/
├── main.py                 # FastAPI application entry point
├── db.py                   # Database configuration
├── seed.py                 # Database seeding utilities
│
├── auth/                   # Authentication & authorization
│   ├── routes.py           # Auth API endpoints
│   ├── schemas.py          # Auth data models
│   └── utils.py            # JWT, password hashing
│
├── chatbot/                # Payment assistant chatbot
│   ├── agents.py           # Chatbot agent logic
│   ├── service.py          # Chatbot orchestration
│   ├── llm.py              # LLM integration
│   ├── mcp_client.py       # MCP server client
│   ├── routes.py           # Chatbot API endpoints
│   └── schemas.py          # Chatbot data models
│
├── qa/                     # Question-answering system
│   ├── agents/             # Multi-agent system
│   │   ├── main_agent.py   # Main orchestrator agent
│   │   ├── rag_agent.py    # RAG-based retrieval agent
│   │   └── sql_agent.py    # SQL query generation agent
│   ├── rag/                # Retrieval-Augmented Generation
│   │   ├── retriever.py    # Vector search & retrieval
│   │   ├── create_embeddings.py  # Embedding generation
│   │   └── parse_transactions.py # Transaction parsing
│   ├── sql/crud.py         # Database CRUD operations
│   ├── tools/              # Agent tools (rag_tool, sql_tool)
│   ├── chatbot_service.py  # QA service orchestration
│   ├── memory.py           # Conversation memory
│   └── routes.py           # QA API endpoints
│
├── transactions/           # Transaction management
│   ├── routes.py · schemas.py · services.py · examples.py
│
├── utils/                  # Utilities
│   ├── routes.py · schemas.py
│   └── unusual_behavior.py # Anomaly detection
│
└── models/                 # Database models
```

**Stack:** FastAPI · SQLAlchemy 2 · Pydantic · LangChain + OpenAI · ChromaDB (vector store) · python-jose JWT · bcrypt.

## Frontend

Next.js application for user interface and interaction.

```
frontend/
├── app/                    # Next.js app directory (page, layout, globals.css)
├── components/
│   ├── ui/                 # Reusable shadcn/ui primitives
│   ├── login-screen.tsx
│   ├── dashboard-screen.tsx
│   ├── chatbot-screen.tsx       # Payment assistant chat
│   ├── qa-chatbot-screen.tsx    # Smart search interface
│   ├── send-money-page.tsx      # Transaction interface
│   ├── ai-helper-popup.tsx      # AI assistance overlay
│   └── payment-suggestion-popup.tsx
├── hooks/                  # use-mobile, use-toast
├── lib/                    # api.ts (API client), utils.ts
└── public/                 # Static assets
```

**Stack:** Next.js 16 · React 18 · Tailwind CSS · shadcn/ui (Radix) · react-hook-form + zod · recharts.

## MCP Server

Model Context Protocol server exposing banking tools to the agents.

```
mcp_server/
├── server.py               # MCP server entry point
├── tools.py                # MCP tool definitions
├── database.py             # Database operations
├── schemas.py              # Data schemas
├── app.py                  # Application setup
└── Dockerfile
```

## Shared

Shared code and models across services.

```
shared/
├── database.py             # Shared database configuration
└── models/                 # user.py · transaction.py · person_to_contact.py
```

## Configuration

All config lives in `.env` (copy from `.env.example`).

| Variable             | Default               | Purpose                              |
| -------------------- | --------------------- | ------------------------------------ |
| `DATABASE_NAME`      | —                     | PostgreSQL database name             |
| `DATABASE_USERNAME`  | —                     | PostgreSQL user                      |
| `DATABASE_PASSWORD`  | —                     | PostgreSQL password (set before deploy) |
| `DB_HOST`            | `db`                  | DB host (compose service name)       |
| `DB_PORT`            | `5432`                | DB port                              |
| `MCP_SERVER_URL`     | `http://localhost:8001` | MCP tool server URL                |
| `OPENAI_API_KEY`     | —                     | OpenAI key for LLM + embeddings      |
| `NEXT_PUBLIC_API_URL`| `http://localhost:8000` | Backend URL exposed to the frontend |

## Why accessibility matters

Accessibility features routinely become mainstream innovations:

| Feature               | Original Purpose           | Mainstream Use             | Market Size                 |
| --------------------- | -------------------------- | -------------------------- | --------------------------- |
| **Voice Recognition** | Motor disabilities         | Siri, Alexa, transcription | $14.8B → $61.3B (2024–2033) |
| **Audiobooks**        | Visual impairments         | Entertainment, learning    | $2B+ (2023)                 |
| **Speech-to-text**    | Communication disabilities | Meeting notes, captions    | Global standard             |

**UN Convention on Rights of Persons with Disabilities (CRPD), Article 2:**

> - **"Reasonable accommodation"** requires apps to be usable without disproportionate burden.
> - **"Universal design"** means products work for all people without specialized adaptation.

Our features help neurodivergent users today — and everyone tomorrow.
