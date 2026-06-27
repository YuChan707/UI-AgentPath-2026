# postgresql-db

Schema for the shared **OnLooker Postgres** database. Postgres itself runs as a
stock image in the repo-root `docker-compose.yml`; this folder holds the schema
it loads.

| File | What it is |
|---|---|
| `init.sql` | Full entity schema (one table per entity + `products` for the pipeline). Mounted into the `postgres` container at first init (`/docker-entrypoint-initdb.d/`). Idempotent (`CREATE ... IF NOT EXISTS`). |
| `apply_schema.py` | Applies `init.sql` to an existing DB via `DATABASE_URL` (SQLAlchemy + asyncpg). Used by `make schema`. |

```bash
# Auto-applied on first `docker compose up` (init.sql mount). To (re)apply manually:
make schema                       # = python postgresql-db/apply_schema.py
# or:
psql "$DATABASE_URL" -f postgresql-db/init.sql
```
