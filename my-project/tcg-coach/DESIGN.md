# TCG Coach — DESIGN.md

> Revised 2026-10-31. System type changed from Web app to Claude Code agent cluster.
> Source files read: README.md, CLAUDE.md, .claude/agents/*.md (all four), tools/ (23 Python scripts + scrape_official.js), decks/bw-sf-anti-meta.txt, prior web-app DESIGN.md.

---

## 1. Requirements

| ID | Statement | Type | Priority | Acceptance criterion | Status |
|---|---|---|---|---|---|
| R1 | Card search — given filters (color, type, cost, keyword, trait, card number or name), return matching cards ranked by meta usage then all other matches; show ban status and analysis status. | Functional | Must | search.py stdout returns a two-section list; each card has ban_status, meta_pct, analysis_status; Deck Analyst shows source and date in chat. | OK |
| R2 | Card analysis — given a card number, return a cached judgment (role, strengths, conditions, weaknesses, synergies, copies, rating) if fresh; tell the user when the cache is stale or absent so they can request new analysis. | Functional | Must | Deck Analyst reads card_analysis.jsonl; shows the full record when fresh; prints "no cached analysis — run analysis workflow" when stale or absent; no effect text stored (R11). | OK |
| R3 | Deck legality — given a .txt decklist, check main size (50), resource size (10), copies (max 4), at most 2 colors, ban list (banned, restricted, banned pairs, vanilla rule); return LEGAL or list all problems with rule references. | Functional | Must | deck_check.py exits 0 on a valid deck; an illegal deck prints problems each with code and message; Deck Analyst shows the output in chat. | OK |
| R4 | Deck statistics — given a .txt decklist, compute color breakdown, type breakdown, Lv curve, cost curve, link coverage and hypergeometric opening odds (with optional redraw). | Functional | Must | deck_stats.py returns all fields; Deck Analyst presents them in chat as a table and summary. | OK |
| R5 | Meta collection and archetype table — collect tournament decklists from approved sources; compute card usage shares and archetype groups; flag STALE and LOW CONFIDENCE (fewer than 20 lists); never store player names. | Functional | Must | meta_table.py returns archetypes with share, date range and flags; collect_meta.py + rebuild_all.py refresh; no player names in any file; Meta Coach shows flags in chat. | OK |
| R6 | Matchup and sideboard plan — Meta Coach builds a per-matchup plan (role, key cards, keep/ship) from meta records and local-LLM judgment. | Functional | Must | Output includes role, key cards, keep/ship and side-in/out; every claim cites script data; judgment goes to mcp__local-llm__ask_local_llm; if the tool is missing, Meta Coach says so and stops. | OK |
| R7 | Practice log statistics — given logs/match-log.csv, compute win rates per matchup, going first/second, G1 vs post-side, and classify misplays from notes; list unclassified notes. | Functional | Must | log_stats.py returns all aggregates; under 10 games per matchup is labeled "too few to conclude"; Practice Coach groups unclassified notes in chat via local-LLM judgment. | OK |
| R8 | Event prep plan — given event name, date, deck and tier, generate a dated week-by-week schedule and event-day checklist; write to plans/ only after the user says "yes". | Functional | Must | TCG Lead runs make_plan.py for a preview; shows plan markdown and a Before/After in chat; writes plans/<slug>.md only after "yes" (R13). | OK |
| R9 | Deck optimization — score and rank flex-slot swaps for consistency improvement; show delta-score and sensitivity; each swap reviewed by Deck Analyst before it is presented. | Functional | Should | deck_optimize.py returns ranked swaps with delta_score; Deck Analyst shows a swap table with reasoning; the user must say "yes" before any deck file change (R13). | OK |
| R10 | Knowledge base rebuild — after a new set or ban list, refresh card data, mark stale analyses, rebuild index and FTS5 database via a chat command. | Functional | Must | TCG Lead or the user runs rebuild_all.py; stdout shown in chat; exits 0 on success; errors shown plainly. | OK |
| R11 | Card text policy — card effect text is read live from the official site and never stored in files or shown in chat output. | Constraint | Must | Deck Analyst runs fetch_card.py live when needed; never pastes effect text into chat or analysis records; analysis_schema.py rejects any record containing pasted effect text. | OK |
| R12 | Fair-play boundary — the cluster never surfaces advice on marked cards, stacking, collusion, bribery, angle-shooting or slow-play tactics. | Constraint | Must | No agent generates such content; tcg-prep-standards rules apply to every agent. | OK |
| R13 | Write gate — all writes to user files (decks/, plans/, logs/, data/format.json) require an explicit "yes" in chat, preceded by a Before/After shown by the agent (CLAUDE.md Rule 3). | Constraint | Must | No agent writes a file without first showing Before/After and waiting for "yes"; agents stop on any pending write without "yes"; there is no HTTP endpoint, no confirm body parameter and no 422. | OK |
| R14 | Evidence labeling — every meta claim shows its source and date; STALE and LOW CONFIDENCE flags are visible in chat output; odds claims cite the script and distribution. | Constraint | Must | All meta output includes source, date and STALE/LOW CONFIDENCE flags; odds output cites "hypergeometric, deck_stats.py"; no claim from memory alone. | OK |

---

## 2. Requirement Audit

**Verdict: Pass**

| Goal / user task | R-numbers |
|---|---|
| Card search and browse | R1, R14 |
| Card analysis (cached) | R2, R11 |
| Deck legality check | R3 |
| Deck statistics | R4 |
| Meta collection and archetype table | R5, R14 |
| Matchup plan (data + local-LLM narrative) | R6 |
| Practice log and stats | R7 |
| Event prep plan | R8, R13 |
| Deck optimization | R9, R13 |
| Knowledge base maintenance | R10, R11 |
| Fair play and evidence integrity | R11, R12, R13, R14 |

Coverage gaps: none. Conflicts: none. R6 narrative is delivered by Meta Coach in every session (the old A13 deferral is gone).

Challenge-plan:
1. Break it: the local-LLM tool may be missing or fail. Every agent states the error plainly and stops the judgment step; script-only output is still useful.
2. Skip it: the CLI tools already work without agents. Agents add routing, the write gate and judgment on top of deterministic scripts.
3. Minimize it: minimum viable cluster = TCG Lead + Deck Analyst (R1–R4, R8, R13). Meta Coach and Practice Coach add R5–R7.
4. Maintain it: after each new set only data files change, via rebuild_all.py. No agent file changes are needed.

Result: design holds. A7 (end-to-end test) is the highest-risk item; if local-LLM is unavailable, test script-only paths first.

---

## 3. System Type

**Type: Claude Code agent cluster** (user change, 2026-10-31)

**Owner:** User. The system runs inside Claude Code sessions; no server, browser or build step. The tools/ compute layer was built in Phase 1.

**Architecture:** The interface is the Claude Code chat. The user invokes `/tcg` or addresses TCG Lead, which routes to three specialists. All computation runs through tools/ scripts. Judgment steps (card analysis, matchup plans, misplay grouping, plan priorities) go to the local LLM via `mcp__local-llm__ask_local_llm`. File writes need an explicit "yes" (R13). No web server, no HTTP API, no npm.

**Deployment:** Claude Code session on desktop. Single user. No auth. Only fetch_card.py, refresh_cards.py and collect_meta.py need the network (scrape_official.js is the official-site scraper used by refresh).

**Cost:** no API billing beyond the Claude Code plan. The local LLM runs on the user's machine.

---

## 4. UI Design

The interface is Claude Code chat. There is no browser screen.

| Topic | How the user invokes | Agent response format |
|---|---|---|
| Card search | "find Blue blockers under cost 3" | Numbered list: meta-played section first, then other matches; No., Name, Meta%, Analysis status, Ban status; source and date below (R14) |
| Card analysis | "analyse GD05-002" | Block: Role / Strengths / Conditions / Weaknesses / Synergies / Copies / Rating / Analysed date; R11 note |
| Deck legality | "check my deck" | One line LEGAL or ILLEGAL; problems as "CODE: message"; banlist date |
| Deck statistics | "stats for bw-sf-anti-meta" | Tables: colors, types, Lv curve, cost curve, link coverage, opening odds |
| Meta table | "what is the meta" | Table: Archetype / Share% / Lists / Latest / Flags; source and date; STALE and LOW CONFIDENCE (R14) |
| Matchup plan | "how do I play vs Blue Freedom" | Block: Role / Their key cards / My key cards / Keep-Ship / Side in / Side out / One mistake to avoid |
| Practice stats | "how am I doing" | Overall and per-matchup win rate; G1 vs post-side; misplay groups; drills |
| Event prep | "get me ready for Store Championship 2026-11-21" | Plan preview; Before/After; STOP until "yes" (R13) |
| Deck optimization | "find flex slots" | Swap table Out / In / Delta score / Reasoning; STOP until "yes" (R13) |
| KB rebuild | "rebuild the knowledge base" | rebuild_all.py stdout; success or error stated plainly |

Output conventions:
- English only (CLAUDE.md Rule 1).
- Every judgment step names the local-LLM call, or says "local-LLM tool unavailable" and stops.
- A Before/After block appears before any file write; the agent waits for "yes" (R13).
- STALE and LOW CONFIDENCE flags appear in all meta output (R14).
- Effect text never appears in chat output (R11). Fair-play boundary applies to all output (R12).

Demo: demo/demo.html simulates agent chat flows as a guided tour; it is not the real interface.

---

## 5. Text Design

### Agents

| Agent | Single responsibility | R |
|---|---|---|
| TCG Lead | Entry point; builds the prep plan; routes to specialists; enforces the write gate | R8, R13 |
| Deck Analyst | Card search, card analysis (cache first), legality, consistency, deck math, swaps | R1, R2, R3, R4, R9, R11 |
| Meta & Matchup Coach | Sourced meta; archetype table; per-matchup and sideboard plan | R5, R6, R14 |
| Practice Coach | Match-log stats; misplay grouping; drill recommendations | R7 |

### Scripts and owners

| Script | Owner | Function | R |
|---|---|---|---|
| search.py | Deck Analyst | Card search with meta ranking and ban check | R1, R14 |
| fetch_card.py | Deck Analyst | Live card text (never stored) | R2, R11 |
| build_context.py | Deck Analyst | RAG context for card questions | R2 |
| deck_check.py | Deck Analyst | Legality check | R3 |
| deck_stats.py | Deck Analyst | Curve, colors, link coverage, opening odds | R4 |
| deck_math.py | Deck Analyst | Joint odds, on-curve odds, goldfish simulation | R4 |
| deck_optimize.py | Deck Analyst | Flex-slot swap scoring | R9 |
| analysis_schema.py | Deck Analyst | Template and validation for the analysis cache | R2, R11 |
| build_db.py, rag_index.py | rebuild_all | FTS5 index, RAG chunk index | R1, R2, R10 |
| collect_meta.py | Meta Coach | Collect tournament decklists from approved sources | R5 |
| meta_table.py | Meta Coach | Archetype table with share and flags | R5, R14 |
| card_usage.py | Meta Coach | Per-card usage share | R5, R6 |
| archetypes.py | Meta Coach | Archetype grouping | R5 |
| log_stats.py | Practice Coach | Win rates, G1/post-side, misplay groups | R7 |
| make_plan.py | TCG Lead | Event prep plan skeleton | R8 |
| mark_stale.py, rebuild_all.py, refresh_cards.py, export_sets.py, verify_cards.py, batch_targets.py, scrape_official.js | TCG Lead / rebuild_all | Knowledge base refresh and integrity | R10, R11 |
| common.py | All | Shared utilities | All |

### Skills

| Skill | Agents | Purpose |
|---|---|---|
| tcg-prep-standards | All | Tournament prep rules, fair play (R12), write gate (R13) |
| gundam-gcg-rag | All | RAG map: card search, analysis, meta, log, optimization |
| long-context-lost-in-the-middle | All | Place critical facts at start and end of long prompts |

### Agent, skill and tool changes needed

| Item | Change | Reason |
|---|---|---|
| tcg-lead-main-agent.md | Verify routing rows; no web references | Web path removed |
| tcg-deck-analyst-sub-agent.md | Verify write gate for the analysis cache (R13) | Gate is chat "yes" |
| tcg-meta-coach / tcg-practice-coach | None expected | Already chat-native |
| gundam-gcg-rag SKILL.md | Verify all workflows map to named scripts | Completeness |
| tools_bridge.py, web/ | Not built | Dropped with the web app |

### LLM processes (local LLM)

All judgment goes to `mcp__local-llm__ask_local_llm` with think=True and a file excerpt. If the tool is missing or errors, the agent says so and stops.

| Process | Agent | Judgment | R |
|---|---|---|---|
| Card analysis | Deck Analyst | Role, strengths, conditions, weaknesses, synergies, copies, rating | R2 |
| Deck swap rationale | Deck Analyst | Why each swap helps in the expected meta | R9 |
| Matchup and sideboard plan | Meta Coach | Role, key cards, keep/ship, side-in/out | R6 |
| Misplay grouping and drills | Practice Coach | Group unclassified notes; recommend drills | R7 |
| Prep plan priorities | TCG Lead | Top 3 findings merged into the plan | R8 |

### Non-functional
- Secrets: none. No credentials or API keys (CLAUDE.md Rule 4).
- Write gate: no write without Before/After and "yes" (R13).
- Offline: all tools work offline except fetch_card.py, refresh_cards.py and collect_meta.py. Agents say when the network is needed.
- Freshness: agents check stale_before in format.json and flag STALE (R14).
- Language: English only.

### Out of scope
Browser, FastAPI, React, HTTP API, web server, tools_bridge.py, mobile app, multi-user, auth, other card games, deck construction from scratch, live tournament coverage, public deployment.

---

## 6. Roadmap

Phase 1 — Python tools and agents (done): knowledge base, scripts, agent cluster, 2026-08-03 to 2026-10-12 [x]

Phase 2 — Agent cluster verification and hardening (planned):
- Routing and workflow verification: 2026-11-03 to 2026-11-13 (critical path)
- Buffer (20%): 2026-11-16 to 2026-11-17
- Post-GD07 data refresh: milestone 2027-01-15

Phase 2 done check: all workflows give correct chat output; write gate tested (plan write, log append, format.json edit); end-to-end event-prep flow completes.

---

## 7. Start -> Goal List

Start: tools and agent cluster exist; the design planned a web app with an HTTP 422 write gate; narrative matchup analysis was deferred (A13).
Goal: the agent cluster is verified and hardened as the primary system; every workflow gives correct output; the write gate is the chat "yes"; Meta Coach delivers the R6 narrative; no web server is needed.

| ID | Item | Serves | Owner | Depends on | Output | Done check | Est (d) | Start | End | Critical | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1-S12 | Phase 1: tools, knowledge base, agent cluster | R1-R14 | Python Automation Lead / User | — | tools/, .claude/ agents | Scripts run; rebuild_all.py exits 0 | — | 2026-08-03 | 2026-10-12 | — | [x] |
| A1 | Verify TCG Lead routing | R8, R13 | User | S1-S12 | Agent file if fixed | Routing rows reach the right specialist | 1 | 2026-11-03 | 2026-11-03 | Yes | [ ] |
| A2 | Verify Deck Analyst workflow | R1 R2 R3 R4 R9 R11 | User | A1 | Verified or updated agent | Scripts give correct output; analysis_schema rejects effect text | 2 | 2026-11-04 | 2026-11-05 | Yes | [ ] |
| A3 | Verify Meta Coach workflow | R5 R6 R14 | User | A1 | Verified or updated agent | Flags correct; matchup plan cites script data | 2 | 2026-11-06 | 2026-11-07 | Yes | [ ] |
| A4 | Verify Practice Coach workflow | R7 | User | A1 | Verified or updated agent | "too few to conclude" rule holds; misplays grouped | 1 | 2026-11-10 | 2026-11-10 | Yes | [ ] |
| A5 | Write-gate audit of all four agents | R13 | User | A2 A3 A4 | Agent files if fixed | No agent writes without "yes" | 1 | 2026-11-11 | 2026-11-11 | Yes | [ ] |
| A6 | Skill check: gundam-gcg-rag maps workflows to scripts | Skills | User | A2 | Updated SKILL.md if needed | Every workflow names a real script | 1 | 2026-11-11 | 2026-11-11 | No | [ ] |
| A7 | End-to-end event-prep test | All R | User | A5 A6 | Pass/fail notes | All agents correct; gate and R14 flags tested | 2 | 2026-11-12 | 2026-11-13 | Yes | [ ] |
| A8 | Post-GD07 data refresh | R5 R10 R14 | User | A7 | Updated cards.json, tcg.db, card-usage.json | rebuild_all.py exits 0 | 2 | 2027-01-13 | 2027-01-15 | No | [ ] |

---

## 8. Schedule

Mode A — estimate. All estimates are hypotheses. Capacity: 2 h/day, 5 d/week. Start 2026-11-03.

| ID | O | M | P | Expected | Confidence | Basis |
|---|---|---|---|---|---|---|
| A1 | 0.5 | 1 | 2 | 1d | High | Routing table exists; smoke test |
| A2 | 1 | 2 | 3 | 2d | Medium | Many scripts; schema validation |
| A3 | 1 | 2 | 3 | 2d | Medium | Depends on live sources |
| A4 | 0.5 | 1 | 2 | 1d | High | Single script |
| A5 | 0.5 | 1 | 2 | 1d | High | Audit and fix |
| A6 | 0.5 | 1 | 2 | 1d | High | Skill file check |
| A7 | 1 | 2 | 3 | 2d | Medium | Local-LLM availability varies |
| Buffer | — | — | — | 2d | — | 20% of 9d critical path |

Critical path: A1 -> A2 -> A3 -> A4 -> A5 -> A7 = 9d. A6 runs in parallel with A5. A8 is a milestone.
Range: 2026-11-03 to 2026-11-17.

Top risks:
1. Local-LLM tool unavailable during A7: test script-only paths first.
2. collect_meta.py source sites changed: A3 catches it.
3. analysis_schema.py rejects valid records: A2 tests a good and a bad record.

```
Nov 03  A1 [=]    TCG Lead routing (1d)       CRITICAL
Nov 04  A2 [==]   Deck Analyst (2d)           CRITICAL
Nov 06  A3 [==]   Meta Coach (2d)             CRITICAL
Nov 10  A4 [=]    Practice Coach (1d)         CRITICAL
Nov 11  A5 [=]    Write-gate audit (1d)       CRITICAL
Nov 11  A6 [=]    Skill check (1d)            parallel
Nov 12  A7 [==]   End-to-end test (2d)        CRITICAL
Nov 16  BUF [==]  Buffer 2d
Nov 17  DONE
Jan 13  A8 [==]   Post-GD07 refresh (2d)      milestone
```

---

## 9. Structure

```
my-project/tcg-coach/
|-- .claude/agents/        tcg-lead-main-agent, tcg-deck-analyst-sub-agent,
|                          tcg-meta-coach-sub-agent, tcg-practice-coach-sub-agent
|-- .claude/skills/        tcg-prep-standards, gundam-gcg-rag, long-context-lost-in-the-middle
|-- claude-config/         Sync source for .claude/ (install.bat copies)
|-- tools/                 Compute layer (Python scripts + scrape_official.js)
|-- knowledge/gundam-gcg/  cards, index, meta, banlist, glossary
|-- data/format.json, decks/, logs/, plans/, tests/
|-- demo/demo.html         Offline guided tour (agent chat flows)
|-- demo/diagrams.html     Offline architecture and flow diagrams
`-- README.md, CLAUDE.md, install.bat

NOT present: web/ (FastAPI + React) — dropped.

External (read-only, approved sources):
  gundam-gcg.com               fetch_card.py, refresh_cards.py — R2 R10 R11
  tcgtopdecks-hq.com           collect_meta.py — R5
  deckbuilder.egmanevents.com  collect_meta.py — R5
```

---

## 10. Working Flow

User (Claude Code chat) -> TCG Lead -> specialist agents -> tools/ scripts -> knowledge base files.

```
User (chat) --"get me ready for Store Championship 2026-11-21"--> TCG Lead
   |-- find cards / deck review -> Deck Analyst
   |-- meta / matchup           -> Meta & Matchup Coach
   |-- practice stats           -> Practice Coach
   `-- event prep               -> all three, then merge
TCG Lead merges findings, runs make_plan.py preview
   -> plan markdown + Before/After in chat -> STOP, wait for "yes" (R13)
   -> "yes" -> plans/store-championship.md written
```

Card search (R1, R14):
```
User -> TCG Lead -> Deck Analyst -> search.py --color Blue --keyword Blocker --max_cost 3
     <- two-section list; each card: No., Name, Meta%, Analysis, Ban
     <- "Source: TopDecks HQ + Egman, since 2026-09-25" (R14)
```

Write gate (R8, R13):
```
TCG Lead: make_plan.py (preview, no write) -> plan markdown in chat
  Before: plans/store-championship.md -- does not exist
  After:  plans/store-championship.md -- created
  STOP: "Type 'yes' to save, anything else to cancel"
"yes" -> make_plan.py --write -> "Plan saved"
anything else -> no write
```

---

## 11. Logic Flow

Card search with meta ranking (R1, R5, R14):
```
User asks -> TCG Lead routes to Deck Analyst
  tcg.db present? no -> run rebuild_all.py (R10)
  yes -> search.py
  meta stale? yes -> flag STALE
  lists < 20? yes -> LOW CONFIDENCE note
  -> two-section list in chat
  user asks for card detail -> cache fresh? yes -> show analysis (+R11 note)
                                           no  -> run analysis workflow (local LLM)
```

Write gate (R13):
```
User: "plan for event" -> make_plan.py preview -> plan in chat
-> Before/After -> STOP "Type 'yes' to save"
-> "yes": make_plan.py --write -> file written -> "Plan saved"
-> else: not saved
```

---

## 12. Data Model

ER does not apply: file-based storage. tcg.db is a generated read-only FTS5 index. The agent cluster adds no new persistent storage.

Authority files (unchanged): cards.json (no effect text), decklists.jsonl (no player names), card_analysis.jsonl (no effect text), match-log.csv, format.json, plans/*.md, decks/*.txt.
Generated by rebuild_all.py: tcg.db, index/chunks.jsonl, meta/card-usage.json, cards/by-set/*.md.
In flight only: script stdout and local-LLM responses.

match-log.csv columns: date, event, my_deck, opp_deck, game, went_first, result, notes.

---

## 13. Type Add-On (Agent cluster)

```
Claude Code session -> TCG Lead
   +-> Deck Analyst: search, deck_check, deck_stats, deck_math, deck_optimize,
   |                 fetch_card (live, R11), analysis_schema   -> local LLM judgment
   +-> Meta Coach:   collect_meta, meta_table, card_usage      -> local LLM judgment
   `-> Practice Coach: log_stats                               -> local LLM judgment
TCG Lead: make_plan.py (R8); write gate = Before/After + "yes" (R13)
```

| Request type | Routed to | Primary scripts |
|---|---|---|
| Find cards | Deck Analyst | search.py |
| Review or tune a decklist; judge a card | Deck Analyst | deck_check.py, deck_stats.py, fetch_card.py |
| Optimize a deck with maths | Deck Analyst | deck_optimize.py, deck_math.py |
| Meta, matchup, sideboard | Meta & Matchup Coach | meta_table.py, card_usage.py |
| Practice review | Practice Coach | log_stats.py |
| Full event prep | All three, TCG Lead merges | make_plan.py |

---

## 14. Demo

Path: my-project/tcg-coach/demo/demo.html. Form: guided tour of agent chat flows. Open by double-click; no server; all content inline. Sample data only.

| R | In demo? | Step |
|---|---|---|
| R1 | Yes | Card search |
| R2, R11 | Yes | Card analysis |
| R3, R4, R9 | Yes (R9 partial) | Deck analysis |
| R5, R6, R14 | Yes | Meta |
| R7 | Yes | Practice log |
| R8, R13 | Yes | Event plan write gate |
| R10 | Yes | KB rebuild |
| R12 | Yes | Agent routing note |

---

## 15. Requirement Traceability

| R | Where |
|---|---|
| R1 | Deck Analyst, search.py; sections 10, 11 |
| R2 | Deck Analyst, analysis_schema.py; section 11 |
| R3, R4 | Deck Analyst, deck_check.py, deck_stats.py, deck_math.py |
| R5, R6, R14 | Meta Coach, collect_meta.py, meta_table.py; section 13 |
| R7 | Practice Coach, log_stats.py |
| R8, R13 | TCG Lead, make_plan.py; sections 10, 11, 13 |
| R9 | Deck Analyst, deck_optimize.py |
| R10 | TCG Lead, rebuild_all.py |
| R11 | fetch_card.py (live only), analysis_schema.py |
| R12 | tcg-prep-standards skill; all agent rules |
