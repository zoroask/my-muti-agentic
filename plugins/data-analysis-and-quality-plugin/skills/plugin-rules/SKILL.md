---
name: plugin-rules
description: "Shared rules every agent, skill and command in this plugin refers to: language, approval gate before changes, and secrets handling. Use when another plugin file cites 'plugin-rules', or when the user asks for the plugin's working rules."
---

# Skill: Plugin Rules

Other files in this plugin cite these sections as `plugin-rules § <section>`.

## Language
Replies, comments, commit messages and documentation are in English, whatever language the request uses.

## Approval gate
Before any file change, reply with these sections, in this order:
- **Summary**: what will change and why, as bullets.
- **Workflow**: the flow through stages, tools or agents, or "N/A" for one step.
- **Action plan**: the steps to take, as bullets.
- **Before / After**: the exact changed lines, or "N/A".
- **STOP**: wait for an explicit "yes" before executing. Never auto-execute after showing a plan.

A pipeline reaching PASS internally never waives this gate.

## Secrets
- Never stage, commit or push `.env` or any `.env.*` file except `.env.example`. The plugin's `env_guard.py` hook enforces this.
- Secrets come from environment variables or a git-ignored `.env`, never from code.
- When a secret is found, report its location and type only, never its value.
