# Agent Improvement Workflow

## What an Agent Is
An agent in this project is a `.claude/agents/<kebab-name>.md` file: YAML frontmatter (`name`, `description`, `model`) followed by a system prompt body. The `.md` file is the complete, sole definition — there is no corresponding Python class.

---

## How to Improve an Existing Agent

### 1. Improve the System Prompt
The fastest way to improve an agent's output quality is to refine its system prompt body.

Tips for better prompts:
- Be specific about output format (exact JSON schema, exact block markers, etc.)
- Add examples of good vs bad output in the prompt
- Add negative constraints ("do NOT use Tailwind", "NEVER add placeholder comments")
- For coder-style personas: specify which libraries/conventions to use or avoid

### 2. Keep the Role Focused
Each agent should do one thing well. If a persona is accumulating unrelated responsibilities, split it into a new agent rather than growing the prompt indefinitely.

---

## How to Add a New Agent

Use `/upsert-agent`, or follow these steps manually:

### Step 1 — Create the persona file
```markdown
---
name: My Agent
description: One-line description of role and when to invoke it
model: claude-sonnet-4-6
---

<System prompt: role, rules, expected input, expected output, constraints>
```
Save as `.claude/agents/<kebab-name>.md`.

### Step 2 — Define its contract
State clearly in the system prompt:
- What input it expects (a plan, a file, a user description, feedback from another agent, etc.)
- What output it produces and in what format (plain text, JSON with a specific schema, file blocks, etc.)
- Any hard constraints or things it must never do

### Step 3 — Verify discovery
Any `.claude/agents/*.md` file is automatically available as a subagent — no separate registration step is needed.

---

## Agent Design Principles

1. **Single responsibility** — each agent does one thing well
2. **Structured output** — if an agent's output feeds another agent or process, specify the exact format (JSON schema, delimiter blocks, etc.) explicitly in the prompt
3. **Fail gracefully** — instruct the agent what to do when it can't produce a confident answer (ask a clarifying question, say so explicitly) rather than guessing silently
4. **Prompt = behavior** — all of an agent's intelligence lives in its system prompt; there is no code layer to fall back on
5. **No side effects beyond scope** — an agent should stay within the role described in its prompt

---

## Hooks Reference

| Hook | Trigger | Action |
|---|---|---|
| `PreToolUse` (Write/Edit/Read) | Before any file is read, written, or edited | Runs `path_guard.py` — blocks access outside `D:\my-muti-agentic\` |
| `PostToolUse` (Write/Edit) | After any `.py` file is written or edited | Runs `syntax_check.py` to catch Python syntax errors |

Hook scripts: `.claude/hooks/path_guard.py`, `.claude/hooks/syntax_check.py`
Hook config: `.claude/settings.json`
