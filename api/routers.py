import asyncio
import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.schemas import (
    GenerateRequest,
    GenerateResponse,
    JobStatus,
    JobStatusResponse,
    ResumeResponse,
)

router = APIRouter()


def _to_status_response(record) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=record.job_id,
        thread_id=record.thread_id,
        topic=record.topic,
        status=JobStatus(record.status),
        current_node=record.current_node,
        progress_detail=record.progress_detail,
        sections_done=record.sections_done,
        sections_total=record.sections_total,
        error=record.error,
        result_url=f"/jobs/{record.job_id}/result" if record.status == "completed" else None,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
