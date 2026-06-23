# OnLooker — AI Presentation Intelligence

OnLooker is an event-driven AI assistant that analyses presentations, documents, and written content through a Dapr microservice pipeline. Upload a `.pptx`, `.docx`, or `.pdf` in **Chat Box** mode and get structured audience simulation, content feature extraction, and a final insight report — all powered by local LLMs via Ollama, with no external API keys required.

---

## Architecture overview

```
Upload ──► [backend]
              │ publishes document-submitted
              ▼
     [embedding-service]   ← embeds chunks into ChromaDB (nomic-embed-text)
              │ publishes embedding-complete
              ▼
     [features-extractor]  ← extracts 8-12 content features (llama3.2)
              │ publishes features-extracted
              ▼
     [audience-settings]   ← simulates per-feature audience reactions (llama3.2)
              │ publishes audience-processed
              ▼
     [develop-analysis]    ← generates strengths / weaknesses / potential / report (llama3.2)
              │ publishes report-ready
              ▼
     [backend] ◄── UI polls GET /pipeline/{run_id}/report
```

All pub/sub runs through **Redis Streams** via the Dapr `onlooker-pubsub` component.  
Raw files are stored in **PostgreSQL bytea** (no external blob storage).  
Vector embeddings live in **ChromaDB**.

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Docker + Docker Compose | 24+ | Runs every service |
| Ollama | latest | Must be running on the host before `docker compose up` |
| Node.js | 20+ | Only needed for non-Docker frontend dev |

> **No external API keys required.** All LLM inference is handled locally by Ollama.

### Pull the required Ollama models first

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

---

## Quick Start (Docker Compose)

```bash
git clone <repo-url>
cd UI-AgentPath-2026

docker compose up --build
```

| Service | URL |
|---|---|
| Frontend (Next.js) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |
| Dapr Dashboard | http://localhost:8080 |

The first startup seeds the PostgreSQL schema automatically via `infra/postgres/`.

---

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt

# Minimal .env for local dev
echo DATABASE_URL=postgresql+asyncpg://onlooker:onlooker@localhost:5432/onlooker > .env
echo CHROMA_HOST=localhost >> .env
echo OLLAMA_HOST=http://localhost:11434 >> .env

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd ui-onlooker
npm install
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
npm run dev
```

---

## API Endpoints

### Document upload & pipeline

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/document/upload` | Upload a file — stores in PostgreSQL, fires Dapr pipeline |
| `GET` | `/pipeline/{run_id}/status` | Poll pipeline progress (5 stages) |
| `GET` | `/pipeline/{run_id}/report` | Fetch final report (202 if not ready) |

#### `POST /document/upload` — form fields

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | required | `.pptx`, `.docx`, or `.pdf` |
| `session_id` | string | `"chat"` | Session identifier |
| `audience_environment` | string | `"Professional setting"` | Audience context |
| `audience_size` | int | `100` | Simulated audience size |
| `age_dstn` | string | `"25-45"` | Age distribution range |
| `detect_strengths` | bool | `true` | Include strengths section in report |
| `detect_weaknesses` | bool | `true` | Include weaknesses section |
| `detect_potential` | bool | `true` | Include potential section |
| `general_report` | bool | `true` | Include general overview |

#### Pipeline status values

```
submitted → embedding_complete → features_extracted → audience_processed → report_ready
```

### Feedback (synchronous, no pipeline)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/feedback/settings` | List all 6 feedback personas |
| `POST` | `/feedback/generate` | Generate structured feedback for a text snippet |
| `GET` | `/feedback/available-perspectives` | Personas grouped by category |

#### `POST /feedback/generate` — request body

```json
{
  "text": "Your content here...",
  "feedback_setting": "startup",
  "complexity": "medium",
  "environment": "professional"
}
```

#### 6 feedback personas

| Key | Location | Culture | Best for |
|---|---|---|---|
| `academic_us` | United States | Western | Research, evidence-based content |
| `academic_europe` | Europe | Western | Theoretical, philosophical content |
| `business_uk` | United Kingdom | Western | Formal, diplomatic content |
| `business_asia` | Asia | Eastern | Relationship-focused, consensus-building |
| `startup` | Global | Innovation | Fast-paced, disruptive ideas |
| `community` | Diverse | Multicultural | Practical, accessible content |

