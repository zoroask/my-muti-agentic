# Skill: Intent Guard Shield

Keep an agent faithful to the user's stated intent: no silent workarounds, no false successes, no drifting interpretation. Use when a request states a goal rather than a strict procedure, when the agent must choose a strategy, or when a failure could be masked by an apparent success.

## Steps
1. Restate the intent in one unambiguous sentence.
2. List explicit constraints, prohibitions, success criteria, failure criteria, and the points where you must stop and ask. Separate real constraints from your own assumptions.
3. If missing information would change the meaning of the action, ask before acting.
4. Define what observable evidence counts as success and what triggers an immediate stop.
5. Run the smallest possible test first and compare the result with the goal.
6. If the result deviates, say so plainly. Widen scope only after the minimal test is validated.

## Stop immediately when
An essential command fails; a critical step is ambiguous; the result depends on an unvalidated assumption; it "succeeds" without objective proof; or you are tempted to bypass a constraint you cannot justify.

## Never
- Replace a constraint with an unannounced approximation.
- Reach "success" by quietly changing the metric or the scope.
- Suppress a visible error without explaining its cause.
- Satisfy the overall intent by violating an explicit prohibition. Bypassing an anti-bot wall, CAPTCHA or login gate counts.
A necessary detour is announced as a detour, with its trade-off.

## Output
Restated intent; assumptions used; result; deviations found; confidence; what to verify manually.

Intent guides the action; verification guards the truth. For grading claims by evidence strength see verification-rigoureuse.
