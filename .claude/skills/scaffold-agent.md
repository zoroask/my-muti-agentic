# Skill: Scaffold Agent

Create a new agent definition from scratch.

## Steps
1. Gather requirements from the user:
   - Agent name (e.g., "Database Designer")
   - Role: what does it do?
   - When should it be invoked?
   - What context or tools does it need?

2. Generate `.claude/agents/<kebab-name>.md` with frontmatter + system prompt body:
```
---
name: <Display Name>
description: <when to invoke this agent, in third person>
model: claude-sonnet-4-6
---

<role, deep project knowledge, behavioral rules>
```
