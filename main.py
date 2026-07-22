"""
Run ResearchFlow end-to-end.

Usage:
    python main.py "The future of vertical farming"
"""
import sys
from datetime import date

from graph import build_graph


def main():
    topic = " ".join(sys.argv[1:]) or "The future of vertical farming"

    app = build_graph()
    result = app.invoke(
        {
            "topic": topic,
            "as_of": date.today().isoformat(),
            "sections": [],
        }
    )

    print("=" * 70)
    print(f"TOPIC: {topic}")
    print(f"MODE: {result.get('mode')}")
    print("=" * 70)
    print(result.get("final", "(no final output produced)"))


if __name__ == "__main__":
    main()
