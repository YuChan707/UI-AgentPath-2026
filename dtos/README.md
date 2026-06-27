# dtos

Domain entities as **Marshmallow schemas** plus the **Dapr message contracts**
(`messages.py`, pydantic) — the shared layer between the microservices. Validate
Marshmallow with `.load()` / serialize with `.dump()`; do not pass loose dicts
around the code.

## Modules

| File | Entities |
|---|---|
| `data_ingestors.py` | RAW data + behavior model: `Location`, `LocationStatistics`, `DemographicGroup`, `BehaviorFormula`, `FactorModifier`, `FieldBehaviorGroup`, `GroupBehaviorProfile`, `MetricRange` + vocabularies (`GENDERS`, `INCOME_BRACKETS`, `FIELD_DOMAINS`, `BEHAVIOR_METRICS`, …) |
| `data_processors.py` | Output: `AudienceSegment`, `ProjectAsset`, `ReactionProfile` |
| `audience.py`, `analytics.py`, `reports.py` | Audience, analytics and reports |
| `messages.py` | Dapr pub/sub contracts (pydantic): `DocumentUploaded`, `ServiceProgress`, `CollectionReady`, `AudienceSettings`, `InsightSelection` |
| `ENTIDADES.txt` | Readable dictionary of all entities |

## Important note

There is a **divergent copy** in [`../data_ingestor/dtos/`](../data_ingestor/dtos/):
the `data_ingestor` is self-contained and uses its own; `data_processor` and the
microservices use **this** one (root), which is the source of truth.
If a change must apply to both, it has to be reflected in the two copies.
