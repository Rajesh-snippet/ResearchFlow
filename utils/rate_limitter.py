"""
Global concurrency limiter for LLM requests.

Purpose
-------
Prevent too many simultaneous LLM requests from exceeding the
Groq free-tier Tokens-Per-Minute (TPM) limit.

Every LLM invocation should acquire this semaphore before making
an API call and release it immediately afterward.

Usage
-----
from utils.rate_limiter import llm_semaphore

with llm_semaphore:
    response = invoke_with_retry(...)
"""

from threading import BoundedSemaphore

from utils.constants import MAX_PARALLEL_LLM_CALLS


# Global semaphore shared across the application.
#
# Example:
#
# MAX_PARALLEL_LLM_CALLS = 2
#
# Only two worker threads may perform an LLM call simultaneously.
llm_semaphore = BoundedSemaphore(MAX_PARALLEL_LLM_CALLS)