// Server-only Postgres pool (node-postgres). The UI is I/O only: its server
// routes store/read data here; they never talk to an LLM.
import { Pool } from "pg";

declare global {
  // eslint-disable-next-line no-var
  var _onlookerPool: Pool | undefined;
}

export function pool(): Pool {
  if (!globalThis._onlookerPool) {
    globalThis._onlookerPool = new Pool({
      connectionString:
        process.env.DATABASE_URL ||
        "postgresql://postgres:postgres@localhost:5432/onlooker",
    });
  }
  return globalThis._onlookerPool;
}
