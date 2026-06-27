# Implementation Plan: Complete OnLooker pipeline + UiPath integration

**Branch**: `001-uipath-integration` | **Date**: 2026-06-27 | **Spec**: [spec.md](spec.md)

## Technical Context

**Languages**: Python 3.11 (services/agents), TypeScript/Next.js 16 (UI).
**Frameworks**: FastAPI + Dapr (subscribers), LangGraph + `uipath-langchain`
(agents), Next.js App Router (UI), `pg` (UI DB access).
**LLM**: local **Ollama** (`llama3.1`, `nomic-embed-text`) — no cloud. Async via
`ainvoke` / concurrent `httpx` bounded by `OLLAMA_NUM_PARALLEL`.
**Infra**: Postgres + ChromaDB + Redis (Dapr pub/sub) + Ollama as stock images;
each service is a self-contained top-level folder; run via `docker-compose`
(`--profile pipeline`).
**UiPath**: Python Agent SDK (`uipath`, `uipath-langchain`); `uipath init` /
`uipath pack`; Orchestrator connection via `UIPATH_URL` / `UIPATH_ACCESS_TOKEN`
/ `UIPATH_FOLDER`.

## Constitution Check

- Self-contained containers (vendored `contracts.py`, own build context): PASS.
- No cloud LLM (local Ollama only): PASS.
- Single source of truth for contracts (`dtos/`, re-vendored via `make vendor-all`): PASS.

## Project Structure (relevant)

```
ui-onlooker/        # Next.js — I/O only (app/api/documents/upload, app/api/pipeline/status)
embeding_service/   # extract+clean+chunk -> Ollama embeddings -> Chroma
features_extractor/ # UiPath agent: Chroma -> features (Ollama)
audience_settings/  # UiPath agent: group x feature reactions (Ollama, bounded)
develop_analysis/   # UiPath agent: aggregate -> selected insights (Ollama)
dtos/messages.py    # Dapr contracts (canonical)
postgresql-db/      # init.sql schema + apply_schema.py
docker-compose.yml  # default = infra+ui ; --profile pipeline = the 4 services + daprd sidecars
```

## Phasing

1. Finish the UI I/O slice (deps, env, compose sidecar, wire form/dashboard).
2. Verify end-to-end locally (compose up + ollama models + a real upload).
3. Connect the agents to UiPath (init/pack/publish + Orchestrator config).
4. Hardening (retries, idempotency, observability).

See [tasks.md](tasks.md) for the actionable breakdown.
