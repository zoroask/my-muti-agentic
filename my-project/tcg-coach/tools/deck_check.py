"""Deck legality check against data/format.json (deterministic, no LLM).

Usage:  python tools/deck_check.py decks/my-deck.txt [--json]
Checks: main deck size, resource deck size, copies per card number, 1-2 colors,
banned cards, restricted counts, banned pairs, the vanilla-unit rule, unknown cards.
Exit code 0 = legal, 1 = problems found, 2 = input error.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def check(deck: dict, cards: dict, fmt: dict) -> list[dict]:
    rules, bl = fmt["deck"], fmt.get("banlist", {})
    problems: list[dict] = []

    def add(code, msg):
        problems.append({"code": code, "message": msg})

    main, res = deck["main"], deck["resource"]
    for line in deck["unknown"]:
        add("UNPARSED", f"Could not read line: {line.strip()}")
    for no in list(main) + list(res):
        if no not in cards:
            add("UNKNOWN_CARD", f"{no} is not in cards.json (typo, or run refresh_cards.py after a new set)")

    n_main, n_res = sum(main.values()), sum(res.values())
    if n_main != rules["main_size"]:
        add("MAIN_SIZE", f"Main deck has {n_main} cards; must be exactly {rules['main_size']}")
    if n_res != rules["resource_size"]:
        add("RESOURCE_SIZE", f"Resource deck has {n_res} cards; must be exactly {rules['resource_size']}")

    for no, n in main.items():
        if n > rules["max_copies"]:
            add("COPIES", f"{no} x{n}: max {rules['max_copies']} copies per card number")
    for no in res:
        c = cards.get(no)
        if c and c.get("type") not in ("RESOURCE", None):
            add("RESOURCE_TYPE", f"{no} ({c.get('type')}) is in the resource deck but is not a Resource card")
    for no in main:
        c = cards.get(no)
        if c and c.get("type") == "RESOURCE":
            add("MAIN_TYPE", f"{no} is a Resource card; it belongs in the resource deck")

    colors = sorted({cards[no]["color"] for no in main if no in cards and cards[no].get("color")})
    if len(colors) > rules["max_colors"]:
        add("COLORS", f"Deck uses {len(colors)} colors ({', '.join(colors)}); max {rules['max_colors']}")

    everything = {**main}
    for no, n in res.items():
        everything[no] = everything.get(no, 0) + n
    for no in everything:
        if no in bl.get("banned", []):
            add("BANNED", f"{no} {cards.get(no, {}).get('name', '')} is banned")
    for no, limit in bl.get("restricted", {}).items():
        if everything.get(no, 0) > limit:
            add("RESTRICTED", f"{no} x{everything[no]}: restricted to {limit}")
    for a, b in bl.get("banned_pairs", []):
        if a in everything and b in everything:
            add("BANNED_PAIR", f"{a} and {b} cannot be used together")

    rule = bl.get("vanilla_rule")
    if rule:
        vanillas = {no: n for no, n in main.items() if no in cards and common.is_vanilla(cards[no], fmt)}
        if len(vanillas) > rule.get("max_distinct", 1):
            add("VANILLA_PAIR", "More than one different vanilla Lv2/cost1/2AP/2HP Unit: "
                + ", ".join(f"{k} x{v}" for k, v in vanillas.items()) + " (any two form a banned pair)")
        if sum(vanillas.values()) > rule.get("max_total", 4):
            add("VANILLA_TOTAL", f"{sum(vanillas.values())} vanilla Units; max {rule.get('max_total', 4)}")
    return problems


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    path = Path(args.deck)
    if not path.exists():
        print(f"No such file: {path}", file=sys.stderr)
        return 2
    cards, fmt = common.load_cards(), common.load_format()
    deck = common.parse_decklist(path.read_text(encoding="utf-8"), cards)
    problems = check(deck, cards, fmt)
    bl = fmt.get("banlist", {})
    if args.json:
        print(json.dumps({"deck": str(path), "legal": not problems, "problems": problems,
                          "banlist_dated": bl.get("dated"), "rules_version": fmt.get("rules_source", {}).get("version")}, indent=2))
    else:
        print(f"Deck: {path}")
        print(f"Checked against: rules {fmt.get('rules_source', {}).get('version')} | ban list dated {bl.get('dated')}")
        if problems:
            print(f"NOT LEGAL - {len(problems)} problem(s):")
            for p in problems:
                print(f"  [x] {p['code']}: {p['message']}")
        else:
            print("LEGAL")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
