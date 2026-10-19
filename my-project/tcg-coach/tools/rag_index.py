"""Chunk the knowledge markdown into retrievable pieces (deterministic, no LLM).

Usage:  python tools/rag_index.py
Reads every .md under knowledge/gundam-gcg/ (except cards/by-set, which are tables served
by search.py), splits by headings into chunks of at most ~400 words, and writes
knowledge/gundam-gcg/index/chunks.jsonl. Each chunk: id (file#heading-slug[-n]),
file, heading, text, as_of (from an 'as_of: YYYY-MM-DD' line in the file), source.
Run build_db.py afterwards to load the chunks into the SQLite full-text index.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

MAX_WORDS = 400
SKIP_DIRS = {"by-set", "index", "decklists"}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "top"


def chunk_file(path: Path, rel: str) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    as_of = (re.search(r"^as_of:\s*(\S+)", text, re.M) or [None, None])[1]
    source = (re.search(r"^source:\s*(.+)$", text, re.M) or [None, None])[1]
    sections, heading, buf = [], "top", []
    for line in text.splitlines():
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            if buf:
                sections.append((heading, buf))
            heading, buf = m.group(2).strip(), []
        elif not re.match(r"^(as_of|source):", line):
            buf.append(line)
    if buf:
        sections.append((heading, buf))
    chunks = []
    for heading, lines in sections:
        words = " ".join(lines).split()
        if not words:
            continue
        parts = [words[i:i + MAX_WORDS] for i in range(0, len(words), MAX_WORDS)]
        for n, part in enumerate(parts):
            cid = f"{rel}#{slug(heading)}" + (f"-{n + 1}" if len(parts) > 1 else "")
            chunks.append({"id": cid, "file": rel, "heading": heading, "text": " ".join(part),
                           "as_of": as_of, "source": source})
    return chunks


def build() -> list[dict]:
    chunks = []
    for path in sorted(common.KB.rglob("*.md")):
        if SKIP_DIRS & set(path.relative_to(common.KB).parts):
            continue
        chunks.extend(chunk_file(path, path.relative_to(common.KB).as_posix()))
    seen = {}
    for c in chunks:  # make ids unique
        if c["id"] in seen:
            seen[c["id"]] += 1
            c["id"] += f"~{seen[c['id']]}"
        else:
            seen[c["id"]] = 1
    return chunks


def main() -> int:
    common.utf8_stdout()
    chunks = build()
    common.CHUNKS_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with common.CHUNKS_JSONL.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Wrote {len(chunks)} chunks to {common.CHUNKS_JSONL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
