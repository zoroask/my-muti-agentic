# Claude Code Configuration Library — Project Rules

## Strict Rules (Always Enforced)

1. **English only** — All responses, comments, commit messages, and documentation must be written in English. No exceptions, except Thai trigger keywords in `.claude/skills/README.md`, which exist only so Thai requests match a skill. Replies stay English regardless of the request language.

2. **No modifications outside this project** — Never read, write, edit, or delete any file outside `D:\my-muti-agentic\` without explicit user permission. This includes system files, other projects, and global config files.

3. **Response format** — Keep replies short, clear, in basic English: common words, max 15 words per sentence, no filler, greeting or recap. Never drop not, never, no, only, except. Keep code, paths, numbers, errors exact. Limits: Summary ≤3 bullets; Workflow ≤4 steps or "N/A"; Action plan ≤5 bullets; Before / After diff lines only, or "N/A"; STOP one full sentence. Use full sentences for security warnings and irreversible actions. "normal mode" turns this off. Every response must begin with these five sections, in order, none dropped:
   - **Summary** — detail as bullet points explaining what and why
   - **Workflow** — the flow of the thing being discussed, as a numbered or ASCII step diagram: what moves through which stage, in order. Show it whenever a request involves more than one stage, tool, or agent; write "N/A" for a single-step answer. This is the system's flow, not my task list — the task list belongs in Action plan.
   - **Action plan** — bullet list of steps to be taken
   - **Before / After** — show exact changes for any code or config edit
   - **STOP** — wait for explicit user approval ("yes") before executing any change. Never auto-execute after showing a plan. Exception: inside the automation review loop, fixes for Automation Reviewer findings are applied without a new approval, within the limits in `.claude/skills/python-automation-standards/SKILL.md` (Fix-loop limits).
   - **Process** — requests with more than one stage, tool or agent follow `.claude/skills/core-process/SKILL.md`; its stage 6 is this rule.

4. **Never commit or push `.env`** — `.env` (and any `.env.*` file except `.env.example`) must never be staged, committed, or pushed. Enforced by `env_guard.py`, which blocks force-adds and blocks commit/push while a `.env` file is staged.

---

## Project Purpose
A Claude Code configuration library for designing and prototyping multi-agent system architectures. This project provides reusable subagent personas (`.claude/agents/*.md`), procedural skills (`.claude/skills/*/SKILL.md`), and slash commands (`.claude/commands/*.md`) for building, reviewing, and iterating on multi-agent system designs directly inside Claude Code. All model work executes inside a Claude Code session. `agent_runtime/` is a stdlib-only Python state machine that sequences those subagent invocations and enforces pass caps and approval gates as code — it never calls an LLM API itself, so it adds no cost.

---

## Hooks
Run the Python audit only after a system change: edits to `.claude/` (agents, skills, commands, hooks, settings), `agent_runtime/`, or `CLAUDE.md`. Skip it for chat-only work, memory, and `my-project/` content.
Project hooks are configured in `.claude/settings.json`.
- **PreToolUse (Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell)**: `path_guard.py` — blocks paths outside `D:\my-muti-agentic\` (the memory directory is also allowed). Checks `file_path`, `notebook_path`, `path` and batch-edit targets. For Bash/PowerShell it catches only *literal* absolute paths — a variable or a `cd` defeats it, so treat that part as a speed bump, not containment.
- **PreToolUse (Bash/PowerShell)**: `env_guard.py` — blocks git commands that would force-add, commit, or push a `.env`-style file, including a force-add of a directory that would sweep one in. Fails closed if git cannot be queried.
- **PostToolUse (Write/Edit .py files)**: `syntax_check.py` — catches Python syntax errors immediately
- See `.claude/settings.json` and `.claude/hooks/` for details

---

## Skills vs Agents

- **Skill** (`.claude/skills/*/SKILL.md`) — a step-by-step procedure Claude follows itself. No persona, no memory. Invoked by referencing in conversation: "use the debug-agent skill" or "follow the scaffold-agent skill".
- **Agent** (`.claude/agents/*.md`) — an AI persona with a defined role, deep project knowledge, and behavioral rules. Invoked as a Claude Code subagent with its own context window.

Never put procedural steps in an agent file. Never put persona/role definitions in a skill file.

---

## Custom Commands
| Command | Purpose |
|---|---|
| `/upsert-agent` | Add a new agent or update an existing one |
| `/remove-agent` | Safely remove an agent definition |
| `/improve-agent` | Refine an agent's system prompt |
| `/list-agents` | Show all agent definitions |
| `/list-skills` | Show all available skills with usage |
| `/list-my-command` | List every slash command with its purpose, and flag table drift |
| `/update-detail-project` | Sync README.md, API/MCP/path details, scripts and site/index.html with the real project, approval-gated |
| `/agent-report` | Full audit of all agents |
| `/review-agents` | Review all agents for quality and consistency |
| `/audit-chain` | Delegate a task through Architect Advisor → Bug Fixer → PA Right-Hand Audit & Testing, looping on failure |
| `/focus-project` | Web App cluster: run Web App Lead → Coder → Reviewer scoped to a chosen my-project/ subproject, with a required approval gate before writing any file |
| `/tcg` | TCG Coach cluster: Gundam Card Game prep (card search, deck review, meta, practice, event plan) via TCG Lead in my-project/tcg-coach, write-gated |
| `/project-design` | Design Lead: requirement audit → system type → UI spec → design, diagrams, schedule and offline demo for a my-project/ idea; writes DESIGN.md + demo only after approval |
| `/run-agents` | Drive a chain through `agent_runtime/`, which enforces agent order, the 3-pass cap and approval gates in code |
| `/full-audit-and-testing` | Audit and test every file in the project and write `audit-report.html` |
| `/commit-push-github` | Commit and push to GitHub, gated on the audit and test suite |

---

## Skill Triggers
At the start of every chat, and whenever a request matches a trigger below (English or Thai, or the same intent in other words), read the matching skill file in `.claude/skills/` before acting and follow it. Skills never override Rule 3. Reply in English whatever the trigger language.

@.claude/skills/README.md

### Always-on skills
These two skills load in every session. Apply their rules throughout; run their full step lists only when a trigger above matches.

@.claude/skills/token-optimization/SKILL.md
@.claude/skills/rescue-tokens/SKILL.md

---

## Memory
Project memory is stored in `C:\Users\zoroa\.claude\projects\D--my-muti-agentic\memory\`, indexed from `MEMORY.md`. Each entry is its own `.md` file with YAML frontmatter (`name`, `description`, `metadata.type`, `metadata.updated`). Types: `user`, `feedback`, `project`, `reference`. All `user` knowledge lives in one file, `user-profile.md`. Detail that does not fit an entry goes in `details/<name>.md`, opened only on demand.

Budget (the single source for these numbers; memory is re-read every session):
- `MEMORY.md`: index only, one line per entry: `- [type] name — description (≤15 words) #tag #tag → file.md`; max 40 lines
- Entry body: max 12 lines; `Summary`, `Why` and `Ref` lines are required
- `details/<name>.md`: max 60 lines, including a dated `## History` section
- `user-profile.md`: max 40 lines; every line ends `(confirmed|corrected YYYY-MM-DD)`
- Never store secrets, full diffs, logs or transcripts; point to them with `Ref:`

Compression rule: recall first, precision second. If unsure whether a detail matters, move it to `details/`, never drop it. Constraints, exceptions, rejected alternatives, exact values and the user's own words are copied verbatim, never paraphrased.

Standing practice:
- Session start: read `MEMORY.md` and `user-profile.md` only. Brief check-in: ask if anything changed, and re-confirm any profile line older than 60 days.
- Read and write memory as `.claude/skills/core-process/SKILL.md` Stage 2 and Stage 10 describe.
- Prefer asking over silently inferring; confirm an inferred preference before saving it, at most one such question per session.
- Every save shows the saved entry text in the reply; "forget <name>" removes it.
