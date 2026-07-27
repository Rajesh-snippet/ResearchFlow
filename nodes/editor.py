"""
Editor node.

Takes the merged markdown from all workers and performs a final editorial
pass before images are planned.

Responsibilities:
- Improve grammar and readability.
- Smooth transitions between sections.
- Remove repetition.
- Standardize tone and terminology.
- Preserve ALL markdown, code blocks, citations and URLs.
- Never introduce new factual claims.
"""

from langchain_core.messages import HumanMessage, SystemMessage

from config import llm
from state import State
from utils.logger import get_logger

log = get_logger(__name__)

EDITOR_SYSTEM = """
You are a senior technical editor.

Your job is to polish an already-written technical article.

Responsibilities:
- Improve grammar and readability.
- Improve sentence flow.
- Improve transitions between sections.
- Remove repetitive sentences.
- Keep terminology consistent.
- Preserve Markdown formatting.
- Preserve headings.
- Preserve tables.
- Preserve code blocks exactly.
- Preserve every citation and URL exactly.
- Preserve all factual claims.

Rules:
- DO NOT invent facts.
- DO NOT perform research.
- DO NOT remove citations.
- DO NOT rewrite URLs.
- DO NOT change code.
- DO NOT shorten the article significantly.

Return ONLY the final edited markdown.
"""


def editor_node(state: State) -> dict:
    log.info("Running editor node...")

    merged_md = state["merged_md"]

    edited_md = llm.invoke(
        [
            SystemMessage(content=EDITOR_SYSTEM),
            HumanMessage(content=merged_md),
        ]
    ).content.strip()

    log.info("Editor completed.")

    return {
        "edited_md": edited_md
    }