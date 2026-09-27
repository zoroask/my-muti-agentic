Drive a multi-agent chain whose ordering, pass cap and approval gates are
enforced by `agent_runtime/` instead of by prompt instructions.

The Python runtime never calls an LLM. It tells you which agent to invoke
next; you invoke it as a Claude Code subagent, then report its output back.

## Usage
- `/run-agents audit "<task>"` — Architect Advisor → Bug Fixer → PA Right-Hand
- `/run-agents pipeline "<description>"` — Planner → both Coders → Reviewer
- `/run-agents status` — where the current run stands
- `/run-agents list` — available chains and their steps
- `/run-agents validate` — check every chain against `.claude/agents/`

## Steps
1. Ask the user for the task if it was not given as an argument.
2. Start the run:
   `python -m agent_runtime start <chain> "<task>"`
3. Read the `KEY=value` block from stdout. It tells you:
   - `NEXT_AGENTS` — the agent(s) to invoke, `|`-separated
   - `PARALLEL` — `yes` means invoke them together in one message
   - `PROMPT<<< ... >>>` — the exact text to pass them
4. Invoke those agents with the Agent tool. Pass the `PROMPT` block as the
   task. Never answer a step yourself — the run is only meaningful if the
   named persona actually produces the output.
5. Write each agent's report to a file, then record it:
   `python -m agent_runtime record --agent "<name>" --output-file <path>`
   Record one command per agent, including for a parallel step.
6. Act on the new `STATUS`:
   - `RUNNING` — go back to step 3.
   - `GATE=approval_required` — show the user Summary / Action plan /
     Before-After per CLAUDE.md Rule 3 and **STOP**. On an explicit "yes",
     run `python -m agent_runtime approve`; on anything else, run
     `python -m agent_runtime reject`.
   - `DONE` — report the result to the user.
   - `STALLED` — the same findings repeated across passes. Report every
     `FINDING=` line verbatim and state that the chain stalled.
   - `EXHAUSTED` — the pass cap was reached while still failing. Report the
     remaining `FINDING=` lines verbatim.
   - `REJECTED` — stop; apply nothing.

## Rules
- Never invoke an agent the runtime did not name. `record` will refuse an
  out-of-turn agent, and that refusal is the point of the runtime.
- Never run `approve` on your own judgement — only on the user's explicit
  "yes". Running inside this chain does not waive CLAUDE.md Rule 3.
- Report `FINDING=` lines verbatim. Do not paraphrase or soften them.
- Do not edit `runs/` by hand. It is the ledger of what actually happened.
- If `validate` reports `RESULT=FAIL`, fix the chain or the persona before
  starting a run.
