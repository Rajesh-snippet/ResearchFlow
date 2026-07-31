"""
Retry wrapper for structured-output LLM calls.

Provides automatic retries for transient failures such as:

- Rate limiting (HTTP 429)
- Temporary network failures
- Timeouts
- Occasional malformed structured outputs

Features
--------
- Exponential backoff
- Honors Groq's suggested retry delay when available
- Configurable retry settings
- Detailed retry logging
"""

from __future__ import annotations

import re
import time

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


def _extract_retry_delay(exc: Exception) -> float | None:
    """
    Extract the retry delay suggested by Groq.

    Example message:

    "Please try again in 17.085s"

    Returns:
        float delay in seconds or None.
    """
    match = re.search(r"try again in\s+([\d.]+)s", str(exc), re.IGNORECASE)

    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None

    return None


def _log_retry(retry_state):
    exc = retry_state.outcome.exception()

    log.warning(
        "Retrying LLM call (%d/%d): %s",
        retry_state.attempt_number,
        RETRY_MAX_ATTEMPTS,
        exc,
    )

    delay = _extract_retry_delay(exc)

    if delay:
        log.warning(
            "Groq requested %.2f seconds before retrying.",
            delay,
        )
        time.sleep(delay)


@retry(
    stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(
        min=RETRY_WAIT_MIN_SECONDS,
        max=RETRY_WAIT_MAX_SECONDS,
    ),
    retry=retry_if_exception_type(Exception),
    before_sleep=_log_retry,
    reraise=True,
)
def invoke_with_retry(runnable, messages):
    """
    Invoke an LLM runnable with automatic retries.

    Parameters
    ----------
    runnable
        LangChain Runnable.

    messages
        Input messages passed to runnable.invoke().

    Returns
    -------
    Structured LLM response.

    Raises
    ------
    Exception
        Re-raises the final exception after all retries fail.
    """
    return runnable.invoke(messages)