"""Practice-log statistics (deterministic, no LLM).

Usage:  python tools/log_stats.py [--log logs/match-log.csv] [--deck "My Deck"] [--since 2026-10-01] [--json]
CSV columns: date,event,my_deck,opp_deck,game,went_first,result,notes  (one row per game)
  result: W / L / D    went_first: Y / N    game: 1, 2 or 3
Outputs win rates per matchup, going first vs second, game 1 vs post-side (games 2-3),
and misplay categories from the notes (keyword groups). Notes that match no group are
listed as "unclassified" for the coach to read.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

MIN_GAMES = 10  # under this, a win rate is "too few to conclude" (tcg-prep-standards)

MISPLAY_GROUPS = {
    "mulligan": ["mulligan", "redraw", "kept", "keep", "ship"],
    "sequencing": ["sequenc", "order", "wrong order", "should have played", "too early", "too late"],
    "resource/curve": ["resource", "curve", "mana", "lv too", "level", "couldn't play", "stuck"],
    "combat/blocking": ["block", "blocker", "attack into", "combat", "trade", "first strike", "math"],
    "shields/burst": ["burst", "shield"],
    "rules/misread": ["misread", "rule", "forgot", "missed trigger", "didn't know"],
    "clock/time": ["time", "clock", "slow", "rushed"],
    "deck/draw": ["flood", "brick", "no draw", "screw", "dead card"],
}


def rate(w: int, n: int) -> str:
    if n == 0:
        return "-"
    pct = f"{100 * w / n:.0f}%"
    return f"{pct} ({w}/{n})" + ("" if n >= MIN_GAMES else " - too few to conclude")


def classify(note: str) -> list[str]:
    low = note.lower()
    return [g for g, words in MISPLAY_GROUPS.items() if any(w in low for w in words)]


def analyse(rows: list[dict]) -> dict:
    out = {"games": len(rows)}
    agg = defaultdict(lambda: [0, 0])
    def bump(key, row):
        agg[key][1] += 1
        agg[key][0] += 1 if row["result"].upper() == "W" else 0
    for r in rows:
        bump(("all",), r)
        bump(("opp", r["opp_deck"]), r)
        bump(("first", r["went_first"].upper()), r)
        bump(("game", "G1" if str(r["game"]).strip() == "1" else "G2-3"), r)
    out["overall"] = rate(*agg[("all",)])
    out["by_matchup"] = sorted(
        [{"opp_deck": k[1], "games": v[1], "win_rate": rate(*v)} for k, v in agg.items() if k[0] == "opp"],
        key=lambda x: -x["games"])
    out["going_first"] = rate(*agg[("first", "Y")])
    out["going_second"] = rate(*agg[("first", "N")])
    out["game1"] = rate(*agg[("game", "G1")])
    out["post_side"] = rate(*agg[("game", "G2-3")])
    cats, unclassified = defaultdict(int), []
    for r in rows:
        note = (r.get("notes") or "").strip()
        if not note:
            continue
        groups = classify(note)
        for g in groups:
            cats[g] += 1
        if not groups:
            unclassified.append(f"{r['date']} vs {r['opp_deck']}: {note}")
    out["misplay_groups"] = dict(sorted(cats.items(), key=lambda x: -x[1]))
    out["unclassified_notes"] = unclassified
    return out


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=str(common.LOG_CSV))
    ap.add_argument("--deck", help="only rows where my_deck equals this")
    ap.add_argument("--since", help="YYYY-MM-DD")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    with open(args.log, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r.get("date")]
    if args.deck:
        rows = [r for r in rows if r["my_deck"] == args.deck]
    if args.since:
        rows = [r for r in rows if r["date"] >= args.since]
    res = analyse(rows)
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    print(f"Games: {res['games']} | overall {res['overall']}")
    print(f"Going first {res['going_first']} | going second {res['going_second']}")
    print(f"Game 1 {res['game1']} | post-side (G2-3) {res['post_side']}")
    print("\nBy matchup:")
    print(common.table(res["by_matchup"], ["opp_deck", "games", "win_rate"]))
    if res["misplay_groups"]:
        print("\nMisplay groups (from notes): " + ", ".join(f"{k} {v}" for k, v in res["misplay_groups"].items()))
    if res["unclassified_notes"]:
        print("\nUnclassified notes (for the coach to read):")
        for n in res["unclassified_notes"]:
            print("  - " + n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
