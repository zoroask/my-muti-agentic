# Token Usage Monitor — Improvements and Hand-off

**Date:** 2026-10-30
**Status:** Working prototype. Reads real transcripts; splits usage by agent, skill, command and main session.
**Owner for changes:** Web App Lead, via `/focus-project` → `token-usage-monitor`.

---

## Current state

| Area | State |
|---|---|
| Backend | FastAPI + stdlib sqlite3, `127.0.0.1:8000` only |
| Frontend | React 18 + Vite + Tailwind, built to `backend/dist/`, offline |
| Data | `data/tokens.db`, filled on **Refresh** only (history view, not real-time) |
| Start | `start.bat` (creates venv, installs, builds, starts, opens browser) |
| Verified | 79 sessions scanned, 0 errors; agent/skill/command tabs populated (2026-10-30) |

### Verified transcript fields (OQ1 closed 2026-10-30)
- Counted lines: `type == "assistant"` with `message.usage`.
- `attributionAgent` → agent name (e.g. `Design Lead`).
- `attributionSkill` → skill or command name; counted as **command** if typed as `<command-name>/x</command-name>` earlier in the same file.
- Lines repeat one `message.id` with identical usage: count each id once (5,018 lines → 2,175 messages).
- Subagent transcripts live in `<session>/subagents/*.jsonl`; each file is its own session row.
- Not yet used: `attributionMcpServer`, `message.model`, `cost-state` lines.

---

## Recommended improvements (priority order)

### P1 — Correctness
1. **Timezone on date filter.** Timestamps are UTC; the picker uses local date (UTC+7). Send UTC bounds from the frontend (`start 00:00 local → UTC`), or store a local date column.
2. **Keep history before Claude Code deletes transcripts.** Old transcripts are removed after `cleanupPeriodDays` (default about 30 days; confirm). Add a daily scheduled Refresh (Task Scheduler → `POST /api/refresh`, or a CLI `python scanner.py`). Deleted files keep their rows, because rows are replaced only when a file changes.
3. **Same name in two categories** (e.g. `project-design` as skill and command). Show the category in chart labels and the Overview table, e.g. `project-design (command)`.

### P2 — Useful additions
4. **MCP category.** Use `attributionMcpServer` (e.g. `ccd_turn`, `local-llm`) as a 5th tab or a tag.
5. **Model column.** Store `message.model` per turn; show tokens per model.
6. **Cost estimate (optional).** Read `cost-state.totalCostUSD`, or apply a local price table. No API calls (R8).
7. **Nested context.** An agent run inside a command counts only as the agent. Add a `parent_command` column if a "by command, including its agents" view is wanted.
8. **Auto-refresh toggle** (e.g. every 60 s) for a near-real-time view.

### P3 — Code quality
9. Routes are `async` but call sync SQLite → change to plain `def` (FastAPI runs them in a threadpool).
10. `@app.on_event("startup")` is deprecated → use a `lifespan` handler.
11. `App.tsx`: ignore stale fetch responses on fast tab/date changes; toast ids from `Date.now()` can collide → use a counter.
12. `TRANSCRIPT_DIR` is hard-coded with the username → read from an env var with this as default.
13. Add `pytest` tests for `scanner.py` using small synthetic `.jsonl` fixtures (agent, skill, typed command, duplicate ids, bad JSON). Never commit real transcripts.

### P4 — Housekeeping
14. **`.gitignore`**: `backend/.venv/`, `frontend/node_modules/`, `backend/dist/`, `data/tokens.db*`, `.edge-profile/`.
15. **npm audit**: 3 vulnerabilities (1 moderate, 2 high) reported on install; review before any update. `esbuild` install script was blocked by npm but the build worked.
16. **`start.bat`**: detect a busy port 8000 and print a clear message.
17. **Update `DESIGN.md`**: no `screens/` folder (`App.tsx` renders all tabs); `tokens.db` is created on server start; OQ1 resolved; `pydantic` pinned to `2.14.2` (Python 3.14 wheels).

---

## Hand-off checklist

- [ ] Run `start.bat`; dashboard opens at `http://127.0.0.1:8000`.
- [ ] Click **Refresh**; toast shows sessions scanned, 0 errors.
- [ ] By Agent / By Skill / By Command each show rows.
- [ ] Pick P1 items first; run each through `/focus-project` (approval-gated).
- [ ] After a scanner change: delete `data/tokens.db*`, then Refresh (unchanged files are otherwise skipped).
- [ ] Never store or commit prompt/response text or real transcripts (R7).

## Key files
| File | Role |
|---|---|
| `backend/scanner.py` | Reads `.jsonl`, de-duplicates, attributes, writes turns |
| `backend/db.py` | SQLite schema and date-filtered queries |
| `backend/routes/*.py` | `/api/summary`, `/api/by-{agent,skill,command}`, `/api/refresh` |
| `frontend/src/App.tsx` | Tabs, date filter, Refresh, data loading |
| `start.bat` | One-click setup and start |
| `demo/diagrams.html` | Data-flow diagrams (phone-friendly) |
