"""Refresh cards.json from the official site (facts + tags only; no effect text stored).

Usage:
  python tools/refresh_cards.py                  # full refresh, all product groups (~25-45 min, throttled)
  python tools/refresh_cards.py --only GD06-002  # one or more cards
  python tools/refresh_cards.py --new-only       # detail pages only for card numbers not yet in cards.json (after a new set);
                                                 # stored cards still get new prints/groups from the list pages
Same parsing and tag patterns as tools/scrape_official.js. Runs on your PC (needs internet).
After a refresh run: export_sets.py, rag_index.py, build_db.py (or just: python tools/rebuild_all.py).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

LIST_URL = "https://www.gundam-gcg.com/en/cards/index.php?search=true&package={pkg}"
INDEX_URL = "https://www.gundam-gcg.com/en/cards/"
DELAY = 1.0


def packages() -> dict[str, str]:
    """Read package ids from the live filter list, so new sets are picked up automatically.

    Falls back to the known list in common.PACKAGES if the page layout cannot be read.
    """
    try:
        page = common.http_get(INDEX_URL)
    except OSError:
        return dict(common.PACKAGES)
    found = dict.fromkeys(re.findall(r'data-val="(616\d{3})"', page))
    names = dict(re.findall(r'data-val="(616\d{3})"[^>]*>\s*([^<]+?)\s*<', page))
    out = {}
    for pid in found:
        code = re.search(r"\[([A-Z]{2}\d{2})\]", names.get(pid, ""))
        out[pid] = code.group(1) if code else {"616701": "OTHER", "616000": "BETA", "616801": "BASIC",
                                                "616901": "PROMO"}.get(pid, pid)
    return {**common.PACKAGES, **out} if out else dict(common.PACKAGES)


def merge_prints(existing: dict, membership: dict, skip: set) -> list[str]:
    """Add newly listed groups/prints (reprints) to stored cards that are not re-read. Returns the card numbers changed."""
    changed = []
    for no in sorted(membership.keys() & existing.keys() - skip):
        card = existing[no]
        groups = sorted(set(card.get("groups", [])) | membership[no]["groups"])
        prints = sorted(set(card.get("prints", [])) | membership[no]["prints"])
        if (groups, prints) != (card.get("groups"), card.get("prints")):
            card["groups"], card["prints"] = groups, prints
            changed.append(no)
    return changed


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--new-only", action="store_true")
    args = ap.parse_args()
    existing = common.load_cards() if common.CARDS_JSON.exists() else {}

    membership: dict[str, dict] = {}
    if args.only:
        for no in args.only:
            old = existing.get(no.upper(), {})
            membership[no.upper()] = {"groups": set(old.get("groups", [])), "prints": set(old.get("prints", []))}
    else:
        for pid, code in packages().items():
            page = common.http_get(LIST_URL.format(pkg=pid))
            for cid in dict.fromkeys(re.findall(r'detailSearch=([^"&]+)', page)):
                base = re.sub(r"_p\d+$", "", cid, flags=re.I)
                m = membership.setdefault(base, {"groups": set(), "prints": set()})
                m["groups"].add(code)
                m["prints"].add(cid)
            print(f"list {code}: done", flush=True)
            time.sleep(DELAY)
    todo = [no for no in membership if not (args.new_only and no in existing)]
    if args.new_only:
        reprints = merge_prints(existing, membership, set(todo))
        print(f"{len(reprints)} stored card(s) got new prints/groups (no detail page read)", flush=True)
    print(f"{len(todo)} detail pages to read", flush=True)
    changed = []
    for i, no in enumerate(todo, 1):
        try:
            card = common.public_fields(common.parse_detail(common.http_get(common.OFFICIAL_DETAIL.format(no=no)), no))
            card["groups"] = sorted(membership[no]["groups"])
            card["prints"] = sorted(membership[no]["prints"])
            if existing.get(no, {}).get("text_hash") not in (None, card["text_hash"]):
                changed.append(no)
            existing[no] = card
        except OSError as e:
            print(f"  {no}: {e}", flush=True)
        if i % 50 == 0:
            print(f"  {i}/{len(todo)}", flush=True)
        time.sleep(DELAY)
    out = {"source": "https://www.gundam-gcg.com/en/cards/", "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "note": "Facts and pattern-derived tags only; effect text is not stored. Read it live with fetch_card.py.",
           "cards": sorted(existing.values(), key=lambda c: c["no"])}
    common.CARDS_JSON.parent.mkdir(parents=True, exist_ok=True)
    common.CARDS_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"Wrote {len(existing)} cards to {common.CARDS_JSON}")
    if changed:
        print("Effect text changed (errata?) for: " + ", ".join(changed))
        print("Run: python tools/mark_stale.py --cards " + ",".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
