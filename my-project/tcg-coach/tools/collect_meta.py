"""Collect tournament decklists from the approved results sources (deterministic, no LLM).

Usage:
  python tools/collect_meta.py --source egman   [--set-group GD05]
  python tools/collect_meta.py --source topdecks [--page gundam-cg-decks-gd-05-freedom-ascension]
  python tools/collect_meta.py --source all
Approved sources (named by the user, robots.txt checked 2026-10-19):
  egman    - https://deckbuilder.egmanevents.com/gundam/tournaments  (reads its /api/tournaments/gundam data, one request)
  topdecks - https://tcgtopdecks-hq.com/gundamcardgame-decks/          (reads one set page, one request)
Saves decklist facts only (cards + counts, event, date, placement, players, archetype label, colors).
Player names are never saved. Lists already stored (same date + cards) are skipped; new ones are appended to meta/decklists.jsonl.
Only rows dated within LOOKBACK_DAYS of the newest stored list from that source are read; --all-dates reads every row.
Then run: python tools/rebuild_all.py
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

EGMAN_API = "https://deckbuilder.egmanevents.com/api/tournaments/gundam"
EGMAN_PAGE = "https://deckbuilder.egmanevents.com/gundam/tournaments"
TOPDECKS = "https://tcgtopdecks-hq.com/{page}/"
LOOKBACK_DAYS = 14  # results sites post late, so re-read this many days before the newest stored list


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40]


_EXISTING: set | None = None


def existing_lists() -> set:
    """(date, cards) of every saved decklist, so reruns never duplicate a list under another file name."""
    global _EXISTING
    if _EXISTING is None:
        _EXISTING = set()
        from card_usage import iter_decklists
        for d in iter_decklists():
            _EXISTING.add((d["meta"].get("date"), frozenset(d["main"].items())))
    return _EXISTING


def since_date(prefix: str) -> str:
    """Oldest date worth reading from one source: its newest stored list minus LOOKBACK_DAYS ('' = read all)."""
    from card_usage import iter_decklists
    dates = [d["meta"].get("date", "") for d in iter_decklists() if d["file"][11:].startswith(prefix + "-")]
    newest = common.parse_date(max(dates)) if dates else None
    return (newest - timedelta(days=LOOKBACK_DAYS)).isoformat() if newest else ""


def write_list(prefix: str, date: str, event_slug: str, n: int, header: list[str], pairs: list[tuple[str, int]]) -> bool:
    """Append one decklist to meta/decklists.jsonl unless the same list (date + cards) is already stored."""
    key = (date, frozenset(dict(pairs).items()))
    if key in existing_lists():
        return False
    existing_lists().add(key)
    meta = {}
    for h in header:
        k, v = h.lstrip("# ").split(":", 1)
        meta[k.strip()] = v.strip()
    total = sum(c for _, c in pairs)
    meta["total"] = str(total)
    if total != 50:
        meta["note"] = "not exactly 50 main-deck cards (sideboard mixed in?) - excluded from usage stats"
    rec = {"id": f"{date}-{prefix}-{event_slug}-{n:02d}", "meta": meta, "main": dict(pairs)}
    common.DECKLISTS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with common.DECKLISTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return True


def egman_rows(data: list[dict], set_group: str) -> list[dict]:
    rows = []
    for t in data:
        if set_group and t.get("set_group") != set_group:
            continue
        for r in t.get("tournament_results") or []:
            urls = [u for u in ([r.get("deck_list_url")] if isinstance(r.get("deck_list_url"), str) else r.get("deck_list_url") or []) if u]
            if not urls:
                continue
            m = re.search(r"deck=([^&]+)", urls[0])
            pairs = [(no, int(c)) for no, c in re.findall(r"([A-Z]{2,3}\d{2}-\d{3}):(\d+)", m.group(1) if m else "")]
            rows.append({"date": t["start_date"], "event": t["tournament_name"], "type": t.get("event_type"),
                         "format": t.get("format"), "players": t.get("player_count"), "rounds": t.get("rounds"),
                         "place": r.get("placement"), "w": r.get("wins"), "l": r.get("losses"),
                         "label": r.get("deck_type", "") + ("/" + "/".join(r["deck_type_secondary"]) if r.get("deck_type_secondary") else ""),
                         "colors": r.get("deck_colors") or [], "pairs": pairs})
    return rows


def collect_egman(set_group: str, since: str = "") -> tuple[int, int]:
    """Returns (new lists written, rows skipped as older than since)."""
    data = json.loads(common.http_get(EGMAN_API))
    rows = egman_rows(data, set_group)
    fresh = [r for r in rows if r["date"] >= since]
    written, n = 0, Counter()
    for r in sorted(fresh, key=lambda r: (r["date"], r["event"], r["place"] or 0)):
        s = slug(r["event"])
        n[(r["date"], s)] += 1
        rec = f" ({r['w']}-{r['l']})" if r["w"] is not None else ""
        header = [f"# source: {EGMAN_PAGE}", f"# date: {r['date']}", f"# event: {r['event']} ({r['type']}; {r['format']})",
                  "# kind: tournament", f"# name: {r['label']}", f"# colors: {'-'.join(r['colors'])}",
                  f"# placement: {r['place']}{rec}", f"# players: {r['players'] or 'n/a'}", f"# rounds: {r['rounds'] or 'n/a'}"]
        written += write_list("egman", r["date"], s, n[(r["date"], s)], header, r["pairs"])
    return written, len(rows) - len(fresh)


def topdecks_rows(page_html: str) -> list[dict]:
    """Parse the results table. Columns: Deck Composition | ViewDeck | Deck Color | Deck Profile | Deck Name |
    Date | Country | Author | Placement | Tournament | Host. Author (a player name) is ignored."""
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page_html, re.S):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 11 or not re.search(r"\dn[A-Z]{2}\d{2}-\d{3}", cells[0]):
            continue
        try:
            date = datetime.strptime(cells[5], "%m/%d/%Y").strftime("%Y-%m-%d")
        except ValueError:
            continue
        pairs = [(no, int(c)) for c, no in re.findall(r"(\d+)n([A-Z]{2,3}\d{2}-\d{3})", cells[0])]
        players = (re.search(r"\((\d+)\)", cells[10]) or re.search(r"\((\d+)\)", cells[9]) or [None, None])[1]
        rows.append({"date": date, "colors": cells[2], "label": cells[4], "region": cells[6], "place": cells[8],
                     "tour": cells[9], "host": cells[10], "players": players, "pairs": pairs})
    return rows


def collect_topdecks(page: str, since: str = "") -> tuple[int, int]:
    """Returns (new lists written, rows skipped as older than since)."""
    url = TOPDECKS.format(page=page)
    rows = topdecks_rows(common.http_get(url))
    fresh = [r for r in rows if r["date"] >= since]
    written, n = 0, Counter()
    for r in sorted(fresh, key=lambda r: (r["date"], r["tour"], r["host"])):
        s = slug(f"{r['tour']}-{r['host']}")
        n[(r["date"], s)] += 1
        header = [f"# source: {url}", f"# date: {r['date']}", f"# event: {r['tour']} ({r['host']}) - {r['region']}",
                  "# kind: tournament", f"# name: {r['label']}", f"# colors: {r['colors']}", f"# placement: {r['place']}",
                  f"# players: {r['players'] or 'n/a'}"]
        written += write_list("topdecks", r["date"], s, n[(r["date"], s)], header, r["pairs"])
    return written, len(rows) - len(fresh)


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["egman", "topdecks", "all"], required=True)
    ap.add_argument("--set-group", default="GD05", help="Egman set group (format), e.g. GD05; '' for all")
    ap.add_argument("--page", default="gundam-cg-decks-gd-05-freedom-ascension", help="TopDecks HQ set page slug")
    ap.add_argument("--all-dates", action="store_true", help="read every row, not only rows near the newest stored list")
    args = ap.parse_args()
    for prefix, label, collect, arg in (("egman", "Egman", collect_egman, args.set_group),
                                        ("topdecks", "TopDecks HQ", collect_topdecks, args.page)):
        if args.source in (prefix, "all"):
            since = "" if args.all_dates else since_date(prefix)
            written, skipped = collect(arg, since)
            print(f"{label}: {written} new decklist(s); {skipped} row(s) older than {since or '-'} skipped")
    print("Next: python tools/rebuild_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
