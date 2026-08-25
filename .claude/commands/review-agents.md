Review all agents in the system for quality, consistency, and improvement opportunities.

Steps:
1. Read every file in `.claude/agents/`

2. For each agent, evaluate:
   - Is the system prompt clear and specific enough about the agent's role and scope?
   - Does it explicitly define the expected output format (structure, schema, or block markers)?
   - Are behavioral rules unambiguous ("never", "always", explicit constraints)?
   - Does it reference any project file paths — if so, verify those files still exist
   - Are there any hardcoded values or stale assumptions that should be generalized?

3. Check `docs/agent-workflow.md` for consistency with the actual agent roster

4. Produce a summary report with:
   - Issues found (agent name + description)
   - Suggested improvements (prioritized: high / medium / low)
   - Quick wins that can be done immediately

Ask the user which improvements to apply before making any changes.
