List all available skills in `.claude/skills/` with their purpose and how to invoke each one.

## Available Skills

| Skill | File | Purpose | How to invoke |
|---|---|---|---|
| Debug Agent | `debug-agent.md` | Diagnose why an agent produced bad, empty, or malformed output | "use the debug-agent skill" |
| Scaffold Agent | `scaffold-agent.md` | Create a new agent definition from scratch | "use the scaffold-agent skill" |
| Refine Prompt | `refine-prompt.md` | Improve an agent's system prompt using structured reasoning | "use the refine-prompt skill" |

## Skills vs Agents

- **Skill** — a step-by-step procedure Claude follows itself. No persona, no memory.
- **Agent** — an AI persona with role, context, and behavioral rules. Runs as a subagent.

Use `/list-agents` to see all available agents.
