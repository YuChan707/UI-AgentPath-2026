# features-extractor

Second component of the OnLooker **product pipeline**, and the first **UiPath
Agent**: a LangGraph agent (UiPath Python Agent SDK / `uipath-langchain`) that
extracts a product's **features** from its embedded document, using a **local
Ollama** model — no cloud. It runs as a Dapr subscriber and can also be packed and
deployed to UiPath Orchestrator.

## Flow

```
embeding-service --(features.extract {id_product, collection})--> features-extractor
   1. read the product's chunks from the Chroma collection
   2. run the LangGraph agent (Ollama) -> list of {feature_id, name, description}
   3. persist into products.features (status=extracted)
   4. publish embedding.progress (success) to the UI
   5. publish features.ready {id_product, n_features} --> audience-settings
```

## Contents

| Path | What it is |
|---|---|
| `agent.py` | LangGraph agent: compiled `graph` (Ollama model). Packed by UiPath. |
| `main.py` | Dapr subscriber (FastAPI): `/dapr/subscribe` + `/events/features-extract` |
| `chroma_io.py` | Reads the product's chunks from ChromaDB |
| `db.py` | Writes `products.features` (asyncpg) |
| `dapr_io.py` | Publishes events to the Dapr sidecar |
| `contracts.py` | Vendored Dapr contracts (copy of root `dtos/messages.py`; `make vendor`) |
| `langgraph.json`, `pyproject.toml` | UiPath agent packaging (`uipath init` / `uipath pack`) |
| `components/pubsub.yaml` | Dapr Redis pub/sub component |
| `Dockerfile`, `requirements.txt`, `Makefile` | Self-contained packaging (build context = this folder) |

Self-contained: builds from its own folder; the normal run is the repo-root
`docker-compose.yml` (`--profile pipeline`).

## Run

```bash
docker compose --profile pipeline up --build   # whole stack
make dapr                                       # this service + Dapr sidecar
make build                                      # standalone image (proves self-containment)
```

As a UiPath agent (optional, needs UiPath credentials in `.env`):

```bash
make uipath-init      # uipath init  -> entry-points.json
make uipath-pack      # uipath pack  -> deployable .nupkg
```

## Environment

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/onlooker` | Postgres (write features) |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | `http://localhost:11434/v1` / `llama3.1` | Agent LLM (local) |
| `CHROMA_HOST` / `CHROMA_PORT` | `localhost` / `8000` | ChromaDB server |
| `REDIS_HOST` | `redis:6379` (Compose) | Dapr pub/sub |
| `UIPATH_URL` / `UIPATH_ACCESS_TOKEN` / `UIPATH_FOLDER` | — | Optional: UiPath Orchestrator publish/monitor |
