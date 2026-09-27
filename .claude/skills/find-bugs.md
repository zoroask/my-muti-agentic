# Skill: Find Bugs

Analyse one file for real bugs and propose fixes.

## Steps
1. Identify the target file (ask if not given) and read it in full.
2. Run any available linter or type checker for extra signal.
3. Look for logic errors, off-by-one, unhandled null/None, race conditions, resource leaks, poor error handling, security holes.
4. Report a numbered list: line(s), issue, impact, proposed fix as a diff.
5. Ask which fixes to apply (all / some / none) and apply only those, through the CLAUDE.md Rule 3 gate.

## Rules
- Real bugs only: no refactoring, style or performance opinions unless they cause a bug.
- One file at a time. If none are found, say so instead of inventing problems.
- For multi-file or repo-wide work use repo-security-audit; for a cause that isn't obvious use diagnose.
