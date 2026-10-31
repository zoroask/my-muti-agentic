# Project Design — Design and diagrams (step 7)

For the chosen type, write the text design, then present the diagrams.

## Text design
- components and their single responsibility
- contracts between components (file paths, JSON shapes, API endpoints, signals)
- tech stack, matching the owner's standards skill
- file layout under `my-project/<subproject>/`
- non-functional: secrets (CLAUDE.md Rule 4), logging, error handling, security
- out of scope
- UI spec from step 6 (tokens, screens, components), referenced, not repeated
- Start → Goal list: Start (current state, one sentence), Goal (finished state, one sentence, from the "done" definition), and ordered items between them, as a table:

  | ID | Item | Serves | Owner | Depends on | Output | Done check | Est (d) | Start | End | Critical | Status |
  |---|---|---|---|---|---|---|---|---|---|---|---|

  Est, Start, End and Critical read "—" until step 8 (project-schedule) fills them. Status uses `[ ]` todo, `[~]` doing, `[x]` done. Detail only the first milestone's items; later milestones stay at headline level.

## Diagrams (Mermaid except b, each with a one-line caption)
Light depth: skip a (one milestone; the step 8 gantt covers it); draw b, c, d and e; d and f follow their own Light notes.

a. **Roadmap** (`gantt`) — milestones in order with dates from step 8; the first is the smallest runnable slice; each milestone names its "done" check and the R-numbers it delivers.
b. **Structure** (folder tree in a plain code block, drawn with `├──`, `│` and `└──`, not Mermaid) — the static architecture as containment: root = subproject, first level = layers (e.g. Frontend, Backend, Data, External), then each component under its parent, one parent per item. Each line: name — role, R-numbers, phase when phased, [owning specialist] (e.g. `ItemCard.jsx — R2 R3 [Frontend Coder]`). External libraries and services sit under External. Calls and dependencies are not drawn here; they belong in diagram c.
c. **Working flow** (`flowchart LR` or `sequenceDiagram`) — actors, components and hand-offs: what moves from which part to which, in order, including the user, external systems and scheduled triggers. Draw the system inside a `subgraph` as its trust boundary, and mark where data leaves it and where secrets enter.
d. **Logic flow** (`flowchart TD`) — the core decision path: inputs, validation, branches, error and retry paths, and every end state (success, failure, stop). One per core use case, at most 3 (Light: one, for the main use case).
e. **Data model**, one of:
   - **ER diagram** (`erDiagram`) when the system stores related entities in a database: entities, key fields, primary and foreign keys, cardinality.
   - **Non-ER model** when it does not: a JSON schema or file-layout diagram for file or API data, or a `stateDiagram-v2` for state held in memory or a save file. Say in one line why ER does not apply.
f. **Type add-on** — one more diagram for the chosen type only (Light: only if it shows something diagrams b–e do not):
   - Web app: a `sequenceDiagram` per main API call, plus a deployment sketch (frontend, backend, ports, allowed origin)
   - Automation: a run-lifecycle `stateDiagram-v2` (scheduled, locked, running, done, failed, retry)
   - GUI or TUI app: the navigation map from the UI spec (screen → action → screen)
   - Game: a game-state diagram (title, play, pause, save) with the signals that move between states
   - Other: none unless the design needs one

## Checks before presenting
- every component, path, endpoint, entity and field named in a diagram appears with the same name in the contracts and in the Structure diagram, and the reverse
- every requirement R1…Rn is labelled on at least one diagram element; an unlabelled must-have is not designed yet
- each Mermaid diagram has at most ~15 nodes (split by use case or layer if larger; the Structure tree may be longer), labels edges with the data that moves, and shows error and stop paths
- the Working flow has no unexplained dependency cycle; every Structure tree item has exactly one parent, and every component has exactly one owning specialist; where no cluster owns the chosen type (GUI, TUI), mark every owner "unassigned (no cluster)" and record it as a stated gap instead of failing the check
- every component in the UI wireframes appears with the same name in the Structure diagram, and every screen appears in the navigation map
- Start → Goal list: item 1 begins from the Start state; the last item's done check proves the Goal; every R1…Rn appears in at least one item; every item has one owner, an output and an observable done check; no item depends on itself through a cycle; at most ~12 items per milestone
- Schedule: every dependency finishes before its dependent starts; no item exceeds 3 days; the critical path is marked (or "all items serial" is stated); the 20% buffer is its own line; the stated capacity and blocked dates are listed; in modes B and C the deadline is met or the gap is shown with its options

## DESIGN.md sections (step 12)
Requirement (R1…Rn), Requirement audit (verdict, assumptions, resolved conflicts, open questions, coverage gaps), System type, UI design (if any), Text design, Roadmap, Start → Goal list, Schedule (mode, assumptions, dated table, gantt, total range, risks), Structure, Working flow, Logic flow, Data model, Type add-on (if any), Demo (path, how to open, which R-numbers it covers and which it does not; or "No demo (user choice)"), Requirement traceability (R1…Rn → diagram element).
