"""
LangGraph state schema.
"""
import operator
from typing import Annotated, List, Optional, TypedDict

from schemas import EvidenceItem, Plan


class State(TypedDict):
    topic: str

    # routing / research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # recency
    as_of: str
    recency_days: int

    # workers - operator.add merges parallel worker outputs into one list
    sections: Annotated[List[tuple], operator.add]  # (task_id, section_md)

    # reducer / image
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]

    final: str
