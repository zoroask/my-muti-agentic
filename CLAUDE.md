# Claude Code Configuration Library — Project Rules

## Strict Rules (Always Enforced)

1. **English only** — All responses, comments, commit messages, and documentation must be written in English. No exceptions, except Thai trigger keywords in `.claude/skills/README.md`, which exist only so Thai requests match a skill. Replies stay English regardless of the request language.

2. **No modifications outside this project** — Never read, write, edit, or delete any file outside `D:\my-muti-agentic\` without explicit user permission. This includes system files, other projects, and global config files.

3. **Response format** — Every response must begin with:
   - **Summary** — detail as bullet points explaining what and why
   - **Workflow** — the flow of the thing being discussed, as a numbered or ASCII step diagram: what moves through which stage, in order. Show it whenever a request involves more than one stage, tool, or agent; write "N/A" for a single-step answer. This is the system's flow, not my task list — the task list belongs in Action plan.
   - **Action plan** — bullet list of steps to be taken
   - **Before / After** — show exact changes for any code or config edit
   - **STOP** — wait for explicit user approval ("yes") before executing any change. Never auto-execute after showing a plan.

4. **Never commit or push `.env`** — `.env` (and any `.env.*` file except `.env.example`) must never be staged, committed, or pushed. Enforced by `env_guard.py`, which blocks force-adds and blocks commit/push while a `.env` file is staged.

---

## Project Purpose
A Claude Code configuration library for designing and prototyping multi-agent system architectures. This project provides reusable subagent personas (`.claude/agents/*.md`), procedural skills (`.claude/skills/*.md`), and slash commands (`.claude/commands/*.md`) for building, reviewing, and iterating on multi-agent system designs directly inside Claude Code. All model work executes inside a Claude Code session. `agent_runtime/` is a stdlib-only Python state machine that sequences those subagent invocations and enforces pass caps and approval gates as code — it never calls an LLM API itself, so it adds no cost.

---

## Hooks
Project hooks are configured in `.claude/settings.json`.
- **PreToolUse (Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell)**: `path_guard.py` — blocks paths outside `D:\my-muti-agentic\` (the memory directory is also allowed). Checks `file_path`, `notebook_path`, `path` and batch-edit targets. For Bash/PowerShell it catches only *literal* absolute paths — a variable or a `cd` defeats it, so treat that part as a speed bump, not containment.
- **PreToolUse (Bash/PowerShell)**: `env_guard.py` — blocks git commands that would force-add, commit, or push a `.env`-style file, including a force-add of a directory that would sweep one in. Fails closed if git cannot be queried.
- **PostToolUse (Write/Edit .py files)**: `syntax_check.py` — catches Python syntax errors immediately
- See `.claude/settings.json` and `.claude/hooks/` for details

---

## Skills vs Agents

- **Skill** (`.claude/skills/*.md`) — a step-by-step procedure Claude follows itself. No persona, no memory. Invoked by referencing in conversation: "use the debug-agent skill" or "follow the scaffold-agent skill".
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
| `/agent-report` | Full audit of all agents |
| `/review-agents` | Review all agents for quality and consistency |
| `/audit-chain` | Delegate a task through Architect Advisor → Bug Fixer → PA Right-Hand Audit & Testing, looping on failure |
| `/focus-project` | Run Pipeline Planner → Coder → Reviewer scoped to a chosen my-project/ subproject, with a required approval gate before writing any file |
| `/run-agents` | Drive a chain through `agent_runtime/`, which enforces agent order, the 3-pass cap and approval gates in code |
| `/full-audit-and-testing` | Audit and test every file in the project and write `audit-report.html` |
| `/commit-push-github` | Commit and push to GitHub, gated on the audit and test suite |

---

## Skill Triggers
At the start of every chat, and whenever a request matches a trigger below (English or Thai, or the same intent in other words), read the matching skill file in `.claude/skills/` before acting and follow it. Skills never override Rule 3. Reply in English whatever the trigger language.

@.claude/skills/README.md

---

## Memory
Project memory is stored in `C:\Users\zoroa\.claude\projects\D--my-muti-agentic\memory\`, indexed from `MEMORY.md`. Each entry is its own `.md` file with YAML frontmatter (`name`, `description`, `metadata.type`); `MEMORY.md` itself is just a one-line-per-entry index, never the content. Four types are in use: `user` (who the user is, working style, priorities), `feedback` (guidance on how to work with them), `project` (ongoing work/decisions), `reference` (pointers to external systems).

Standing practice:
- At the start of a new session in this project, give a brief check-in — surface what's currently known about the user/project and ask if anything's changed — before diving into task work. Keep it light, not an interview.
- Prefer asking directly over silently inferring when a preference would materially change how work gets done.
- When writing a new memory entry, say so in the response rather than saving invisibly.
- Update memory when architecture decisions change, or when something durable and non-obvious is learned about the user or how they want to work.
