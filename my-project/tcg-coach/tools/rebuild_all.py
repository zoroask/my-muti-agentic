"""Rebuild every generated file after data changes (deterministic).

Usage:  python tools/rebuild_all.py
Runs, in order: export_sets.py -> card_usage.py --current --write -> rag_index.py -> build_db.py -> analysis_schema.py --check
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [["export_sets.py"], ["card_usage.py", "--current", "--write", "--top", "5"], ["rag_index.py"], ["build_db.py"],
         ["analysis_schema.py", "--check"]]


def main() -> int:
    for step in STEPS:
        print(f"\n>>> {' '.join(step)}", flush=True)
        r = subprocess.run([sys.executable, str(HERE / step[0]), *step[1:]])
        if r.returncode != 0:
            print(f"Step failed: {step[0]} (exit {r.returncode})")
            return r.returncode
    print("\nAll generated files are up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
