# TCG Coach — Project Rules

AI assistant and advisor for Gundam Card Game tournament preparation.
Sub-project of the `D:\my-muti-agentic` library; open Claude Code in this folder to use it.

## Rules
1. English only — all responses in English regardless of request language.
2. Start every TCG request with **TCG Lead** (`.claude/agents/tcg-lead-main-agent.md`); it routes to the specialists.
3. Before any change to the user's files (decks, plans, logs, data), show a Before/After and wait for an explicit "yes".
4. Follow `.claude/skills/tcg-prep-standards.md` and `.claude/skills/gundam-gcg-rag.md`.
5. Code first, LLM last: if a script in `tools/` can compute it, run the script. Judge only what scripts can't.
6. Ban lists, legality, rulings and meta numbers come from a current, dated source, never from memory.
7. Card effect text is read live (`tools/fetch_card.py`) and never stored in files.
8. Write only inside `decks/`, `logs/`, `data/`, `plans/`, `knowledge/`. Never write into `.claude/` — edit `claude-config/` and run `install.bat`.
9. Fair play only — no help with cheating, collusion or breaking tournament rules.

## Quick commands
- Search: `python tools/search.py --color Blue --type UNIT --keyword Blocker`
- Card text: `python tools/fetch_card.py GD06-002`
- Deck: `python tools/deck_check.py decks/<deck>.txt` and `python tools/deck_stats.py decks/<deck>.txt`
- Log: `python tools/log_stats.py`
- Rebuild generated files: `python tools/rebuild_all.py`
- Tests: `python -m unittest discover -s tests`

## Skill triggers
"prepare for a TCG tournament", "review my deck", "tcg meta", "matchup", "sideboard", "practice log", "gundam card", "find cards" /
"เตรียมแข่ง TCG", "จัดเด็ค", "วิเคราะห์ meta", "แมตช์อัพ", "ไซด์เด็ค", "ค้นหาการ์ด", "วิเคราะห์การ์ด" → read `.claude/skills/tcg-prep-standards.md` and `.claude/skills/gundam-gcg-rag.md` first.
