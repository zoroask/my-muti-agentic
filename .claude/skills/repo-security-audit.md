# Skill: Repo Security Audit

Deep audit of a repository or subproject for bugs, security problems, test gaps and API design issues, optionally turning findings into GitHub issues. Report-only until the user approves.

## Steps
1. Target: a local path or `owner/repo`. Ask whether GitHub issues should be created at the end.
2. Explore: README, dependency manifest (`requirements.txt`, `pyproject.toml`, `package.json`), entry points, tests layout, `.gitignore`, and what is actually tracked (`git ls-files`).
3. Analyse each module for:
   - Bugs: logic errors, off-by-one, wrong argument order, race conditions, swallowed exceptions.
   - Performance: busy-wait loops, missing caching or pooling, unbounded growth.
   - Security: `eval`/`exec` on input, unsafe deserialisation, secrets hard-coded, logged or tracked in git, personal data (resumes, databases, backups, logs) not ignored, files created with loose permissions.
   - API design: return types that don't match, inconsistent behaviour, missing validation at boundaries.
   - Tests and docs: documented features with no tests, docs that contradict behaviour.
4. Report each finding as file:line with a tag on the same scale as PA Right-Hand Audit: [H] breaks operation, leaks data or silently misbehaves; [M] noticeable inconsistency or gap; [L] cosmetic. Give what, why it fails, and a suggested fix.
5. Present the summary and ask which severities (default [H] only) to open issues for.
6. If confirmed, create one issue per finding: `gh issue create --repo <owner/repo> --title "<under 80 chars>" --body "<Description / Location / Current behaviour / Expected / Suggested fix / Impact / Priority>"`. Issues are visible to others: confirm the target repo and the list of titles first.
7. Close with a table of created issues and a suggested fix order.

## Rules
- Read-only until the user approves fixes or issue creation (CLAUDE.md Rule 3).
- Never print secret values in the report: name the file and key only.
- One issue per finding; write issues in English.
- To review only the pending diff, prefer the built-in security-review.
