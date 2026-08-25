# Multi-Agent App Builder

A Claude Code configuration library for designing, prototyping, and reviewing multi-agent system architectures — used entirely inside Claude Code sessions. There is no standalone application to install or run.

## What's here

### `.claude/agents/` — Subagent personas
AI personas with a defined role, project knowledge, and behavioral rules. Each runs as a Claude Code subagent with its own context window:
- Pipeline design personas (`pipeline-planner-agent`, `pipeline-frontend-coder-agent`, `pipeline-backend-coder-agent`, `pipeline-reviewer-agent`) — model the stages of a generation pipeline
- Personal-assistant personas (`pa-*` prefixed) — architect advisor, bug fixer, code mentor, project manager, workflow monitor, audit & testing
- General-purpose personas — architect advisor, backend/frontend coder, bug fixer, code mentor, monitor, planner, project manager, reviewer, workflow monitor, base-agent

Invoke one by name via the Agent/Task tool, or by asking Claude Code directly (e.g. "use the Bug Fixer agent").

### `.claude/skills/` — Procedures
Step-by-step procedures Claude follows itself, with no persona attached:
- `debug-agent.md` — diagnose why an agent definition produces bad output
- `scaffold-agent.md` — create a new agent persona from scratch
- `refine-prompt.md` — improve an agent's system prompt using structured reasoning

Invoke by referencing them in conversation, e.g. "use the debug-agent skill".

### `.claude/commands/` — Slash commands
| Command | Purpose |
|---|---|
| `/upsert-agent` | Add a new agent or update an existing one |
| `/remove-agent` | Safely remove an agent definition |
| `/improve-agent` | Refine an agent's system prompt |
| `/list-agents` | Show all agent definitions |
| `/list-skills` | Show all available skills with usage |
| `/agent-report` | Full audit of all agents |
| `/review-agents` | Review all agents for quality and consistency |

### `.claude/hooks/` — Safety hooks
- `path_guard.py` (PreToolUse: Write/Edit/Read) — blocks file access outside this project directory
- `syntax_check.py` (PostToolUse: Write/Edit) — checks Python syntax on any `.py` file written or edited

## Usage
Open this project in Claude Code, then:
- Invoke an agent persona by name to get its role-specific behavior in a subagent
- Reference a skill by name to have Claude follow its procedure inline
- Run a slash command (e.g. `/list-agents`) to manage agent and skill definitions

## Governance
Every response in this project follows the format defined in `CLAUDE.md`: Summary → Action plan → Before/After → STOP for explicit approval before any change is executed.
