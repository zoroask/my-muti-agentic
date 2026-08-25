Generate a full audit report of all agents in the system.

Steps:
1. Read every file in `.claude/agents/`
2. Read `docs/agent-workflow.md` for documented design intent

Produce a structured report covering:

### 1. Agent Roster Summary
- All agents currently defined and their roles
- How they're typically invoked (directly, or as part of a documented workflow)

### 2. Per-Agent Analysis
For each agent:
- **Role**: what it does
- **System prompt quality**: is it specific enough? Are rules clear?
- **File references**: does it name specific project files/paths — do they still exist?
- **Issues found**: vague scope, missing constraints, stale references, documentation gaps

### 3. Improvement Opportunities
Ranked list of suggested improvements (high / medium / low priority):
- High: stale file references, broken or missing behavioral rules
- Medium: prompt improvements for better output quality
- Low: style, documentation gaps

### 4. Recommended Next Steps
Top 3 actions to take now

Ask the user which improvements to apply before making any changes.
