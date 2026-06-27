# data_ingestor

Ingestion of **real RAW data** from New York state. Downloads demographics at
the `zip_code` (ZCTA) level from the **US Census ACS5**, maps it to the
`Location` / `LocationStatistics` entities (Marshmallow) and **persists** one per zip.

It is the entry point of the pipeline: it produces the real data on which the
[`data_processor`](../data_processor/) builds the synthetic audience.

## Contents

| Path | What it is |
|---|---|
| `main.py` | Downloads ACS5 (2 requests for all ZCTAs), builds `LocationEntity` and `persist_locations()` one JSON per zip |
| `dtos/` | Local copy of the entities (self-contained service) |
| `data/nyc_zip_codes.csv` | Input: NY zip codes |
| `components/` | Dapr: `pubsub.yaml` (redis) + `statestore.yaml` (Postgres, persistence in DB) |
| `Dockerfile`, `.dockerignore`, `requirements.txt` | Service packaging |

## How to run

```bash
# Requires CENSUS_DATA_API in .env
python -m data_ingestor.main
# -> writes data_ingestor/data/locations/<zip>.json + _index.json
```

The persisted JSON is the source of truth, later consumed by `python -m data_processor`.

## Notes

- `data/locations/` is a runtime artifact and is in `.gitignore`.
