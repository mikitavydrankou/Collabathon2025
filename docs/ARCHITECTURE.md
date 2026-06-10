# Architecture

EasyFocus started as a hackathon monolith and was restructured into a
**microservices** platform: independent FastAPI services, async messaging over
Kafka, a Next.js frontend, an MCP tool server — deployed to Kubernetes via a Helm
chart and Argo CD GitOps, with full observability and Terraform-provisioned GKE.

```
                              ┌──────────────────────────────┐
        client ──HTTPS──▶     │   Gateway API edge (L7 LB)    │
                              │   kind: Envoy · GKE: gke-l7   │
                              └───────────────┬──────────────┘
                       ┌──────────────────────┼───────────────────────┐
                       ▼ /                     ▼ /auth /qa /chatbot ... ▼
                ┌────────────┐          ┌──────────────────┐   nginx app-gateway
                │  frontend  │          │  auth-svc        │   (path → service)
                │  Next.js   │          │  transactions-svc│
                │  :3000     │          │  chatbot-svc     │
                └────────────┘          │  qa-svc · mcp    │
                                        └────────┬─────────┘
                          produce on             │
                       transactions.created      ▼
                              ┌──────────── Kafka (KRaft, 1 broker) ───────────┐
                              │              2 consumer groups                 │
                              ▼                                                ▼
                     ┌──────────────────┐                          ┌──────────────────┐
                     │ embedding-worker │──▶ Chroma (vector RAG)    │  anomaly-worker  │──▶ Postgres flag
                     └──────────────────┘                          └──────────────────┘
       outbox-relay: transactional outbox in Postgres → Kafka (exactly-once-ish, no dual-write)

   shared Postgres 17  ·  Redis (OpenAI daily cap + gateway rate-limit)  ·  Chroma (embeddings)
```

## Services

Each service has its own `pyproject.toml` + `Dockerfile` and pulls a shared,
installable library (`shared-lib/`) via a poetry path-dependency. JWT is validated
locally in every service through a shared secret — no network hop to auth.

| Service             | Port   | Role                                                          |
| ------------------- | ------ | ------------------------------------------------------------ |
| `frontend`          | `3000` | Next.js 16 UI (React 18, Tailwind, shadcn/ui)                |
| `auth-svc`          | `8000` | Login, JWT issue, user lookup                                |
| `transactions-svc`  | `8000` | Transactions CRUD/stats, anomaly validation, outbox producer |
| `chatbot-svc`       | `8000` | Payment-assistant chat (LangChain agents, MCP client)        |
| `qa-svc`            | `8000` | Conversational search — RAG + SQL multi-agent                |
| `mcp`               | `8001` | Model Context Protocol tool server                           |
| `embedding-worker`  | —      | Kafka consumer → embeds transactions into Chroma             |
| `anomaly-worker`    | —      | Kafka consumer → scores transactions, flags in Postgres      |
| `outbox-relay`      | —      | Polls the Postgres outbox, publishes to Kafka               |
| `gateway`           | `8000` | nginx app-gateway, path-routes API prefixes to services      |

## Async / messaging

The transactional **outbox** pattern avoids the dual-write problem: a transaction
write and its event are committed in the same Postgres transaction (table
`OutboxEvent`); `outbox-relay` ships those rows to the Kafka topic
`transactions.created`. Two independent consumer groups react:

- **embedding-worker** → generates an embedding, upserts into Chroma (powers RAG search).
- **anomaly-worker** → scores the transaction, sets an anomaly flag surfaced in the UI.

OpenTelemetry trace context is propagated through the outbox into the Kafka
records, so a trace spans HTTP → outbox → worker in Tempo.

## Repository layout

```
services/<name>-svc/<name>_svc/   # hyphen dir, underscore package; entrypoint <name>_svc.main:app
workers/{embedding,anomaly}-worker/, workers/outbox-relay/
shared-lib/shared/                # app_factory, db, security, messaging, seed, migrations, tracing, usage, models
mcp_server/                       # MCP tool server
gateway/nginx.conf                # edge app-gateway
frontend/                         # Next.js app
migrate/ · seed/                  # one-shot Jobs (Alembic migrate, DB seed)
deploy/                           # helm/ · argo/ · gke/ · kind/ · metallb/ + bootstrap scripts
infrastructure/                   # Terraform: GKE Autopilot, Artifact Registry, VPC, WIF, static IP
tests/                            # pytest suite (security, usage fail-open, anomaly validation)
```

## Deployment

- **Helm** — one umbrella chart `deploy/helm/easyfocus` renders the whole stack
  (~30 objects). `values.yaml` = base (kind), `values-gke.yaml` = GKE overlay,
  `values-local.yaml` = gitignored secrets.
- **Argo CD** — the cluster syncs the app + monitoring stack from this repo
  (`deploy/argo/`). `deploy/gitops-up.sh` bootstraps the bits Argo can't
  (cluster, MetalLB, Gateway CRDs, Argo itself, out-of-band Secrets).
- **Edge** — Gateway API HTTPRoute, single origin (one host serves UI + API,
  path-split, no CORS). Envoy Gateway on kind; managed L7 LB (`gke-l7-*`) on GKE,
  TLS terminated with a cert-manager + Let's Encrypt cert (`deploy/gke/`).
- **Cloud** — Terraform (`infrastructure/`) provisions GKE Autopilot, Artifact
  Registry, a dedicated VPC, a reserved edge IP, and Workload Identity Federation
  for keyless CI image push.

## Observability

- **Metrics** — Prometheus (kube-prometheus-stack) scrapes per-service `/metrics`
  (prometheus-fastapi-instrumentator) via ServiceMonitors, plus kafka-exporter
  (consumer lag) and postgres-exporter. Grafana dashboard `easyfocus-overview`:
  RED per service, error ratio, Kafka lag per group, Postgres connections, RPS.
- **Logs** — Loki + promtail, correlated in Grafana.
- **Traces** — Tempo + OpenTelemetry, context propagated through the Kafka outbox.
- **Alerts** — PrometheusRule → Alertmanager → Telegram.

## Configuration

Non-secret config is mounted into every service via a ConfigMap (`config:` in
`values.yaml`); secrets (`DATABASE_PASSWORD`, `JWT_SECRET`, `OPENAI_API_KEY`)
come from the gitignored `values-local.yaml`. For Docker Compose, all config
lives in `.env` (copy from `.env.example`).

| Variable             | Purpose                                            |
| -------------------- | -------------------------------------------------- |
| `DATABASE_*`         | PostgreSQL name / user / password                  |
| `JWT_SECRET`         | Shared HMAC secret — every service validates JWT locally |
| `OPENAI_API_KEY`     | OpenAI key for LLM + embeddings                    |
| `KAFKA_BROKERS`      | Kafka bootstrap (`kafka:9092`)                     |
| `REDIS_URL`          | Redis for the OpenAI daily cap + rate-limit        |
| `CHROMA_HOST/PORT`   | Vector store for RAG                               |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Tempo OTLP endpoint (empty disables tracing) |

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
