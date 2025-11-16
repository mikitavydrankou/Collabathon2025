# EasyFocus Assistant

> **Team Beszketnyky** | Collabathon 2025 for Commerzbank

**AI-powered banking companion for everyone who needs a helping hand.**

**Live Demo:** http://68.183.76.153:3000/

---

## The Problem

**~1 billion people (16% of the world's population) live with significant disability**, many neurodevelopmental or cognitive in nature. This includes:

-   **10-15% of the population** has neurodivergent conditions (autism, ADHD, dyslexia, dyscalculia)
-   Difficulty with money concepts, arithmetic, and time management
-   Problems with multi-step instructions, complex forms, and organization
-   **Result:** Banking apps become a source of major anxiety and avoidance

### Real Barriers

-   Complex forms, small fonts, inflexible interfaces
-   Lost passwords, forgotten payment dates
-   Fear of making costly mistakes
-   No immediate help when confused

## Our Solution

EasyFocus Assistant provides **adaptive levels of support** based on user preference and confidence:

### Support Levels

**1. Payment assistant chat**

-   Conversational AI guides you through transactions
-   Natural language interaction: "I want to send €50 to John"
-   Asks clarifying questions to gather all required information
-   Remembers context from previous messages
-   Speech-to-text for hands-free banking

**2. Step-by-step explanations**

-   AI chatbot guides through every action
-   Speech-to-text for easier input
-   Visual feedback with emojis and arrows
-   Photo-based invoice parsing

**3. Quality checks only**

-   Checks unusual behavior (anomaly detection)
-   Validates amounts, account numbers, recipient names
-   Proactive warnings before mistakes
-   Comparison with historical transactions

### Proactive Features

-   **Payment Reminders:** Detects recurring payments (phone bills, rent) and asks for confirmation
-   **Offline Mode:** Saves transactions when connection drops, reminds user to go online
-   **Biometric Login:** Face ID/fingerprint—no passwords to lose
-   **Smart Search:** Chat with your banking data and get conversational answers with transaction details.

---

## Why This Matters

Accessibility features often become mainstream innovations:

| Feature               | Original Purpose           | Mainstream Use             | Market Size                 |
| --------------------- | -------------------------- | -------------------------- | --------------------------- |
| **Voice Recognition** | Motor disabilities         | Siri, Alexa, transcription | $14.8B → $61.3B (2024-2033) |
| **Audiobooks**        | Visual impairments         | Entertainment, learning    | $2B+ (2023)                 |
| **Speech-to-text**    | Communication disabilities | Meeting notes, captions    | Global standard             |

Our features help neurodivergent users today—and everyone tomorrow.

### Legal & Ethical Foundation

**UN Convention on Rights of Persons with Disabilities (CRPD):**

> **Article 2 - Definitions:**
>
> -   **"Reasonable accommodation"** requires apps to be usable without disproportionate burden
> -   **"Universal design"** means products work for all people without specialized adaptation

---

## Project Structure

**Backend (/backend)**

Core Python FastAPI application handling AI orchestration, authentication, and data processing.

```
backend/
├── src/backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── db.py                   # Database configuration
│   ├── seed.py                 # Database seeding utilities
│   │
│   ├── auth/                   # Authentication & authorization
│   │   ├── routes.py           # Auth API endpoints
│   │   ├── schemas.py          # Auth data models
│   │   └── utils.py            # Auth utilities (JWT, password hashing)
│   │
│   ├── chatbot/                # Payment assistant chatbot
│   │   ├── agents.py           # Chatbot agent logic
│   │   ├── service.py          # Chatbot orchestration
│   │   ├── llm.py              # LLM integration
│   │   ├── mcp_client.py       # MCP server client
│   │   ├── routes.py           # Chatbot API endpoints
│   │   └── schemas.py          # Chatbot data models
│   │
│   ├── qa/                     # Question-answering system
│   │   ├── agents/             # Multi-agent system
│   │   │   ├── main_agent.py   # Main orchestrator agent
│   │   │   ├── rag_agent.py    # RAG-based retrieval agent
│   │   │   └── sql_agent.py    # SQL query generation agent
│   │   │
│   │   ├── rag/                # Retrieval-Augmented Generation
│   │   │   ├── retriever.py    # Vector search & retrieval
│   │   │   ├── create_embeddings.py  # Embedding generation
│   │   │   └── parse_transactions.py # Transaction parsing
│   │   │
│   │   ├── sql/                # SQL operations
│   │   │   └── crud.py         # Database CRUD operations
│   │   │
│   │   ├── tools/              # Agent tools
│   │   │   ├── rag_tool.py     # RAG tool for agents
│   │   │   └── sql_tool.py     # SQL tool for agents
│   │   │
│   │   ├── chatbot_service.py  # QA service orchestration
│   │   ├── memory.py           # Conversation memory
│   │   └── routes.py           # QA API endpoints
│   │
│   ├── transactions/           # Transaction management
│   │   ├── routes.py           # Transaction API endpoints
│   │   ├── schemas.py          # Transaction data models
│   │   ├── services.py         # Transaction business logic
│   │   └── examples.py         # Sample transaction data
│   │
│   ├── utils/                  # Utility functions
│   │   ├── routes.py           # Utility API endpoints
│   │   ├── schemas.py          # Utility data models
│   │   └── unusual_behavior.py # Anomaly detection
│   │
│   └── models/                 # Database models
│       └── README.md           # Model documentation
│
├── pyproject.toml              # Poetry dependencies
└── poetry.lock                 # Dependency lock file
```

**Frontend (/frontend)**

Modern Next.js application for user interface and interaction.

```
frontend/
├── app/                        # Next.js app directory
│   ├── page.tsx               # Homepage
│   ├── layout.tsx             # Root layout
│   └── globals.css            # Global styles
│
├── components/                 # React components
│   ├── ui/                    # Reusable UI components (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── dialog.tsx
│   │   └── ...                # Additional UI primitives
│   │
│   ├── login-screen.tsx       # Authentication interface
│   ├── dashboard-screen.tsx   # Main dashboard
│   ├── chatbot-screen.tsx     # Payment assistant chat
│   ├── qa-chatbot-screen.tsx   # Smart search interface
│   ├── send-money-page.tsx    # Transaction interface
│   ├── transaction-details.tsx # Transaction view
│   ├── ai-helper-popup.tsx    # AI assistance overlay
│   ├── payment-suggestion-popup.tsx # Payment suggestions
│   └── ...                    # Additional feature components
│
├── hooks/                      # Custom React hooks
│   ├── use-mobile.ts          # Mobile detection
│   └── use-toast.ts           # Toast notifications
│
├── lib/                        # Utility libraries
│   ├── api.ts                 # API client functions
│   └── utils.ts               # Helper functions
│
├── public/                     # Static assets
│   └── Commerzbank-logo.png   # Brand assets
│
├── package.json                # NPM dependencies
└── next.config.ts             # Next.js configuration
```

**MCP Server (/mcp_server)**

Model Context Protocol server for tool integration.

```
mcp_server/
├── server.py                   # MCP server entry point
├── tools.py                    # MCP tool definitions
├── database.py                 # Database operations
├── schemas.py                  # Data schemas
├── app.py                      # Application setup
├── Dockerfile                  # Container configuration
└── pyproject.toml              # Poetry dependencies
```

**Shared (/shared)**

Shared code and models across services.

```
shared/
├── database.py                 # Shared database configuration
└── models/                     # Shared data models
    ├── user.py                # User model
    ├── transaction.py         # Transaction model
    └── person_to_contact.py   # Contact model
```

---
