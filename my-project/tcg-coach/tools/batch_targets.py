"""List the most-used cards that still need an analysis (deterministic).

Usage:  python tools/batch_targets.py [--top 100]
Ranks cards by usage share (card-usage.json) and prints those with no analysis or a stale one,
so an optional batch pre-analysis spends LLM effort only on cards people actually play.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--top", type=int, default=100)
    args = ap.parse_args()
    cards, usage, analysis = common.load_cards(), common.load_usage()["cards"], common.load_analysis()
    rows = []
    for no, u in list(usage.items())[: args.top]:
        status = analysis.get(no, {}).get("status")
        if status != "fresh":
            rows.append({"no": no, "name": cards.get(no, {}).get("name", "?"), "share": f"{100 * u['share']:.0f}%",
                         "analysis": status or "missing"})
    print(f"{len(rows)} of the top {args.top} used cards need analysis")
    print(common.table(rows, ["no", "name", "share", "analysis"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
