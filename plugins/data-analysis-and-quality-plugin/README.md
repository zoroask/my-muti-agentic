# data-analysis-and-quality-plugin

A Claude Code plugin built from the `.claude/` folder of
[zoroask/my-muti-agentic](https://github.com/zoroask/my-muti-agentic).

## Install

From GitHub:

```
/plugin marketplace add zoroask/my-muti-agentic
/plugin install data-analysis-and-quality-plugin@zoroask-my-muti-agentic
```

From a local clone: `/plugin marketplace add <path-to-clone>`, then the same install line.

Plugin names are namespaced, e.g. `/data-analysis-and-quality-plugin:focus-project`.

## Contents

- `agents/` — 36 subagent personas (architecture, audit, automation, web app, game, design, security learning, DQA data quality)
- `skills/` — 28 skills (plus their reference files and an index `README.md`), including `plugin-rules` (language, approval gate, secrets) that the other files cite
- `commands/` — 10 slash commands: agent-report, audit-chain, focus-project, improve-agent, list-agents, list-skills, project-design, remove-agent, review-agents, upsert-agent
- `hooks/` — `env_guard.py` (blocks committing or pushing `.env` files) and `syntax_check.py` (Python syntax check after Write/Edit)

`<project-root>/` in any file means the project you opened Claude Code in.

## Requirements

- Claude Code
- Python 3 on PATH, for the two hooks
- Optional: a `local-llm` MCP server for RE Tutor. Without it, that agent loses its local-LLM tools.

## Not included

The source repo's `CLAUDE.md`, memory, `agent_runtime/`, personal settings and Windows notification hooks, `path_guard.py` (machine-specific), the retired Monitor agent, and the repo-only commands `run-agents`, `commit-push-github`, `full-audit-and-testing`, `update-detail-project`, `list-my-command` and `tcg`.
