"""
TokenStore: SQLite schema and date-filtered queries.
Uses stdlib sqlite3 only — no SQLAlchemy or external DB libs.
DB path: ../data/tokens.db relative to this file.
"""
import sqlite3
import threading
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "tokens.db"

_lock = threading.Lock()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _lock:
        conn = get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS session (
                    id        TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    scanned_at TEXT NOT NULL,
                    file_size  INTEGER NOT NULL DEFAULT 0,
                    file_mtime TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS turn (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id        TEXT NOT NULL REFERENCES session(id),
                    timestamp         TEXT NOT NULL,
                    attribution_type  TEXT NOT NULL,
                    attribution_name  TEXT NOT NULL,
                    input_tokens      INTEGER NOT NULL DEFAULT 0,
                    output_tokens     INTEGER NOT NULL DEFAULT 0,
                    cache_read_tokens  INTEGER NOT NULL DEFAULT 0,
                    cache_write_tokens INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_turn_session ON turn(session_id);
                CREATE INDEX IF NOT EXISTS idx_turn_ts     ON turn(timestamp);
                CREATE INDEX IF NOT EXISTS idx_turn_attr   ON turn(attribution_type, attribution_name);
            """)
            conn.commit()
        finally:
            conn.close()


def upsert_session(session_id: str, file_path: str, scanned_at: str, file_size: int, file_mtime: str) -> None:
    with _lock:
        conn = get_connection()
        try:
            conn.execute(
                """
                INSERT INTO session (id, file_path, scanned_at, file_size, file_mtime)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    scanned_at = excluded.scanned_at,
                    file_size  = excluded.file_size,
                    file_mtime = excluded.file_mtime
                """,
                (session_id, file_path, scanned_at, file_size, file_mtime),
            )
            conn.commit()
        finally:
            conn.close()


def delete_turns_for_session(session_id: str) -> None:
    with _lock:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM turn WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()


def insert_turns(turns: list[dict]) -> None:
    if not turns:
        return
    with _lock:
        conn = get_connection()
        try:
            conn.executemany(
                """
                INSERT INTO turn
                    (session_id, timestamp, attribution_type, attribution_name,
                     input_tokens, output_tokens, cache_read_tokens, cache_write_tokens)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        t["session_id"], t["timestamp"], t["attribution_type"], t["attribution_name"],
                        t["input_tokens"], t["output_tokens"], t["cache_read_tokens"], t["cache_write_tokens"],
                    )
                    for t in turns
                ],
            )
            conn.commit()
        finally:
            conn.close()


def get_session_cache(session_id: str) -> Optional[dict]:
    conn = get_connection()
    try:
        row = conn.execute("SELECT file_size, file_mtime FROM session WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def query_summary(start: Optional[str], end: Optional[str]) -> list[dict]:
    conn = get_connection()
    try:
        params: list = []
        where = _date_where(start, end, params)
        sql = f"""
            SELECT
                attribution_type  AS category,
                attribution_name  AS name,
                SUM(input_tokens)       AS input,
                SUM(output_tokens)      AS output,
                SUM(cache_read_tokens)  AS cache_read,
                SUM(cache_write_tokens) AS cache_write
            FROM turn
            {where}
            GROUP BY attribution_type, attribution_name
            ORDER BY (SUM(input_tokens) + SUM(output_tokens)) DESC
        """
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def query_by_category(category: str, start: Optional[str], end: Optional[str]) -> list[dict]:
    conn = get_connection()
    try:
        params: list = [category]
        where = "WHERE attribution_type = ?" + _date_suffix(start, end, params)
        sql = f"""
            SELECT
                attribution_type  AS category,
                attribution_name  AS name,
                SUM(input_tokens)       AS input,
                SUM(output_tokens)      AS output,
                SUM(cache_read_tokens)  AS cache_read,
                SUM(cache_write_tokens) AS cache_write
            FROM turn
            {where}
            GROUP BY attribution_name
            ORDER BY (SUM(input_tokens) + SUM(output_tokens)) DESC
        """
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _date_where(start: Optional[str], end: Optional[str], params: list) -> str:
    clauses = []
    if start:
        clauses.append("timestamp >= ?")
        params.append(start)
    if end:
        clauses.append("timestamp <= ?")
        params.append(end + "T23:59:59.999999Z")
    return ("WHERE " + " AND ".join(clauses)) if clauses else ""


def _date_suffix(start: Optional[str], end: Optional[str], params: list) -> str:
    parts = []
    if start:
        parts.append(" AND timestamp >= ?")
        params.append(start)
    if end:
        parts.append(" AND timestamp <= ?")
        params.append(end + "T23:59:59.999999Z")
    return "".join(parts)
