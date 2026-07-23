"""
Research node.

M1: swapped Tavily -> DuckDuckGo (via the `ddgs` package). No API key
needed. Trade-off vs Tavily: results are noisier and rarely include a
reliable published date, so the extraction/dedup LLM pass below matters
more here - and open_book recency filtering will drop more items since
published_at is often unknown (extractor is told not to guess dates).
"""
from datetime import date, timedelta
from typing import List, Optional

from config import structured
from langchain_core.messages import HumanMessage, SystemMessage
from schemas import EvidencePack
from state import State


def _ddg_search(query: str, max_results: int = 6) -> List[dict]:
    try:
        from ddgs import DDGS
    except ImportError:
        return []

    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
        out = []
        for r in results or []:
            out.append(
                {
                    "title": r.get("title") or "",
                    "url": r.get("href") or r.get("url") or "",
                    "snippet": r.get("body") or "",
                    # DuckDuckGo results don't reliably expose a publish date
                    "published_at": None,
                    "source": None,
                }
            )
        return out
    except Exception:
        return []


def _iso_to_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None


RESEARCH_SYSTEM = """You are a research synthesizer.

Given raw web search results, produce EvidenceItem objects.

Rules:
- Only include items with a non-empty url.
- Prefer relevant + authoritative sources.
- Normalize published_at to ISO YYYY-MM-DD only if reliably stated in the
  snippet/title; else leave it null. Do NOT guess.
- Keep snippets short.
- Deduplicate by URL.
"""


def research_node(state: State) -> dict:
    queries = (state.get("queries") or [])[:10]
    raw: List[dict] = []
    for q in queries:
        raw.extend(_ddg_search(q, max_results=6))

    if not raw:
        return {"evidence": []}

    extractor = structured(EvidencePack)
    pack = extractor.invoke(
        [
            SystemMessage(content=RESEARCH_SYSTEM),
            HumanMessage(
                content=(
                    f"As-of date: {state['as_of']}\n"
                    f"Recency days: {state['recency_days']}\n\n"
                    f"Raw results:\n{raw}"
                )
            ),
        ]
    )

    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e
    evidence = list(dedup.values())

    if state.get("mode") == "open_book":
        as_of = date.fromisoformat(state["as_of"])
        cutoff = as_of - timedelta(days=int(state["recency_days"]))
        # DDG rarely provides a real published_at, so only drop items we can
        # PROVE are stale. Undated items pass through unfiltered (we can't
        # verify recency either way) rather than being dropped by default -
        # otherwise open_book runs would end up with near-zero evidence.
        evidence = [
            e for e in evidence
            if (d := _iso_to_date(e.published_at)) is None or d >= cutoff
        ]

    return {"evidence": evidence}
