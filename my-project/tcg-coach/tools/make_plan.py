"""Generate a prep-plan skeleton for an event (deterministic; the coach adds priorities).

Usage:
  python tools/make_plan.py --event "Store Championship" --date 2026-11-14 --deck decks/my-deck.txt [--sessions-per-week 3]
  ... add --write to save plans/<event-slug>.md (only after the user approved the plan)
Fills: days left, a week-by-week session grid ending on the event date, the event-day checklist,
and the latest deck_check result. Leaves 'Priorities' for the coach to fill from the specialists' findings.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

CHECKLIST = [
    "Decklist registered / submitted before the deadline",
    "Deck sleeved + spare sleeves",
    "Resource deck (10) separate and sleeved",
    "Deck box, playmat",
    "EX Base / EX Resource tokens, damage counters, dice",
    "Photo ID / player registration (Bandai TCG+ account if required)",
    "Water and food",
    "Travel time + arrival 30 min early",
    "Comprehensive Rules and ban list open on phone",
]


def schedule(today: date, event: date, per_week: int) -> list[str]:
    lines, week_start, n = [], today, 1
    while week_start <= event:
        week_end = min(week_start + timedelta(days=6), event)
        sessions = per_week if (week_end - week_start).days >= 5 else max(1, per_week * ((week_end - week_start).days + 1) // 7)
        final = week_end == event
        lines.append(f"### Week {n}: {week_start} - {week_end}" + (" (event week)" if final else ""))
        for s in range(1, sessions + 1):
            lines.append(f"- Session {s}: goal: ____  (matchup / drill)  | games: __ | logged: [ ]")
        if final:
            lines.append("- Last 2 days: no deck changes; light games only; check ban list again")
        week_start, n = week_end + timedelta(days=1), n + 1
    return lines


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--event", required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--deck")
    ap.add_argument("--tier", default="local")
    ap.add_argument("--sessions-per-week", type=int, default=3)
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    today = date.fromisoformat(args.today) if args.today else date.today()
    event = date.fromisoformat(args.date)
    if event < today:
        raise SystemExit("Event date is in the past.")
    fmt = common.load_format()
    check = "(no deck given)"
    if args.deck:
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("deck_check.py")), args.deck],
                           capture_output=True, text=True, encoding="utf-8")
        check = r.stdout.strip()
    md = [f"# Prep plan: {args.event}", "",
          "| Field | Value |", "|---|---|",
          f"| Event | {args.event} |", f"| Date | {event} |", f"| Tier | {args.tier} |",
          f"| Days left | {(event - today).days} (from {today}) |", f"| Deck | {args.deck or '-'} |",
          f"| Ban list | {fmt['banlist']['dated']} |", f"| Rules | Ver. {fmt['rules_source']['version']} |", "",
          "## Deck check", "```", check, "```", "",
          "## Priorities (coach fills from Deck Analyst / Meta Coach / Practice Coach findings)",
          "1. ", "2. ", "3. ", "",
          "## Schedule", *schedule(today, event, args.sessions_per_week), "",
          "## Event-day checklist", *[f"- [ ] {c}" for c in CHECKLIST], ""]
    text = "\n".join(md)
    if args.write:
        slug = re.sub(r"[^a-z0-9]+", "-", args.event.lower()).strip("-")
        out = common.ROOT / "plans" / f"{slug}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text)
        print("\n(preview only - add --write after approval)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
