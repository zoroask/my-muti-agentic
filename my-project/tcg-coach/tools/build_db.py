"""Build knowledge/gundam-gcg/tcg.db (SQLite + FTS5) from the JSON sources (deterministic).

Usage:  python tools/build_db.py
Sources (the files are the truth; the DB is generated and git-ignored):
  cards/cards.json, meta/card-usage.json, analysis/card_analysis.jsonl, index/chunks.jsonl
Tables: cards, tags, usage, analysis, chunks (+ FTS5 indexes cards_fts, chunks_fts).
If this Python's SQLite lacks FTS5, plain tables are built and search.py falls back to LIKE.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def fts5_available(con: sqlite3.Connection) -> bool:
    try:
        con.execute("CREATE VIRTUAL TABLE temp.t USING fts5(x)")
        con.execute("DROP TABLE temp.t")
        return True
    except sqlite3.OperationalError:
        return False


def build(db_path: Path | None = None) -> dict:
    db_path = db_path or common.DB_PATH
    cards = common.load_cards()
    fmt = common.load_format()
    usage = common.load_usage()["cards"]
    analysis = common.load_analysis()
    chunks = []
    if common.CHUNKS_JSONL.exists():
        chunks = [json.loads(l) for l in common.CHUNKS_JSONL.read_text(encoding="utf-8").splitlines() if l.strip()]

    tmp = db_path.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    fts = fts5_available(con)
    con.executescript("""
        CREATE TABLE cards(no TEXT PRIMARY KEY, name TEXT, rarity TEXT, type TEXT, color TEXT, lv INT, cost INT,
            ap INT, hp INT, zone TEXT, traits TEXT, link TEXT, source_title TEXT, groups_ TEXT, has_effect INT,
            ban TEXT, vanilla INT, hidden INT, text_hash TEXT, faq TEXT, url TEXT);
        CREATE TABLE tags(no TEXT, kind TEXT, value TEXT);
        CREATE INDEX tags_i ON tags(kind, value);
        CREATE TABLE usage(no TEXT PRIMARY KEY, decks INT, share REAL, avg_copies REAL);
        CREATE TABLE analysis(no TEXT PRIMARY KEY, status TEXT, analyzed_at TEXT, record TEXT);
        CREATE TABLE chunks(id TEXT PRIMARY KEY, file TEXT, heading TEXT, text TEXT, as_of TEXT, source TEXT);
        CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT);
    """)
    for no, c in cards.items():
        con.execute("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            no, c.get("name"), c.get("rarity"), c.get("type"), c.get("color"), c.get("lv"), c.get("cost"),
            c.get("ap"), c.get("hp"), " ".join(c.get("zone") or []), ";".join(c.get("traits") or []),
            ";".join(c.get("link") or []), c.get("source_title"), ";".join(c.get("groups") or []),
            int(bool(c.get("has_effect"))), common.ban_status(no, fmt), int(common.is_vanilla(c, fmt)),
            int(common.is_hidden_by_default(c)), c.get("text_hash"),
            ";".join(f["q"] for f in c.get("faq") or []), c.get("url")))
        for kind in ("triggers", "keywords", "actions", "traits", "link"):
            for v in c.get(kind) or []:
                con.execute("INSERT INTO tags VALUES (?,?,?)", (no, kind.rstrip("s") if kind != "link" else "link", v))
    for no, u in usage.items():
        con.execute("INSERT INTO usage VALUES (?,?,?,?)", (no, u["decks"], u["share"], u["avg_copies"]))
    for no, rec in analysis.items():
        con.execute("INSERT INTO analysis VALUES (?,?,?,?)", (no, rec.get("status"), rec.get("analyzed_at"),
                                                             json.dumps(rec, ensure_ascii=False)))
    for ch in chunks:
        con.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?)",
                    (ch["id"], ch["file"], ch["heading"], ch["text"], ch.get("as_of"), ch.get("source")))
    if fts:
        con.executescript("""
            CREATE VIRTUAL TABLE cards_fts USING fts5(no UNINDEXED, name, traits, link, source_title, tags);
            CREATE VIRTUAL TABLE chunks_fts USING fts5(id UNINDEXED, heading, text);
            INSERT INTO chunks_fts SELECT id, heading, text FROM chunks;
        """)
        for no, c in cards.items():
            tags = " ".join((c.get("triggers") or []) + (c.get("keywords") or []) + (c.get("actions") or []))
            con.execute("INSERT INTO cards_fts VALUES (?,?,?,?,?,?)", (no, c.get("name"), " ".join(c.get("traits") or []),
                        " ".join(c.get("link") or []), c.get("source_title") or "", tags))
    con.execute("INSERT INTO meta VALUES ('fts5', ?)", ("1" if fts else "0",))
    con.execute("INSERT INTO meta VALUES ('banlist_dated', ?)", (fmt.get("banlist", {}).get("dated"),))
    con.commit()
    con.close()
    tmp.replace(db_path)
    return {"cards": len(cards), "usage": len(usage), "analysis": len(analysis), "chunks": len(chunks), "fts5": fts}


def main() -> int:
    common.utf8_stdout()
    stats = build()
    print(f"Built {common.DB_PATH}: " + ", ".join(f"{k}={v}" for k, v in stats.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
