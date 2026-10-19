"""Spot-check cards.json against the live official pages (deterministic, no LLM).

Usage:  python tools/verify_cards.py [--n 20] [--seed 1] [--cards GD06-002,ST01-010]
Re-reads N random cards and compares every stored field (facts, tags, FAQ numbers, text hash).
Mismatches are reported, never silently fixed. Exit code 1 if any mismatch.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

FIELDS = ["name", "rarity", "type", "color", "lv", "cost", "ap", "hp", "zone", "traits", "link",
          "has_effect", "triggers", "keywords", "actions", "text_hash"]


def compare(stored: dict, live: dict) -> list[str]:
    diffs = [f"{f}: stored={stored.get(f)!r} live={live.get(f)!r}" for f in FIELDS if stored.get(f) != live.get(f)]
    sq, lq = [x["q"] for x in stored.get("faq", [])], [x["q"] for x in live.get("faq", [])]
    if sq != lq:
        diffs.append(f"faq: stored={sq} live={lq}")
    return diffs


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--cards")
    args = ap.parse_args()
    cards = common.load_cards()
    picks = [c.strip().upper() for c in args.cards.split(",")] if args.cards else \
        random.Random(args.seed).sample(sorted(cards), min(args.n, len(cards)))
    bad = 0
    for i, no in enumerate(picks):
        if i:
            time.sleep(1)
        live = common.parse_detail(common.http_get(common.OFFICIAL_DETAIL.format(no=no)), no)
        diffs = compare(cards[no], live)
        print(f"[{'x' if diffs else 'ok'}] {no} {cards[no].get('name')}")
        for d in diffs:
            print("     " + d)
        bad += bool(diffs)
    print(f"\n{len(picks) - bad}/{len(picks)} match")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
