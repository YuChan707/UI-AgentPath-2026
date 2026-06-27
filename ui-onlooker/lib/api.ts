// Client helper for the UI's own server routes (same-origin). The browser never
// talks to an LLM or to the pipeline directly — only to these I/O endpoints.

export interface AudienceSettings {
  audience_type?: string;
  audience_enviroment?: string;
  audience_area?: string;
  audience_size?: number;
  gender_dstn?: string;
  age_dstn?: string;
  main_goal?: string;
  response_goal?: string;
}

export interface InsightSelection {
  detect_strengts?: boolean;
  detect_weakness?: boolean;
  detect_potential?: boolean;
  general_report?: boolean;
}

export interface UploadResult {
  id_product: string;
  status: string;
  doc_type: string;
}

export async function uploadDocument(
  file: File,
  settings: AudienceSettings = {},
  insights: InsightSelection = {},
): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  for (const [k, v] of Object.entries(settings)) {
    if (v !== undefined && v !== null) form.append(k, String(v));
  }
  for (const [k, v] of Object.entries(insights)) {
    form.append(k, v ? "true" : "false");
  }
  const res = await fetch("/api/documents/upload", { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `upload failed: ${res.status}`);
  }
  return res.json();
}

export interface PipelineStatus {
  product: {
    id_product: string;
    document_name: string;
    doc_type: string;
    status: string;
    features: unknown;
    date_upload: string;
  };
  n_responses: number;
  analysis: {
    strengths: string[] | null;
    weakness: string[] | null;
    points_with_potential: string[] | null;
    audience_response_analysis: string | null;
    final_recomendations: string[] | null;
    aggregate_scores: Record<string, number> | null;
  } | null;
}

export async function getPipelineStatus(id: string): Promise<PipelineStatus> {
  const res = await fetch(`/api/pipeline/status?id=${encodeURIComponent(id)}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `status failed: ${res.status}`);
  }
  return res.json();
}
