# Skill: Token Optimization

Reduce token cost in a Claude Code session or multi-agent run. Use when the user mentions cost, slow sessions, context bloat, or before launching a multi-agent chain. For emergencies (rate limit hit, context nearly full) use rescue-tokens.

## Steps
1. Audit: ask the user to run `/context` (Claude cannot run slash commands itself). Flag more than 3 MCP servers, plugins unrelated to the task, or a large base token count on an empty session. Recommend disabling what is unused.
2. Protect the cache: the cached prefix is system instructions (CLAUDE.md), the tool/MCP list, then message history. Changing an earlier layer mid-session re-bills everything after it. Finish configuration (MCPs, CLAUDE.md, model) before work starts; if a change is unavoidable, summarise and start a new session.
3. Isolate heavy work: delegate web search, large-file reads and codebase exploration to a subagent so only the result returns. Spawn early, because a subagent inherits the parent's context at spawn time. Do not delegate work that needs shared context (multi-file refactors with common dependencies).
4. Match model and effort to the task: low for known commands, medium by default, high only for architecture or hard reasoning. Changing model mid-session invalidates the cache (step 2).
5. Shrink inputs: give explicit file paths instead of letting Claude explore, read PDFs by page range, ask for text excerpts instead of images, and prefer summary forms of verbose commands (e.g. `git diff --stat` before `git diff`).
6. Verify: re-run `/context`; the base session should be smaller and isolated tasks should return summaries, not transcripts.

## Rules
- Advisory only: never edit settings.json, CLAUDE.md or global config to "optimise" without the CLAUDE.md Rule 3 approval gate.
- Do not recommend third-party tools or installs unless asked, and do not quote savings figures you have not verified.
- Multi-agent note: every subagent has its own context cost; prefer a few focused agents over many.
