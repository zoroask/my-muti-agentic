List all agents in the system with their roles, files, and current status.

Steps:
1. Read every file in `.claude/agents/`
2. Read `docs/agent-workflow.md` for documented design patterns and naming conventions

Print a table like this:

```
AGENT REGISTRY
==============
# | Name              | MD File                                | Description (from frontmatter)
--|--------------------|----------------------------------------|----------------------------------
1 | Project Manager    | .claude/agents/project-manager-agent.md      | ...
2 | Bug Fixer          | .claude/agents/bug-fixer-agent.md            | ...
3 | Architect Advisor  | .claude/agents/architect-advisor-agent.md    | ...
```

Flag any agent that:
- Has a `.md` file with a missing or empty frontmatter `description`
- Is documented in `docs/agent-workflow.md` or `CLAUDE.md` but has no corresponding `.md` file in `.claude/agents/`
- Exists as a `.md` file but is not mentioned in `docs/agent-workflow.md`
