# Connecting the OnLooker agents to UiPath

The three LLM stages — `features_extractor`, `audience_settings`,
`develop_analysis` — are **UiPath Agents** built with the UiPath Python Agent SDK
(`uipath` + `uipath-langchain`). Each is a self-contained LangGraph agent whose
compiled `graph` is exported from `agent.py` and referenced by `langgraph.json`.

They run two ways from the **same** code:

1. **Locally over Dapr** (default) — `main.py` (the Dapr subscriber) calls
   `graph.ainvoke(...)`, model = **local Ollama**. This is what `docker compose
   --profile pipeline up` runs.
2. **On UiPath Orchestrator** — `uipath pack` packages the `graph`; UiPath runs it
   and provides the input/output. The model is selected by `model.py`:
   - `UIPATH_BYO_CONNECTION_ID` **unset** → local Ollama (`langchain_openai.ChatOpenAI`
     pointed at `OLLAMA_BASE_URL`).
   - `UIPATH_BYO_CONNECTION_ID` **set** → `uipath_langchain.chat.UiPathChatOpenAI`
     (routes through a registered UiPath connection / LLM Gateway).

## Per-agent layout (already in place)

```
<agent>/
  agent.py        # GraphInput/GraphOutput (pydantic) + compiled `graph`
  model.py        # chat_model(): Ollama by default, UiPathChatOpenAI if configured
  main.py         # Dapr subscriber that calls graph.ainvoke()
  langgraph.json  # { "graphs": { "<agent>": "./agent.py:graph" } }
  pyproject.toml  # name/version/description/authors + uipath + uipath-langchain
```

## Connect & deploy (run inside each agent folder)

```bash
# 0) one-time: install the CLI into the agent's environment
pip install uipath uipath-langchain        # (or: uv add ...)

# 1) authenticate to your UiPath tenant (writes tokens to .env)
uipath auth

# 2) generate the agent schemas from langgraph.json
uipath init                                 # -> entry-points.json, bindings.json, agent.mermaid

# 3) (optional) run the graph locally with a sample input
uipath run features-extractor '{"chunks": ["..."]}'

# 4) package and publish to Orchestrator
uipath pack                                 # -> <name>.<version>.nupkg
uipath publish
```

`make uipath-auth | uipath-init | uipath-pack | uipath-publish | uipath-run` wrap
these in each agent's `Makefile`.

### Input / output schemas (what UiPath invokes)

| Agent | Input (`GraphInput`) | Output (`GraphOutput`) |
|---|---|---|
| features-extractor | `{ chunks: string[] }` | `{ features: object[] }` |
| audience-settings | `{ group: object, feature: object }` | `{ scores: object }` |
| develop-analysis | `{ features: object[], aggregate: object, insights: object }` | `{ analysis: object }` |

The IO around the graph (Chroma/Postgres/Dapr) lives in `main.py`, so the graph
stays a pure input→output function that UiPath can invoke directly.

## Using local Ollama from UiPath

The agents call Ollama at `OLLAMA_BASE_URL`. To use Ollama **while running on
UiPath**, either:

- run the agent on a **local/self-hosted UiPath robot** that can reach
  `http://localhost:11434`, or
- register an **OpenAI-compatible connection** in UiPath Integration Service that
  points at your Ollama endpoint and set `UIPATH_BYO_CONNECTION_ID` to it, or
- expose Ollama to UiPath Cloud via a tunnel and set `OLLAMA_BASE_URL` accordingly.

For purely cloud LLMs, set `UIPATH_BYO_CONNECTION_ID` to a UiPath LLM Gateway
model connection instead — no Ollama needed.

## Run topology (choose one)

- **A — Dapr drives (current default):** the Dapr subscriber owns orchestration
  and calls the local `graph`. UiPath is used for packaging, versioning and
  monitoring. Simplest; everything local.
- **B — UiPath drives:** a thin Dapr→UiPath bridge starts the published agent via
  the Orchestrator API on each topic and waits for the result. Use this when the
  agents must run/scale on UiPath infrastructure.

## Test the agent on its own (no Dapr, no DB)

The graph is a pure input→output function, so you can run it directly. Needs
**Python 3.11–3.13** (the repo's 3.14 is incompatible) and Ollama running:

```bash
cd features_extractor
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.1
uipath auth          # once, to link a tenant (optional for pure-local run)
uipath init          # generates entry-points.json from langgraph.json
uipath run features-extractor '{"chunks": ["Our product does X and Y."]}'
# -> prints {"features": [...]}
```

For **visual step-by-step debugging**, point LangGraph/LangSmith Studio at the
graph (set `LANGCHAIN_TRACING_V2=true` + `LANGCHAIN_API_KEY` to also get traces).
`uipath-dev` (installed via the `dev` group) is an interactive TUI for the same.

## Edit & debug in UiPath Studio Web (Coded agents, Preview)

These Python agents are **coded agents** — you do NOT open them in classic
desktop Studio (XAML). You sync them to **Studio Web**:

```text
1. studio.uipath.com -> Create New -> Agent -> type: "Coded"  -> copy the project key
2. add it to the agent's .env:      UIPATH_PROJECT_ID=<project-key>
3. from the agent folder:           uipath push
   (syncs agent.py/graph, entry-points.json, pyproject.toml, uipath.json, bindings)
4. in Studio Web: Debug / Debug step-by-step / run evaluations / Publish
```

> **Ollama-from-cloud caveat:** a graph debugged/run **inside Studio Web (cloud)**
> cannot reach your `localhost:11434` Ollama. For cloud runs set
> `UIPATH_BYO_CONNECTION_ID` to a UiPath model connection (or LLM Gateway), or run
> on a **local/self-hosted UiPath robot** that can reach Ollama. Local `uipath run`
> uses Ollama directly.

## Environment (per agent `.env`)

| Var | Purpose |
|---|---|
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | local model (default path) |
| `UIPATH_URL` / `UIPATH_ACCESS_TOKEN` / `UIPATH_FOLDER` | Orchestrator connection |
| `UIPATH_PROJECT_ID` | Studio Web coded-agent project key (for `uipath push`) |
| `UIPATH_BYO_CONNECTION_ID` / `UIPATH_MODEL_NAME` | switch to a UiPath-managed model |

> **Note:** the structure here was conformed to the official
> [`uipath-langchain` samples](https://github.com/UiPath/uipath-langchain-python/tree/main/samples)
> (notably `bring-your-own-model`). Live `uipath init`/`pack` was **not** run in
> this environment because only Python 3.14 is available (incompatible with the
> current `uipath`/`pydantic` stack); run the steps above on Python 3.11–3.13.
