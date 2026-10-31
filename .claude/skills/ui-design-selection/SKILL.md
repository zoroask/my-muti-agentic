---
name: ui-design-selection
description: "Round-by-round UI choices (style, theme, layout, fonts, navigation, components, accessibility) recorded as a UI spec; called by project-design-steps. Use when the user says 'choose a UI style', 'ui design', 'design the interface', or similar."
---

# Skill: UI Design Selection

Let the user choose a system's UI design in detail, then record the choices as a UI spec the builders follow. Called by project-design-steps step 6, or directly ("choose a UI style"). Selection and specification only, no code.

## When
- GUI app, TUI app, web app, game: run it.
- Automation: skip it; if a person reads the output, ask one question: report format (Excel, HTML email, console summary, none).

## Steps
1. **Read context** — requirements R1…Rn, users, devices, system type. Rank every option for this requirement; recommended first, labelled "(Recommended)".
2. **Ask in rounds** — questions follow the project-design-steps Conventions, including "Ask less": skip any question whose answer would not change the spec and record its recommended option in the recap. Light depth or Game: one round only (Catalog D plus palette), always shown to the user. Options come from the catalogs in `reference.md`; read it when the first round starts. Show the 3–4 best-fitting options per question; the rest stay reachable through "Other". "Decide the rest" ends the rounds early.
   - Round 1 — Look and layout (Catalog A)
   - Round 2 — Detail (Catalog B)
   - Round 3 — Components and access (Catalog C)
   - Round 4 — Type-specific (Catalog D)
   - TUI app: Catalog A is for graphical UIs and does not apply. Round 1 asks the TUI questions of Catalog D (library, layout, keys, colour); Round 2 asks Catalog B without Typography (the terminal font is the user's) and Responsiveness (state a minimum terminal size instead); Round 3 asks Catalog C without Icons (use Unicode symbols); Round 4 is skipped.
3. **Cross-check** — before the recap, map every R-number to the components it needs (a "fix a value" requirement needs an edit control; charts need a chart component; an import needs a file input). If an answer leaves out a component a requirement needs, or two answers conflict, name it and state the assumption you will use; the user confirms or changes it in the recap.
4. **Recap** — one table: question, choice, source (user / recommended / default). List every default taken, including ones never asked (density, motion, minimum size, font, icons), and every assumption from the cross-check. Offer one pass of changes.
5. **Write the UI spec** (see Output).
6. **Preview (ask first)** — ASCII wireframes are always in the spec; a visual mockup is made only if the user asks, as an HTML file written only after approval.
7. **Return** — hand the spec back to project-design-steps step 7; it goes into `DESIGN.md` under "UI design".

## Output — UI spec
- **Choices table** — every question, the choice, user or recommended
- **Design tokens** — colours (background, surface, text, muted, accent, success, warning, danger; light and dark values if both), font family and size scale, spacing scale (4/8 px), radius, shadow, motion durations
- **Screen list** — each screen, its purpose, the R-numbers it serves
- **Wireframes** — ASCII, one per main screen, at most 3; components labelled with the names used in the Structure diagram
- **Component inventory** — each component with its states (default, hover, focus, disabled, empty, loading, error)
- **Navigation map** — screen → action → screen; becomes project-design-steps diagram f for GUI and TUI apps
- **Accessibility and language notes**

## Rules
- Never choose silently; the recap shows every default taken.
- Check that text/background token pairs meet the chosen WCAG contrast level before presenting. For a 16-colour or other terminal palette the real colours depend on the user's terminal theme and cannot be checked: say so, avoid dim colours for essential text, and require that colour is never the only signal (add a symbol or label).
- Generic styles only: never copy a specific product's or brand's look, logo or assets; fonts and icons must be openly licensed.
- Choices must fit the owner's standards skill (plain CSS unless a library is named in the plan; games within godot-game-standards).
- GUI and TUI specs can be recorded but not built yet: no build cluster exists (project-design-steps `system-types.md`, Gaps).
