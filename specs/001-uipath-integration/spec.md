# Feature Specification: Complete OnLooker pipeline + UiPath integration

**Feature Branch**: `001-uipath-integration`
**Status**: Draft
**Created**: 2026-06-27

## Summary

Finish the OnLooker product-analysis pipeline (UI I/O → embeding-service →
features-extractor → audience-settings → develop-analysis, over Dapr, all local
Ollama) and **connect the three LLM agents to UiPath** so they run as UiPath
Agents (Python Agent SDK / `uipath-langchain`), deployable to and monitored by
UiPath Orchestrator, while still runnable locally via docker-compose.

## User Scenarios

### US1 — Upload a product document and get an analysis (P1)
A user uploads a `.pdf/.pptx/.docx/.txt/.md`, configures the audience + insights,
and receives strengths/weaknesses/potential/report driven by a synthetic
audience reacting to the product's features. Everything runs locally.

### US2 — Run the LLM agents as UiPath Agents (P1)
The features-extractor, audience-settings and develop-analysis agents are packed
with `uipath pack` and published to UiPath Orchestrator; they can be triggered
and monitored from UiPath, with the model served by local Ollama.

### US3 — Operate the system (P2)
Operators can start the whole stack with one command, watch per-service success
events in the UI, and recover from a failed stage without losing data.

## Requirements

- **FR-001**: The UI MUST store the document in `products` and publish
  `document.uploaded` over Dapr; it MUST NOT call an LLM directly.
- **FR-002**: Each pipeline stage MUST publish a success event and hand off to
  the next via Dapr pub/sub (`pubsub`, Redis).
- **FR-003**: All LLM/embedding calls to Ollama MUST be async + bounded by
  `OLLAMA_NUM_PARALLEL` (DONE — see `embeding_service/embed.py` and the agents).
- **FR-004**: The three agents MUST be packageable as UiPath Agents
  (`langgraph.json` + `pyproject.toml`) with the model pointing at Ollama.
- **FR-005**: Each container MUST stay self-contained (copyable individually) and
  the normal run path MUST remain docker-compose.

## Key Entities

`products`, `audience_responses`, `product_analysis` (see
`postgresql-db/init.sql`); Dapr contracts in `dtos/messages.py`.

## Success Criteria

- **SC-001**: From upload, the pipeline produces a `product_analysis` row with the
  selected insights, end-to-end, on a local stack.
- **SC-002**: `uipath pack` succeeds for all three agents and they appear in UiPath
  Orchestrator.
- **SC-003**: Embeddings + reactions run concurrently (bounded), not serially.
