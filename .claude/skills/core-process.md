# Skill: Core Process

The standard path for every request that involves more than one stage, tool or agent. The main Claude Code session ("agent core") follows it. It sits on top of CLAUDE.md and never overrides it — stage 6 *is* Rule 3.

Sources behind the order: Claude Code best practices (explore → plan → implement, runnable verification, adversarial review), Anthropic's multi-agent research system (scale effort to complexity, brief sub-agents fully, save the plan), and Reflexion (store lessons in memory and reuse them).

## Stage 1 — Agent core: size the task
- **Small task** — you could describe the whole change in one sentence, or it is a quick question: skip stages 2–5 and 7. A question is just answered. A change still gets the Rule 3 response and waits for "yes" (stage 6), then any available check runs (stage 8) and the result is summarized (stage 9). Say that you took the fast path.
- **Everything else** — run all stages in order.

## Stage 2 — Find history
Look for related past work before planning:
- Memory: `MEMORY.md` index, then only the entries whose description matches the task
- Past runs: the most recent `agent_runtime/runs/*/transcript.jsonl` for the same chain or files
- Git: `git log --oneline -- <files involved>` for recent decisions
Use what you find; do not re-litigate settled decisions without saying why.

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
- If the task taught something durable and non-obvious, write **one short memory entry** (`feedback` for how the user wants work done, `project` for a decision) and add its line to `MEMORY.md`
- Say in the reply that you saved it (CLAUDE.md Memory rules)
- Record lessons in memory, never in CLAUDE.md; never store secrets
- Nothing new learned → write nothing
