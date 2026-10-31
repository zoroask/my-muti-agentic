---
name: project-design-steps
user-invocable: false
description: "Requirement intake and audit, system-type choice, UI design, system design with diagrams, schedule and an optional offline demo for a <project-root>/ subproject, before any build. Use when the user says 'design a system', 'gather requirements', or similar."
---

# Skill: Project Design

Turn one requirement into one audited design for one `<project-root>/<subproject>/`, then present it to another team. Design only, no code. Run by Design Lead (`/project-design`) or Project Manager.

## Conventions (every step)
- **Questions** — at most 4 per batch; multiple choice, recommended answer first labelled "(Recommended)", with a one-line "why it matters". "Decide for me" takes the recommended answer and records it as an assumption (A1, A2, …). Ask with AskUserQuestion; when run as a subagent, return the batch to the caller instead.
- **Ask less** — ask only when the answer changes the design, the owner or the schedule; take the recommended option for everything else and list it in the step 11 recap, where the user can still change it, except steps 5 and 6, which are always asked.
- **IDs** — requirements R1…Rn and assumptions A1…An are never renumbered; new ones take the next number; withdrawn ones are marked "withdrawn".
- **Honesty** — findings and estimates are hypotheses until the user confirms them (verification-rigoureuse); never choose, resolve or shorten anything silently (intent-guard-shield). These rules are complete here; do not open those skills.
- **Owners** — build owners come from `system-types.md` (keep it in sync with the core-process Stage 7 table).
- **Depth** — Light when there are 8 or fewer requirements and one milestone, otherwise Full. Phase skills and reference files mark what Light skips.
- **Load on demand** — read a phase skill or reference file only when its step starts; never re-read a file already read in the same run.
- **Handoff** — steps 4, 6 and 9 each end with a STATE block in the format of `state-schema.md`, so a fresh runner can continue without the earlier history.
- **Output size** — `DESIGN.md` and `demo.html` are delivered in separate replies, never together.

## Phases
| Phase | Steps | Skill or file | Input | Output |
|---|---|---|---|---|
| A | 1–4 | requirement-audit | the user's requirement | audit report + STATE #1 |
| B | 5–6 | `system-types.md`, ui-design-selection | STATE #1 | system type, UI spec, demo choice + STATE #2 |
| C | 7–9 | `design-and-diagrams.md`, project-schedule, challenge-plan | STATE #2 | text design, diagrams, schedule + STATE #3 |
| D | 10 | `demo.md` (only if chosen) | STATE #3 | demo.html, in its own reply |

## Steps
1. **Intake** — if no requirement was given, first ask for it and the project name in the user's own words (free text, no options), and in the same message ask the usual constraints: OS, online or offline, whether data is kept between sessions, deadline, hours per week. Never offer system types before step 5. Then capture: project name (becomes the `<project-root>/<name>/` folder: lowercase kebab-case, not already taken), goal (one sentence), users, inputs, outputs, must-haves (R1, R2, …), nice-to-haves, constraints (OS, offline/online, deadline, budget, capacity: hours per day and days per week, start date, blocked dates), and what "done" looks like. Ask only for what is missing.
2. **Restate** — one unambiguous sentence of intent plus the assumptions made; separate real constraints from assumptions.
3. **Classify** — who operates it (a person interactively / unattended on a schedule or trigger), where it runs (desktop window, terminal, browser + server), data and integrations (files, APIs, databases, other apps).
4. **Audit requirements** — follow the requirement-audit skill, before any system type is chosen. A Blocked verdict stops here unless the user says "proceed with risk", which is recorded in the report.
5. **System type** — follow `system-types.md` (all five types, ranked, recommended first, one single-select question, never chosen silently; a type with no owner follows its Gaps section). Ask the system-type question first; ask the first UI round in the next batch, after the type is known.
6. **UI design** — if the chosen type has a UI (GUI, TUI, web, game), follow ui-design-selection and keep its UI spec. Automation: ask only that skill's report-format question. In this phase's last question batch, ask "Do you need a demo? Yes (Recommended) / No"; do not open `demo.md` for it. Never default this step: ask at least one UI round (style, theme, layout, density). Only the user may say "decide for me".
7. **Design** — follow `design-and-diagrams.md`.
8. **Schedule** — follow the project-schedule skill.
9. **Challenge** — run challenge-plan; revise or drop what fails.
10. **Demo (if chosen)** — follow `demo.md`; skip this step when the user chose "No demo".
11. **Present** — run the central cross-check, then plugin-rules § Approval gate: the audit summary, design, diagrams, schedule and the demo if one was made; then STOP.
12. **Save and hand off** — on "yes", write `<project-root>/<subproject>/DESIGN.md` (sections in `design-and-diagrams.md`) and, if a demo was made, `<project-root>/<subproject>/demo/demo.html`, then give the owner a four-part brief (objective, output format, tools and sources, boundaries), pointing to `DESIGN.md`. The brief is for the presentation only; never start or offer the build.

## Central cross-check (step 11)
Before presenting, check across all phases: the STATE Answers hold a user or "decide for me" source for steps 5 and 6 (if not, go back and ask; never present); every R appears in the Start → Goal list and on a diagram; every name in diagrams, wireframes and contracts matches the STATE names registry; every assumption is listed; schedule dates skip weekends and blocked dates; the demo (if made) covers or lists every R; every user answer Qn is quoted exactly where risks and assumptions cite it; every dependency of a first-milestone item is also in the first milestone. Fix mismatches before presenting.

## Rules
- One requirement → one design → one subproject.
- Never stretch a cluster beyond its scope to cover a type it does not build; gaps are stated, never papered over (`system-types.md`).
- Diagram names must match the text design and contracts (checked in `design-and-diagrams.md`); the demo's limits are in `demo.md` Honesty.
- The Start → Goal list is the hand-off checklist: a reader can follow it top to bottom as the plan; it is not a build order.
