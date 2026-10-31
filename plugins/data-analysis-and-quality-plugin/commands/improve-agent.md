Improve a specific agent's system prompt for better output quality.

Steps:
1. Ask the user: which agent to improve?
2. Read the agent's `.claude/agents/<name>.md` file
3. Ask the user: what is the problem or improvement goal?
   - Examples: "output is too verbose", "misses certain cases", "format is inconsistent", "quality is low"
4. Analyze the current system prompt body and identify weaknesses
5. Propose a specific rewrite of the relevant section
6. Show a diff (before vs after) and explain the reasoning
7. Ask the user to confirm before applying
8. On confirmation: update the system prompt body in `.claude/agents/<name>.md` (leave frontmatter untouched unless the role itself changed)
9. Suggest invoking the agent with a sample task to verify the improvement
