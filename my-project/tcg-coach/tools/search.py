"""Card search: most-used cards first, then the rest of the catalog (deterministic, no LLM).

Usage examples:
  python tools/search.py --color Blue --trait Orb --type UNIT --max-cost 3 --keyword Blocker
  python tools/search.py "Strike Freedom"            # full-text over name, traits, link, tags
  python tools/search.py --action bounce --trigger Deploy --legal-only
  python tools/search.py --rules "first strike damage"   # search the rules notes instead of cards
Flags: --all (include Edition Beta / Promo-only cards), --legal-only (drop banned),
       --limit N (per part), --json.
Output part 1 "Played in the meta" (ranked by usage share, then avg copies) and part 2
"Other matches" (marked low/no usage). Each row shows ban status and the stored analysis status.
Requires tcg.db (run build_db.py).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def connect() -> sqlite3.Connection:
    if not common.DB_PATH.exists():
        raise SystemExit("tcg.db not found - run: python tools/build_db.py")
    con = sqlite3.connect(common.DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def has_fts(con) -> bool:
    row = con.execute("SELECT v FROM meta WHERE k='fts5'").fetchone()
    return bool(row and row[0] == "1")


def fts_query(text: str) -> str:
    """Turn free text into a safe FTS5 query: each word as a prefix term, AND-ed."""
    words = [w for w in "".join(ch if ch.isalnum() else " " for ch in text).split() if w]
    return " ".join(f'"{w}"*' for w in words)


def search_cards(con, args) -> list[dict]:
    where, params = ["1=1"], []
    if not args.all:
        where.append("c.hidden = 0")
    if args.legal_only:
        where.append("c.ban NOT IN ('BANNED')")
    for col, val in (("c.color", args.color), ("c.type", args.type)):
        if val:
            where.append(f"UPPER({col}) = UPPER(?)")
            params.append(val)
    for col, lo, hi in (("c.cost", args.min_cost, args.max_cost), ("c.lv", args.min_lv, args.max_lv)):
        if lo is not None:
            where.append(f"{col} >= ?")
            params.append(lo)
        if hi is not None:
            where.append(f"{col} <= ?")
            params.append(hi)
    for kind, values in (("trait", args.trait), ("keyword", args.keyword), ("trigger", args.trigger),
                         ("action", args.action), ("link", args.link)):
        for v in values or []:
            where.append("EXISTS (SELECT 1 FROM tags t WHERE t.no = c.no AND t.kind = ? AND LOWER(t.value) LIKE LOWER(?))")
            params += [kind, f"{v}%"]
    rank_sql = "0"
    if args.query:
        if has_fts(con):
            where.append("c.no IN (SELECT no FROM cards_fts WHERE cards_fts MATCH ?)")
            params.append(fts_query(args.query))
        else:
            where.append("(LOWER(c.name) LIKE LOWER(?) OR LOWER(c.traits) LIKE LOWER(?))")
            params += [f"%{args.query}%"] * 2
    sql = f"""
        SELECT c.*, COALESCE(u.share, 0) AS share, COALESCE(u.avg_copies, 0) AS avg_copies, COALESCE(u.decks, 0) AS decks,
               a.status AS analysis_status, {rank_sql} AS rank
        FROM cards c LEFT JOIN usage u ON u.no = c.no LEFT JOIN analysis a ON a.no = c.no
        WHERE {' AND '.join(where)}
        ORDER BY share DESC, avg_copies DESC, c.no
    """
    return [dict(r) for r in con.execute(sql, params)]


def search_rules(con, text: str, limit: int) -> list[dict]:
    if has_fts(con):
        sql = "SELECT c.id, c.heading, c.as_of, snippet(chunks_fts, 2, '[', ']', ' ... ', 18) AS snip, bm25(chunks_fts) AS score " \
              "FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.id WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?"
        return [dict(r) for r in con.execute(sql, (fts_query(text).replace(" ", " OR "), limit))]
    like = f"%{text}%"
    return [dict(r) for r in con.execute("SELECT id, heading, as_of, substr(text,1,160) AS snip FROM chunks "
                                         "WHERE text LIKE ? OR heading LIKE ? LIMIT ?", (like, like, limit))]


COLS = ["no", "name", "type", "color", "lv", "cost", "ap", "hp", "tags", "usage", "ban", "analysis"]


def fmt_row(r: dict, con) -> dict:
    tags = [f"{t['kind'][:3]}:{t['value']}" for t in con.execute(
        "SELECT kind, value FROM tags WHERE no=? AND kind IN ('keyword','trigger','action')", (r["no"],))]
    return {**r, "tags": " ".join(tags[:8]) + (" ..." if len(tags) > 8 else ""),
            "usage": f"{100 * r['share']:.0f}% x{r['avg_copies']}" if r["share"] else "low/none",
            "ban": r["ban"] or "", "analysis": r["analysis_status"] or "-"}


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?")
    ap.add_argument("--color"), ap.add_argument("--type")
    ap.add_argument("--trait", action="append"), ap.add_argument("--keyword", action="append")
    ap.add_argument("--trigger", action="append"), ap.add_argument("--action", action="append")
    ap.add_argument("--link", action="append")
    ap.add_argument("--min-cost", type=int), ap.add_argument("--max-cost", type=int)
    ap.add_argument("--min-lv", type=int), ap.add_argument("--max-lv", type=int)
    ap.add_argument("--all", action="store_true"), ap.add_argument("--legal-only", action="store_true")
    ap.add_argument("--rules", metavar="TEXT", help="search rules notes instead of cards")
    ap.add_argument("--limit", type=int, default=15), ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    con = connect()

    if args.rules:
        hits = search_rules(con, args.rules, args.limit)
        if args.json:
            print(json.dumps(hits, indent=2, ensure_ascii=False))
        else:
            print(common.table(hits, ["id", "heading", "as_of", "snip"]))
        return 0

    rows = search_cards(con, args)
    played = [fmt_row(r, con) for r in rows if r["share"] > 0][: args.limit]
    others = [fmt_row(r, con) for r in rows if r["share"] == 0][: args.limit]
    meta = json.loads(common.USAGE_JSON.read_text(encoding="utf-8"))["meta"] if common.USAGE_JSON.exists() else {}
    if args.json:
        print(json.dumps({"usage_meta": meta, "played": played, "others": others, "total_matches": len(rows)},
                         indent=2, ensure_ascii=False))
        return 0
    print(f"{len(rows)} matching cards" + ("" if args.all else " (Edition Beta / Promo-only hidden; --all to include)"))
    if meta:
        print(f"Usage data: {meta.get('decklists')} decklists, {meta.get('period')}, kinds {meta.get('kinds')}"
              + (" - LOW CONFIDENCE" if meta.get("low_confidence") else ""))
    print("\n## Played in the meta")
    print(common.table(played, COLS) if played else "(none - no usage data for these filters)")
    print("\n## Other matches (low / no usage)")
    print(common.table(others, COLS))
    if len(rows) > len(played) + len(others):
        print(f"\n... {len(rows) - len(played) - len(others)} more; narrow the filters or raise --limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
