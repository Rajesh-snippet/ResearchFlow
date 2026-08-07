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


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest, request: Request):
    job_manager = request.app.state.job_manager
    record = job_manager.create_job(req.topic, req.mode, req.recency_days)
    return GenerateResponse(
        job_id=record.job_id,
        thread_id=record.thread_id,
        status=JobStatus(record.status),
        status_url=f"/jobs/{record.job_id}",
        stream_url=f"/jobs/{record.job_id}/stream",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, request: Request):
    job_manager = request.app.state.job_manager
    record = job_manager.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found (or expired)")
    return _to_status_response(record)



@router.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str, request: Request):
    job_manager = request.app.state.job_manager
    record = job_manager.get(job_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Job not found (or expired)")

    queue = job_manager.subscribe(job_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Job not found (or expired)")

    async def event_generator():
        try:
            # Send current status immediately so late subscribers aren't
            # stuck waiting for the next node transition.
            yield f"data: {json.dumps({'event': 'status', 'status': record.status})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # Heartbeat comment keeps proxies (Railway, etc.) from
                    # closing an idle connection.
                    yield ": heartbeat\n\n"
                    continue
                yield f"data: {json.dumps(payload)}\n\n"
                if payload.get("event") == "end":
                    break
        finally:
            job_manager.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering if fronted by one
        },
    )
