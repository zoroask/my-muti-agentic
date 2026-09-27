Commit the current work and push it to GitHub, gated on this project's own
audit and test suite.

## Steps
1. `git status --short` and `git branch --show-current`. Group the changes by
   what they are, and state which groups you believe are in scope.
2. If more than one group exists, ASK which to commit. Never assume "all".
3. Safety — Rule 4 is absolute:
   `git ls-files` must show no `.env` file except `.env.example`, and
   `git diff --cached --name-only` must contain none. If one is staged, stop and
   say so; `env_guard.py` would block the commit anyway.
4. Quality gate. Both must pass before any commit:
   - `python -m agent_runtime audit --strict`
   - `python -m unittest discover -s tests -t .`
   Report a failure and stop. Never commit over a red suite or an `ATTENTION`
   audit result.
5. Read the diff of anything you did not write this session before describing it
   in a commit message. Do not narrate changes you have not looked at.
6. If on the default branch (`master`), create a branch first, unless the user
   has said to commit to it directly.
7. Stage explicit paths only. Never an *unscoped* `git add -A`, `git add .` or
   `git add -u` — that is how an ignored file becomes a tracked one. To stage a
   deletion, `git add -A -- <the one path>` is fine, and may be necessary:
   plain `git add` refuses a file already gone from disk, and `git rm` can be
   blocked as a removal against the project path.
8. Before every commit, run `git diff --cached --name-status` and check it holds
   only what you intended. `git commit` takes the whole index, so anything
   staged earlier in the session rides along silently.
9. Split into logical commits: one concern each, subject in the imperative and
   under 72 characters.
10. Show the user Summary / Workflow / Action plan / Before-After per CLAUDE.md
    Rule 3 and STOP. Wait for an explicit "yes".
11. Commit. Then STOP again before pushing — a push is public and hard to undo,
    and approval to commit is not approval to publish.
12. On approval: `git push -u origin <branch>`.
13. Verify and report: `git log --oneline -5`, `git status --short`, and the URL
    from `git remote get-url origin`.

## Rules
- Never push without explicit approval, and never `--force` unless the user asks
  for that specific push.
- End every commit message with the attribution line Claude Code specifies for
  the session.
- Never stage a file the user has not seen in your Before / After.
- Changes that were already uncommitted when the session started are not in
  scope unless the user includes them — nobody reviewed them here.
- `references/` is vendored third-party code. Never commit it incidentally.
- `env_guard.py` is wired to the Bash tool only. Git run through the PowerShell
  tool bypasses it, so step 3 is a real check, not a formality.
- Never rewrite a file's text with `Get-Content | Set-Content` on Windows
  PowerShell: a BOM-less UTF-8 file is read as ANSI and every non-ASCII
  character is corrupted. Use the editing tools instead.
