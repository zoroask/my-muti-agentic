"""Card usage statistics from collected decklists (deterministic, no LLM).

Usage:  python tools/card_usage.py [--current | --since 2026-09-25 --kind tournament] [--write]
Reads knowledge/gundam-gcg/meta/decklists.jsonl (collected lists: {"id", "meta": {...}, "main": {no: n}})
and knowledge/gundam-gcg/meta/decklists/*.txt (your own lists). A .txt file is one decklist with header lines:
  # source: <url>          # date: YYYY-MM-DD
  # event: <name>          # kind: tournament | official-featured
  # name: <archetype or list name>   (optional)
Writes meta/card-usage.json (with --write) and prints the top cards.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

LOW_CONFIDENCE_DECKS = 20
SKIPPED: list[str] = []  # decklists left out because they are not exactly 50 main-deck cards
DUPLICATES: list[str] = []  # same list reported by two sources for the same event


def iter_decklists(cards: dict | None = None):
    """Collected lists (decklists.jsonl) first, then your own .txt files, each as {'meta','main','resource','file'}."""
    if common.DECKLISTS_JSONL.exists():
        for line in common.DECKLISTS_JSONL.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                yield {"meta": rec["meta"], "main": rec["main"], "resource": {}, "unknown": [], "file": rec["id"]}
    if common.DECKLISTS_DIR.exists():
        for path in sorted(common.DECKLISTS_DIR.glob("*.txt")):
            d = common.parse_decklist(path.read_text(encoding="utf-8"), cards)
            d["file"] = path.name
            yield d


def _day(s: str) -> int:
    d = common.parse_date(s)
    return d.toordinal() if d else 0


def load_decklists(cards: dict | None = None, since: str | None = None, kind: str | None = None) -> list[dict]:
    """Load decklists, skipping non-50-card lists and cross-source duplicates.

    A duplicate is an identical 50-card list dated within 2 days of one already loaded
    (the same event reported by two results sites). The first file in name order is kept.
    """
    decks = []
    seen: dict[frozenset, list[int]] = {}
    SKIPPED.clear()
    DUPLICATES.clear()
    for d in iter_decklists(cards):
        meta = d["meta"]
        if since and (meta.get("date") or "") < since:
            continue
        if kind and meta.get("kind") != kind:
            continue
        if sum(d["main"].values()) != 50:  # e.g. lists that mix in a sideboard; counts would be skewed
            d["skipped"] = True
            SKIPPED.append(d["file"])
            continue
        key, day = frozenset(d["main"].items()), _day(meta.get("date", ""))
        if any(abs(day - other) <= 2 for other in seen.get(key, [])):
            DUPLICATES.append(d["file"])
            continue
        seen.setdefault(key, []).append(day)
        decks.append(d)
    return decks


def usage(decks: list[dict]) -> dict:
    per = defaultdict(lambda: {"decks": 0, "copies": 0})
    for d in decks:
        for no, n in d["main"].items():
            per[no]["decks"] += 1
            per[no]["copies"] += n
    total = len(decks)
    out = {}
    for no, v in per.items():
        out[no] = {"decks": v["decks"], "share": round(v["decks"] / total, 3) if total else 0,
                   "avg_copies": round(v["copies"] / v["decks"], 2)}
    dates = sorted(d["meta"].get("date", "") for d in decks if d["meta"].get("date"))
    kinds = defaultdict(int)
    for d in decks:
        kinds[d["meta"].get("kind", "unknown")] += 1
    meta = {"decklists": total, "period": [dates[0], dates[-1]] if dates else None, "kinds": dict(kinds),
            "low_confidence": total < LOW_CONFIDENCE_DECKS,
            "sources": sorted({d["meta"].get("source", "") for d in decks if d["meta"].get("source")})}
    return {"meta": meta, "cards": dict(sorted(out.items(), key=lambda kv: (-kv[1]["share"], -kv[1]["avg_copies"])))}


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since")
    ap.add_argument("--kind", choices=["tournament", "official-featured"])
    ap.add_argument("--current", action="store_true",
                    help="tournament lists dated on/after format.json stale_before (falls back to all lists if none)")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--write", action="store_true", help="write meta/card-usage.json")
    args = ap.parse_args()
    cards = common.load_cards()
    if args.current:
        since = common.load_format().get("stale_before")
        decks = load_decklists(cards, since, "tournament")
        if not decks:
            print("No current tournament decklists - using all decklists (check the kinds below).")
            decks = load_decklists(cards)
    else:
        decks = load_decklists(cards, args.since, args.kind)
    res = usage(decks)
    m = res["meta"]
    print(f"Decklists: {m['decklists']} | period {m['period']} | kinds {m['kinds']}"
          + (" | LOW CONFIDENCE (under 20 lists)" if m["low_confidence"] else ""))
    if SKIPPED:
        print(f"Left out {len(SKIPPED)} list(s) that are not exactly 50 main-deck cards (e.g. sideboard mixed in).")
    if DUPLICATES:
        print(f"Left out {len(DUPLICATES)} duplicate list(s) reported by more than one source.")
    rows = [{"no": no, "name": cards.get(no, {}).get("name", "?"), "share": f"{100 * v['share']:.0f}%",
             "avg_copies": v["avg_copies"], "decks": v["decks"]} for no, v in list(res["cards"].items())[: args.top]]
    print(common.table(rows, ["no", "name", "share", "avg_copies", "decks"]))
    if args.write:
        common.USAGE_JSON.parent.mkdir(parents=True, exist_ok=True)
        common.USAGE_JSON.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\nWrote {common.USAGE_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
