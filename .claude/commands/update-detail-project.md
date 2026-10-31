Sync the project's docs and scripts with what is really in the project: `README.md`, API/MCP/path details, hard-coded script lists, and `site/index.html` (Multi-Agent Library Overview).

Steps:
1. Inventory the real project:
   - Agents: every file in `.claude/agents/` (frontmatter `name`, `description`)
   - Skills: every `.claude/skills/*/SKILL.md`
   - Commands: every file in `.claude/commands/`
   - Hooks: `.claude/hooks/*.py` and their wiring in `.claude/settings.json`
   - MCP servers: `.mcp.json`, plus the tools in `ollama_mcp.py` (`@mcp.tool()` functions)
   - APIs: the env var NAMES each script reads (e.g. `LLM_BACKEND`, `LLM_BASE_URL`) and their default endpoints
   - Key paths: `agent_runtime/`, `tools/`, `site/`, `my-project/`, the memory root, and `ALLOWED_ROOTS` in `.claude/hooks/path_guard.py`
2. Compare the inventory against:
   - Docs: `README.md`, the tables in `CLAUDE.md`, `.claude/skills/README.md`, `docs/agent-workflow.md`
   - Scripts: `CLUSTERS` in `tools/build_site.py`, `ALLOWED_ROOTS` in `.claude/hooks/path_guard.py`, `.mcp.json`, the `ollama_mcp.py` docstring
   List each gap as `file — what is stale — what it should say`.
3. Show a Before / After for every doc and script change, then STOP and wait for "yes" (CLAUDE.md Rule 3).
4. After approval:
   - Apply the edits
   - Rebuild the overview page: `python tools/build_site.py`
   - Verify: `python -m agent_runtime audit`, and report `RESULT` and any finding verbatim

## Rules
- Never read `.env` files or print a secret value. Name env vars, never their values.
- Never edit `my-project/` content or `references/`.
- Never widen `ALLOWED_ROOTS` in `path_guard.py` without the user's explicit approval of that exact change.
- Never trim the `CLAUDE.md` command table; the audit requires every command row.
- Change only what is stale. Do not rewrite sections that already match.
