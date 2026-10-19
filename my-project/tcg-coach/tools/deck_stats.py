"""Deck statistics: counts, curve and opening-hand odds (deterministic, no LLM).

Usage:
  python tools/deck_stats.py decks/my-deck.txt
  python tools/deck_stats.py decks/my-deck.txt --key GD05-002,ST04-001 --key EB01-041
Each --key is a group of card numbers counted together ("any of these").
Odds use the hypergeometric distribution: P(at least 1 card of the group among the
first N cards seen), for N = 5 (opening hand, before redraw) up to 12.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def p_at_least_one(deck_size: int, copies: int, seen: int) -> float:
    if copies <= 0:
        return 0.0
    if seen >= deck_size:
        return 1.0
    return 1 - comb(deck_size - copies, seen) / comb(deck_size, seen)


def p_with_redraw(deck_size: int, copies: int, hand: int = 5) -> float:
    """Opening hand with the optional one-time full redraw taken only when the first hand misses.

    The redraw puts the hand on the bottom and redraws from the remaining cards (rule 6-2-1-6),
    so the second hand is drawn from deck_size - hand cards that still contain every copy.
    """
    p1 = p_at_least_one(deck_size, copies, hand)
    p2 = p_at_least_one(deck_size - hand, copies, hand)
    return p1 + (1 - p1) * p2


def stats(deck: dict, cards: dict, keys: list[list[str]], deck_size: int) -> dict:
    main = deck["main"]
    known = {no: n for no, n in main.items() if no in cards}
    color, typ, lv, cost = Counter(), Counter(), Counter(), Counter()
    for no, n in known.items():
        c = cards[no]
        color[c.get("color") or "none"] += n
        typ[c.get("type") or "?"] += n
        if c.get("lv") is not None:
            lv[c["lv"]] += n
        if c.get("cost") is not None:
            cost[c["cost"]] += n
    units = [(no, n) for no, n in known.items() if cards[no].get("type") == "UNIT"]
    pilots_link = Counter()
    for no, n in known.items():
        if cards[no].get("type") == "PILOT":
            pilots_link[cards[no]["name"]] += n
    link_targets = []
    for no, n in units:
        for need in cards[no].get("link", []):
            have = sum(v for name, v in pilots_link.items() if need.lower() in name.lower())
            link_targets.append({"unit": f"{no} {cards[no]['name']}", "needs": need, "pilots_in_deck": have})
    odds = []
    for group in keys:
        copies = sum(main.get(no, 0) for no in group)
        row = {"group": "+".join(group), "copies": copies,
               "open_5": round(p_at_least_one(deck_size, copies, 5), 3),
               "open_5_with_redraw": round(p_with_redraw(deck_size, copies), 3)}
        for seen in range(6, 13):
            row[f"seen_{seen}"] = round(p_at_least_one(deck_size, copies, seen), 3)
        odds.append(row)
    return {
        "main_count": sum(main.values()), "resource_count": sum(deck["resource"].values()),
        "colors": dict(color), "types": dict(typ),
        "lv_curve": dict(sorted(lv.items())), "cost_curve": dict(sorted(cost.items())),
        "avg_cost_nonresource": round(sum(k * v for k, v in cost.items()) / max(1, sum(cost.values())), 2),
        "link_coverage": link_targets, "odds": odds,
        "unknown_cards": [no for no in main if no not in cards],
    }


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--key", action="append", default=[], help="comma-separated card numbers counted as one group")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    cards, fmt = common.load_cards(), common.load_format()
    deck = common.parse_decklist(Path(args.deck).read_text(encoding="utf-8"), cards)
    keys = [[x.strip().upper() for x in k.split(",") if x.strip()] for k in args.key]
    s = stats(deck, cards, keys, fmt["deck"]["main_size"])
    if args.json:
        print(json.dumps(s, indent=2, ensure_ascii=False))
        return 0
    print(f"Main {s['main_count']} | Resource {s['resource_count']} | avg cost {s['avg_cost_nonresource']}")
    print("Colors: " + ", ".join(f"{k} {v}" for k, v in s["colors"].items()))
    print("Types:  " + ", ".join(f"{k} {v}" for k, v in s["types"].items()))
    print("Lv curve:   " + "  ".join(f"Lv{k}:{v}" for k, v in s["lv_curve"].items()))
    print("Cost curve: " + "  ".join(f"{k}:{v}" for k, v in s["cost_curve"].items()))
    if s["link_coverage"]:
        print("\nLink coverage (pilots in deck whose name contains the link condition):")
        print(common.table(s["link_coverage"], ["unit", "needs", "pilots_in_deck"]))
    if s["odds"]:
        print("\nOdds of at least one (hypergeometric):")
        print(common.table(s["odds"], ["group", "copies", "open_5", "open_5_with_redraw", "seen_6", "seen_8", "seen_10", "seen_12"]))
    if s["unknown_cards"]:
        print("\nUnknown cards (not in cards.json): " + ", ".join(s["unknown_cards"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
