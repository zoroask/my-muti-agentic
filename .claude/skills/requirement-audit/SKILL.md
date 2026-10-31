---
name: requirement-audit
description: "Audit a set of requirements for correctness, coverage and conflicts, turn gaps into questions, and return a requirement table with a Pass / Blocked verdict. Use when the user says 'audit requirements', 'check my requirements', or similar; also project-design-steps step 4."
---

# Skill: Requirement Audit

Check that the requirements are correct, cover the goal and do not conflict, and ask for what is missing, before any system type is chosen. Questions, IDs and the hypothesis rule follow the project-design-steps Conventions. Lists used by the checks are in `reference.md`; read it when check A starts. Depth: follows the project-design-steps Conventions (Light = 8 or fewer requirements and one milestone) → light audit (checks A and C, plus a one-pass coverage check); otherwise full.

## Steps
1. **A. Correctness** — for every R check: one thing only (split "and"); one reading only; testable (an observer can say pass or fail); states what, not how; feasible within the stated constraints; needed (traces to the goal). Flag vague words (`reference.md`) and ask for a number or an example. Give each R an acceptance criterion (measurable, or Given/When/Then), a type (functional, quality, constraint) and a priority (Must, Should, Could).
2. **B. Coverage** — build a matrix of the goal, each user task, each input, each output and the "done" definition against the R-numbers. Every row needs at least one R, and every R needs a row (an R with no row is unneeded, or the goal is under-stated). Then walk the coverage checklist (`reference.md`) and mark each item covered, not applicable (with the reason) or gap.
3. **C. Conflicts** — compare every pair of requirements (group by area above ~15) and each R against the intake constraints (OS, offline, deadline, budget, capacity), using the conflict types in `reference.md`. For each conflict show the pair, why they clash, and 2–3 resolutions: drop one, rank them, reword or split the scope, or defer one to a later release. The user chooses; never resolve silently.
4. **D. Questions** — turn every gap, vague R and conflict into a question (Conventions). At most 2 rounds, counting the intake batch cap. Unattended: take the recommended answers and flag them. After each batch of answers, re-run checks B and C on the answers: an answer can create a new gap or conflict (for example a retention limit raises the question of what happens to the oldest data). Ask those as a follow-up batch; it counts as round 2. What is still open after round 2 is listed as an open question with the risk it carries.
5. **Report** — write the output below and, inside project-design-steps, end with STATE #1 (`project-design-steps/state-schema.md`).

## Output — the requirement audit report
- final requirement table: ID, statement, type, priority, acceptance criterion, status (OK / fixed / needs answer); the priorities are proposed by the audit, so ask the user to confirm or change them
- coverage matrix with its gaps
- conflicts and the chosen resolutions
- assumptions, open questions and open items (for example a sample file still to supply)
- verdict: Pass / Pass with assumptions / Blocked (a Must-level conflict or gap is unresolved)

## Rules
- If requirements change after the audit, re-run it on the changed ones before continuing.
- Limit: the audit shows what the text, the goal and the checklist reveal; it cannot prove nothing is missing. Say so in the report.
