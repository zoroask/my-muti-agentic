Safely remove an agent definition.

Steps:
1. Ask the user which agent to remove
2. Check `docs/agent-workflow.md` and `CLAUDE.md` for any mention of this agent, and check other `.claude/commands/*.md` or `.claude/skills/*.md` files for references to it by name
3. Warn the user about downstream effects if other commands, skills, or agents reference this one
4. Ask the user to confirm removal after seeing the impact
5. On confirmation, make these changes:
   - Delete `.claude/agents/<name>.md`
   - Update `CLAUDE.md` if the agent is listed there
6. Confirm no remaining file references the removed agent by name
