# OnLooker — Synthetic Audience for Product Documents

OnLooker takes a **product document** (a spec, deck, or report), simulates how a
**synthetic audience** reacts to each of its features, and produces an analysis
(strengths, weaknesses, potential, general report). It runs as **Docker
microservices intercommunicated through Dapr** (Redis pub/sub) — the UI only
sends and receives information; it never talks to an LLM directly.

> **Migration in progress.** The project is pivoting from a monolithic
> presentation-coaching backend to this microservices pipeline. The old
> `backend/` monolith has been removed; services are being built one vertical
> slice at a time. All LLM work is **local Ollama (llama3.1)** — no cloud.

## Architecture

```
ui-onlooker ──(document.uploaded {id_product, doc_type})──► embeding-service
   (I/O only)                                                  extract+clean+chunk
        ▲                                                      → Ollama embeddings
        │  progress/results                                    → ChromaDB
        │                                                          │ features.extract
        │                                                          ▼
        │                                                   features-extractor
        │                                                   (Chroma + LLM → features)
        │                                                          │ features.ready
        │                                                          ▼
        │                                                    audience-settings
        │                                                   (group reactions per feature,
        │                                                    async Ollama → scores in DB)
        │                                                          │ audience.ready
        │                                                          ▼
        └──────────────────────────────────────────────────  develop-analysis
                                                              (strengths/weakness/
                                                               potential/general report)
```

Shared infra: **PostgreSQL** (entities + documents), **ChromaDB** (vectors),
**Ollama** (LLM + embeddings), **Redis** (Dapr pub/sub).

## Top-level layout (microservices + shared)

| Folder | Role |
|---|---|
| [`ui-onlooker/`](ui-onlooker/) | Next.js UI — I/O only (upload, settings, results) |
| [`embeding_service/`](embeding_service/) | document → clean text → page chunks → Ollama embeddings → ChromaDB |
| `features_extractor/` | *(to build)* Chroma collection + LLM → product features |
| `audience_settings/` | *(to build)* each audience group reacts to each feature |
| `develop_analysis/` | *(to build)* selected insights from the reactions |
| [`data_ingestor/`](data_ingestor/) | batch: US Census ACS5 → location JSON |
| [`data_processor/`](data_processor/) | batch: location JSON → synthetic audience (prompts as `PromptSpec`) |
| [`dtos/`](dtos/) | shared contracts — incl. Dapr messages ([`dtos/messages.py`](dtos/messages.py)) |
| [`agent_prompts/`](agent_prompts/) | salvaged, versionable prompt artifacts |
| [`postgresql-db/`](postgresql-db/) | Postgres schema (`init.sql`) + `apply_schema.py` |

## Run

<<<<<<< HEAD
=======
---

## Folder structure

