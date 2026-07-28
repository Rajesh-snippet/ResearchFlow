"""
Citation sanity checks.

check_citations (M3): workers are prompted to only cite URLs from the
evidence they were given, but nothing previously verified they actually
did. Extracts every markdown link a worker wrote and flags any URL that
isn't in the evidence list - catching hallucinated citations.

check_edit_preserved_citations (M4): the editor node is told not to touch
citations, but nothing verified it complied. Confirms every citation URL
present before editing is still present after.

Both are sanity checks, not hard gates: they log a warning rather than
raising, since a false positive shouldn't kill a whole run over a
heuristic.
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


def check_edit_preserved_citations(
    original_md: str, edited_md: str, section_title: str = ""
) -> dict:
    """
    Sanity check for the editor node: confirms every citation URL present
    before editing is still present after. Logs a warning (does not raise)
    on mismatch.

    Returns:
        {
            "original_urls": [...],
            "edited_urls": [...],
            "dropped_urls": [...],   # present before, missing after
            "is_clean": bool,
        }
    """
    original_urls = set(extract_cited_urls(original_md))
    edited_urls = set(extract_cited_urls(edited_md))
    dropped = original_urls - edited_urls

    if dropped:
        log.warning(
            "Editor dropped %d citation URL(s) that were present before editing%s: %s",
            len(dropped),
            f" ('{section_title}')" if section_title else "",
            list(dropped),
        )

    return {
        "original_urls": list(original_urls),
        "edited_urls": list(edited_urls),
        "dropped_urls": list(dropped),
        "is_clean": not dropped,
    }
