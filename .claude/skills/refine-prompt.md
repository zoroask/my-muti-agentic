# Skill: Refine Prompt

Improve an agent's system prompt using structured reasoning.

## Steps
1. Ask which agent to improve and what the problem is
2. Read the current system prompt from `.claude/agents/<name>.md`
3. Identify the root cause of the problem:
   - Too vague? Add specific constraints
   - Wrong output format? Add explicit format examples
   - Missing rules? Add negative constraints ("never", "always")
   - Too long? Trim to essentials
4. Rewrite only the affected section — keep working parts intact
5. Show before/after diff with explanation
6. On approval: update `.claude/agents/<name>.md`

## Prompt Improvement Patterns

| Problem | Fix |
|---|---|
| Output has extra text | Add: "Output ONLY ... no extra text" |
| Wrong structure | Add the exact expected format as an example |
| Missing required elements | Add: "Every required element MUST be present" |
| Low quality output | Add: "No placeholder content, fully complete and specific" |
| Scope creep | Add explicit boundaries: what this agent does NOT do |
