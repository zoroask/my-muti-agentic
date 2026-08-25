# Bug & Issue Fix Checklist (Archived)

> Archived 2026-08-22 — historical record from when this project was a runnable Python CLI multi-agent pipeline (`main.py` → `core/orchestrator.py` → `agents/*.py`). The pipeline has since been retired; the project is now a Claude Code configuration library only. This document no longer reflects current project structure.

Progress: 15 / 15 fixed

---

## S1 — Critical

- [x] **S1-1** `settings.json` — Hook matcher `"Write|Edit|Read"` pipe syntax unverified — hooks may never fire
- [x] **S1-2** `agents/base_agent.py:15` — No error handling on `client.messages.create()` — API errors crash pipeline
- [x] **S1-3** `agents/frontend_coder.py:42` + `backend_coder.py:43` — Regex fails on Windows `\r\n` line endings — extracted files silently empty

## S2 — High

- [x] **S2-1** Root `orchestrator.py` / `file_writer.py` may still exist — wrong module imported silently
- [x] **S2-2** `agents/planner.py:40-45` — No validation of required JSON keys from Planner output
- [x] **S2-3** `path_guard.py:24` — `os.path.abspath()` unreliable when CWD differs

## S3 — Medium

- [x] **S3-1** `core/orchestrator.py:57-80` — Both agents fail simultaneously on last retry — sub-optimal files written
- [x] **S3-2** `requirements.txt` — Versions not pinned (`>=`) — reproducibility risk
- [x] **S3-3** `agents/monitor.py:15` — `AGENT_NAMES` hardcoded — new agents invisible in monitor if forgotten

## M1 — Maintenance Critical

- [x] **M1-1** `agents/frontend_coder.py` + `backend_coder.py` — Duplicate `_plan_summary()` and `_extract_files()` — move to `agents/utils.py`
- [x] **M1-2** `agents/frontend_coder.py:36` + `backend_coder.py:37` — `import json` inside function body
- [x] **M1-3** `docs/agent-workflow.md` — Stale paths (`orchestrator.py` → `core/orchestrator.py`)

## M2 — Maintenance Medium

- [x] **M2-1** `.claude/skills/` — Not connected to `commands/` — no `/promote-skill` automation
- [x] **M2-2** `pyproject.toml:12` — Script entry point `build-app = "main:main"` won't work when installed
- [x] **M2-3** `.claude/agents/pa-project-manager.md` — Bug list outdated (fixed bugs still listed as open)

## M3 — Maintenance Low

- [ ] **M3-1** `core/orchestrator.py` — `MAX_RETRIES = 2` hardcoded, not CLI-configurable
- [ ] **M3-2** `core/orchestrator.py` — No file logging, only Rich console output
- [ ] **M3-3** `agents/base_agent.py` — Model hardcoded, not overridable per-agent or per-run

> Note: M3-1 through M3-3 were left open when the Python pipeline was retired and are now moot — the files they reference no longer exist.

---

## Fixed Log

| ID | Fixed | Notes |
|---|---|---|
| S1-1 | 2026-08-22 | Split pipe matcher into one entry per tool in `.claude/settings.json` |
| S1-2 | 2026-08-22 | Added `try/except` for `AuthenticationError`, `RateLimitError`, `APIConnectionError`, `APIStatusError` in `agents/base_agent.py` |
| S1-3 | 2026-08-22 | Changed `\n` to `\r?\n` in `_extract_files()` regex in both `frontend_coder.py` and `backend_coder.py` |
| S2-1 | 2026-08-22 (corrected) | Originally logged as "deleted stale root `orchestrator.py` and `file_writer.py`" — this was recorded prematurely; the fix was not actually applied at the time and both files remained on disk. They were actually removed on 2026-08-22, but later the same day, as part of the full Python-pipeline retirement cleanup (after `agents/*.py` was deleted and the CLI pipeline was retired entirely) — not as an isolated fix for this item. |
| S2-2 | 2026-08-22 | Added `REQUIRED_KEYS` validation in `PlannerAgent.plan()` — raises `ValueError` with missing key names |
| S2-3 | 2026-08-22 | Replaced `os.path.abspath()` with `isabs()` check in `path_guard.py` — relative paths now resolve against `PROJECT_ROOT` not CWD |
| S3-1 | 2026-08-22 | Reviewer retry now guards reassignment with `if result:` — preserves last good files; added empty-check before `write_files` |
| S3-2 | 2026-08-22 | Pinned `anthropic==1.0.0` and `rich==15.0.0` in `requirements.txt` |
| S3-3 | 2026-08-22 | Removed `AGENT_NAMES` from `monitor.py`; `MonitorAgent` now accepts `agent_names` param; orchestrator passes `[a.name for a in pipeline]` |
| M1-1 | 2026-08-22 | Created `agents/utils.py` with `_plan_summary()` and `_extract_files()`; both coders now import from there |
| M1-2 | 2026-08-22 | `import json` moved to top-level in `agents/utils.py` — resolved as part of M1-1 |
| M1-3 | 2026-08-22 | Updated `docs/agent-workflow.md` — fixed `/add-agent`→`/upsert-agent`, `orchestrator.py`→`core/orchestrator.py`, pipeline pattern, monitor step, hooks table |
| M2-1 | 2026-08-22 | Created `/list-skills` command; added Skills vs Agents definition to `CLAUDE.md` |
| M2-2 | 2026-08-22 | Removed `[project.scripts]` from `pyproject.toml`; synced `dependencies` versions to `==1.0.0` / `==15.0.0` |
| M2-3 | 2026-08-22 | Updated `pa-project-manager.md`, `pa-bug-fixer.md`, `pa-workflow-monitor.md` bug lists to reflect current fixed/open state |
