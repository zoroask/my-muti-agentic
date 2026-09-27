# agent_runtime

A stdlib-only state machine that sequences Claude Code subagent invocations.

## What it is for

The project already had multi-agent chains described in `.claude/commands/`.
The problem with describing a chain in prose is that prose is a request: an
agent can ignore "do NOT apply anything yet", and once did — the pipeline
coders wrote to disk and scope-crept despite explicit instructions not to.

This package moves the parts that must not be negotiable out of the prompt and
into code:

| Enforced here, not in a prompt | Where |
|---|---|
| Which agent may run next | `state.Run.record` refuses any other agent |
| The 3-pass cap | `state.Run._settle_verdict` |
| Stopping a loop that repeats itself | same, via `previous_findings` |
| Pausing for user approval | `chains.Step.gate` / `Chain.final_gate` |
| A record of what actually ran | `transcript.py` → `runs/<id>/transcript.jsonl` |

## What it deliberately does not do

**It never calls an LLM API.** There is no `anthropic` import and no API key,
so it adds no cost beyond the Claude Code session you are already in. All
model work happens as Claude Code subagents, using the personas in
`.claude/agents/` — the same files this package reads to validate a chain.

That split is the whole design: **Python decides the order, Claude Code does
the thinking.**

## Requirements

Python 3.10+. No dependencies — standard library only, so there is no
`requirements.txt` to install.

## Use it from Claude Code

    /run-agents audit "harden env_guard.py"
    /full-audit-and-testing

See `.claude/commands/` for what those commands do on your behalf.

## Use it directly

    python -m agent_runtime list
    python -m agent_runtime validate
    python -m agent_runtime start audit "harden env_guard.py"
    python -m agent_runtime record --agent "Architect Advisor" --output-file plan.md
    python -m agent_runtime approve
    python -m agent_runtime status
    python -m agent_runtime audit

Every command prints `KEY=value` lines, with long text wrapped in `<<<` /
`>>>`, so the calling session can act on the result without guessing.

## The chains

`audit` — mirrors `/audit-chain`:

    Architect Advisor -> Bug Fixer -> [gate] -> Bug Fixer -> PA Right-Hand Audit
                              ^                                       |
                              +---------------- FAIL, max 3 passes ----+

`pipeline` — mirrors the Pipeline Planner orchestration behind `/focus-project`:

    Pipeline Planner -> Frontend Coder + Backend Coder -> Pipeline Reviewer
                                  ^         (parallel)             |
                                  +------- FAIL, max 3 passes -----+
                                                                   |
                                             [gate: write to disk] -+

## Verdicts

A chain's last step decides PASS or FAIL. Two modes, both in `state.classify`:

- `audit` — findings are the lines marked `[x]`; a clean report has none.
- `json` — the first JSON object in the output must carry `"status": "PASS"`.

On FAIL the chain restarts from step 1, carrying the findings into the next
prompt — unless the findings are identical to the previous pass (`STALLED`) or
the pass cap is reached (`EXHAUSTED`).

## Whole-project audit

    python -m agent_runtime audit

Runs eight deterministic checks over every file, runs the test suite, and writes
a self-contained `audit-report.html`:

| Check | Catches |
|---|---|
| Agent personas | missing frontmatter, duplicate names, empty bodies |
| Skill index | `.claude/skills/README.md` drifting from the files on disk |
| Command index | a command that exists but is undocumented, or vice versa |
| Hook wiring | a hook script nothing references, or a settings file naming a script that is not there (reads `settings.local.json` too; a script launched from outside, such as by an OS protocol handler, opts out with a `hook-wiring: external` comment) |
| Chain wiring | a chain naming a missing or retired agent |
| Python syntax | anything that will not parse |
| Doc links | relative markdown links pointing at deleted files |
| Git hygiene | `.env`, databases, logs or PDFs tracked in git |

Severity follows `.claude/skills/repo-security-audit.md`: `[H]` breaks
operation, leaks data or silently misbehaves; `[M]` noticeable gap; `[L]`
cosmetic. Secret files are reported **by name only** — their contents are never
read.

Flags: `--html PATH`, `--findings PATH` (merge a subagent's report),
`--include-references` (audit the vendored `references/` tree too),
`--no-tests`, `--strict` (exit 1 on any `[H]`).

`/full-audit-and-testing` wraps this: Python does the checks above, then
`PA Right-Hand Audit & Testing` adds the judgement half, and both land in one
report.

## Layout

    registry.py    parse .claude/agents/*.md into Agent objects
    chains.py      the two chains, declared as plain data
    state.py       the state machine: gates, pass cap, stagnation stop
    transcript.py  append-only JSONL ledger
    audit.py       the deterministic whole-project checks
    report.py      render an audit as self-contained HTML
    cli.py         the KEY=value command surface

## Tests

    python -m unittest discover -s tests -t .

113 tests, no network, no API key, nothing to pay for. `test_chains.py` checks
every agent named by a chain still exists in `.claude/agents/`, which is what
catches a renamed persona before a run does.
