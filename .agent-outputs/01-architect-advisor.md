## Design: Fix 9 doc-drift findings from audit-findings.txt

**Ground truth confirmed from `.claude/settings.json`:**
- path_guard.py fires on: `Write|Edit|Read|NotebookEdit|Glob|Grep|Bash|PowerShell` (8 tools)
- env_guard.py fires on: `Bash|PowerShell` (both shell tools, not Bash only)
- syntax_check.py fires on: `Write|Edit`

---

### Six files to touch (9 findings resolved across them)

---

**File 1: `.claude/commands/commit-push-github.md` lines 48–49** — Finding 1 [M]

The claim that env_guard is Bash-only and PowerShell bypasses it is false since settings.json commit d168f87.

Old:
```
- `env_guard.py` is wired to the Bash tool only. Git run through the PowerShell
  tool bypasses it, so step 3 is a real check, not a formality.
```
New:
```
- `env_guard.py` is wired to both the Bash and PowerShell tools. Step 3 is still
  a real check: belt-and-suspenders is the right posture for a hard Rule-4
  obligation.
```

---

**File 2: `.claude/agents/base-agent.md` line 53** — Finding 2 [M]

Old:
```
- The only Python that actually executes in this repo is `.claude/hooks/path_guard.py` and `.claude/hooks/syntax_check.py`, invoked by Claude Code's hook system per `.claude/settings.json`
```
New:
```
- The only Python that actually executes in this repo is `.claude/hooks/path_guard.py`, `.claude/hooks/env_guard.py`, and `.claude/hooks/syntax_check.py`, invoked by Claude Code's hook system per `.claude/settings.json`
```

---

**File 3: `.claude/agents/code-mentor-sub-agent.md` line 20** — Finding 3 [M]

Old (line 20):
```
- **`.claude/hooks/*.py`** — the only Python that actually executes: `path_guard.py` (blocks file access outside the project) and `syntax_check.py` (AST syntax check after `.py` writes/edits)
```
New:
```
- **`.claude/hooks/*.py`** — the only Python that actually executes: `path_guard.py` (blocks file access outside the project), `env_guard.py` (blocks git commands that would commit or push a `.env` file), and `syntax_check.py` (AST syntax check after `.py` writes/edits)
```
Also add to the Key Files section (after the syntax_check.py bullet):
```
- `.claude/hooks/env_guard.py` — blocks git force-add, commit, and push of `.env`-style files
```

---

**File 4: `README.md`** — Findings 4 [M] and 5 [M]

*Finding 4* — hooks section (lines 37–38):

Old:
```
- `path_guard.py` (PreToolUse: Write/Edit/Read) — blocks file access outside this project directory
- `syntax_check.py` (PostToolUse: Write/Edit) — checks Python syntax on any `.py` file written or edited
```
New (the path_guard tool scope was also understated in this bullet, corrected in the same edit):
```
- `path_guard.py` (PreToolUse: Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell) — blocks file access outside this project directory
- `env_guard.py` (PreToolUse: Bash/PowerShell) — blocks git commands that would force-add, commit, or push a `.env`-style file
- `syntax_check.py` (PostToolUse: Write/Edit) — checks Python syntax on any `.py` file written or edited
```

*Finding 5* — commands table: add 4 missing rows after the `/audit-chain` row:
```
| `/focus-project` | Run Pipeline Planner → Coder → Reviewer scoped to a chosen my-project/ subproject, with a required approval gate before writing any file |
| `/run-agents` | Drive a chain through `agent_runtime/`, which enforces agent order, the 3-pass cap and approval gates in code |
| `/full-audit-and-testing` | Audit and test every file in the project and write `audit-report.html` |
| `/commit-push-github` | Commit and push to GitHub, gated on the audit and test suite |
```

---

**File 5: `.claude/commands/list-skills.md`** — Finding 6 [M]

Add row after the `Rigorous Verification` row (currently the last table row):
```
| Python Automation Standards | `python-automation-standards.md` | Shared rules for Python automation scripts (location, approval flow, script checklist) | "use the python-automation-standards skill" |
```

---

**File 6: `docs/agent-workflow.md` lines 72–73** — Findings 7 [L] and 8 [L]

*Finding 7* — path_guard row:

Old:
```
| `PreToolUse` (Write/Edit/Read) | Before any file is read, written, or edited | Runs `path_guard.py` — blocks access outside `D:\my-muti-agentic\` |
```
New:
```
| `PreToolUse` (Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell) | Before any file is read, written, edited, searched, or a shell command runs | Runs `path_guard.py` — blocks access outside `D:\my-muti-agentic\` |
```

*Finding 8* — env_guard row:

Old:
```
| `PreToolUse` (Bash) | Before any Bash command runs | Runs `env_guard.py` — blocks git commands that would force-add, commit, or push a `.env`-style file |
```
New:
```
| `PreToolUse` (Bash/PowerShell) | Before any Bash or PowerShell command runs | Runs `env_guard.py` — blocks git commands that would force-add, commit, or push a `.env`-style file |
```

---

**File 7: `agent_runtime/chains.py` line 73** — Finding 9 [L]

ASCII hyphen → em dash, to match the PA Right-Hand persona's own declared output format at `.claude/agents/pa-right-hand-audit-testing-sub-agent.md:103`.

Old:
```python
                "[ ] (passed) bullets, or exactly 'AUDIT CLEAN - no issues found'."
```
New:
```python
                "[ ] (passed) bullets, or exactly 'AUDIT CLEAN — no issues found'."
```

---

### What is deliberately NOT being done

- **`tests/test_state.py` line 20** (`CLEAN = "AUDIT CLEAN - no issues found"`): the finding confirms `classify()` scans for `[x]` lines, not the exact phrase, so the ASCII-hyphen constant works correctly as a sample input. Changing it would be noise with no correctness benefit.
- **`CLAUDE.md`**: already names all three hooks with correct scopes. Not touched.
- **`.claude/commands/audit-chain.md`**: already uses the em dash. Not touched.
- **Hook Python logic** in `.claude/hooks/`: all 9 findings are documentation drift against already-correct wiring. No behavior changes.
- **README.md prose** beyond the two targeted edits: only the table and the hooks bullets are changed, not the surrounding descriptive text.
- **Memory or project config**: the stale claims are confined to the 6 documentation/code files named above.
