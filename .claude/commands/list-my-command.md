List every slash command in `.claude/commands/` with its purpose and how to run it.

Steps:
1. Read every `.md` file in `.claude/commands/`.
2. Take the purpose from the frontmatter `description`, or the first non-empty line if there is no frontmatter.
3. Read the Custom Commands table in `CLAUDE.md`.

Print a table like this:

```
COMMAND REGISTRY
================
# | Command        | File                             | Purpose
--|----------------|----------------------------------|---------------------------
1 | /agent-report  | .claude/commands/agent-report.md | Generate a full audit report of all agents
```

Then flag:
- A command file with no row in the `CLAUDE.md` table
- A `CLAUDE.md` row with no command file

Read-only: never edit any file. Use `/list-skills` for skills and `/list-agents` for agents.
