# Skill: Diagnose

Disciplined loop for hard bugs (non-obvious cause, flaky behaviour, performance regressions). If the cause is obvious on one read, just fix it through the normal Bug Fixer flow; for "why did an agent produce bad output" use debug-agent.

## Steps
1. Build a feedback loop first: a fast, deterministic pass/fail signal you can run yourself. Try, in order: a failing test at the right seam; a script with fixture input diffed against a known-good result; replaying a captured payload or log; a throwaway harness around one function; a fuzz loop for "sometimes wrong"; a bisect harness (`git bisect run`) if it worked before; an old-vs-new differential run. For non-deterministic bugs, raise the reproduction rate instead of chasing a clean repro. If no loop is possible, stop, list what you tried, and ask for an environment, a captured artifact (log, dump) or permission for temporary instrumentation. Do not hypothesise without a loop.
2. Reproduce: run it and watch the failure the user actually described (not a nearby one); capture the exact symptom.
3. Hypothesise: write 3-5 ranked, falsifiable hypotheses ("if X is the cause, changing Y makes it vanish") and show them to the user before testing; don't block if they are away.
4. Instrument: one probe per hypothesis, one variable at a time; prefer a debugger or targeted logs at the boundaries that separate hypotheses; tag every debug line with a unique prefix (e.g. `[DEBUG-a4f2]`) so cleanup is one grep. For performance, measure a baseline first, then bisect.
5. Fix and regression-test: write the failing test before the fix only where a seam exercises the real bug pattern; if none exists, report that as a finding. Watch it fail, fix, watch it pass, re-run the step 1 loop on the original scenario.
6. Clean up: remove tagged instrumentation and throwaway files, confirm the original repro is gone, and state the winning hypothesis in the change description. Then ask what would have prevented the bug; if the answer is structural, suggest improve-codebase-architecture.

## Rules
- Any fix is a change: present it under the CLAUDE.md Rule 3 gate before applying.
- Reproduce against fixtures or a dry-run mode, never by performing real side effects (submitting applications, sending messages, hitting live third-party sites).
