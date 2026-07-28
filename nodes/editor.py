"""
Editor node.

Takes the merged markdown from all workers and performs a final editorial
pass BEFORE images are planned - polishing prose first means image
captions/placement (decided next) match the final phrasing, not the
rough draft.

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
from utils.retry import invoke_with_retry
from utils.validators import check_edit_preserved_citations

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
    plan = state.get("plan")

    edited_md = invoke_with_retry(
        llm,
        [
            SystemMessage(content=EDITOR_SYSTEM),
            HumanMessage(content=merged_md),
        ],
    ).content.strip()

    # M4: sanity-check the editor didn't drop any citation URLs while
    # "polishing" - logs a warning, doesn't block the run.
    check_edit_preserved_citations(
        merged_md, edited_md, section_title=plan.blog_title if plan else ""
    )

    log.info("Editor completed.")
    return {"edited_md": edited_md}
