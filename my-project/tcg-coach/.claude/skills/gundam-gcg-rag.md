# Skill: Gundam GCG RAG (card search, card analysis, meta, counter-deck)

Procedure for answering Gundam Card Game questions with this project's local knowledge base.
Principle: **code first, LLM last.** If a script can compute it, run the script and use its output.
Use judgement only for what scripts cannot decide: a card's role, matchup plans, which swaps to make.

All commands run from the `tcg-coach` folder. Scripts are stdlib Python; the official site is only
needed by `fetch_card.py`, `verify_cards.py` and `refresh_cards.py`.

## Step 0: freshness (every request)
1. Read `data/format.json`: ban list date, rules version, latest set, `stale_before`.
2. If the user says a new set or ban list came out after those dates, stop and offer to refresh
   (`refresh_cards.py --new-only`, update format.json, `mark_stale.py --before <date>`, `rebuild_all.py`).
3. If `knowledge/gundam-gcg/tcg.db` is missing: `python tools/rebuild_all.py`.

## Workflow 1: card search
1. Turn the request into flags (or use the user's flags as given).
   Example: "Blue (Orb) units, cost ≤ 3, with Blocker" →
   `python tools/search.py --color Blue --trait Orb --type UNIT --max-cost 3 --keyword Blocker`
2. The script already does: usage ranking first (part "Played in the meta"), then the rest of the
   catalog ("Other matches"), ban status, Beta/Promo-only hiding (`--all` to include), analysis status.
3. Show the two tables as they are. Do not re-rank or add cards from memory.
4. Name the usage data's sample size and kinds (the script prints them). If usage comes only from
   `official-featured` lists, say: "featured by the publisher, not tournament results".
5. If the user picks a card to look at → workflow 2.

## Workflow 2: card analysis (cache first)
1. `python tools/search.py "<card name or no>"` → check the `analysis` column.
   - `fresh` → read the stored record from `knowledge/gundam-gcg/analysis/card_analysis.jsonl` (latest line for that card)
     and answer from it. No new analysis needed.
   - `stale` or `-` → continue.
2. Live text + rulings: `python tools/fetch_card.py <NO>` (prints official effect text, FAQ, text_hash;
   saves nothing). If it reports TEXT CHANGED, tell the user and suggest `refresh_cards.py --only <NO>`.
3. Context: `python tools/fetch_card.py <NO> | python tools/build_context.py "<question>" --stdin`
   ([A] card text + top rules chunks, [B] summaries, [C] recap + question).
4. Judge (LLM): role, strengths, conditions/costs, weaknesses, synergies, recommended copies, rating 1-5.
   For synergies run a tag search, e.g. `search.py --trait Orb --action self-mill`.
5. Save: `python tools/analysis_schema.py --template <NO> > tmp.json`, fill it in (your own words; never
   paste the effect text), then `python tools/analysis_schema.py --add tmp.json`, delete tmp.json,
   then `python tools/build_db.py`. The schema check rejects copied text and missing sources.
6. Answer with citations: official URL + read date, FAQ numbers, rules chunk ids.

## Workflow 3: meta analysis
1. TCG Lead confirms the event: format, date, tier, days left.
2. Refresh results (code, approved sources only): `python tools/collect_meta.py --source all`, then
   `python tools/rebuild_all.py`. Sources: TCG TopDecks HQ and Egman Events (references.md). For the user's own
   store results, save each list as `knowledge/gundam-gcg/meta/decklists/<YYYY-MM-DD>-<event>-<n>.txt` with
   `# source:`, `# date:`, `# event:`, `# kind: tournament`, `# name:`, `# placement:`, `# players:`. Never store player names.
3. `python tools/meta_table.py --kind tournament --since <stale_before>` (archetypes grouped by colors + main Unit,
   with each source's names as "aka"; duplicates across sources and non-50-card lists are left out automatically).
4. Present the meta table as printed (decks, share, latest, kinds, STALE flags, LOW CONFIDENCE).
   Keep data (counts) separate from opinion. Official featured decks are not meta share.
5. For the top 3-5 archetypes: their key cards → workflow 2 → threats and how each deck wins.
6. Local events: note that a local meta can differ from published results.

## Workflow 4: counter deck-building and matchup prep
1. `python tools/deck_check.py decks/<deck>.txt` → legality (must be LEGAL before anything else).
2. `python tools/deck_stats.py decks/<deck>.txt --key <key cards>` → curve, colors, link coverage, opening odds.
3. `python tools/log_stats.py --deck "<deck name>"` → win rates per matchup, play/draw, G1 vs post-side,
   misplay groups (read the "unclassified" notes yourself).
4. Meta needs from workflow 3 → what each matchup requires.
5. Candidates: workflow 1 searches; evaluate with workflow 2 (cache first).
6. Propose as Before/After: `-N <out> / +N <in> — reason`, per-matchup plan (role, their key cards,
   keep/ship, side in/out only if the event's BO3 rules allow a sideboard).
7. STOP for "yes". Then TCG Lead writes `decks/<deck>.txt`, re-runs `deck_check.py`, and
   `python tools/make_plan.py --event ... --date ... --deck ... --write` for `plans/<event>.md`.
8. Practice → log games → repeat from step 3 until the event date.

## Context layout
Long prompts follow the **long-context-lost-in-the-middle** skill; `build_context.py` implements its
A/B/C layout. Put the card text and hard constraints first, restate the question last.

## Boundaries
- Effect text is read live and never stored or pasted into files. Quote at most a short phrase when needed.
- Fair play only (tcg-prep-standards).
- No scraping of third-party sites; decklists from them are entered by the user or with their approval.