```
AGENTS-LEAGUE-HACKATHON-2026/
│
├── .env                              ← secrets (never commit)
├── .env.example                      ← safe template with placeholders
├── requirements.txt                  ← Python dependencies
├── onlooker.db                       ← SQLite dev database (auto-created)
│
├── backend/                          ← FastAPI application
│   ├── main.py                       ← app entry point, router registration
│   ├── database.py                   ← async engine setup
│   │
│   ├── agents/                       ← AI agent implementations
│   │   ├── orchestrator.py           ← fans out to all agents in parallel
│   │   ├── speech.py                 ← pace / filler words / clarity (no LLM)
│   │   ├── audience.py               ← Llama persona reactions
│   │   ├── coaching.py               ← Llama live coaching tips
│   │   ├── cultural.py               ← ChromaDB RAG + Llama cultural flags
│   │   └── vision.py                 ← Llama 4 Scout screen-frame analysis
│   │
│   ├── routes/                       ← API route handlers
│   │   ├── health.py                 ← GET /health
│   │   ├── session.py                ← session CRUD + report generation
│   │   ├── stream.py                 ← WebSocket /ws/stream (Alive mode)
│   │   ├── analyze.py                ← POST /analyze/chunk (Chat Box)
│   │   └── document.py               ← POST /document/upload
│   │
│   ├── services/                     ← shared service layer
│   │   ├── chroma_service.py         ← ChromaDB seed + cosine query
│   │   ├── document_service.py       ← PPTX / DOCX / PDF text extraction
│   │   ├── ingestion_service.py      ← event + analytics persistence
│   │   ├── pptx_generator.py         ← branded PPTX report builder
│   │   └── email_service.py          ← follow-up email draft (Llama)
│   │
│   └── models/
│       └── database.py               ← SQLAlchemy async ORM models
│
├── ui-onlooker/                      ← Next.js frontend
│   ├── app/
│   │   ├── page.tsx                  ← root page: Dashboard / Analysis views
│   │   ├── layout.tsx                ← global fonts + providers
│   │   └── globals.css               ← design tokens + Tailwind base
│   │
│   ├── components/
│   │   ├── AliveModeView.tsx         ← screen share, REC timer, video AI feed
│   │   ├── ChatBoxMode.tsx           ← document upload + AI chat interface
│   │   ├── DashboardView.tsx         ← analytics / engagement visualizer
│   │   ├── ProjectSettings.tsx       ← audience context form → POST /session/start
│   │   ├── AnalysisGraphPanel.tsx    ← analysis graph visualizer
│   │   ├── DocumentsPanel.tsx        ← uploaded documents panel
│   │   ├── FeedbackFeed.tsx          ← multi-perspective feedback feed
│   │   └── ui/                       ← shadcn/ui primitives
│   │       ├── badge.tsx
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── progress.tsx
│   │       └── select.tsx
│   │
│   ├── lib/
│   │   ├── store.ts                  ← Zustand store (session, events, metrics)
│   │   ├── useWebSocket.ts           ← singleton WS hook (connect / sendFrame)
│   │   └── utils.ts                  ← cn() and shared helpers
│
├── dtos/                             ← shared Pydantic DTOs
│   ├── analytics.py
│   ├── audience.py
│   ├── reports.py
│   ├── data_ingestors.py
│   └── data_processors.py
│
├── data_processor/                   ← Data Commons fetch + profile builder
│   ├── fetch_data_commons.py
│   └── build_profiles.py
│
├── data_ingestor/                    ← one-time DB seed script
│   └── seed_database.py
│
└── containers_env/                   ← Docker Compose (optional for prod)
    ├── embeds-db/                    ← ChromaDB container config
    └── postgresql-db/                ← PostgreSQL container config
```

---

# Quick Start Guide - Feedback Agent

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Installation
Ensure all dependencies are installed:
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
```bash
cp .env.example .env          # fill in CENSUS_DATA_API; LLM is local Ollama

# Infra + UI
docker compose up -d

# + the product-pipeline microservices (with Dapr sidecars)
docker compose --profile pipeline up --build

# Pull the models once Ollama is up
ollama pull llama3.1
ollama pull nomic-embed-text
```

See each service's `README.md` for its own contract, topics, and env.

## Dapr message contracts

Defined in [`dtos/messages.py`](dtos/messages.py): `DocumentUploaded`,
`ServiceProgress`, `CollectionReady`, `AudienceSettings` (with documented
defaults), `InsightSelection`, `FeaturesReady`, `AudienceReady`, `AnalysisReady`.
Topics: `document.uploaded`, `embedding.progress`, `features.extract`,
`features.ready`, `audience.ready`, `analysis.ready`.

## Async Ollama

All Ollama access is **non-blocking and bounded by `OLLAMA_NUM_PARALLEL`**
(defaults to CPU count):

- **embeddings** ([embeding_service/embed.py](embeding_service/embed.py)) run
  concurrently via `asyncio.gather` + a semaphore (order preserved).
- **agents** (`features_extractor`, `audience_settings`, `develop_analysis`) use
  native async `graph.ainvoke` / `llm.ainvoke`; `audience_settings` fans out the
  group×feature reactions concurrently under the same semaphore.

## Roadmap / tasks

The plan to finish the system and **connect the agents to UiPath** is tracked
with spec-kit in [`specs/001-uipath-integration/`](specs/001-uipath-integration/)
(`spec.md`, `plan.md`, `tasks.md`).
