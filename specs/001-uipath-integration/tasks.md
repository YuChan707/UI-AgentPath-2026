---
description: "Tasks to complete the OnLooker pipeline and connect it to UiPath"
---

# Tasks: Complete OnLooker pipeline + UiPath integration

**Input**: [spec.md](spec.md), [plan.md](plan.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: US1 (analysis flow) · US2 (UiPath) · US3 (operate)
- Paths are repo-relative.

## Already done (context, do not redo)

- [X] Pipeline scaffolded: `embeding_service/`, `features_extractor/`,
  `audience_settings/`, `develop_analysis/` (self-contained containers + Dapr).
- [X] Schema: `products`, `audience_responses`, `product_analysis` in
  `postgresql-db/init.sql`. Contracts in `dtos/messages.py`.
- [X] **Async Ollama**: concurrent embeddings (`embeding_service/embed.py`) and
  native `ainvoke` agents, bounded by `OLLAMA_NUM_PARALLEL`.
- [X] UI server routes: `ui-onlooker/app/api/documents/upload/route.ts`,
  `app/api/pipeline/status/route.ts`, `lib/{db,dapr,api}.ts`.

---

## Phase 1: Finish the UI I/O slice (US1)

- [ ] T001 [US1] Add `pg` + `@types/pg` to `ui-onlooker/package.json` and run `npm install`.
- [ ] T002 [US1] Add server env to `ui-onlooker/.env.local` (`DATABASE_URL`,
      `DAPR_HTTP_PORT`, `PUBSUB_NAME`, `REDIS_HOST`); mirror in `.env.example`.
- [ ] T003 [US1] Add `ui-onlooker` + `ui-onlooker-dapr` (daprd sidecar, app-port 3000,
      mount `./ui-onlooker/components`) to `docker-compose.yml`; add `DATABASE_URL`/
      `PUBSUB_NAME`/`DAPR_HTTP_PORT` env to the `ui-onlooker` service.
- [ ] T004 [P] [US1] Rebuild the settings form (`ui-onlooker/components/ProjectSettings.tsx`
      + page) to the mockup: audience_type, environment, area, **audience_size**
      (Global/Big/Small/Local), **gender_dstn**, **age_dstn** slider, **main_goal**,
      and the 4 insight checkboxes. Map to the `AudienceSettings`/`InsightSelection` keys.
- [ ] T005 [US1] Wire upload to `lib/api.ts#uploadDocument` (drop the old
      `${API_BASE}/document/upload` call in `components/ChatBoxMode.tsx`); store
      `id_product` in `lib/store.ts`.
- [ ] T006 [US1] Add result polling: after upload, poll `lib/api.ts#getPipelineStatus`
      and render progress + final analysis (DashboardView / a results panel).
- [ ] T007 [P] [US1] Update `ui-onlooker/README.md` with the I/O routes + run instructions.

## Phase 2: End-to-end local verification (US1, US3)

- [ ] T008 [US3] `docker compose up -d` (infra+ui) then `docker compose --profile pipeline up --build`.
- [ ] T009 [US3] Pull models: `ollama pull llama3.1` and `ollama pull nomic-embed-text`
      (or `make model-pull`).
- [ ] T010 [US1] Upload a sample doc; verify the chain: `embedding.progress` →
      `features.ready` → `audience.ready` → `analysis.ready`; check rows in
      `products` / `audience_responses` / `product_analysis` and the Chroma collection.
- [ ] T011 [P] [US3] Tune `OLLAMA_NUM_PARALLEL` per box; confirm embeddings + reactions
      run concurrently (not serially).

## Phase 3: Connect the agents to UiPath (US2)

- [ ] T012 [US2] Install the UiPath CLI in each agent env (`pip install uipath uipath-langchain`).
- [ ] T013 [P] [US2] `uipath init` in `features_extractor/`, `audience_settings/`,
      `develop_analysis/` (generates `entry-points.json` from each `langgraph.json`).
- [ ] T014 [US2] Configure the agent model to use **local Ollama** under UiPath
      (confirm `langchain_openai.ChatOpenAI` base_url works packed, or switch to the
      UiPath chat-model wrapper pointing at Ollama). Verify against UiPath docs.
- [ ] T015 [US2] Set Orchestrator connection (`UIPATH_URL`, `UIPATH_ACCESS_TOKEN`,
      `UIPATH_FOLDER`) in each agent `.env`; `uipath auth` if required.
- [ ] T016 [P] [US2] `uipath pack` each agent → `.nupkg`; publish to UiPath Orchestrator.
- [ ] T017 [US2] Decide the run topology: (a) Dapr subscriber calls the local graph
      (current), or (b) a Dapr→UiPath bridge triggers the published agent via the
      Orchestrator API and waits for completion. Document the choice in each README.
- [ ] T018 [US2] Trigger one agent from UiPath Orchestrator and confirm it runs against
      local Ollama and writes to Postgres; verify monitoring/traces in UiPath.

## Phase 4: Hardening (US3)

- [ ] T019 [P] [US3] Add a `pipeline_events` (or reuse `ingestion_events`) write per
      `ServiceProgress` so the UI shows real-time stage status from the DB.
- [ ] T020 [US3] Idempotency + retries: make each handler safe to re-deliver (Dapr
      at-least-once); upsert on re-run; dead-letter on repeated failure.
- [ ] T021 [P] [US3] Structured logging + correlation by `id_product` across services.
- [ ] T022 [US3] `make vendor-all` in CI to prevent contract drift; basic smoke test
      that builds each container from its own folder (self-containment check).

## Dependencies

- Phase 1 (T001–T007) before Phase 2.
- Phase 2 (local working) before Phase 3 (UiPath) — agents must work locally first.
- T012–T013 before T014–T018. T017 gates T018.
- Phase 4 can start once Phase 2 passes; T019 unblocks richer UI status (T006).

## Parallel example

`T004`, `T007`, `T011`, `T013`, `T016`, `T019`, `T021` are marked `[P]` — different
files/services, safe to run concurrently within their phase.
