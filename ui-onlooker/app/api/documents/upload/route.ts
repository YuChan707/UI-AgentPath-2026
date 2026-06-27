// POST /api/documents/upload
// Stores the uploaded document in `products` (bytes + settings + insights) and
// publishes `document.uploaded` over Dapr. The UI does no analysis itself.
import { pool } from "@/lib/db";
import { publish } from "@/lib/dapr";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const ACCEPTED = ["txt", "md", "pdf", "pptx", "docx"];

export async function POST(request: Request) {
  const form = await request.formData();
  const file = form.get("file");
  if (!(file instanceof File)) {
    return Response.json({ error: "file is required" }, { status: 400 });
  }
  const name = file.name || "document";
  const ext = (name.split(".").pop() || "").toLowerCase();
  if (!ACCEPTED.includes(ext)) {
    return Response.json(
      { error: `unsupported file type .${ext}. Accepted: ${ACCEPTED.join(", ")}` },
      { status: 415 },
    );
  }
  const bytes = Buffer.from(await file.arrayBuffer());

  const str = (k: string, d = "") => ((form.get(k) as string | null) ?? d).toString();
  const num = (k: string, d: number) => {
    const v = form.get(k);
    const n = v != null && v !== "" ? Number(v) : NaN;
    return Number.isFinite(n) ? n : d;
  };
  const bool = (k: string) =>
    ["true", "1", "on", "yes"].includes(String(form.get(k) || "").toLowerCase());

  // AudienceSettings — empty values keep the documented defaults.
  const settings = {
    audience_type: str("audience_type"),
    audience_enviroment: str("audience_enviroment"),
    audience_area: str("audience_area"),
    audience_size: num("audience_size", 1500),
    gender_dstn: str("gender_dstn", "generic"),
    age_dstn: str("age_dstn", "20-45"),
    main_goal: str("main_goal"),
    response_goal: str("response_goal"),
  };
  const insights = {
    detect_strengts: bool("detect_strengts"),
    detect_weakness: bool("detect_weakness"),
    detect_potential: bool("detect_potential"),
    general_report: bool("general_report"),
  };

  const { rows } = await pool().query(
    `INSERT INTO products (document_name, doc_type, content, settings, insights, status)
     VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, 'uploaded')
     RETURNING id_product`,
    [name, ext, bytes, JSON.stringify(settings), JSON.stringify(insights)],
  );
  const id_product: string = rows[0].id_product;

  // Hand off to the pipeline (embeding-service subscribes to this topic).
  await publish("document.uploaded", { id_product, doc_type: ext });

  return Response.json({ id_product, status: "uploaded", doc_type: ext });
}
