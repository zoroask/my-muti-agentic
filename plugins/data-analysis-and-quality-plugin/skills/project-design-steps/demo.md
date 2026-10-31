# Project Design — Demo (step 10)

Build a standalone demo of the design for the presentation, so the audience sees it working before anything is built.

## Choice
Step 6 asks only Yes / No. On Yes, step 10 picks the form below: Guided tour unless the user named another, recorded as an assumption the user can change in the step 11 recap (no extra round):
- Guided tour (Recommended) — Next and Back steps walk through the main use case, each step tagged with the R-numbers it shows
- Free-click prototype — the audience clicks or types through the screens
- Both — the tour plus a free mode toggle
- No demo (the step 6 "No") — skip step 10; DESIGN.md records "No demo (user choice)"

## Form
One self-contained `.html` file with inline CSS and JS; no network calls, no external fonts, scripts, images or CDN links, no build step, no server; it opens offline by double-click. System fonts only, with a Thai-capable fallback.

## Look by type
- Web app, GUI app: the UI spec's tokens, layout and screens (a GUI app inside a window frame)
- TUI app: a terminal-style page on the 16-colour palette, with the spec's keys working (arrows, Enter, shortcuts, language switch)
- Automation: a step-through replay of a `--dry-run` log, with the output files shown
- Game: a HUD and menu mock with a state walkthrough
- Other: the nearest of the above

## Content
Scripted flows only — the happy path of the first Logic flow plus one error path — on invented sample data shaped like the Data model. Every R-number appears in at least one step or screen; an R that cannot be shown goes on a "Not in demo" panel with the reason.

## Honesty
A visible banner "DEMO — sample data, not the real system"; no real data, credentials or secrets (plugin-rules § Secrets); nothing in it is presented as built, tested or estimated. It is a prototype: it never replaces the build, never proves feasibility or the estimates, and is never described as working software.

## Checks
No `http://` or `https://` loads (grep), no `fetch`, `XMLHttpRequest` or URL `import`; no console errors; every screen reachable by keyboard; labels and names match the UI spec and the Structure diagram; the R-coverage panel is complete; file size under 1 MB. Run these checks yourself before returning the demo and fix every hit; the grep also matches visible words such as "fetched", so reword them.

## Delivery
Return the demo in its own reply, separate from `DESIGN.md`, and keep it compact (shared CSS, no long comments). Write `<project-root>/<subproject>/demo/demo.html` only after the plugin-rules approval in step 11.
