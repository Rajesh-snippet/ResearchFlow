# --- Append these to utils/constants.py (do not create a separate file) ---

# M6: FastAPI job control
# Separate from MAX_PARALLEL_LLM_CALLS (which throttles individual LLM calls
# inside one graph run). This caps how many FULL PIPELINE RUNS can be
# in-flight at once on the server. Each running job spins up its own set of
# parallel workers, so this is the knob that actually protects Render/Railway
# free-tier memory limits — MAX_PARALLEL_LLM_CALLS alone won't save you if
# 10 users hit /generate at the same moment.
MAX_CONCURRENT_JOBS = 2

# How long a completed/failed job's status stays queryable before the
# in-memory record is evicted. Doesn't affect the SQLite checkpoint (that's
# permanent until you delete the .db) — only the API-layer status dict.
JOB_TTL_SECONDS = 60 * 60  # 1 hour

# Max number of buffered progress events per SSE subscriber queue, to avoid
# unbounded memory growth if a client connects but never reads.
SSE_QUEUE_MAXSIZE = 100
