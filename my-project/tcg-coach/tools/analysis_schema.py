"""Validate and store per-card analysis summaries (deterministic).

Usage:
  python tools/analysis_schema.py --add record.json      # validate, then append to card_analysis.jsonl
  python tools/analysis_schema.py --check                # validate every stored record
  python tools/analysis_schema.py --template GD06-002    # print a blank record with facts pre-filled
A record is the agent's OWN analysis (role, strengths, conditions...). It must not copy the card's
effect text; 'summary' fields are capped in length and checked against an obvious copy pattern.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

REQUIRED = {
    "card_no": str, "role": str, "strengths": list, "conditions": list, "weaknesses": list,
    "synergy_tags": list, "fits": list, "copies": int, "rating": int, "sources": list,
    "text_hash": str, "analyzed_at": str, "status": str,
}
OPTIONAL = {"notes": str, "banlist_dated": str, "archetype_context": str}
STATUSES = {"fresh", "stale"}
MAX_ITEM_CHARS = 200


def validate(rec: dict) -> list[str]:
    errs = []
    for k, t in REQUIRED.items():
        if k not in rec:
            errs.append(f"missing field: {k}")
        elif not isinstance(rec[k], t):
            errs.append(f"{k} must be {t.__name__}")
    for k in rec:
        if k not in REQUIRED and k not in OPTIONAL:
            errs.append(f"unknown field: {k}")
    if errs:
        return errs
    if rec["status"] not in STATUSES:
        errs.append(f"status must be one of {sorted(STATUSES)}")
    if not 1 <= rec["rating"] <= 5:
        errs.append("rating must be 1-5")
    if not 0 <= rec["copies"] <= 4:
        errs.append("copies must be 0-4")
    if not re.fullmatch(r"[0-9a-f]{64}", rec["text_hash"]):
        errs.append("text_hash must be the 64-char sha256 printed by fetch_card.py")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", rec["analyzed_at"]):
        errs.append("analyzed_at must be YYYY-MM-DD")
    for k in ("role", "strengths", "conditions", "weaknesses"):
        items = rec[k] if isinstance(rec[k], list) else [rec[k]]
        for it in items:
            if len(it) > MAX_ITEM_CHARS:
                errs.append(f"{k}: keep each item under {MAX_ITEM_CHARS} chars (analysis, not a copy of the card text)")
            if "【" in it:
                errs.append(f"{k}: looks like copied effect text (contains 【...】) - describe it in your own words")
    if not rec["sources"]:
        errs.append("sources: cite the official page (and FAQ numbers) with dates")
    return errs


def template(no: str) -> dict:
    cards = common.load_cards()
    c = cards.get(no, {})
    fmt = common.load_format()
    return {"card_no": no, "role": "", "strengths": [], "conditions": [], "weaknesses": [],
            "synergy_tags": [f"trait:{t}" for t in c.get("traits", [])] + [f"link:{l}" for l in c.get("link", [])],
            "fits": [c.get("color") or ""], "copies": 0, "rating": 3,
            "sources": [f"{c.get('url', '')} (read {date.today()})"] + [f"FAQ {f['q']} ({f['date']})" for f in c.get("faq", [])],
            "text_hash": c.get("text_hash") or "", "analyzed_at": str(date.today()), "status": "fresh",
            "banlist_dated": fmt.get("banlist", {}).get("dated", "")}


def append(rec: dict) -> None:
    common.ANALYSIS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with common.ANALYSIS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--add", metavar="FILE")
    g.add_argument("--check", action="store_true")
    g.add_argument("--template", metavar="CARD_NO")
    args = ap.parse_args()
    if args.template:
        print(json.dumps(template(args.template.upper()), indent=2, ensure_ascii=False))
        return 0
    if args.check:
        bad = 0
        for no, rec in common.load_analysis().items():
            errs = validate(rec)
            if errs:
                bad += 1
                print(f"[x] {no}: " + "; ".join(errs))
        print(f"{bad} invalid record(s)")
        return 1 if bad else 0
    rec = json.loads(Path(args.add).read_text(encoding="utf-8"))
    errs = validate(rec)
    if errs:
        print("NOT SAVED:\n  - " + "\n  - ".join(errs))
        return 1
    append(rec)
    print(f"Saved analysis for {rec['card_no']} to {common.ANALYSIS_JSONL}. Run build_db.py to refresh search.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
