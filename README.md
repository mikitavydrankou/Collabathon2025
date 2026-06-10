<div align="center">

# EasyFocus Assistant

### AI banking companion for everyone who needs a helping hand

Adaptive, conversational banking for neurodivergent and cognitively diverse users —
chat your way through payments, get step-by-step guidance, catch mistakes before they happen.

![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=nextdotjs&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Postgres 17](https://img.shields.io/badge/PostgreSQL-17-4169e1?logo=postgresql&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-KRaft-231f20?logo=apachekafka&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Helm-326ce5?logo=kubernetes&logoColor=white)
![Argo CD](https://img.shields.io/badge/Argo%20CD-GitOps-ef7b4d?logo=argo&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-GKE-7b42bc?logo=terraform&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Grafana-e6522c?logo=prometheus&logoColor=white)

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

---

## Architecture

The hackathon monolith was cut into **microservices** and built out into a production-style
platform: async messaging, Kubernetes with GitOps, full observability, and infrastructure as code.

```
                              ┌──────────────────────────────┐
        client ──HTTPS──▶     │   Gateway API edge (L7 LB)    │     TLS, single origin
                              │   kind: Envoy · GKE: gke-l7   │     path-split routing
                              └───────────────┬──────────────┘
                       ┌──────────────────────┼───────────────────────┐
                       ▼ /                     ▼ /auth /qa /chatbot ... ▼
                ┌────────────┐          ┌──────────────┐        (nginx app-gateway)
                │  frontend  │          │   backends   │
                │  Next.js   │          │  auth · tx   │
                └────────────┘          │  chatbot·qa  │
                                        │  + mcp tools │
                                        └──────┬───────┘
                   transactions.created        │ produce
                          Kafka  ◀─────────────┘
                       (KRaft, 1 broker)
                         │           │  2 consumer groups
            ┌────────────┘           └────────────┐
            ▼                                      ▼
   ┌──────────────────┐                  ┌──────────────────┐
   │ embedding-worker │──▶ Chroma (RAG)  │  anomaly-worker  │──▶ Postgres flag
   └──────────────────┘                  └──────────────────┘
            ▲ outbox-relay (transactional outbox → Kafka)
            │
   ┌──────────────────┐   shared Postgres 17 · Redis (LLM cap + rate-limit)
   │  all services    │──────────────────────────────────────────────
   └──────────────────┘
```

- **Services** (own `pyproject.toml` + Dockerfile, share an installable `shared-lib/` via poetry path-dep):
  `auth-svc`, `transactions-svc`, `chatbot-svc`, `qa-svc`, `mcp` · workers: `embedding-worker`,
  `anomaly-worker`, `outbox-relay` · `frontend` (Next.js).
- **Async core**: `transactions.created` events flow through a **transactional outbox** → **Kafka**
  → two consumer groups (embed into Chroma for RAG; score for anomalies, flag in Postgres).
- **Edge**: Gateway API (HTTPRoute), single origin — one host serves UI + API, no CORS.

Full service map + config reference: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Platform / DevOps

| Concern        | Tooling                                                                       |
| -------------- | ----------------------------------------------------------------------------- |
| Orchestration  | **Kubernetes** — one umbrella **Helm** chart (`deploy/helm/easyfocus`)        |
| GitOps         | **Argo CD** — cluster syncs the app + monitoring straight from this repo      |
| Messaging      | **Kafka** (KRaft, single broker) + kafka-ui + kafka-exporter                  |
| Observability  | **Prometheus + Grafana** (RED dashboard), **Loki** logs, **Tempo** + OTel traces, alerts → Telegram |
| CI/CD          | **GitHub Actions** — build only changed images, **Trivy** CVE scan, pytest suite |
| Cloud / IaC    | **Terraform** → **GKE Autopilot**, Artifact Registry, VPC, WIF (keyless CI)   |
| Edge           | Gateway API — Envoy (kind) / managed L7 LB (GKE), TLS via cert-manager + Let's Encrypt |

## Quick start

### Local (Docker Compose) — fastest look

```bash
git clone https://github.com/mikitavydrankou/Collabathon2025.git
cd Collabathon2025
cp .env.example .env        # set DB creds + OPENAI_API_KEY
docker compose up -d --build
```

Open **http://localhost:3000**.

### Kubernetes (kind) — the real stack, GitOps

```bash
# needs WSL with docker + kind + kubectl + helm
# create deploy/helm/easyfocus/values-local.yaml with your creds (see deploy/README.md)
bash deploy/gitops-up.sh    # kind + MetalLB + Envoy Gateway + Argo CD + apps, all idempotent
bash deploy/cluster.sh pf   # port-forward Grafana / Prometheus / Argo + print URLs/creds
```

### Cloud (GKE) — Terraform

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars   # set project_id
bash apply.sh                                   # GKE Autopilot + Artifact Registry + WIF + static IP
# then deploy with the GKE overlay + HTTPS — see infrastructure/README.md and deploy/gke/README.md
```

> [!TIP]
> Set `OPENAI_API_KEY` before building — the chatbot and QA agents need it for LLM calls and embeddings.

## Observability

The umbrella chart ships a custom Grafana dashboard (`easyfocus-overview`): RED metrics per service,
error ratio, Kafka consumer lag per group, Postgres connections, and a traffic overview — plus Loki
log correlation and Tempo distributed traces (context propagated through the Kafka outbox).

<!-- Drop a dashboard screenshot at docs/img/grafana-overview.png to render it here: -->
<!-- ![Grafana — EasyFocus overview](docs/img/grafana-overview.png) -->

## Stack

**Frontend** Next.js 16 · React 18 · Tailwind · shadcn/ui
**Backend** FastAPI · SQLAlchemy 2 · LangChain + OpenAI · ChromaDB RAG · JWT auth
**Data/Async** PostgreSQL 17 · Redis · Kafka (KRaft) · Chroma · transactional outbox
**Platform** Kubernetes · Helm · Argo CD · Gateway API · Prometheus/Grafana/Loki/Tempo · Terraform/GKE · GitHub Actions + Trivy

---

<div align="center"><sub>Built so banking works for everyone — clear, calm, mistake-proof.</sub></div>
