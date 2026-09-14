Delegate a task through Architect Advisor → Bug Fixer → PA Right-Hand
Audit & Testing, and loop back on failure.

## Steps
1. Ask the user (if not given as an argument): what task/change should
   be designed and implemented?
2. Plan — invoke Architect Advisor with the task. Get its recommended
   approach and the specific file(s)/change(s) it advises.
3. Implement (propose only) — invoke Bug Fixer with Architect Advisor's
   plan. Bug Fixer reads the relevant files and proposes a concrete
   before/after diff — it does NOT apply anything yet.
4. Approve — show the diff to the user per CLAUDE.md Rule 3 (Summary /
   Action plan / Before-After / STOP). Wait for explicit "yes".
5. Apply — re-invoke Bug Fixer to apply the approved diff.
6. Audit — invoke PA Right-Hand Audit & Testing over the changed area.
7. Branch on the audit result:
   - FAIL (report contains any [x] finding, i.e. not "AUDIT CLEAN"):
     list every failed item verbatim from the report, then re-invoke
     Architect Advisor and Bug Fixer with that failure list as the new
     task — repeat from step 2. Cap at 3 audit passes total; if still
     failing after pass 3, stop and report the remaining failures to
     the user instead of looping again.
   - PASS ("AUDIT CLEAN — no issues found"): stop looping and report
     the final result directly to the user.

## Rules
- Never apply a Bug Fixer diff without the user's explicit approval —
  running inside this chain does not waive CLAUDE.md Rule 3.
- Each loop iteration re-reads current file state — never assume the
  prior pass's diff applied cleanly.
- Always show the user the audit report's exact findings on FAIL, not
  a paraphrase.
- Max 3 audit passes before escalating to the user regardless of
  outcome.
