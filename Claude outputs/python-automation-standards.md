# Skill: Python Automation Standards

Shared rules for every Python automation script. Followed by the Automation cluster (Python Automation Lead and its five specialists), and by anyone writing an automation script directly.

## Steps
1. **Location** — scripts live in `my-project/<subproject>/`. Ask which subproject if it was not given. Never write scripts into `.claude/`.
2. **Read first** — read any existing code in that subproject before proposing anything.
3. **Clarify** — inputs, outputs, schedule, and what should happen on failure. Ask; don't guess.
4. **Propose** — a short plan plus the exact Before/After diff (or the full new file). Wait for an explicit "yes" (CLAUDE.md Rule 3).
5. **Write** — only the approved files.
6. **Verify** — `python -m py_compile <file>`, then a `--dry-run` where it is safe to run.
7. **Report** — how to run it, how to schedule it, and where the logs go.

## Every script has
- An `argparse` CLI with a `--dry-run` flag that changes nothing
- `logging` to the console and to a rotating log file in the subproject's `logs/` folder
- Explicit timeouts on all network and process calls; clear error messages; a non-zero exit code on failure
- Type hints and a module docstring stating what it automates
- A pinned `requirements.txt` and a short `README.md` with run and schedule instructions

## Hard rules
- Secrets (API keys, passwords, tokens) come from environment variables or a `.env` file only — never hard-coded. `.env` is never committed (CLAUDE.md Rule 4); ship a `.env.example` instead.
- Never delete or overwrite user files. Write outputs beside their sources, or move unwanted files to a `_to_delete/` folder.
- One script, one job. Split unrelated tasks into separate scripts.
- Standard library first; add a third-party package only when it clearly saves effort.
