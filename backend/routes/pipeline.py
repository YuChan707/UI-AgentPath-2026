"""
Pipeline status & report endpoints.

The UI polls these after submitting a document via /document/upload
to track microservice progress and retrieve the final report.
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import get_db

router = APIRouter(tags=["pipeline"])


@router.get("/pipeline/{run_id}/status")
async def get_pipeline_status(run_id: str):
    """
    Returns current status of a pipeline run.

    Status progression:
      submitted → embedding_complete → features_extracted
      → audience_processed → report_ready
    """
    async for db in get_db():
        row = await db.execute(
            text(
                "SELECT status, created_at, updated_at "
                "FROM pipeline_runs WHERE run_id = :run_id"
            ),
            {"run_id": run_id},
        )
        result = row.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    # Fetch the last 5 status log entries for progress detail
    async for db in get_db():
        logs_row = await db.execute(
            text(
                "SELECT stage, detail, logged_at FROM pipeline_status_log "
                "WHERE run_id = :run_id ORDER BY logged_at DESC LIMIT 5"
            ),
            {"run_id": run_id},
        )
        logs = [dict(r._mapping) for r in logs_row.fetchall()]

    return {
        "run_id":     run_id,
        "status":     result.status,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "log":        logs,
    }


@router.get("/pipeline/{run_id}/report")
async def get_pipeline_report(run_id: str):
    """Returns the final analysis report when status is report_ready."""
    async for db in get_db():
        row = await db.execute(
            text(
                "SELECT status, metrics, final_report FROM pipeline_runs "
                "WHERE run_id = :run_id"
            ),
            {"run_id": run_id},
        )
        result = row.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Run not found")

    if result.status != "report_ready":
        raise HTTPException(
            status_code=202,
            detail=f"Report not ready yet — current status: {result.status}",
        )

    return {
        "run_id":  run_id,
        "metrics": result.metrics,
        "report":  result.final_report,
    }


@router.post("/pipeline/status-ingest")
async def ingest_pipeline_status(body: dict):
    """
    Dapr subscription handler for the 'pipeline-status' topic.
    Logs status updates from all microservices into pipeline_status_log.
    """
    data = body.get("data", body)
    run_id = data.get("run_id")
    stage  = data.get("stage", "")
    detail = data.get("detail", "")

    if run_id:
        async for db in get_db():
            await db.execute(
                text(
                    "INSERT INTO pipeline_status_log (run_id, stage, detail) "
                    "VALUES (:run_id, :stage, :detail)"
                ),
                {"run_id": run_id, "stage": stage, "detail": detail},
            )
            await db.commit()

    return {"status": "SUCCESS"}
