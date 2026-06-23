import json
import os
import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, File, Form, UploadFile
from sqlalchemy import text

from database import get_db
from services.document_service import extract_text

router = APIRouter(tags=["document"])

DAPR_HTTP   = f"http://localhost:{os.getenv('DAPR_HTTP_PORT', '3510')}"
PUBSUB_NAME = "onlooker-pubsub"


async def _publish(topic: str, data: dict) -> None:
    url = f"{DAPR_HTTP}/v1.0/publish/{PUBSUB_NAME}/{topic}"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=data, timeout=10)
        except Exception:
            pass  # Dapr unavailable in local dev — pipeline is optional


@router.post("/document/upload")
async def upload_document(
    file: Annotated[UploadFile, File()],
    session_id: Annotated[str, Form()] = "chat",
    # Audience settings forwarded to the microservice pipeline
    audience_type: Annotated[str, Form()] = "General professional audience",
    audience_environment: Annotated[str, Form()] = "Professional setting",
    audience_area: Annotated[str, Form()] = "Technology",
    audience_size: Annotated[int, Form()] = 100,
    age_dstn: Annotated[str, Form()] = "25-45",
    location: Annotated[str, Form()] = "Global",
    # Insight flags — which report sections to generate
    detect_strengths: Annotated[bool, Form()] = True,
    detect_weaknesses: Annotated[bool, Form()] = True,
    detect_potential: Annotated[bool, Form()] = True,
    general_report: Annotated[bool, Form()] = True,
):
    """
    Upload a .pptx, .docx, or .pdf.

    Stores the raw file in PostgreSQL, then fires a Dapr pub/sub event that
    kicks off the microservice pipeline:
      embedding-service → features-extractor → audience-settings → develop-analysis

    Returns immediately with {run_id, document_id} so the UI can poll
    GET /pipeline/{run_id}/status for progress.
    """
    file_bytes = await file.read()
    ext        = (file.filename or "").rsplit(".", 1)[-1].lower() or "bin"
    doc_id     = uuid.uuid4()
    run_id     = uuid.uuid4()

    audience_config = {
        "audience_type":        audience_type,
        "audience_environment": audience_environment,
        "audience_area":        audience_area,
        "audience_size":        audience_size,
        "age_dstn":             age_dstn,
        "location":             location,
    }
    insight_flags = {
        "detect_strengths":  detect_strengths,
        "detect_weaknesses": detect_weaknesses,
        "detect_potential":  detect_potential,
        "general_report":    general_report,
    }

    # Store raw file in PostgreSQL (open-source replacement for Azure Blob)
    async for db in get_db():
        await db.execute(
            text(
                "INSERT INTO documents (document_id, filename, file_ext, file_data, file_size) "
                "VALUES (:doc_id, :filename, :ext, :data, :size)"
            ),
            {"doc_id": str(doc_id), "filename": file.filename, "ext": ext,
             "data": file_bytes, "size": len(file_bytes)},
        )
        await db.execute(
            text(
                "INSERT INTO pipeline_runs "
                "  (run_id, document_id, status, audience_config, insight_flags) "
                "VALUES (:run_id, :doc_id, 'submitted', :ac::jsonb, :if::jsonb)"
            ),
            {"run_id": str(run_id), "doc_id": str(doc_id),
             "ac": json.dumps(audience_config), "if": json.dumps(insight_flags)},
        )
        await db.commit()

    # Fire Dapr event — embedding-service picks this up asynchronously
    await _publish("document-submitted", {
        "run_id":          str(run_id),
        "document_id":     str(doc_id),
        "file_extension":  ext,
        "session_id":      session_id,
        "audience_config": audience_config,
        "insight_flags":   insight_flags,
    })

    # Extract text immediately so the UI chat box can display/use it
    await file.seek(0)
    text_content = await extract_text(file)

    return {
        "run_id":      str(run_id),
        "document_id": str(doc_id),
        "filename":    file.filename,
        "word_count":  len(text_content.split()),
        "text":        text_content,
        "status":      "submitted",
    }
