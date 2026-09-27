# Skill: Maths Olympiad Solver

Multi-agent procedure for olympiad problems (IMO, Putnam, USAMO, AIME): parallel solving, adversarial verification in isolated contexts, calibrated abstention. Also a reference pattern for any "generate, then independently verify" agent chain.

## Principles
1. Strip reasoning traces before verifying: a verifier that sees the reasoning leans toward agreeing.
2. A solver never verifies its own solution; verifiers are fresh and blind to each other's verdicts.
3. "No confident solution" beats a wrong confident answer.
4. No web or lookup, ever: do not search for the problem or its solution.

## Steps
1. Interpretation check: list 2-3 readings; if one makes the problem trivial, the harder reading is likely intended. State the chosen reading and why.
2. Solve in parallel: several solver agents (Haiku 8, Sonnet 4, Opus 3), each with a different starting angle (small cases, invariant, extremal, induction, symmetry, work backwards, drop a condition, generalise). Each iterates solve, self-check, fix (max 5 rounds) and returns only its final state: verdict, method, full solution. Solvers run no code and fetch no data; numerical evidence is not a proof step.
3. Clean: pass on only the problem and the final argument; drop scratch work and false starts.
4. Verify adversarially: a fresh verifier gets only problem + cleaned solution and tries to break it: re-check every theorem's hypotheses, check whether it specialises to a famous open problem, test any "one-line lemma" in general form with a small counterexample, and check whether a "remaining gap" is tautological. It returns HOLDS / HOLE FOUND / UNCLEAR with the quoted step.
5. Vote: up to 5 independent verifiers on the top solution; 4 HOLDS confirms, 2 HOLE FOUND refutes; stop once the outcome is decided.
6. Revise: on a hole, a reviser gets the cleaned solution and the hole report only; mark unproven steps inline as [GAP: ...]; up to 3 cycles, then re-vote.
7. Stuck case: check whether the case's hypothesis implies something about another input that removes the split, before grinding.
8. Deep mode on abstain: one last agent with the partial state and the verifier's gap; bounded local computation allowed (mod-k checks, small cases, 60 s limit), still no web.
9. Abstain honestly: report what was tried, what was proven, and where it breaks.
10. Present: once verified, a fresh agent rewrites the proof as the simplest clear version (LaTeX if asked).

## AIME-style numeric answers
Skip the proof machinery: 5-7 varied solvers and a majority vote; with no majority, check the top 2 by substitution.

## Notes for this project
- Solver and verifier personas do not exist here yet. If created they must be `.claude/agents/*.md` files, not part of this skill. A `tools:` list in their frontmatter enforces the no-tools rule; a prompt-only rule does not.
- The upstream reference files (verifier patterns, adversarial prompts, presentation prompts, model-tier defaults) were not vendored. Source: `references/claude-skills/skills/maths-olympiad/`.
