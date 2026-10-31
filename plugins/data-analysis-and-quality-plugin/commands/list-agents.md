List all agents in the system with their roles, files, and current status.

Steps:
1. Read every file in `.claude/agents/`
2. Read `agents/base-agent.md` in this plugin for documented design patterns and naming conventions

Print a table like this:

```
AGENT REGISTRY
==============
# | Name              | MD File                                | Description (from frontmatter)
--|--------------------|----------------------------------------|----------------------------------
1 | Project Manager    | .claude/agents/project-manager-main-agent.md | ...
2 | Bug Fixer          | .claude/agents/bug-fixer-sub-agent.md        | ...
3 | Architect Advisor  | .claude/agents/architect-advisor-main-agent.md | ...
```

Flag any agent that:
- Has a `.md` file with a missing or empty frontmatter `description`
- Is listed in `agents/base-agent.md` but has no corresponding `.md` file in `agents/`
- Exists as a `.md` file but is not listed in `agents/base-agent.md`
