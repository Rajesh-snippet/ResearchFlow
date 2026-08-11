"""
JobManager owns:
- an in-memory dict of job status (queued/running/completed/failed)
- one asyncio background task per running job
- per-job asyncio.Queue fan-out for SSE subscribers
- a semaphore capping concurrent full-pipeline runs (MAX_CONCURRENT_JOBS)
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from utils.logger import get_logger
from utils.text import slugify
from utils.constants import (
    MAX_CONCURRENT_JOBS,
    JOB_TTL_SECONDS,
    SSE_QUEUE_MAXSIZE,
)

logger = get_logger(__name__)


NODE_PROGRESS_MESSAGES = {
    "router": "Deciding research strategy...",
    "research": "Gathering research evidence...",
    "orchestrator": "Planning blog structure...",
    "worker": "Writing a section...",
    "merge_content": "Merging sections...",
    "editor": "Polishing content...",
    "decide_images": "Planning images...",
    "generate_and_place_images": "Generating images...",
}


@dataclass
class JobRecord:
    job_id: str
    thread_id: str
    topic: str
    status: str = "queued"
    current_node: Optional[str] = None
    progress_detail: Optional[str] = None
    sections_done: int = 0
    sections_total: Optional[int] = None
    error: Optional[str] = None
    result_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class JobManager:
    def __init__(self, graph):
        """
        graph: an already-compiled LangGraph instance built with
        build_graph(checkpointer=<AsyncSqliteSaver instance>).

        Compile once at app startup (see app.py lifespan) and reuse
        across all jobs — do NOT rebuild the graph per request.
        """
        self._graph = graph
        self._jobs: Dict[str, JobRecord] = {}
        self._subscribers: Dict[str, list] = {}

        # Limits the number of complete ResearchFlow pipelines that
        # can execute simultaneously.
        self._job_semaphore = asyncio.Semaphore(MAX_CONCURRENT_JOBS)

    # ---------- public API ----------

    def create_job(
        self,
        topic: str,
        mode: Optional[str],
        recency_days: Optional[int],
    ) -> JobRecord:
        job_id = uuid.uuid4().hex[:12]

        # API jobs use a unique thread ID so that two users requesting
        # the same topic do not share the same checkpoint thread.
        thread_id = f"job-{job_id}-{slugify(topic)[:40]}"

        record = JobRecord(
            job_id=job_id,
            thread_id=thread_id,
            topic=topic,
        )

        self._jobs[job_id] = record
        self._subscribers[job_id] = []

        # Fresh graph input must contain the same required initial
        # state fields used by the working CLI in main.py.
        initial_input = {
            "topic": topic,
            "as_of": date.today().isoformat(),
            "sections": [],
        }

        if mode:
            initial_input["mode"] = mode

        if recency_days:
            initial_input["recency_days"] = recency_days

        asyncio.create_task(self._run(job_id, initial_input))

        return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        self._evict_expired()
        return self._jobs.get(job_id)

    def subscribe(self, job_id: str) -> Optional["asyncio.Queue"]:
        if job_id not in self._jobs:
            return None

        q = asyncio.Queue(maxsize=SSE_QUEUE_MAXSIZE)
        self._subscribers[job_id].append(q)

        return q

    def unsubscribe(self, job_id: str, q: "asyncio.Queue") -> None:
        subs = self._subscribers.get(job_id)

        if subs and q in subs:
            subs.remove(q)

    async def resume(self, job_id: str) -> JobRecord:
        """
        Re-invoke a failed job's graph from its last checkpoint.
        """
        record = self._jobs.get(job_id)

        if record is None:
            raise KeyError(job_id)

        if record.status not in ("failed",):
            return record

        record.status = "queued"
        record.error = None
        record.updated_at = datetime.utcnow()

        # Resume trigger:
        # invoke/astream(None, config)
        #
        # NOT a fresh input dictionary. A fresh dictionary would restart
        # the graph from START instead of continuing from the checkpoint.
        asyncio.create_task(self._run(job_id, None))

        return record

    # ---------- internals ----------

    async def _run(
        self,
        job_id: str,
        graph_input: Optional[dict],
    ):
        record = self._jobs[job_id]

        config = {
            "configurable": {
                "thread_id": record.thread_id,
            }
        }

        async with self._job_semaphore:
            record.status = "running"
            record.updated_at = datetime.utcnow()

            await self._publish(
                job_id,
                {
                    "event": "status",
                    "status": "running",
                },
            )

            worker_count = 0

            try:
                async for chunk in self._graph.astream(
                    graph_input,
                    config=config,
                    stream_mode="updates",
                ):
                    for node_name, update in chunk.items():
                        record.current_node = node_name

                        record.progress_detail = NODE_PROGRESS_MESSAGES.get(
                            node_name,
                            f"Running {node_name}...",
                        )

                        # Get total number of planned sections.
                        if (
                            node_name == "orchestrator"
                            and isinstance(update, dict)
                        ):
                            plan = update.get("plan")

                            if plan is not None and hasattr(plan, "tasks"):
                                record.sections_total = len(plan.tasks)

                        # Track worker progress.
                        if node_name == "worker":
                            worker_count += 1
                            record.sections_done = worker_count

                            if record.sections_total:
                                record.progress_detail = (
                                    f"Writing section "
                                    f"{worker_count}/{record.sections_total}..."
                                )

                        record.updated_at = datetime.utcnow()

                        await self._publish(
                            job_id,
                            {
                                "event": "progress",
                                "node": node_name,
                                "detail": record.progress_detail,
                                "sections_done": record.sections_done,
                                "sections_total": record.sections_total,
                            },
                        )

                # Pull final state after the graph finishes.
                final_state = await self._graph.aget_state(config)

                final_values = (
                    final_state.values
                    if final_state
                    else {}
                )

                record.result_path = (
                    final_values.get("final")
                    or final_values.get("md_with_placeholders")
                )

                record.status = "completed"
                record.updated_at = datetime.utcnow()

                await self._publish(
                    job_id,
                    {
                        "event": "status",
                        "status": "completed",
                    },
                )

            except Exception as exc:  # noqa: BLE001
                # A job failure must not crash the FastAPI server.
                logger.exception(
                    "Job %s failed",
                    job_id,
                )

                record.status = "failed"
                record.error = str(exc)
                record.updated_at = datetime.utcnow()

                await self._publish(
                    job_id,
                    {
                        "event": "status",
                        "status": "failed",
                        "error": str(exc),
                    },
                )

            finally:
                await self._publish(
                    job_id,
                    {
                        "event": "end",
                    },
                )

    async def _publish(
        self,
        job_id: str,
        payload: Dict[str, Any],
    ):
        for q in list(self._subscribers.get(job_id, [])):
            try:
                q.put_nowait(payload)

            except asyncio.QueueFull:
                # Slow/abandoned client — drop the event rather than
                # blocking the entire job.
                logger.warning(
                    "SSE queue full for job %s, dropping event",
                    job_id,
                )

    def _evict_expired(self):
        cutoff = (
            datetime.utcnow()
            - timedelta(seconds=JOB_TTL_SECONDS)
        )

        expired = [
            jid
            for jid, rec in self._jobs.items()
            if rec.status in ("completed", "failed")
            and rec.updated_at < cutoff
        ]

        for jid in expired:
            self._jobs.pop(jid, None)
            self._subscribers.pop(jid, None)