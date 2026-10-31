---
name: core-process
description: "Standard 10-stage path for multi-stage requests (history → skills → plan → design → STOP → assign → audit → summary → learn). Use when the user says 'plan this task', 'full process', 'multi-step task', or similar."
---

# Skill: Core Process

The standard path for every request that involves more than one stage, tool or agent. The main Claude Code session ("agent core") follows it. It sits on top of CLAUDE.md and never overrides it — stage 6 *is* Rule 3.

Sources behind the order: Claude Code best practices (explore → plan → implement, runnable verification, adversarial review), Anthropic's multi-agent research system (scale effort to complexity, brief sub-agents fully, save the plan), and Reflexion (store lessons in memory and reuse them).

## Stage 1 — Agent core: size the task
- **Small task** — you could describe the whole change in one sentence, or it is a quick question: skip stages 2–5 and 7. A question is just answered. A change still gets the Rule 3 response and waits for "yes" (stage 6), then any available check runs (stage 8) and the result is summarized (stage 9). Say that you took the fast path.
- **Everything else** — run all stages in order.

## Stage 2 — Find history
Read in tiers and stop as soon as you have enough:
1. Memory: match the task's files, area and keywords against the `MEMORY.md` descriptions and #tags. Open up to 3 entries, or up to 5 if the task spans several areas.
2. Safety net: if nothing matched but the task names a file, Grep the memory folder for that file name (matching lines only, no full reads).
3. Detail: open `details/<name>.md` when an entry's `Caveats` or `Rejected` bear on the task, when the task would reverse or extend that decision, or when the summary is not enough to plan.
4. Git, if the files changed recently: `git log --oneline -n 10 -- <files involved>`.
5. Past runs, only for a re-run of the same chain: the final `STATUS` and `FINDING` lines of the latest `agent_runtime/runs/*/transcript.jsonl`.
List the entries you used in the plan ("Memory used: a, b") so the user can spot a missing one. Treat memory as a hint: check it against the current files before acting on it. Do not re-propose an option listed under `Rejected` without saying what has changed.

## Stage 3 — Check skills and sub-agents
- Match the request against the triggers in `.claude/skills/README.md`; read every matching skill
- Check the roster in `.claude/agents/base-agent.md` for an agent that already owns this kind of work
- Prefer an existing agent or skill over inventing a new approach

## Stage 4 — Plan
- Name the files involved, the approach, and what is deliberately out of scope
- For architecture or persona-library questions, run the **challenge-plan** skill
- Long task (likely to outlive the context window): save the plan to a file in the working area or to memory so it survives compaction

## Stage 5 — Design
Turn the plan into concrete changes: exact files, diffs or new file text, and which sub-agent does what. Use the owning design agent when one exists — Architect Advisor (this library), Project Manager → Python Automation Lead (automation), Web App Lead (`my-project/` app builds) or Game Lead (Godot games).

## Stage 6 — Respond to the user (Rule 3)
Summary → Workflow → Action plan → Before/After → **STOP**. Wait for an explicit "yes". Nothing is changed before this point.

## Stage 7 — Assign sub-agents
Route by kind of work:

| Work | Goes to |
|---|---|
| Python automation | Project Manager → Python Automation Lead (or one specialist directly for a single-area task) |
| Web app build in `my-project/` (Web App cluster) | Project Manager → Web App Lead via `/focus-project` or `/run-agents pipeline` |
| Godot game in `my-project/` (Game cluster) | Project Manager → Game Lead |
| Change to this library (agents, skills, commands, hooks) | `/audit-chain` or `/run-agents audit` |
| Sub-project status and priorities | Project Manager |
| Requirements and system design for a new `my-project/` idea | Design Lead via `/project-design` (or Project Manager) |
| Library status | Architect Advisor → Workflow Monitor |
| Audit, testing, security | PA Right-Hand Audit & Testing (delegates defensive reviews to Security Lead) |
| Security review, detection rules, or RE/CTF learning | Security Lead |
| Explanation | Code Mentor |
| Analyze or deconstruct how an existing app, site or package is built (REA) | Architect Advisor → REA Lead |

Every delegation carries a four-part brief: **objective**, **output format**, **tools and sources to use**, **boundaries** (what not to touch). Use the fewest agents that fit — each extra agent costs a full context.

## Stage 8 — Audit and debug
1. Runnable checks first: tests, `python -m py_compile`, `--dry-run`, `python -m agent_runtime validate`
2. Then an independent reviewer in a fresh context: Automation Reviewer for scripts, Web App Reviewer for web apps, Game Reviewer for games, PA Right-Hand Audit & Testing for this library and for security
3. Only correctness, security or requirement gaps block; style preferences are optional
4. Fix and re-check, at most 3 rounds; stop early if the same findings repeat (**agentic-loop** skill)

## Stage 9 — Summary result
Report what changed, with evidence — test output, the command that ran and its result, the final diff — not just a claim of success. List anything left open.

## Stage 10 — AI learning
1. **Save only if** one of these happened; otherwise write nothing:
   - the user approved a plan at STOP that sets or changes a convention or architecture
   - the user corrected you, or reversed an earlier decision
   - a new external system, path or tool was introduced (`reference`)
   Routine task details and anything git already records are never saved.
2. **Extract the must-keep items first**, copied verbatim: constraints and prohibitions; conditions and exceptions ("only when", "except"); alternatives rejected and why; exact values (paths, flags, numbers, names); open questions; the user's own words for any correction.
3. **Fill the template** within the CLAUDE.md § Memory budget:
   ```
   ---
   name: <kebab-name>
   description: <the words a future task would match>
   metadata: {type: project|feedback|reference, updated: YYYY-MM-DD}
   ---
   Summary: <one line: what was decided>
   Plan/Action: <≤3 bullets>
   Before→After: <file — old behaviour → new behaviour>
   Why: <the reason; the user's exact words if it was a correction>
   Rejected: <option — why not>            (omit if none)
   Caveats: <edge cases, limits, open questions>  (omit if none)
   Ref: <commit / file path / run id; details/<name>.md if written>
   ```
4. **Rehydration test.** Could a fresh session, reading only this entry and its `Ref:`, rebuild the decision and avoid the original mistake? If not, write what is missing to `details/<name>.md`. If unsure, keep it in `details/` rather than drop it.
5. **Update, never re-summarize.** Same topic → rewrite the entry, bump `updated`, and move the previous version to a dated `## History` section in `details/<name>.md`. A reversal records what changed and why.
6. **Learn the user.** Update the matching section of `user-profile.md` (Communication, Working style, Approval patterns, Recurring corrections, Preferences):
   - correction → save immediately, verbatim, with when it applies; tagged `corrected`
   - plan rejected or edited at STOP → note what changed
   - inferred pattern seen twice → don't interrupt; ask once in the Stage 9 summary ("Remember that you prefer X?"); save tagged `confirmed` only on yes
   - new line conflicts with an old one → replace it, keeping the old line in `details/user-profile.md` History
7. **Index and report.** Update the `MEMORY.md` line, including #tags, and show the saved entry text in the reply so the user can correct anything lost.
- Record lessons in memory, never in CLAUDE.md; never store secrets.
