"""
Citation sanity check (M3).

Workers are prompted to only cite URLs from the evidence they were given,
but nothing previously verified they actually did. This extracts every
markdown link the worker wrote and flags any URL that isn't in the
evidence list - catching hallucinated citations before they ship.

This is a sanity check, not a hard gate: it logs a warning rather than
raising, since a false positive (e.g. a legitimate non-citation link)
shouldn't kill a whole run over a heuristic.
"""
import re
from typing import List

from schemas import EvidenceItem
from utils.logger import get_logger

log = get_logger(__name__)

_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def extract_cited_urls(section_md: str) -> List[str]:
    """Returns every URL used in a markdown link like [Source](url)."""
    return [url for _, url in _MARKDOWN_LINK_RE.findall(section_md)]


def check_citations(
    section_md: str, evidence: List[EvidenceItem], section_title: str = ""
) -> dict:
    """
    Returns:
        {
            "cited_urls": [...],
            "unverified_urls": [...],   # cited but not in evidence
            "is_clean": bool,
        }
    Logs a warning (does not raise) if any unverified URLs are found.
    """
    evidence_urls = {e.url for e in evidence}
    cited_urls = extract_cited_urls(section_md)
    unverified = [u for u in cited_urls if u not in evidence_urls]

    if unverified:
        log.warning(
            "Section '%s' cites %d URL(s) not found in provided evidence: %s",
            section_title or "(untitled)",
            len(unverified),
            unverified,
        )

    return {
        "cited_urls": cited_urls,
        "unverified_urls": unverified,
        "is_clean": not unverified,
    }
