"""Live read of a card's official page: full effect text + FAQ (display only, nothing stored).

Usage:  python tools/fetch_card.py GD06-002 [GD05-002 ...] [--no-faq]
Prints the card's facts, its current official effect text and FAQ rulings to the terminal so the
agent can reason over the exact wording. The text is NOT saved anywhere.
Also compares the text fingerprint (sha256) with cards.json and with the stored analysis:
  - mismatch vs cards.json  -> "TEXT CHANGED since the catalog was built (errata?) - run refresh_cards.py"
  - mismatch vs analysis    -> the analysis record is marked stale (mark_stale.py logic)
Runs on your PC (needs internet). Throttled to 1 request per second.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from mark_stale import mark  # noqa: E402


def show(no: str, cards: dict, analysis: dict, with_faq: bool) -> None:
    page = common.http_get(common.OFFICIAL_DETAIL.format(no=no))
    c = common.parse_detail(page, no)
    if not c["name"]:
        print(f"== {no}: not found on the official site ==")
        return
    stats = " | ".join(f"{k} {c[k]}" for k in ("lv", "cost", "ap", "hp") if c[k] is not None)
    print(f"== {no} {c['name']} ({c['rarity']}) - {c['type']} {c['color'] or ''} | {stats}")
    print(f"Traits: {', '.join(c['traits']) or '-'} | Link: {', '.join(c['link']) or '-'} | Zone: {' '.join(c['zone']) or '-'}")
    print(f"Source: {c['url']} (read {time.strftime('%Y-%m-%d')})")
    print("EFFECT (official, live):")
    print("  " + (c["_effect_text"] or "(no effect)"))
    if with_faq and c["_faq_full"]:
        print("FAQ:")
        for f in c["_faq_full"]:
            print(f"  {f['q']} ({f['date']}): Q: {f['question']}  A: {f['answer']}")
    known = cards.get(no)
    if known and known.get("text_hash") and known["text_hash"] != c["text_hash"]:
        print("!! TEXT CHANGED since the catalog was built (errata?) - run: python tools/refresh_cards.py --only " + no)
    rec = analysis.get(no)
    if rec:
        if rec.get("text_hash") != c["text_hash"]:
            mark([no], reason="effect text changed (hash mismatch)")
            print("!! Stored analysis was based on different text - marked STALE; re-analyse this card.")
        else:
            print(f"Stored analysis: {rec.get('status')} (analysed {rec.get('analyzed_at')}) - text unchanged.")
    print(f"text_hash: {c['text_hash']}")
    print()


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", nargs="+")
    ap.add_argument("--no-faq", action="store_true")
    args = ap.parse_args()
    cards = common.load_cards() if common.CARDS_JSON.exists() else {}
    analysis = common.load_analysis()
    for i, no in enumerate(args.cards):
        if i:
            time.sleep(1)
        try:
            show(no.upper(), cards, analysis, not args.no_faq)
        except OSError as e:
            print(f"== {no}: could not reach the official site ({e}) ==")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
