Design a new <project-root>/ sub-project before anything is built: requirement
audit, system type, UI spec, system design with diagrams, schedule and an
offline demo, via the Design Lead. $ARGUMENTS is the idea or requirement.

## Steps
1. If $ARGUMENTS is empty, ask in plain text (no options): "What is the
   project name, and what should the system do, who uses it, and what 'done'
   looks like? Also: which OS, online or offline, deadline, and hours per day
   and days per week you can give it?" Wait for the answer. If a requirement was given without a
   name, ask only for the name. Never offer system types here; that is
   project-design-steps step 5.
2. Check that the Design Lead subagent is available by name (do not read
   its file; the subagent loads it and its own skills), and read the `<project-root>/`
   folder listing. Turn the name into the folder name
   (lowercase kebab-case, e.g. "Expense Tracker" → `expense-tracker`); if that
   folder already exists, ask whether to pick another name or design inside it.
3. Invoke the Design Lead subagent with the request. Loop on its reply:
   - QUESTIONS — ask them with AskUserQuestion (keep its order and the
     "(Recommended)" labels), then continue the same subagent (SendMessage)
     with the answers and its state block.
   - BLOCKED — show the reason and the options it names; stop.
   - PHASE DONE — continue the same subagent (SendMessage) with its STATE block.
   - PACKAGE — check that its STATE Answers include steps 5 and 6 from the
     user. If not, continue the same subagent with those questions; leave the
     loop only when they are answered.
   Stop after 8 passes and show where it got to. Relay answers only; never ask
   the subagent to shorten, merge or skip question batches.
4. Present the package per plugin-rules § Approval gate (audit verdict, design,
   diagrams, schedule, demo summary), then STOP.
5. On "yes", write only `<project-root>/<subproject>/DESIGN.md` and, if a demo
   was produced, `<project-root>/<subproject>/demo/demo.html`, from the package's
   `=== FILE ===` blocks. For a demo, run the checks in `project-design-steps/demo.md`
   (grep for `http://`, `https://`, `fetch`, `XMLHttpRequest`; size under 1 MB).
   Then show the four-part brief for the owning Lead.

## Rules
- Design only: the output is DESIGN.md and the demo, for presenting to
  another team. Never start, offer or route a build from this command.
- No real data, credentials or secrets in DESIGN.md or the demo (plugin-rules § Secrets).
- GUI and TUI apps have no build cluster: record the gap, never assign one.
