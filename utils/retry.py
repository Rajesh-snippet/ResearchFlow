"""
Retry wrapper for structured-output LLM calls (M3).

Groq's json_schema strict mode is generally reliable, but any LLM call
can still fail transiently (rate limit, timeout, an occasional malformed
response). Wrapping .invoke() in a retry means one flaky call doesn't
kill an entire graph run - especially important once workers are
running in parallel and one bad response shouldn't waste the other 4.

Usage (in a node):
    from utils.retry import invoke_with_retry
    decision = invoke_with_retry(structured(RouterDecision), messages)
"""
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from utils.constants import (
    RETRY_MAX_ATTEMPTS,
    RETRY_WAIT_MAX_SECONDS,
    RETRY_WAIT_MIN_SECONDS,
)
from utils.logger import get_logger

log = get_logger(__name__)


def _log_retry(retry_state):
    log.warning(
        "Retrying LLM call (attempt %d/%d) after error: %s",
        retry_state.attempt_number,
        RETRY_MAX_ATTEMPTS,
        retry_state.outcome.exception(),
    )


@retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(min=RETRY_WAIT_MIN_SECONDS, max=RETRY_WAIT_MAX_SECONDS),
    retry=retry_if_exception_type(Exception),
    before_sleep=_log_retry,
    reraise=True,
)
def invoke_with_retry(runnable, messages):
    """
    Calls runnable.invoke(messages), retrying up to RETRY_MAX_ATTEMPTS
    times with exponential backoff on any exception (parse errors,
    validation errors, transient API errors). Re-raises the final
    exception if all attempts fail, so callers still see real failures
    rather than this silently swallowing them.
    """
    return runnable.invoke(messages)
