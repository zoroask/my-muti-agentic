All 9 diffs applied. No skips — every OLD text matched disk exactly.

Diff-by-diff results:

1. APPLIED — .claude/commands/commit-push-github.md line 48–49
   "env_guard.py is wired to the Bash tool only…" → "wired to both the Bash and PowerShell tools…"

2. APPLIED — .claude/agents/base-agent.md line 53
   Added `env_guard.py` to the list of executing hook scripts.

3a. APPLIED — .claude/agents/code-mentor-sub-agent.md line 20
    Added `env_guard.py` description to the hooks bullet in Project Content.

3b. APPLIED — .claude/agents/code-mentor-sub-agent.md Key Files section (after original line 26)
    Inserted `- .claude/hooks/env_guard.py — blocks git force-add, commit, and push of .env-style files` as the third bullet.

4. APPLIED — README.md hooks section (original lines 37–38)
    Expanded path_guard.py tool list; added env_guard.py line between path_guard and syntax_check.

5. APPLIED — README.md commands table (original line 34)
    Appended 4 rows: /focus-project, /run-agents, /full-audit-and-testing, /commit-push-github.

6. APPLIED — .claude/commands/list-skills.md (original line 23)
    Appended Python Automation Standards row after Rigorous Verification.

7. APPLIED — docs/agent-workflow.md hooks table path_guard row (original line 72)
    Expanded tool list and trigger description for path_guard row.

8. APPLIED — docs/agent-workflow.md hooks table env_guard row (original line 73)
    "(Bash)" → "(Bash/PowerShell)" and trigger description updated.

9. APPLIED — agent_runtime/chains.py line 73
    ASCII hyphen (-) → em dash (—) in the AUDIT CLEAN sentinel string.
