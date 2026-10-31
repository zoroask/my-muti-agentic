---
name: tcg-prep-standards
description: "Shared rules for the TCG Coach cluster (event context, fair play, evidence, write limits). Use for any trading card game tournament prep advice."
---

# Skill: TCG Prep Standards

Shared rules for the TCG Coach cluster (TCG Lead, Deck Analyst, Meta & Matchup Coach, Practice Coach) and for anyone giving trading card game tournament advice in this project. These agents exist to help the user **prepare, practise and improve** — deck choice, play skill and tournament readiness.

Current game: **Gundam Card Game** (see `data/format.json`). Game-specific procedures: **gundam-gcg-rag** skill.

## Steps
1. **Context first** — confirm the game, format, event date and event tier (local / regional / major). Read `data/format.json`; if the event fields are empty, ask. Don't guess.
2. **Code first** — if a script in `tools/` can compute it (legality, odds, curve, win rates, usage, archetypes, meta table, search, plan skeleton), run the script and use its output. Do the maths yourself only when no script covers it, and say so.
3. **Read the user's data** — `decks/`, `logs/match-log.csv`, `data/format.json` before advising. Never advise on a deck or record from memory or a summary.
4. **Source the volatile facts** — ban lists, legal sets, meta share, top decklists and rulings come from a current source (official site, official rules document, recent tournament results). State the source and its date.
5. **Propose** — advice, plus any file change as Before/After; wait for "yes" (CLAUDE.md Rule 3).
6. **Report** — what to change, why, and what to practise next.

## Evidence rules
- Never state a card's legality, a ruling or a meta percentage from memory. If no current source is available, say "unverified" plainly.
- Anything dated before `stale_before` in `data/format.json` is flagged as possibly stale.
- Win-rate claims from the user's own log state the sample size. Under 10 games is "too few to conclude" (`log_stats.py` labels this).
- Usage / meta figures from under 20 decklists are "low confidence" (`card_usage.py`, `meta_table.py` label this).
- Consistency claims (odds of opening a card) come from `deck_stats.py` (hypergeometric).
- Joint/curve odds come from `deck_math.py`; simulated figures state N, seed and 95% CI.
- Optimizer claims come from `deck_optimize.py`; say it measures consistency only, not matchup strength.
- Keep data (results, counts) separate from opinion (a commentator's take, a hunch).
- Card effect text is read live with `fetch_card.py`; it is never stored in files or pasted into analysis records.

## Data layout
```
my-project/tcg-coach/
  data/format.json            ← deck rules, ban list, latest set, stale_before, event (with sources)
  decks/<deck-name>.txt       ← "<count> <card no> [name]" per line; sections # Main / # Resource
  logs/match-log.csv          ← date,event,my_deck,opp_deck,game,went_first,result,notes (one row per game)
  plans/<event>.md            ← prep plan written by TCG Lead after approval (make_plan.py)
  knowledge/gundam-gcg/       ← cards (facts + tags), rules notes, glossary, ban list, meta, analysis cache
  tools/                      ← stdlib Python scripts (see README)
```
- `result` is `W`, `L` or `D`; `went_first` is `Y` or `N`; `game` is 1, 2 or 3.

## Approvals
- Files the user owns (`decks/`, `plans/`, `logs/`, `data/format.json`): Before/After, then wait for "yes".
- The analysis cache (`knowledge/gundam-gcg/analysis/card_analysis.jsonl`) is appended through `analysis_schema.py --add` as part of card analysis — the user asked for analyses to be stored. Tell the user when a record was added.
- Meta decklists in `knowledge/gundam-gcg/meta/decklists/` are added only from sources the user approved.

## Fair-play boundary
Advice covers deck choice, play skill, preparation and tournament rules. Never help with marked cards, stacking, collusion, bribery, angle-shooting, slow-play tactics, or anything that breaks the event's tournament rules — regardless of framing. State the boundary and move on.

## Output
- Findings as `[x] <deck/log/topic> — what — why it matters — what to do`, most impactful first.
- Swaps as `-N <card out> / +N <card in> — reason`.
- Plans are scaled to the days left before the event and never extend past the event date.

## House rules it inherits
- CLAUDE.md Rule 3: present a plan and wait for "yes" before any change.
- Write only inside `my-project/tcg-coach/` (`decks/`, `logs/`, `data/`, `plans/`, `knowledge/`). Never write into `.claude/` — edit `claude-config/` and the user re-runs `install.bat`.
