## Bug Fixer Proposal — 9 doc-drift findings

All 7 target files were read. Every "Old" text in the Architect Advisor's plan was verified against disk. The proposal below is **read-only** — no files have been changed.

---

### Discrepancies between audit-findings.txt / plan and actual disk

| Finding | audit-findings.txt says | Actual on disk | Status |
|---|---|---|---|
| Finding 2 (base-agent.md) | line 52 | line 53 | Off by 1 in finding; plan correctly says line 53 |
| Finding 6 (list-skills.md) | line 4 | insertion point is after line 23 (last data row) | Finding points at the table header line; plan description ("after Rigorous Verification row") is correct |
| All others | — | exact match | Verified |

---

### Diff 1 — `.claude/commands/commit-push-github.md` lines 48-49

```
OLD:
- `env_guard.py` is wired to the Bash tool only. Git run through the PowerShell
  tool bypasses it, so step 3 is a real check, not a formality.

NEW:
- `env_guard.py` is wired to both the Bash and PowerShell tools. Step 3 is still
  a real check: belt-and-suspenders is the right posture for a hard Rule-4
  obligation.
```

---

### Diff 2 — `.claude/agents/base-agent.md` line 53

```
OLD:
- The only Python that actually executes in this repo is `.claude/hooks/path_guard.py` and `.claude/hooks/syntax_check.py`, invoked by Claude Code's hook system per `.claude/settings.json`

NEW:
- The only Python that actually executes in this repo is `.claude/hooks/path_guard.py`, `.claude/hooks/env_guard.py`, and `.claude/hooks/syntax_check.py`, invoked by Claude Code's hook system per `.claude/settings.json`
```

---

### Diff 3a — `.claude/agents/code-mentor-sub-agent.md` line 20

```
OLD:
- **`.claude/hooks/*.py`** — the only Python that actually executes: `path_guard.py` (blocks file access outside the project) and `syntax_check.py` (AST syntax check after `.py` writes/edits)

NEW:
- **`.claude/hooks/*.py`** — the only Python that actually executes: `path_guard.py` (blocks file access outside the project), `env_guard.py` (blocks git commands that would commit or push a `.env` file), and `syntax_check.py` (AST syntax check after `.py` writes/edits)
```

### Diff 3b — `.claude/agents/code-mentor-sub-agent.md` Key Files section (insert after line 26)

```
OLD (lines 25-28):
## Key Files to Know
- `.claude/hooks/path_guard.py` — the only enforcement mechanism restricting file access to the project root
- `.claude/hooks/syntax_check.py` — the only automated correctness check in the repo
- `.claude/agents/base-agent.md` — shared conventions every persona file follows
- `.claude/settings.json` — wires hooks to tool events

NEW:
## Key Files to Know
- `.claude/hooks/path_guard.py` — the only enforcement mechanism restricting file access to the project root
- `.claude/hooks/syntax_check.py` — the only automated correctness check in the repo
- `.claude/hooks/env_guard.py` — blocks git force-add, commit, and push of `.env`-style files
- `.claude/agents/base-agent.md` — shared conventions every persona file follows
- `.claude/settings.json` — wires hooks to tool events
```

---

### Diff 4 — `README.md` lines 37-38 (hooks section)

```
OLD:
- `path_guard.py` (PreToolUse: Write/Edit/Read) — blocks file access outside this project directory
- `syntax_check.py` (PostToolUse: Write/Edit) — checks Python syntax on any `.py` file written or edited

NEW:
- `path_guard.py` (PreToolUse: Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell) — blocks file access outside this project directory
- `env_guard.py` (PreToolUse: Bash/PowerShell) — blocks git commands that would force-add, commit, or push a `.env`-style file
- `syntax_check.py` (PostToolUse: Write/Edit) — checks Python syntax on any `.py` file written or edited
```

---

### Diff 5 — `README.md` line 34 (commands table — append 4 rows)

```
OLD (line 34, last table row):
| `/audit-chain` | Delegate a task through Architect Advisor → Bug Fixer → PA Right-Hand Audit & Testing, looping on failure |

NEW (insert 4 rows immediately after):
| `/audit-chain` | Delegate a task through Architect Advisor → Bug Fixer → PA Right-Hand Audit & Testing, looping on failure |
| `/focus-project` | Run Pipeline Planner → Coder → Reviewer scoped to a chosen my-project/ subproject, with a required approval gate before writing any file |
| `/run-agents` | Drive a chain through `agent_runtime/`, which enforces agent order, the 3-pass cap and approval gates in code |
| `/full-audit-and-testing` | Audit and test every file in the project and write `audit-report.html` |
| `/commit-push-github` | Commit and push to GitHub, gated on the audit and test suite |
```

---

### Diff 6 — `.claude/commands/list-skills.md` (append row after line 23)

```
OLD (line 23, last data row):
| Rigorous Verification | `verification-rigoureuse.md` | Sourced, certainty-labelled factual answers | "use the verification-rigoureuse skill" |

NEW:
| Rigorous Verification | `verification-rigoureuse.md` | Sourced, certainty-labelled factual answers | "use the verification-rigoureuse skill" |
| Python Automation Standards | `python-automation-standards.md` | Shared rules for Python automation scripts (location, approval flow, script checklist) | "use the python-automation-standards skill" |
```

---

### Diff 7 — `docs/agent-workflow.md` line 72 (path_guard row)

```
OLD:
| `PreToolUse` (Write/Edit/Read) | Before any file is read, written, or edited | Runs `path_guard.py` — blocks access outside `D:\my-muti-agentic\` |

NEW:
| `PreToolUse` (Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell) | Before any file is read, written, edited, searched, or a shell command runs | Runs `path_guard.py` — blocks access outside `D:\my-muti-agentic\` |
```

---

### Diff 8 — `docs/agent-workflow.md` line 73 (env_guard row)

```
OLD:
| `PreToolUse` (Bash) | Before any Bash command runs | Runs `env_guard.py` — blocks git commands that would force-add, commit, or push a `.env`-style file |

NEW:
| `PreToolUse` (Bash/PowerShell) | Before any Bash or PowerShell command runs | Runs `env_guard.py` — blocks git commands that would force-add, commit, or push a `.env`-style file |
```

---

### Diff 9 — `agent_runtime/chains.py` line 73 (ASCII hyphen → em dash)

```
OLD:
                "[ ] (passed) bullets, or exactly 'AUDIT CLEAN - no issues found'."

NEW:
                "[ ] (passed) bullets, or exactly 'AUDIT CLEAN — no issues found'."
```

---

### Files involved

1. `.claude/commands/commit-push-github.md`
2. `.claude/agents/base-agent.md`
3. `.claude/agents/code-mentor-sub-agent.md`
4. `README.md`
5. `.claude/commands/list-skills.md`
6. `docs/agent-workflow.md`
7. `agent_runtime/chains.py`

All 9 findings are addressed. Awaiting explicit approval before applying any change.
