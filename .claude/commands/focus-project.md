Focus creation/implementation work inside my-project/ by driving the
Pipeline Planner → Coder → Reviewer pipeline, scoped to a chosen
subproject.

## Steps
1. Use AskUserQuestion (skip only for fields already given as explicit
   arguments) with two questions:
   - **Subproject** — single-select. Read `my-project/` fresh each
     time and list every existing folder as an option, plus a final
     "Create new subproject" option. If "Create new subproject" is
     picked, follow up asking for a kebab-case name.
   - **Task** — what to create or implement. Offer a few common
     shortcuts as options ("New feature", "Fix/change existing
     behavior", "New subproject scaffold") but expect the real answer
     via free text ("Other"), since tasks are open-ended.
2. Invoke Pipeline Planner with the task description, plus explicit
   instructions:
   - Every path in `frontend_files` / `backend_files` of its plan JSON
     must be prefixed with `my-project/<subproject>/`.
   - Omit `frontend_files` (and skip Frontend Coder) if the task has
     no UI component; omit `backend_files` (and skip Backend Coder)
     if it has no server/API component. Don't invoke a coder for a
     side that doesn't apply.
   - Drive its own orchestration of the Coders and Reviewer exactly as
     defined in its existing system prompt (up to 3 review passes).
3. Wait for Pipeline Planner's final result:
   - **FAIL after 3 passes:** report the remaining
     `frontend_feedback` / `backend_feedback` verbatim to the user.
     Write nothing to disk.
   - **PASS:** do NOT write any files yet — proceed to step 4.
4. Before writing anything, check whether each target file already
   exists under `my-project/<subproject>/`. Then present to the user
   per CLAUDE.md Rule 3:
   - **Summary** — what feature was planned and why these files.
   - **Action plan** — the list of files to be created/overwritten.
   - **Before/After** — for each file: existing content (or
     "(new file)") vs. the generated content from the coder's
     `=== FILE ===` block.
   - **STOP** — wait for explicit "yes".
5. On "yes": write each file from the coders' `=== FILE ===` blocks to
   `my-project/<subproject>/`, preserving the relative paths from the
   plan JSON.

## Rules
- Never write a generated file to disk before explicit user approval
  of the Before/After diff — this is not waived by the pipeline having
  already reached PASS internally.
- Keep every generated path inside `my-project/<subproject>/`. If
  Pipeline Planner returns a path escaping that directory, correct the
  prefix before showing the diff — never write outside it.
- If a target file already exists, its current content is the
  "Before" — this command can overwrite existing app files (e.g. in
  `job-auto-apply/`), not just create new ones.
