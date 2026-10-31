"""Assemble an agent's reading context in the long-context A/B/C layout (deterministic).

Follows the long-context-lost-in-the-middle skill:
  [A] start  - the top-ranked chunks in full (plus anything piped in, e.g. fetch_card.py output)
  [B] middle - one-line summaries of the supporting chunks
  [C] end    - recap of key facts + the question restated last
Usage:
  python tools/build_context.py "Can a Link Unit attack the turn it is deployed?"
  python tools/fetch_card.py GD06-002 | python tools/build_context.py "How good is this card?" --stdin --top 4
Flags: --top N (chunks in A, default 6), --support N (chunks in B, default 8), --max-words W (budget, default 2500).
Nothing is written to disk; output goes to stdout.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from search import connect, fts_query, has_fts  # noqa: E402


def retrieve(con: sqlite3.Connection, question: str, n: int) -> list[dict]:
    if has_fts(con):
        q = fts_query(question).replace(" ", " OR ")
        sql = ("SELECT c.*, bm25(chunks_fts) AS score FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.id "
               "WHERE chunks_fts MATCH ? ORDER BY score LIMIT ?")
        try:
            return [dict(r) for r in con.execute(sql, (q, n))]
        except sqlite3.OperationalError:
            pass
    words = [w.lower() for w in question.split() if len(w) > 3]
    rows = [dict(r) for r in con.execute("SELECT * FROM chunks")]
    for r in rows:
        r["score"] = -sum(r["text"].lower().count(w) for w in words)
    return sorted([r for r in rows if r["score"] < 0], key=lambda r: r["score"])[:n]


def first_sentence(text: str, limit: int = 30) -> str:
    words = text.split()
    out = []
    for w in words[:limit]:
        out.append(w)
        if w.endswith((".", "!", "?")):
            break
    return " ".join(out) + ("" if out and out[-1].endswith((".", "!", "?")) else " ...")


def build(question: str, piped: str, top: int, support: int, max_words: int) -> str:
    con = connect()
    hits = retrieve(con, question, top + support)
    a, b = hits[:top], hits[top:]
    budget = max_words - len(piped.split()) - len(question.split()) - 60
    kept_a, dropped = [], []
    for h in a:
        n = len(h["text"].split())
        if n <= budget:
            kept_a.append(h)
            budget -= n
        else:
            dropped.append(h["id"])
    banlist = con.execute("SELECT v FROM meta WHERE k='banlist_dated'").fetchone()[0]
    out = ["=== [A] KEY MATERIAL (read closely; cite ids) ==="]
    if piped.strip():
        out += ["--- live input (not stored) ---", piped.strip()]
    for h in kept_a:
        out += [f"--- {h['id']} (as of {h.get('as_of') or '?'}) ---", h["text"]]
    out += ["", "=== [B] SUPPORTING (one line each) ==="]
    for h in b:
        out.append(f"- {h['id']}: {first_sentence(h['text'])}")
    if dropped:
        out.append(f"- (cut for budget: {', '.join(dropped)})")
    out += ["", "=== [C] RECAP ===",
            "- Every section above matters; prefer [A] for exact rules and card text.",
            "- Cite chunk ids or the official URL + date for each claim; say 'unverified' if not covered.",
            f"- Ban list in use: {banlist}",
            "", f"QUESTION: {question}"]
    return "\n".join(out)


def main() -> int:
    common.utf8_stdout()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("question")
    ap.add_argument("--stdin", action="store_true", help="put piped input at the top of [A]")
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--support", type=int, default=8)
    ap.add_argument("--max-words", type=int, default=2500)
    args = ap.parse_args()
    piped = sys.stdin.read() if args.stdin else ""
    print(build(args.question, piped, args.top, args.support, args.max_words))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
