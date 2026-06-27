// GET /api/pipeline/status?id=<id_product>
// Reads the pipeline progress + results for a product from the DB. The UI polls
// this after upload (success-state logic per the flow diagram).
import { pool } from "@/lib/db";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const id = new URL(request.url).searchParams.get("id");
  if (!id) {
    return Response.json({ error: "id is required" }, { status: 400 });
  }
  const db = pool();

  const product = await db.query(
    `SELECT id_product, document_name, doc_type, status, features, date_upload
       FROM products WHERE id_product = $1`,
    [id],
  );
  if (product.rowCount === 0) {
    return Response.json({ error: "product not found" }, { status: 404 });
  }

  const responses = await db.query(
    `SELECT count(*)::int AS n FROM audience_responses WHERE id_product = $1`,
    [id],
  );
  const analysis = await db.query(
    `SELECT strengths, weakness, points_with_potential, audience_response_analysis,
            final_recomendations, aggregate_scores
       FROM product_analysis WHERE id_product = $1`,
    [id],
  );

  return Response.json({
    product: product.rows[0],
    n_responses: responses.rows[0].n,
    analysis: analysis.rows[0] ?? null,
  });
}
