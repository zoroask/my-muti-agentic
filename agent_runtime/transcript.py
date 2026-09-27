"""Append-only JSONL ledger of everything a run did.

One line per event, so a finished run can be read back without replaying it and
without trusting anyone's summary of what happened.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append(path: Path, event: str, **fields: object) -> None:
    """Append one event. Parent directories are created as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"at": timestamp(), "event": event, **fields}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read(path: Path) -> list[dict]:
    """Every event in order. A missing ledger reads as empty, not an error."""
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
