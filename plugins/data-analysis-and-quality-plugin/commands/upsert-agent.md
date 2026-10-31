Add a new agent or update an existing agent definition.

First ask the user: "Do you want to **ADD** a new agent or **UPDATE** an existing one?"

---

## ADD — Add a new agent

1. **Read** an existing `.claude/agents/<name>.md` (e.g. `pipeline-reviewer-sub-agent.md`) as a template for frontmatter and structure
2. **Ask** the user: agent name, role, when it should be invoked, what context/tools it needs
3. **Create** `.claude/agents/<kebab-name>.md`:
   ```
   ---
   name: <Display Name>
   description: <when to invoke this agent, in third person>
   model: claude-sonnet-4-6
   ---

   <system prompt: role, deep project knowledge, behavioral rules>
   ```
   Description field guidance — the description drives agent routing; get it right at creation:
   - Under-triggering (too narrow): "Use when debugging Python syntax errors" — too few triggers; the person won't think to invoke it at the right moment
   - Over-triggering (too broad): "Invoke for any task involving files or code" — picked on unrelated tasks
   - Good pattern: name the role + one concrete trigger condition, e.g. "Invoke when something is broken in the hook scripts or a persona/skill/command file contains an inconsistency"

4. **Test** by invoking the new agent directly with a sample task and reviewing its output

---

## UPDATE — Update an existing agent

1. **Ask** the user: which agent to update and what problem needs fixing
2. **Read** `.claude/agents/<name>.md` — understand the current system prompt
3. **Modify only the system prompt body** — keep frontmatter stable unless the agent's role itself changed
4. **Test** by invoking the agent again with a sample task to confirm the change produces better output

---

## Rules
- Keep system prompts focused — one agent, one responsibility
- `.claude/agents/*.md` is the sole registration point — Claude Code discovers agents automatically from that directory, no other file needs wiring
