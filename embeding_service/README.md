# embeding-service

First component of the OnLooker **product pipeline**. Turns an uploaded product
document into vectors in ChromaDB, driven entirely by Dapr pub/sub. It never
talks to the UI directly — the UI publishes an event and this service reports
progress back over the bus.

## Flow

```
UI  --(document.uploaded {id_product, doc_type})-->  embeding-service
      1. fetch document bytes from Postgres (products.content) by id
      2. extract + clean + page-chunk the text   (.txt .md .pdf .pptx .docx)
      3. embed each chunk with Ollama            (OLLAMA_EMBED_MODEL)
      4. store the vectors in Chroma             (collection product_<id>)
      5. publish embedding.progress (started/progress/success) to the UI
      6. publish features.extract {collection}   --> features-extractor
```

## Contents

| Path | What it is |
|---|---|
| `main.py` | Dapr subscriber (FastAPI): `/dapr/subscribe` + `/events/document-uploaded` |
| `pipeline.py` | Orchestrates fetch -> extract -> embed -> store -> publish |
| `extract.py` | Per-format text extraction + symbol cleaning + page chunking |
| `embed.py` | Ollama embeddings (`/api/embeddings`) + Chroma `HttpClient` store |
| `db.py` | Reads `products.content` by id (asyncpg) |
| `dapr_io.py` | Publishes events to the Dapr sidecar (HTTP) |
<<<<<<< HEAD
| `contracts.py` | Vendored Dapr message contracts (copy of root `dtos/messages.py`; `make vendor`) |
| `components/pubsub.yaml` | Dapr Redis pub/sub component (`name: pubsub`) |
| `Dockerfile`, `requirements.txt`, `Makefile` | Self-contained packaging (build context = this folder) |

This container is **self-contained**: it builds from its own folder (no shared
sibling), so it can be copied out and run on its own. The normal way to run the
whole project is still the repo-root `docker-compose.yml`.
=======
| `components/pubsub.yaml` | Dapr Redis pub/sub component (`name: pubsub`) |
| `Dockerfile`, `requirements.txt` | Service packaging (build from repo root) |
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)

## Run

In the full stack (Dapr sidecar wired in Compose):

```bash
docker compose --profile pipeline up --build
```

<<<<<<< HEAD
On the host with a Dapr sidecar (from this folder):

```bash
make dapr          # = REDIS_HOST=localhost:6379 dapr run ... uvicorn main:app
```

Standalone image build (proves self-containment):

```bash
make build         # docker build -t embeding-service .
=======
On the host with a Dapr sidecar:

```bash
export REDIS_HOST=localhost:6379
dapr run --app-id embeding-service --app-port 8100 \
    --resources-path embeding_service/components \
    -- uvicorn embeding_service.main:app --host 0.0.0.0 --port 8100
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
```

## Environment

| Var | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/onlooker` | Postgres (read product bytes) |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama native API (embeddings) |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model (pull it into Ollama first) |
<<<<<<< HEAD
| `OLLAMA_NUM_PARALLEL` | CPU count | Concurrent embedding requests (async, bounded) |
=======
>>>>>>> 15f913d (cleaning and restructuring to microservices infrastructure)
| `CHROMA_HOST` / `CHROMA_PORT` | `localhost` / `8000` | ChromaDB server |
| `REDIS_HOST` | (required) | Redis for the Dapr pub/sub component (`redis:6379` in Compose) |
| `DAPR_HTTP_PORT` | `3500` | Dapr sidecar (injected by `dapr run`) |
| `PUBSUB_NAME` | `pubsub` | Dapr pub/sub component name |

> Pull the embedding model once: `ollama pull nomic-embed-text`.
