"""
FastAPI entry point for ResearchFlow M6.

Run with:
    uvicorn app:app --host 0.0.0.0 --port 8000

IMPORTANT — async checkpointer:
M5's CLI (main.py) used SqliteSaver (sync) because a CLI script can afford to
block. This server is async end-to-end (async def handlers, graph.astream /
graph.aget_state), so it MUST use AsyncSqliteSaver from
langgraph.checkpoint.sqlite.aio instead. Mixing the sync saver into an async
graph.astream() call will work by accident sometimes and deadlock or block
the event loop other times — don't reuse M5's checkpointer setup as-is.

    pip install langgraph-checkpoint-sqlite  (if not already in requirements.txt)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from api.job_manager import JobManager
from api.routes import router as jobs_router
from graph import build_graph
from utils.constants import CHECKPOINT_DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB_PATH) as checkpointer:
        # Compile the graph ONCE and reuse it across every request/job.
        # thread_id (per-job, set in JobManager) is what isolates runs from
        # each other — you do not need a fresh compiled graph per job.
        compiled_graph = build_graph(checkpointer=checkpointer)
        app.state.job_manager = JobManager(graph=compiled_graph)
        logger.info("ResearchFlow API started; checkpoint db=%s", CHECKPOINT_DB_PATH)
        yield
        logger.info("ResearchFlow API shutting down")


app = FastAPI(title="ResearchFlow API", version="0.6.0", lifespan=lifespan)

# Loosen for local/dev; tighten allow_origins to your actual frontend
# domain(s) before deploying publicly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
