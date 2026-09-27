Audit and test every file in this project, then write `audit-report.html`.

Two halves. `agent_runtime/audit.py` establishes the facts a machine can check
for free; `PA Right-Hand Audit & Testing` supplies the judgement a machine
cannot. Both end up in one report.

## Steps
1. Collect the deterministic facts and write a first report:
   `python -m agent_runtime audit`
   Add `--include-references` only if the user asks for the vendored
   `references/` tree to be audited too.
2. Read the stdout block. It gives you:
   - `FILES_AUDITED`, `CHECKS_PASSED`, `TESTS` — coverage and test result
   - `CHECK=<name>|pass|fail|<detail>` — one line per check
   - `FINDING=[H|M|L] <location> | <check> | <message>` — machine findings
   - `REPORT=<path>`, `RESULT=OK|ATTENTION`
3. Invoke **PA Right-Hand Audit & Testing** for the judgement half. Tell it to
   follow `.claude/skills/repo-security-audit.md` and to cover: persona and
   skill quality, contradictions between docs and behaviour, hook correctness,
   the Python in `agent_runtime/` and `.claude/hooks/`, and the
   `my-project/` subprojects. Give it the `CHECK=` and `FINDING=` lines so it
   does not repeat work the deterministic half already did.
4. Require its findings in this exact line format, one per line:
   `[H] path/to/file.py:42 — what is wrong and why it matters`
   Severity follows the repo-security-audit scale: [H] breaks operation, leaks
   data or silently misbehaves; [M] noticeable gap; [L] cosmetic.
5. Save its report to a file, then merge it into the final report:
   `python -m agent_runtime audit --findings <that file>`
6. Report to the user: the counts, `RESULT`, every `[H]` finding verbatim, and
   the path to `audit-report.html`.

## Rules
- Report only. Propose no fix and change no file without going through
  CLAUDE.md Rule 3 first (Summary / Action plan / Before-After / STOP).
- Never print the contents of a secret. `.env` files are named, never read —
  the deterministic half already reports whether they are tracked or ignored.
- Report `[H]` findings verbatim. Do not soften or summarise them away.
- `references/` is vendored third-party code and is excluded by default.
  Findings there are not this project's bugs.
- If the audit reports `RESULT=ATTENTION`, say so plainly in the first line of
  your summary rather than burying it under the passing checks.
- To fix what the audit finds, hand the findings to `/run-agents audit "<task>"`
  so the repair goes through the enforced chain.
