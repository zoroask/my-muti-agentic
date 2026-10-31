# TCG Coach — Gundam Card Game

A small multi-agent assistant for Gundam Card Game tournament prep: card search, card analysis, meta analysis, counter deck-building and practice review. **Code first, LLM last:** stdlib Python scripts do every count, check and calculation; the agents use judgement only where scripts can't (card roles, matchup plans, swap choices).

## Agents
| Agent | File | Does |
|---|---|---|
| **TCG Lead** (main) | `claude-config/agents/tcg-lead-main-agent.md` | Front door: event context, routing, prep plan |
| Deck Analyst | `claude-config/agents/tcg-deck-analyst-sub-agent.md` | Card search, card analysis (cached), legality, odds, swaps |
| Meta & Matchup Coach | `claude-config/agents/tcg-meta-coach-sub-agent.md` | Sourced meta, archetypes, matchup plans |
| Practice Coach | `claude-config/agents/tcg-practice-coach-sub-agent.md` | Match-log stats, misplays, drills |

Skills: `tcg-prep-standards` (shared rules), `gundam-gcg-rag` (the four workflows), `long-context-lost-in-the-middle` (A/B/C context layout, copied from the library).

## Install / update
Double-click `install.bat` after any change in `claude-config\` (it copies agents and skills into `.claude\`). Then open Claude Code in this folder:
`cd D:\my-muti-agentic\my-project\tcg-coach` → `claude` → *"TCG Lead: get me ready for <event> on <date> with decks/<deck>.txt"*.

## Knowledge base (`knowledge/gundam-gcg/`)
| Path | Contents |
|---|---|
| `cards/cards.json`, `cards.csv` | Every card's facts + tags (triggers, keywords, actions) + official link + text fingerprint. No effect text. |
| `cards/by-set/*.md` | One table per product group |
| `rules/*.md`, `glossary.md` | Rules notes in our own words with rule numbers (Comprehensive Rules Ver. 1.10.0, 2026-10-16) |
| `banlist.md` + `data/format.json` | Ban list dated 2026-09-25 (human + machine readable) |
| `references.md` | Every official URL |
| `meta/decklists/*.txt` | Decklists with source, date and kind (`tournament` or `official-featured`) |
| `meta/card-usage.json` | Usage share / average copies (generated) |
| `analysis/card_analysis.jsonl` | Per-card analysis summaries (cache; written via `analysis_schema.py`) |
| `index/chunks.jsonl`, `tcg.db` | Generated search index (SQLite + FTS5); `tcg.db` is git-ignored |

**Card text policy:** effect text is read live from the official page (`fetch_card.py`) when analysing; it is never stored.
**Meta data:** tournament results come from TCG TopDecks HQ and Egman Events (`collect_meta.py`); the official site's featured decks are kept but labelled "official-featured" and left out of meta shares. Duplicate lists reported by both sites, and lists that mix in a sideboard, are skipped automatically. Player names are never stored.

## Tools (`python tools/<script> --help` for options)
| Script | Purpose |
|---|---|
| `search.py` | Card search: most-used first, then the rest; `--rules` searches rules notes |
| `fetch_card.py` | Live official text + FAQ for a card; flags errata and stale analyses |
| `build_context.py` | A/B/C reading context for an agent (pipe `fetch_card.py` into it with `--stdin`) |
| `deck_check.py` | Legality: sizes, copies, colors, ban list, banned pairs, vanilla rule |
| `deck_stats.py` | Curve, colors, link coverage, hypergeometric opening odds |
| `log_stats.py` | Win rates per matchup, play/draw, G1 vs post-side, misplay groups |
| `collect_meta.py` | Collect new tournament decklists from TopDecks HQ and Egman (one request each) |
| `card_usage.py` / `archetypes.py` / `meta_table.py` | Usage stats (`--current`), archetype grouping (colors + main Unit), meta table with STALE / LOW CONFIDENCE flags |
| `make_plan.py` | Prep-plan skeleton up to the event date (`--write` after approval) |
| `analysis_schema.py` / `mark_stale.py` / `batch_targets.py` | Analysis cache: validate + save, mark stale, list cards worth pre-analysing |
| `refresh_cards.py` / `verify_cards.py` | Refresh card data after a new set; spot-check against the live site |
| `export_sets.py` / `rag_index.py` / `build_db.py` / `rebuild_all.py` | Rebuild generated files |
| `scrape_official.js` | The browser scraper used for the first build (same parsing as `refresh_cards.py`) |

Tests: `python -m unittest discover -s tests`

## Weekly meta refresh
`python tools/collect_meta.py --source all` then `python tools/rebuild_all.py`.
When a new format starts, pass the new set: `--set-group GD06` (Egman) and `--page <TopDecks set page slug>`.

## After a new set or ban list
1. Update `data/format.json` (ban list, `latest_set`, `stale_before`) from the official pages.
2. `python tools/refresh_cards.py --new-only` (or a full refresh), then `python tools/mark_stale.py --before <date>`.
3. `python tools/rebuild_all.py`.

## Your files
| Folder | Contents |
|---|---|
| `decks/` | One `.txt` per deck: `<count> <card no> [name]`, sections `# Main` / `# Resource` (egman deckbuilder exports work if they list card numbers) |
| `logs/match-log.csv` | One row per game: `date,event,my_deck,opp_deck,game,went_first,result,notes` |
| `plans/` | Prep plans written by TCG Lead |
| `data/format.json` | Rules numbers, ban list, latest set, event details |
