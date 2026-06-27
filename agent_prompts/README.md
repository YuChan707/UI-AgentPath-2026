# agent_prompts

Versionable, reusable **prompt artifacts** — separate from service code. These
were salvaged when the monolithic `backend/` was removed in the microservices
pivot; the prompts are the one thing worth keeping from the old agents.

| File | Origin | Reused by |
|---|---|---|
| [`document_analysis.md`](document_analysis.md) | `backend/agents/document_analyst.py` | **features-extractor** (classify doc, extract fields) |
| [`audience_reaction.md`](audience_reaction.md) | `backend/agents/audience.py` + `feedback.py` | **audience-settings** (group reactions to features) |
| [`legacy_coaching.md`](legacy_coaching.md) | coaching / cultural / vision agents | archived reference only (coaching product removed) |

The formula-grounded synthetic-audience prompts (`BEHAVIOR_MODEL`, `FIELD_GROUPS`,
`GROUP_PROFILE`, `REACTION`) live as `PromptSpec` entities in
[`../data_processor/prompts.py`](../data_processor/prompts.py).
