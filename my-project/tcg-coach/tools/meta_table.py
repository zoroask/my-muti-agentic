"""Meta table with sample sizes and staleness flags (deterministic, no LLM).

Usage:  python tools/meta_table.py [--since YYYY-MM-DD] [--kind tournament] [--top 8]
A group whose latest decklist is older than format.json "stale_before" is flagged STALE.
"official-featured" decks are showcase lists from the official site, NOT tournament results;
the table says so, and the coach must not present them as meta share.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from archetypes import group  # noqa: E402
from card_usage import LOW_CONFIDENCE_DECKS, load_decklists  # noqa: E402


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since")
    ap.add_argument("--kind", choices=["tournament", "official-featured"])
    ap.add_argument("--top", type=int, default=8)
    args = ap.parse_args()
    cards, fmt = common.load_cards(), common.load_format()
    decks = load_decklists(cards, args.since, args.kind)
    groups = group(decks, cards)
    stale_before = fmt.get("stale_before", "")
    kinds = {d["meta"].get("kind", "?") for d in decks}
    print(f"Decklists: {len(decks)} | kinds: {', '.join(sorted(kinds)) or '-'} | stale before: {stale_before}")
    if len(decks) < LOW_CONFIDENCE_DECKS:
        print(f"LOW CONFIDENCE: under {LOW_CONFIDENCE_DECKS} decklists")
    if kinds == {"official-featured"}:
        print("NOTE: only official featured decks - these show what the publisher highlights, not what wins.")
    rows = []
    for g in groups[: args.top]:
        rows.append({"archetype": g["archetype"], "aka (source names)": "; ".join(g["names"]), "decks": g["decks"], "share": f"{100 * g['share']:.0f}%",
                     "latest": g["latest"], "kinds": ",".join(g["kinds"]),
                     "flag": "STALE" if g["latest"] and g["latest"] < stale_before else ""})
    print(common.table(rows, ["archetype", "decks", "share", "latest", "flag", "aka (source names)"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
