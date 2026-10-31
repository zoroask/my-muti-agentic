"""Mark stored card analyses as stale (deterministic).

Usage:
  python tools/mark_stale.py --cards GD06-002,ST01-010 [--reason "errata"]
  python tools/mark_stale.py --before 2026-10-16          # analysed before a new set / ban list
  python tools/mark_stale.py --banlist-changed            # ban status differs from when it was analysed
Appends a new record (status=stale, stale_reason in notes) per card; history is kept.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def mark(nos: list[str], reason: str) -> list[str]:
    from analysis_schema import append  # local import avoids a cycle
    current = common.load_analysis()
    done = []
    for no in nos:
        rec = current.get(no)
        if not rec or rec.get("status") == "stale":
            continue
        new = {**rec, "status": "stale", "notes": (rec.get("notes", "") + f" [stale: {reason}]").strip()}
        append(new)
        done.append(no)
    return done


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cards")
    ap.add_argument("--before")
    ap.add_argument("--banlist-changed", action="store_true")
    ap.add_argument("--reason", default="manual")
    args = ap.parse_args()
    current = common.load_analysis()
    targets, reason = [], args.reason
    if args.cards:
        targets = [c.strip().upper() for c in args.cards.split(",")]
    elif args.before:
        targets = [no for no, r in current.items() if r.get("analyzed_at", "") < args.before]
        reason = f"analysed before {args.before}"
    elif args.banlist_changed:
        fmt = common.load_format()
        dated = fmt.get("banlist", {}).get("dated", "")
        targets = [no for no, r in current.items() if r.get("banlist_dated", "") != dated]
        reason = f"ban list changed to {dated}"
    else:
        ap.error("give --cards, --before or --banlist-changed")
    done = mark(targets, reason)
    print(f"Marked {len(done)} stale: {', '.join(done) or '-'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
