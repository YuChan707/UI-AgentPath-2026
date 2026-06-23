-- ============================================================================
-- Microservices pipeline tables — appended by docker-compose init order.
-- IDEMPOTENT: all statements use IF NOT EXISTS.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Raw uploaded file storage (replaces Azure Blob Storage)
CREATE TABLE IF NOT EXISTS documents (
    document_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    filename      text NOT NULL,
    file_ext      text NOT NULL,   -- pdf / pptx / docx / txt
    file_data     bytea NOT NULL,  -- full file bytes
    file_size     integer NOT NULL,
    uploaded_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_documents_ext ON documents (file_ext);

-- One record per analysis run — tracks the full pipeline lifecycle
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id       uuid REFERENCES documents (document_id) ON DELETE SET NULL,
    collection_name   text,         -- ChromaDB collection created by embedding-service
    status            text NOT NULL DEFAULT 'submitted',
    -- submitted → embedding_complete → features_extracted → audience_processed → report_ready
    audience_config   jsonb NOT NULL DEFAULT '{}'::jsonb,
    insight_flags     jsonb NOT NULL DEFAULT '{}'::jsonb,
    features          jsonb,        -- written by features-extractor
    audience_reactions jsonb,       -- written by audience-settings
    metrics           jsonb,        -- aggregate scores written by audience-settings
    final_report      jsonb,        -- written by develop-analysis
    error             text,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs (status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_doc    ON pipeline_runs (document_id);

-- Real-time status log (published by every service via pipeline-status topic)
CREATE TABLE IF NOT EXISTS pipeline_status_log (
    id          bigserial PRIMARY KEY,
    run_id      uuid NOT NULL,
    stage       text NOT NULL,
    detail      text,
    logged_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pipeline_status_run ON pipeline_status_log (run_id, logged_at DESC);

-- Auto-update updated_at on pipeline_runs
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END; $$;

DROP TRIGGER IF EXISTS trg_pipeline_runs_updated ON pipeline_runs;
CREATE TRIGGER trg_pipeline_runs_updated
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
