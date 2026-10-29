# Multi-Agent App Builder

A Claude Code configuration library for designing, prototyping, and reviewing multi-agent system architectures — used entirely inside Claude Code sessions. There is no standalone application to install or run.

## What's here

### `.claude/agents/` — Subagent personas
AI personas with a defined role, project knowledge, and behavioral rules. Each runs as a Claude Code subagent with its own context window:
- Web App cluster (`pipeline-planner-main-agent`, `pipeline-frontend-coder-sub-agent`, `pipeline-backend-coder-sub-agent`, `pipeline-reviewer-sub-agent`) — builds new web apps (React + FastAPI) in `my-project/<subproject>/`; Web App Lead drives the pipeline, calling the other three as sub-agents
- Audit & Testing Core (`pa-right-hand-audit-testing-main-agent`) — main agent for audits and internal/external security testing; delegates sub-project reviews to Automation Reviewer and Web App Reviewer
- Automation cluster (`python-automation-lead-main-agent`, `automation-*-sub-agent`) — Python automation split by area: APIs, scraping, scheduled jobs, desktop/GUI, files/Excel, plus a read-only Automation Reviewer with a fix loop
- Security Learning cluster (`security-lead-main-agent`, `security-*-sub-agent`) — defensive-security and reverse-engineering learning agents behind a single Security Lead front door: RE tutor, CTF study buddy, YARA rule writer, malware report reader, code vulnerability reviewer, dependency/supply-chain checker, secrets scanner; authorization-gated and defensive-only (see the `security-learning-standards` skill)
- Game cluster (`game-lead-main-agent`, `game-*-sub-agent`) — Godot 4 top-down pixel-art games, built one milestone at a time: systems, world/tilemap, pixel art, UI, plus a read-only Game Reviewer with a fix loop
- Design Lead (`design-lead-sub-agent`) — requirement audit, UI spec and design package via `/project-design`; read-only
- REA Lead (`rea-lead-main-agent`) — drives the REA MCP server to analyse how existing software is built
- General-purpose personas — architect advisor, bug fixer, code mentor, project manager, workflow monitor, base-agent, and the retired monitor

Invoke one by name via the Agent/Task tool, or by asking Claude Code directly (e.g. "use the Bug Fixer agent").

### `.claude/skills/` — Procedures
26 skills in `.claude/skills/<name>/SKILL.md`; run `/list-skills` for the full list with triggers.

Invoke by referencing them in conversation, e.g. "use the debug-agent skill".

### `.claude/commands/` — Slash commands
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

### `.claude/hooks/` — Safety hooks
- `path_guard.py` (PreToolUse: Write/Edit/Read/NotebookEdit/Glob/Grep/Bash/PowerShell) — blocks file access outside this project directory
- `env_guard.py` (PreToolUse: Bash/PowerShell) — blocks git commands that would force-add, commit, or push a `.env`-style file
- `syntax_check.py` (PostToolUse: Write/Edit) — checks Python syntax on any `.py` file written or edited
- `notify_done.ps1` (Stop, in `settings.local.json`) — finish notification; launches `notify_popup.ps1` → `focus_session.ps1`

## MCP servers and APIs
| Server | Source | Tools / notes |
|---|---|---|
| `rea` | `.mcp.json` → `npx -y rea-agents@6.7.0 mcp` | Reverse-engineering analysis tools |
| `local-llm` | `ollama_mcp.py` (not registered in `.mcp.json`) | `list_local_models`, `ask_local_llm`, `summarize_file_locally` |

`ollama_mcp.py` env vars: `LLM_BACKEND` (ollama|openai), `LLM_BASE_URL` (default `http://localhost:11434` or `http://localhost:8000/v1`), `LLM_DEFAULT_MODEL`, `LLM_API_KEY`, `LLM_TIMEOUT`.

## Key paths
- `agent_runtime/` — stdlib sequencer and audit: `python -m agent_runtime audit`
- `tools/build_site.py` → `site/index.html` (Multi-Agent Library Overview)
- `my-project/` — subprojects: `job-auto-apply`, `tcg-coach`, `web-show-pre-order-date`
- `path_guard.py` allows only the project root and the memory root (`PATH_GUARD_ROOT`, `PATH_GUARD_MEMORY` override for tests)

## Usage
Open this project in Claude Code, then:
- Invoke an agent persona by name to get its role-specific behavior in a subagent
- Reference a skill by name to have Claude follow its procedure inline
- Run a slash command (e.g. `/list-agents`) to manage agent and skill definitions

## Governance
Every response in this project follows the format defined in `CLAUDE.md`: Summary → Workflow → Action plan → Before/After → STOP for explicit approval before any change is executed.
