# Skill: Improve Codebase Architecture

Find "deepening" opportunities: refactors that turn shallow modules into deep ones, for testability and easier navigation. Recommendations only; nothing is refactored without approval.

## Vocabulary (use exactly; don't drift into "component", "service", "boundary")
- Module: anything with an interface and an implementation (function, class, package).
- Interface: everything a caller must know: types, invariants, error modes, ordering, config.
- Depth: much behaviour behind a small interface (deep) vs an interface nearly as complex as the implementation (shallow).
- Seam: where an interface lives and behaviour can change without editing in place. One adapter = hypothetical seam; two = real seam.
- Leverage: what callers gain from depth. Locality: change, bugs and knowledge concentrated in one place.
- Deletion test: imagine deleting the module. If complexity vanishes it was a pass-through; if it reappears in N callers it earned its keep.

## Steps
1. Explore (an Explore subagent is fine). Note where understanding one concept means bouncing across many small modules, where modules are shallow, where extracted pure functions hide bugs in how they're called, where tightly coupled modules leak across seams, and what is hard to test through its current interface. If the project has a domain glossary or ADRs (CONTEXT.md, docs/adr/), read them first and don't re-litigate recorded decisions.
2. Apply the deletion test to each suspected shallow module.
3. Present candidates in chat: files involved, problem, proposed change in plain words, benefit (locality, leverage, testing), strength (Strong / Worth exploring / Speculative). End with the one you'd do first. Do not propose interfaces yet.
4. Ask which to explore, then walk the design with the user: constraints, dependencies, what sits behind the seam, which tests survive.
