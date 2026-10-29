Call the TCG Coach cluster (Gundam Card Game tournament prep) in
my-project/tcg-coach/ from the library root. $ARGUMENTS is the request.

## Steps
1. If $ARGUMENTS is empty, use AskUserQuestion: "What do you need?" with
   options Card search, Deck review, Meta & matchups, Practice review,
   Get me ready for an event (free text via Other).
2. Read fresh: `my-project/tcg-coach/.claude/agents/tcg-lead-main-agent.md`
   and the skills `tcg-prep-standards/SKILL.md` and `gundam-gcg-rag/SKILL.md` in
   `my-project/tcg-coach/.claude/skills/`. If missing, tell the user to
   run `my-project/tcg-coach/install.bat` and stop.
3. Act as TCG Lead: run the freshness check (gundam-gcg-rag Step 0) and
   pick the fewest specialists from its routing table.
4. For each specialist, launch a general-purpose subagent whose prompt is
   the specialist's persona file + the two skills + the request, with:
   run every tool from `my-project/tcg-coach` (`python tools/...`);
   read-only — return findings, write nothing.
5. Merge the findings as TCG Lead. For an event request, preview
   `python tools/make_plan.py ...` without `--write`.
6. Present per CLAUDE.md Rule 3, then STOP. On "yes", write only inside
   `my-project/tcg-coach/` (`decks/`, `plans/`, `logs/`, `data/`); re-run
   `tools/deck_check.py` after any deck edit.

## Rules
- Fair-play boundary in tcg-prep-standards applies.
- Never write into `my-project/tcg-coach/.claude/` — edit `claude-config/`.
