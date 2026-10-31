"""
TranscriptScanner + AttributionEngine

OQ1 — field names verified against real transcripts on 2026-10-30:
timestamp, message.id, message.usage.*, attributionAgent, attributionSkill,
and <command-name> tags on user lines.  The schema is not officially
documented, so every field access still uses dict.get() with safe fallbacks.
Lines repeating a message.id carry the same usage and are counted once.

Only reads from TRANSCRIPT_DIR.  Never writes to it.
Skips files whose size + mtime are unchanged since the last scan.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from db import (
    delete_turns_for_session,
    get_session_cache,
    insert_turns,
    upsert_session,
)

TRANSCRIPT_DIR = Path(r"C:\Users\zoroa\.claude\projects\D--my-muti-agentic")

logger = logging.getLogger(__name__)


class AttributionEngine:
    """
    Determines (attribution_type, attribution_name) for a single .jsonl line.

    Uses the fields Claude Code writes on assistant lines (verified 2026-10-30):
      - attributionAgent -> subagent type, e.g. "Design Lead"
      - attributionSkill -> skill or slash-command name, e.g. "tcg"
    A skill name the user typed as /name in the same file counts as a command.
    When neither field is set, returns ("main_session", "main_session").
    """

    _CMD_TAG = re.compile(r"<command-name>/?([\w:.-]+)</command-name>")

    def commands_in(self, line: dict) -> list[str]:
        """Names the user typed as /commands on a user line."""
        if line.get("type") != "user":
            return []
        message = line.get("message") if isinstance(line.get("message"), dict) else {}
        content = message.get("content")
        texts = [content] if isinstance(content, str) else [
            b.get("text", "") for b in content or []
            if isinstance(b, dict) and b.get("type") == "text"
        ]
        return [m for t in texts for m in self._CMD_TAG.findall(t or "")]

    def detect(self, line: dict, typed_commands: set[str]) -> tuple[str, str]:
        """Return (attribution_type, attribution_name)."""
        agent = line.get("attributionAgent")
        if agent:
            return ("agent", str(agent))
        skill = line.get("attributionSkill")
        if skill:
            kind = "command" if skill in typed_commands else "skill"
            return (kind, str(skill))
        return ("main_session", "main_session")


class TranscriptScanner:
    """
    Scans TRANSCRIPT_DIR for .jsonl files, extracts token usage, writes to DB.
    Never modifies files in TRANSCRIPT_DIR.
    """

    def __init__(self) -> None:
        self._attribution = AttributionEngine()

    def scan_all(self) -> dict:
        errors: list[dict] = []
        sessions_scanned = 0

        if not TRANSCRIPT_DIR.exists():
            logger.warning("Transcript directory not found: %s", TRANSCRIPT_DIR)
            return {"sessions_scanned": 0, "errors": [
                {"file": str(TRANSCRIPT_DIR), "error": "Directory not found"}
            ]}

        jsonl_files = list(TRANSCRIPT_DIR.rglob("*.jsonl"))
        logger.info("Found %d .jsonl files in %s", len(jsonl_files), TRANSCRIPT_DIR)

        for fpath in jsonl_files:
            try:
                scanned = self._scan_file(fpath)
                if scanned:
                    sessions_scanned += 1
            except Exception as exc:
                logger.error("Unhandled error scanning %s: %s", fpath, exc)
                errors.append({"file": str(fpath), "error": str(exc)})

        status = "ok" if not errors else "partial"
        return {"status": status, "sessions_scanned": sessions_scanned, "errors": errors}

    def _scan_file(self, fpath: Path) -> bool:
        try:
            stat = fpath.stat()
        except OSError as exc:
            logger.warning("Cannot stat %s: %s", fpath, exc)
            return False

        file_size = stat.st_size
        file_mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
        default_session_id = fpath.stem

        cached = get_session_cache(default_session_id)
        if (
            cached
            and cached.get("file_size") == file_size
            and cached.get("file_mtime") == file_mtime
        ):
            logger.debug("Skipping unchanged file: %s", fpath)
            return False

        turns = self._parse_file(fpath, default_session_id)
        if turns is None:
            return False

        scanned_at = datetime.now(tz=timezone.utc).isoformat()
        session_id = default_session_id

        upsert_session(session_id, str(fpath), scanned_at, file_size, file_mtime)
        delete_turns_for_session(session_id)
        insert_turns(turns)
        logger.info("Scanned %s: %d turns", fpath.name, len(turns))
        return True

    def _parse_file(self, fpath: Path, default_session_id: str) -> Optional[list[dict]]:
        turns: list[dict] = []
        seen_ids: set[str] = set()
        typed_commands: set[str] = set()
        try:
            with fpath.open("r", encoding="utf-8", errors="replace") as fh:
                for lineno, raw in enumerate(fh, start=1):
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        line: dict = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        logger.warning("%s line %d: JSON decode error — %s", fpath.name, lineno, exc)
                        continue
                    if not isinstance(line, dict):
                        logger.warning("%s line %d: expected dict, got %s", fpath.name, lineno, type(line))
                        continue
                    typed_commands.update(self._attribution.commands_in(line))
                    msg = line.get("message")
                    mid = msg.get("id") if isinstance(msg, dict) else None
                    if mid:
                        if mid in seen_ids:
                            continue
                        seen_ids.add(mid)
                    turn = self._extract_turn(line, default_session_id, typed_commands)
                    if turn is not None:
                        turns.append(turn)
        except OSError as exc:
            logger.error("Cannot read %s: %s", fpath, exc)
            return None
        return turns

    def _extract_turn(self, line: dict, default_session_id: str, typed_commands: set[str]) -> Optional[dict]:
        """
        OQ1 — UNVERIFIED field names. All access via .get() with fallbacks.
        Fields attempted:
          session_id   : file stem (one session row per .jsonl file)
          timestamp    : line["timestamp"]
          usage        : line["message"]["usage"]
          input_tokens : usage["input_tokens"]
          output_tokens: usage["output_tokens"]
          cache_read   : usage["cache_read_input_tokens"]
          cache_write  : usage["cache_creation_input_tokens"]
        """
        session_id = default_session_id

        timestamp: str = str(line.get("timestamp") or "1970-01-01T00:00:00Z")

        message: dict = line.get("message") or {}
        if not isinstance(message, dict):
            message = {}

        usage: dict = message.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}

        def _safe_int(val) -> int:
            try:
                return int(val) if val is not None else 0
            except (TypeError, ValueError):
                return 0

        input_tokens       = _safe_int(usage.get("input_tokens"))
        output_tokens      = _safe_int(usage.get("output_tokens"))
        cache_read_tokens  = _safe_int(usage.get("cache_read_input_tokens"))
        cache_write_tokens = _safe_int(usage.get("cache_creation_input_tokens"))

        if input_tokens == output_tokens == cache_read_tokens == cache_write_tokens == 0:
            return None

        attribution_type, attribution_name = self._attribution.detect(line, typed_commands)

        return {
            "session_id":         session_id,
            "timestamp":          timestamp,
            "attribution_type":   attribution_type,
            "attribution_name":   attribution_name,
            "input_tokens":       input_tokens,
            "output_tokens":      output_tokens,
            "cache_read_tokens":  cache_read_tokens,
            "cache_write_tokens": cache_write_tokens,
        }
