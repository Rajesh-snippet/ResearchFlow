"""
Run ResearchFlow end-to-end.

Usage:
    python main.py "The future of vertical farming"

M5: checkpoints every run to a local SQLite file (utils/constants.py:
CHECKPOINT_DB_PATH). thread_id is derived deterministically from the
topic (slugified), so re-running the exact same topic string targets
the same thread.

Resume behavior: calling .invoke(fresh_input, config) ALWAYS restarts
execution from START, even with a checkpointer attached - a checkpointer
alone doesn't skip completed nodes on a fresh call. To actually resume a
run that crashed partway through, you must call .invoke(None, config)
instead, which tells LangGraph to continue pending tasks from the last
saved checkpoint rather than restarting. This script checks whether the
thread has an incomplete run (state.next is non-empty) and picks the
right call accordingly.

Security note: the checkpoint serializer is configured with an explicit
allowed_msgpack_modules allowlist (utils/constants.py) restricted to our
own schema classes, rather than relying on the default "allow anything,
just warn" behavior - see CHECKPOINT_ALLOWED_MSGPACK_MODULES for why.
"""
import sqlite3
import sys
from datetime import date

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite import SqliteSaver

from graph import build_graph
from utils.constants import CHECKPOINT_ALLOWED_MSGPACK_MODULES, CHECKPOINT_DB_PATH
from utils.logger import get_logger
from utils.text import slugify

log = get_logger(__name__)


def main():
    topic = " ".join(sys.argv[1:]) or "The future of vertical farming"
    thread_id = slugify(topic)

    conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
    serde = JsonPlusSerializer(allowed_msgpack_modules=CHECKPOINT_ALLOWED_MSGPACK_MODULES)
    checkpointer = SqliteSaver(conn, serde=serde)

    app = build_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": thread_id}}

    existing_state = app.get_state(config)
    is_incomplete_run = bool(existing_state.values) and bool(existing_state.next)

    if is_incomplete_run:
        log.info(
            "Found an incomplete checkpoint for thread '%s' (pending: %s) - "
            "resuming from the last saved step instead of restarting.",
            thread_id,
            existing_state.next,
        )
        result = app.invoke(None, config=config)
    else:
        result = app.invoke(
            {
                "topic": topic,
                "as_of": date.today().isoformat(),
                "sections": [],
            },
            config=config,
        )

    print("=" * 70)
    print(f"TOPIC: {topic}")
    print(f"THREAD ID: {thread_id}  (checkpoints saved to {CHECKPOINT_DB_PATH})")
    print(f"MODE: {result.get('mode')}")
    print("=" * 70)
    print(result.get("final", "(no final output produced)"))

    conn.close()


if __name__ == "__main__":
    main()
