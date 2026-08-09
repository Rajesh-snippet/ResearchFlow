"""
Request/response models for the FastAPI layer.

Kept separate from schemas.py (the graph's internal Pydantic models —
Task, Plan, EvidenceItem, etc.) on purpose: API contracts and graph-internal
state shapes should be free to evolve independently.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=300)
    mode: Optional[str] = Field(
        default=None,
        description="Force 'closed_book' | 'hybrid' | 'open_book'. Omit to let the router decide.",
    )
    recency_days: Optional[int] = Field(
        default=None,
        description="Only used if mode implies open_book research; passed through to state.recency_days.",
    )


class GenerateResponse(BaseModel):
    job_id: str
    thread_id: str
    status: JobStatus
    status_url: str
    stream_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    thread_id: str
    topic: str
    status: JobStatus
    current_node: Optional[str] = None
    progress_detail: Optional[str] = None
    sections_done: Optional[int] = None
    sections_total: Optional[int] = None
    error: Optional[str] = None
    result_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ResumeResponse(BaseModel):
    job_id: str
    thread_id: str
    status: JobStatus
    message: str
