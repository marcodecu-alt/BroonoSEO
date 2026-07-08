"""Run one topic through the full pipeline graph end to end via the CLI.

Usage (from apps/api, with venv active):
    python scripts/run_pipeline.py ["optional topic seed"]
"""

import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.graph.graph import pipeline_graph


def main():
    topic_seed = sys.argv[1] if len(sys.argv) > 1 else None
    initial_state = {"topic_seed": topic_seed}

    final_state = pipeline_graph.invoke(initial_state, config={"recursion_limit": 25})

    print("=== FINAL STATUS ===")
    print(final_state.get("status"))

    print("\n=== RESEARCH CANDIDATES ===")
    print(json.dumps(final_state.get("research_candidates"), indent=2))

    print("\n=== BRIEF ===")
    print(json.dumps(final_state.get("brief"), indent=2))

    print("\n=== REVIEW CHECKLIST ===")
    print(json.dumps(final_state.get("review_checklist"), indent=2))
    print("passed:", final_state.get("review_passed"))

    print("\n=== DRAFT CONTENT ===")
    print(final_state.get("draft_content"))


if __name__ == "__main__":
    main()
