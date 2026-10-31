"""Group decklists into archetypes (deterministic, no LLM).

Group key (default --by signature): deck colors (sorted) + the deck's main Unit, chosen by a fixed rule
(the Unit with 3+ copies that has the highest Lv; ties: more copies, then card no). The same rule is
applied to every list, so results sites that name decks differently still land in one group.
Each group shows the names the sources used ("aka"). --by label groups by those names instead.
Usage:  python tools/archetypes.py [--since YYYY-MM-DD] [--kind tournament] [--by signature|label] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from card_usage import load_decklists  # noqa: E402


def main_unit(deck: dict, cards: dict) -> str | None:
    units = [(cards[no].get("lv") or 0, n, no) for no, n in deck["main"].items()
             if no in cards and cards[no].get("type") == "UNIT" and n >= 3]
    units.sort(key=lambda t: (-t[0], -t[1], t[2]))
    return units[0][2] if units else None


def signature(deck: dict, cards: dict) -> str:
    main = deck["main"]
    colors = sorted({cards[no]["color"] for no in main if no in cards and cards[no].get("color")})
    unit = main_unit(deck, cards)
    return "-".join(colors or ["?"]) + " | " + (f"{unit} {cards[unit]['name']}" if unit else "no 3-of units")


def group(decks: list[dict], cards: dict, by: str = "signature") -> list[dict]:
    groups = defaultdict(list)
    for d in decks:
        label = d["meta"].get("name") if by == "label" and d["meta"].get("kind") == "tournament" else None
        groups[label or signature(d, cards)].append(d)
    total = len(decks)
    out = []
    for sig, ds in groups.items():
        dates = sorted(d["meta"].get("date", "") for d in ds)
        sigs = Counter(signature(d, cards) for d in ds)
        out.append({"archetype": sig, "signature": sigs.most_common(1)[0][0], "decks": len(ds), "share": round(len(ds) / total, 3) if total else 0,
                    "latest": dates[-1] if dates else "", "kinds": sorted({d["meta"].get("kind", "?") for d in ds}),
                    "names": [n for n, _ in Counter(d["meta"].get("name") for d in ds if d["meta"].get("name")).most_common(4)],
                    "files": [d["file"] for d in ds]})
    return sorted(out, key=lambda g: (-g["decks"], g["archetype"]))


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since")
    ap.add_argument("--kind", choices=["tournament", "official-featured"])
    ap.add_argument("--by", choices=["signature", "label"], default="signature")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    cards = common.load_cards()
    groups = group(load_decklists(cards, args.since, args.kind), cards, args.by)
    if args.json:
        print(json.dumps(groups, indent=2, ensure_ascii=False))
    else:
        print(common.table([{**g, "share": f"{100 * g['share']:.0f}%", "kinds": ",".join(g["kinds"]),
                             "names": "; ".join(g["names"])} for g in groups],
                           ["archetype", "decks", "share", "latest", "kinds", "names"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
