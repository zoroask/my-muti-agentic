# Skill: Rescue Tokens

Emergency response when the user hits a rate limit or quota error, or context is nearly full. For proactive setup use token-optimization.

## Triggers (any one)
- Rate-limit or quota warning
- Context above ~40% and still growing, or visibly degrading
- A request that would load PDFs, images or very large files

## Steps
1. Stop expanding context: do not open large files, PDFs or images; ask for excerpts or page ranges.
2. Context 40-70%: recommend the user run `/compact` with a note of the facts to keep. Above 70%: write a 3-sentence handoff (goal, current state, next step) and recommend a fresh session.
3. Right-size the model: Haiku for renames and lookups, Sonnet for implementation and debugging, Opus for architecture only. Recommend switching at a session boundary, not mid-session.
4. Cut output: shorter replies, no restating, no optional tables. The CLAUDE.md Rule 3 gate (Summary / Action plan / Before-After / STOP) still applies to any change; compress the content, never drop the gate.
5. Delegate only isolated work to subagents; do not fan out subagents for shared-context work.

## Rules
- `/compact`, `/clear`, `/mcp` and model switching are user actions: recommend them, never assume they happened.
- Under pressure, state one recommended action instead of asking multiple questions.
- Compress prose, never approval gates or safety checks.
