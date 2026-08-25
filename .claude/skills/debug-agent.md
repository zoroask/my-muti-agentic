# Skill: Debug Agent

Diagnose why an agent produced bad, empty, or malformed output.

## Steps
1. Ask the user: which agent failed and what was the bad output?
2. Read the agent's `.claude/agents/<name>.md` file
3. Check these common failure causes:

### Output format not followed
- [ ] Model added prose instead of the required structure/blocks → tighten "output ONLY <format>, no extra text"
- [ ] Required elements missing from output → list them explicitly, add a self-check instruction
- [ ] Wrong structure/schema → show the exact expected format in the prompt as an example

### Inconsistent or incorrect content
- [ ] Output is too verbose or includes commentary → add explicit negative constraints
- [ ] Scope creep (agent does more/less than intended) → tighten the role definition and boundaries
- [ ] Contradicts a stated rule → the rule may be buried; move it earlier or repeat it as a hard constraint

4. Propose a targeted fix to the system prompt
5. Update `.claude/agents/<name>.md` on approval
6. Re-invoke the agent with the same task to confirm the fix