### Analysis & session

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze/chunk` | Direct coaching feedback on a text chunk |
| `POST` | `/session/start` | Create a session |
| `GET` | `/session/{id}` | Fetch session metadata |
| `GET` | `/health` | DB + version check |

---

## Folder structure

```
UI-AgentPath-2026/
│
├── docker-compose.yml               ← all services + Dapr sidecars
├── ARCHITECTURE_CHANGES.txt         ← before/after migration reference
│
├── dapr/
│   ├── components/
│   │   ├── pubsub.yaml              ← Redis Streams pub/sub component
│   │   └── statestore.yaml          ← Redis state store component
│   └── config/
│       └── config.yaml              ← Dapr tracing + feature flags
│
├── infra/
│   └── postgres/
│       ├── 01_init.sql              ← sessions, events, analytics tables
│       └── 02_pipeline.sql          ← documents, pipeline_runs, status_log
│
├── services/                        ← Dapr microservices (Python / FastAPI)
│   ├── embedding-service/
│   │   └── main.py                  ← PDF/PPTX/DOCX → chunks → ChromaDB
│   ├── features-extractor/
│   │   └── main.py                  ← ChromaDB samples → content features (LLM)
│   ├── audience-settings/
│   │   └── main.py                  ← per-feature audience simulation (LLM)
│   └── develop-analysis/
│       └── main.py                  ← final report generation (LLM)
│
├── backend/                         ← FastAPI gateway
│   ├── main.py                      ← app entry, router registration, Dapr subscribe
│   ├── database.py                  ← async SQLAlchemy engine
│   │
│   ├── routes/
│   │   ├── health.py                ← GET /health
│   │   ├── session.py               ← session CRUD
│   │   ├── analyze.py               ← POST /analyze/chunk (direct Ollama)
│   │   ├── document.py              ← POST /document/upload
│   │   ├── feedback.py              ← POST /feedback/generate
│   │   └── pipeline.py              ← GET /pipeline/{id}/status|report
│   │
│   ├── services/
│   │   ├── chroma_service.py        ← ChromaDB HTTP client + seed
│   │   ├── document_service.py      ← text extraction (pypdf, python-pptx, python-docx)
│   │   └── pptx_generator.py        ← branded PPTX report builder
│   │
│   └── models/
│       └── database.py              ← SQLAlchemy ORM models
│
└── ui-onlooker/                     ← Next.js 14 frontend
    ├── app/
    │   ├── page.tsx                 ← root page
    │   ├── layout.tsx               ← global providers
    │   └── globals.css              ← design tokens + Tailwind
    │
    ├── components/
    │   ├── ChatBoxMode.tsx          ← document upload + chat interface
    │   ├── AnalysisGraphPanel.tsx   ← score visualisation
    │   ├── DashboardView.tsx        ← analytics view
    │   └── ProjectSettings.tsx      ← audience context form
    │
    └── lib/
        ├── store.ts                 ← Zustand global state
        └── utils.ts                 ← cn() and helpers
```

---

## Dapr pub/sub topics

| Topic | Publisher | Consumer | Payload |
|---|---|---|---|
| `document-submitted` | backend | embedding-service | `{run_id, document_id, file_extension, audience_config, insight_flags}` |
| `embedding-complete` | embedding-service | features-extractor | `{run_id, collection_name, chunk_count}` |
| `features-extracted` | features-extractor | audience-settings | `{run_id, features}` |
| `audience-processed` | audience-settings | develop-analysis | `{run_id, metrics}` |
| `report-ready` | develop-analysis | — | `{run_id}` |
| `pipeline-status` | all services | backend | `{run_id, stage, detail}` |

---

## Ports reference

| Service | Port |
|---|---|
| Frontend | 3000 |
| Backend | 8000 |
| Backend Dapr sidecar | 3510 |
| ChromaDB | 8001 |
| Ollama | 11434 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Dapr placement | 50005 |

---

## Customise feedback personas

Personas are defined inline in `backend/routes/feedback.py` in the `FEEDBACK_SETTINGS` dict. Add a new key:

```python
FEEDBACK_SETTINGS["your_key"] = {
    "group":               "business",
    "location":            "Your City",
    "culture":             "Your Culture",
    "communication_style": "Direct and concise",
    "values":              "Efficiency, results",
    "concerns":            ["ROI", "timeline", "risk"],
}
```

Restart the backend — the new persona appears automatically in `/feedback/settings` and the UI dropdown.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Ollama model not found | Run `ollama pull llama3.2` and `ollama pull nomic-embed-text` on the host |
| Pipeline stalls at `submitted` | Check embedding-service logs: `docker compose logs embedding-service` |
| Dapr sidecar not starting | Ensure `dapr-placement` container is healthy before other services |
| ChromaDB connection refused | Wait ~10 s after `docker compose up` for ChromaDB to initialise |
| PostgreSQL init fails | Delete the `pgdata` volume and restart: `docker compose down -v && docker compose up` |
