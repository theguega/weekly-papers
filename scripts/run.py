"""Main entry point — fetch, summarize, render."""

import os
import sys
from pathlib import Path

import yaml

# Allow sibling imports when run as `python scripts/run.py` from the repo root
sys.path.insert(0, str(Path(__file__).parent))

from fetch import fetch_and_filter
from summarize import summarize_papers
from render import generate_digest, update_index


def load_config() -> dict:
    cfg_path = Path(__file__).parent.parent / "config.yaml"
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    docs_dir = Path(__file__).parent.parent / "docs"

    print(f"Fetching papers (last {config['lookback_days']} days)…")
    papers = fetch_and_filter(config)
    print(f"  → {len(papers)} papers selected")

    if not papers:
        print("No papers found this week. Skipping digest generation.")
        return

    print("Summarizing with Gemini Flash…")
    papers = summarize_papers(papers, api_key, config["gemini_model"])
    print(f"  → Done")

    print("Rendering HTML…")
    filename = generate_digest(papers, docs_dir, config["lookback_days"])
    update_index(docs_dir)
    print(f"  → docs/digests/{filename}")
    print(f"  → docs/index.html updated")


if __name__ == "__main__":
    main()
