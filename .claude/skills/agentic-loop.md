# Skill: Agentic Loop

Structure any iterative task that may need more than one attempt (fixing failing CI, clearing lint errors, iterating a PR, or a multi-agent chain that re-runs on FAIL) as observe, decide, act, verify, with explicit stop conditions. Not for single-shot edits. Derived from the upstream agentic-loop-github skill.

## Loop
1. Observe: read the real current state (CI checks and logs, current diff, actual files); never assume it.
2. Decide: one targeted action that addresses the cause shown by the evidence; the minimal fix, not a rewrite.
3. Act: apply it, under the CLAUDE.md Rule 3 gate for changes; commit locally, push only with approval.
4. Verify against the stop criterion, not an impression.
5. Continue, try differently, roll back, or stop. Stop as soon as the criterion is met.

## Objective vs subjective criteria
- Objective (the agent may loop alone): CI green, tests pass, linter clean, build compiles, PR mergeable.
- Subjective (tone, quality, fit): don't loop blindly; ask the user which test to apply, or agree a checkable proxy (e.g. required sections present). Split mixed tasks and give each part its own criterion.

## Guardrails
- Fix a maximum attempt count up front (3-5 for a targeted fix; audit-chain uses 3). Never exceed it silently; on reaching it, report the state and ask.
- Stagnation: if the same error survives 2 different attempts, stop and explain the blockage instead of guessing again (same rule as audit-chain).
- Rollback: if an attempt makes things worse, return to the last known-good state before retrying. Commit or stash first and ask before discarding changes (`git checkout -- <file>` loses work). Never stack fixes on a broken state.
- Keep a short in-task log of what was tried and why it failed, so nothing is retried.

## Example
"CI markdownlint fails": criterion = all checks green. Read the exact error, fix that line, commit, re-check; a different failure means iterate; the same failure twice means stop and report.
