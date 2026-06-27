# audience-settings

Third component of the OnLooker **product pipeline**, a **UiPath Agent**: for each
audience group × product feature it simulates the group's reaction (the seven
AudienceResponse scores) with a LangGraph agent on a **local Ollama** model, over
Dapr. No cloud.

## Flow

```
features-extractor --(features.ready {id_product})--> audience-settings
   1. read products.features + products.settings (the UI's AudienceSettings)
   2. build the audience groups from the settings (defaults: globalized/generic/20-45/~1500)
   3. for each (group x feature): run the reaction agent (Ollama) -> 7 scores [0,1]
      (bounded by OLLAMA_NUM_PARALLEL, defaults to CPU count)
   4. persist into audience_responses (status=reacting)
   5. publish embedding.progress (success) to the UI
   6. publish audience.ready {id_product, n_features, n_groups} --> develop-analysis
```

Scores per response: `confident, complexity, security, engagement, interest,
value_perceived, general_sentiment`.

## Contents

| Path | What it is |
|---|---|
| `agent.py` | LangGraph reaction agent: compiled `graph` (Ollama). Packed by UiPath. |
| `groups.py` | Derives audience groups from the UI settings |
| `main.py` | Dapr subscriber (FastAPI): `features.ready` -> reactions -> `audience.ready` |
| `db.py` | Reads features/settings, writes `audience_responses` (asyncpg) |
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
| `DATABASE_URL` | local Postgres | features/settings in, audience_responses out |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434/v1` / `llama3.1` | reaction agent LLM |
| `OLLAMA_NUM_PARALLEL` | CPU count | concurrent reactions against Ollama |
| `REDIS_HOST` | `redis:6379` (Compose) | Dapr pub/sub |
| `UIPATH_*` | — | optional UiPath Orchestrator publish/monitor |
