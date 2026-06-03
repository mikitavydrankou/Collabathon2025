<div align="center">

# EasyFocus Assistant

### AI banking companion for everyone who needs a helping hand

Adaptive, conversational banking for neurodivergent and cognitively diverse users —
chat your way through payments, get step-by-step guidance, catch mistakes before they happen.

**[Live Demo →](http://68.183.76.153:3000/)**

![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=nextdotjs&logoColor=white)
![React 18](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Postgres 17](https://img.shields.io/badge/PostgreSQL-17-4169e1?logo=postgresql&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-OpenAI-1c3c3c?logo=langchain&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ed?logo=docker&logoColor=white)

<sub>Team Beszketnyky · Collabathon 2025 for Commerzbank</sub>

</div>

---

## Why

**~1 billion people (16% of the world)** live with a significant disability — many cognitive
or neurodevelopmental. Banking apps, with their dense forms and unforgiving flows, turn routine
money tasks into a source of anxiety. EasyFocus meets people where they are, with **as much or
as little help as they want.**

## Features

- **Payment assistant chat** — natural language ("send €50 to John"), clarifying questions, speech-to-text.
- **Step-by-step guidance** — the AI walks you through every action, with visual cues and photo-based invoice parsing.
- **Quality checks** — anomaly detection validates amounts, accounts and recipients, warning before costly mistakes.
- **Proactive help** — recurring-payment reminders, offline mode, biometric login, conversational search over your data.

## Quick start

Needs Docker + Docker Compose.

```bash
git clone https://github.com/mikitavydrankou/Collabathon2025.git
cd Collabathon2025
cp .env.example .env        # set DB creds + OPENAI_API_KEY
docker compose up -d --build
```

Open **http://localhost:3000** — frontend, backend (`:8000`), MCP server (`:8001`),
PostgreSQL (`:5432`) and the pgweb DB admin UI (`:8080`) all come up together.

> [!TIP]
> Set `OPENAI_API_KEY` before building — the chatbot and QA agents need it for LLM calls and embeddings.

## Stack

**Frontend** Next.js 16 · React 18 · Tailwind · shadcn/ui
**Backend** FastAPI · SQLAlchemy 2 · LangChain + OpenAI · ChromaDB RAG · JWT auth
**Infra** PostgreSQL 17 · Model Context Protocol server · Docker Compose

Multi-agent design, service map, full config reference and the accessibility rationale live in
**[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

<div align="center"><sub>Built so banking works for everyone — clear, calm, mistake-proof.</sub></div>
