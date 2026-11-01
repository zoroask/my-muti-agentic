# TCG Coach — Gundam Card Game

A small multi-agent assistant for Gundam Card Game tournament prep: card search, card analysis, meta analysis, counter deck-building and practice review. **Code first, LLM last:** stdlib Python scripts do every count, check and calculation; the agents use judgement only where scripts can't (card roles, matchup plans, swap choices). Everything runs inside a Claude Code session.

Unofficial fan tool. Card names, card numbers and game terms belong to their rights holders.

## 📖 Manual

- [Stack](#stack)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running](#running)
- [Plugin](#plugin)
- [Multi-Agent System](#multi-agent-system)
- [System Reference](#-system-reference)
- [Maintenance](#maintenance)
- [Tests](#tests)

## Stack

- **Agents / skills** — Markdown with YAML frontmatter under `claude-config/`, installed into `.claude/`
- **Tools** — Python 3.10+ stdlib only (`tools/`), no third-party deps
- **Card database** — SQLite + FTS5 (`knowledge/gundam-gcg/tcg.db`), generated, never committed
- **Judgement LLM** — `local-llm` MCP server if registered, otherwise Claude (the session model)

## Project Structure

```
tcg-coach/
├── .claude-plugin/       # marketplace.json — installs the plugin from GitHub
├── claude-config/        # source of truth: agents/, skills/, .claude-plugin/plugin.json
├── .claude/              # installed copy of claude-config (written by install.bat)
├── tools/                # stdlib Python scripts (search, deck checks, meta, rebuild)
├── knowledge/gundam-gcg/ # rules notes, ban list, meta data, search index, tcg.db
├── data/format.json      # rules version, ban list, latest set, event details
├── plans/                # prep plans written by TCG Lead (git-ignored except README)
├── decks/, logs/         # your personal files (git-ignored, created by install.bat)
├── demo/                 # demo.html, diagrams.html (offline design demo)
├── tests/                # unittest suite with its own fixtures
├── install.bat           # install agents/skills, download card data, build tcg.db
├── fix-claude-command.bat# puts the claude command on PATH (or runs the official installer)
├── DESIGN.md             # system design
└── CLAUDE.md             # project rules for Claude Code
```

## Setup

1. Install [Claude Code](https://claude.com/claude-code) and Python 3.10+. If `claude` is not found, run `fix-claude-command.bat`.
2. Clone and install:
   ```
   git clone https://github.com/zoroask/tcg-coach
   cd tcg-coach
   install.bat
   ```
   On first run `install.bat`:
   - copies `claude-config\` agents and skills into `.claude\`;
   - downloads card data from the official site (about 25-45 min, throttled) — card details are never stored in the repo;
   - builds `knowledge/gundam-gcg/tcg.db` with `tools/rebuild_all.py`;
   - creates `decks\` and `logs\match-log.csv`.
3. Optional: register the `local-llm` MCP server. The agents send judgement steps to `mcp__local-llm__ask_local_llm`; without it Claude does the judgement and each answer says which model judged. The server is `ollama_mcp.py` from [zoroask/my-muti-agentic](https://github.com/zoroask/my-muti-agentic) (needs `mcp[cli]<2`, `httpx` and a local Ollama or OpenAI-compatible server).

Run `install.bat` again after any change in `claude-config\`.

## Running

Open the folder in Claude Code, then ask TCG Lead:
```
cd tcg-coach
claude
> TCG Lead: get me ready for <event> on <date> with decks/<deck>.txt
```
Save each deck as `decks/<name>.txt` (format under [Your files](#your-files)). Quick commands:
```
python tools/search.py --color Blue --type UNIT --keyword Blocker
python tools/fetch_card.py GD06-002
python tools/deck_check.py decks/<deck>.txt
python tools/deck_stats.py decks/<deck>.txt
python tools/log_stats.py
```

## Plugin

The agents and skills are also packaged as an installable plugin:
```
/plugin marketplace add zoroask/tcg-coach
/plugin install tcg-coach@zoroask-tcg-coach
```

The plugin carries agents and skills only. They run `tools/` and read `knowledge/`, so open Claude Code inside a clone of this repo that has been through `install.bat`.

## Multi-Agent System

Every TCG request starts with 👑 **TCG Lead**, which sets the event context and routes to the specialists. Scripts compute; agents judge only what scripts can't; any change to your files stops at a Before/After and waits for "yes". See [`CLAUDE.md`](./CLAUDE.md) for rules and [`DESIGN.md`](./DESIGN.md) for the design.

```
You ─▶ 👑 TCG Lead ─┬─▶ Deck Analyst ────────▶ tools/ + tcg.db + live card text
                    ├─▶ Meta & Matchup Coach ─▶ meta data + archetypes
                    └─▶ Practice Coach ───────▶ logs/match-log.csv
                    ─▶ 🛑 Before/After ─▶ "yes" ─▶ write decks/ plans/ logs/
```

## 🤖 System Reference

Icons mark function: 👑 main agent, 🛑 blocking gate, 🔄 sync, 🔍 read-only.

### CLAUDE.md Customizations

- 🌐 **English-only** — replies in English regardless of request language; Thai only as skill triggers.
- 👑 **TCG Lead first** — every TCG request starts with TCG Lead.
- 🛑 **Approval gate** — Before/After and an explicit "yes" before any change to decks, plans, logs or data.
- 🧮 **Code first, LLM last** — if a script in `tools/` can compute it, run the script.
- 📅 **Dated sources** — ban lists, legality, rulings and meta numbers come from a current, dated source, never from memory.
- 📄 **Card text policy** — effect text is read live (`fetch_card.py`) and never stored.
- ✍️ **Write limits** — only `decks/`, `logs/`, `data/`, `plans/`, `knowledge/`; edit `claude-config/`, never `.claude/`.
- 🤝 **Fair play** — no help with cheating, collusion or breaking tournament rules.

### 🤖 Agents (`claude-config/agents/*.md`)

| Agent | File | Does |
|---|---|---|
| 👑 **TCG Lead** (main) | `tcg-lead-main-agent.md` | Front door: event context, routing, prep plan |
| Deck Analyst | `tcg-deck-analyst-sub-agent.md` | Card search, card analysis (cached), legality, odds, swaps; proposes, never edits decks |
| Meta & Matchup Coach | `tcg-meta-coach-sub-agent.md` | Sourced meta, archetypes, matchup plans |
| Practice Coach | `tcg-practice-coach-sub-agent.md` | Match-log stats, misplays, drills |

### 🛠️ Skills (`claude-config/skills/<name>/SKILL.md`)

- **tcg-prep-standards** — shared rules: event context, fair play, evidence, write limits.
- **gundam-gcg-rag** — the four workflows: card search, card analysis, meta, counter-deck.
- **long-context-lost-in-the-middle** — A/B/C context layout (copied from my-muti-agentic).

Triggers: "prepare for a TCG tournament", "review my deck", "tcg meta", "matchup", "sideboard", "practice log", "gundam card", "find cards" (Thai triggers in `CLAUDE.md`).

### 🧰 Tools (`python tools/<script> --help` for options)

| Script | Purpose |
|---|---|
| `search.py` | Card search: most-used first, then the rest; `--rules` searches rules notes |
| `fetch_card.py` | Live official text + FAQ for a card; flags errata and stale analyses |
| `build_context.py` | A/B/C reading context for an agent (pipe `fetch_card.py` into it with `--stdin`) |
| `deck_check.py` | Legality: sizes, copies, colors, ban list, banned pairs, vanilla rule |
| `deck_stats.py` | Curve, colors, link coverage, hypergeometric opening odds |
| `deck_math.py` / `deck_optimize.py` | Exact and simulated draw odds, meta-weighted win rates, swap optimisation (theory in `knowledge/gundam-gcg/deck-math.md`) |
| `log_stats.py` | Win rates per matchup, play/draw, G1 vs post-side, misplay groups |
| `collect_meta.py` | Collect new tournament decklists from TopDecks HQ and Egman (one request each) |
| `card_usage.py` / `archetypes.py` / `meta_table.py` | Usage stats (`--current`), archetype grouping (colors + main Unit), meta table with STALE / LOW CONFIDENCE flags |
| `make_plan.py` | Prep-plan skeleton up to the event date (`--write` after approval) |
| `analysis_schema.py` / `mark_stale.py` / `batch_targets.py` | Analysis cache: validate + save, mark stale, list cards worth pre-analysing |
| `refresh_cards.py` / `verify_cards.py` | Download or refresh card data; spot-check against the live site |
| `export_sets.py` / `rag_index.py` / `build_db.py` / `rebuild_all.py` | 🔄 Rebuild generated files |
| `scrape_official.js` | The browser scraper used for the first build (same parsing as `refresh_cards.py`) |

### 📚 Knowledge base (`knowledge/gundam-gcg/`)

| Path | Contents |
|---|---|
| `cards/cards.json`, `cards.csv` | Every card's facts + tags + official link + text fingerprint. No effect text. Downloaded by `install.bat`, git-ignored |
| `cards/by-set/*.md` | One table per product group (generated, git-ignored) |
| `rules/*.md`, `glossary.md` | Rules notes in our own words with rule numbers (Comprehensive Rules Ver. 1.10.0, 2026-10-16) |
| `banlist.md` + `data/format.json` | Ban list dated 2026-09-25 (human + machine readable) |
| `references.md` | Every official URL |
| `meta/decklists/`, `meta/decklists.jsonl` | Decklists with source, date and kind (`tournament` or `official-featured`) |
| `meta/card-usage.json` | Usage share / average copies (generated) |
| `analysis/card_analysis.jsonl` | Per-card analysis summaries (cache; written via `analysis_schema.py`) |
| `index/chunks.jsonl`, `tcg.db` | Generated search index (SQLite + FTS5); `tcg.db` is git-ignored |

**Meta data:** tournament results come from TCG TopDecks HQ and Egman Events (`collect_meta.py`). The official site's featured decks are kept but labelled "official-featured" and left out of meta shares. Duplicate lists reported by both sites, and lists that mix in a sideboard, are skipped automatically. Player names are never stored.

### 🔌 MCP servers

| Server | Source | Tools |
|---|---|---|
| `local-llm` | `ollama_mcp.py` from zoroask/my-muti-agentic | `ask_local_llm` (judgement steps, think=True; optional, Claude is the fallback) |

### Your files

| Folder | Contents |
|---|---|
| `decks/` | One `.txt` per deck: `<count> <card no> [name]`, sections `# Main` / `# Resource` (egman deckbuilder exports work if they list card numbers) |
| `logs/match-log.csv` | One row per game: `date,event,my_deck,opp_deck,game,went_first,result,notes` |
| `plans/` | Prep plans written by TCG Lead |
| `data/format.json` | Rules numbers, ban list, latest set, event details |

## Maintenance

**Weekly meta refresh:** `python tools/collect_meta.py --source all` then `python tools/rebuild_all.py`.
When a new format starts, pass the new set: `--set-group GD06` (Egman) and `--page <TopDecks set page slug>`.

**After a new set or ban list:**
1. Update `data/format.json` (ban list, `latest_set`, `stale_before`) from the official pages.
2. `python tools/refresh_cards.py --new-only` (or a full refresh), then `python tools/mark_stale.py --before <date>`.
3. `python tools/rebuild_all.py`.

## Tests

```
python -m unittest discover -s tests
```
