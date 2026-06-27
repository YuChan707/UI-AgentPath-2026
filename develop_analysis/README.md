# develop-analysis

Final component of the OnLooker **product pipeline**, a **UiPath Agent**: it turns
the aggregated audience reactions into the insights the user selected, with a
LangGraph agent on a **local Ollama** model, over Dapr. No cloud.

## Flow

```
audience-settings --(audience.ready {id_product})--> develop-analysis
   1. aggregate audience_responses (avg per metric -> % ) + read features + insights
   2. run the analysis agent (Ollama) -> only the requested sections:
        detect_strengts -> strengths
        detect_weakness -> weakness
        detect_potential -> points_with_potential
        general_report  -> audience_response_analysis + final_recomendations
   3. persist into product_analysis (status=analyzed)
   4. publish embedding.progress (success) to the UI
   5. publish analysis.ready {id_product, insights} --> UI reads the result from the DB
```

## Contents

| Path | What it is |
|---|---|
| `agent.py` | LangGraph analysis agent: compiled `graph` (Ollama). Packed by UiPath. |
| `main.py` | Dapr subscriber (FastAPI): `audience.ready` -> analysis -> `analysis.ready` |
| `db.py` | Aggregates `audience_responses`, writes `product_analysis` (asyncpg) |
| `dapr_io.py` | Publishes events to the Dapr sidecar |
| `contracts.py` | Vendored Dapr contracts (`make vendor`) |
| `langgraph.json`, `pyproject.toml` | UiPath agent packaging |
| `components/pubsub.yaml` | Dapr Redis pub/sub component |
| `Dockerfile`, `requirements.txt`, `Makefile` | Self-contained packaging |

## Run

```bash
docker compose --profile pipeline up --build
make dapr      # this service + Dapr sidecar
make build     # standalone image (self-containment)
```

## Environment

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | local Postgres | reactions in, product_analysis out |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434/v1` / `llama3.1` | analysis agent LLM |
| `REDIS_HOST` | `redis:6379` (Compose) | Dapr pub/sub |
| `UIPATH_*` | — | optional UiPath Orchestrator publish/monitor |
