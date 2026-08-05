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