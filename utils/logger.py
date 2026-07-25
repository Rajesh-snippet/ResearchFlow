"""
Shared logger for ResearchFlow.

Usage in any node:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("...")
"""
import logging
import sys

_CONFIGURED = False


def _configure_once():
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name)
