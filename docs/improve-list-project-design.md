# Improve List — `/project-design` speed and accuracy

Source run: 2026-10-28, `web-show-pre-order-date`, Design Lead (`claude-sonnet-4-6`).
Status: proposals only. No skill, agent or command file has been changed.

## Measured run

| Pass | Result | Time | Tool uses | Subagent tokens |
|---|---|---|---|---|
| 1 | QUESTIONS batch 1 (Q1–Q4) | ~82 s | 7 | ~21.9k |
| 2 | QUESTIONS batch 2 (Q5–Q8) | ~129 s | 2 | ~29.9k |
| 3 | PACKAGE (phases B, C, D together) | ~850 s | 11 | ~96.6k |
| Total | | ~1,061 s (~17.7 min) | 20 | |

Time spent waiting for the user's answers is not included.

The skill files are small: 430 lines in total across the agent, command and five skills.
So file reading is not the main cost. Most time goes to writing one very large reply in pass 3.

## Why it was slow (ranked)

1. **Pass 3 wrote everything in one reply.** It produced phases B, C and D, the full `DESIGN.md` and `demo.html` together (~80% of total time).
   This breaks the existing rule `project-design-steps/SKILL.md` line 20: "`DESIGN.md` and `demo.html` are delivered in separate replies, never together."
2. **The 6-pass cap pushes the agent to cram.** Phases A–D need about 5 passes when every question batch is asked.
   The main session also said "keep remaining question batches minimal". The agent then skipped the step 5 and step 6 questions and wrote everything at once.
3. **Questions the command could ask up front were asked later.** Step 1 of `/project-design` asks only name, purpose, users and "done".
   Skill step 1 also wants OS, online/offline, data kept, deadline and hours per week. Missing hours became a guess (A5).
4. **The package repeats content.** Wireframes, the demo and diagrams all restate the same names and screens. The STATE block is repeated in full each pass.
5. **Sequential passes with cold restarts.** Each pass resumes, re-plans and re-writes a state block before new work starts.

## Accuracy problems seen in the same run

- OQ-1 said "User accepted risk", but the user chose "Verify first" (Q5=B). Fixed by main session before writing.
- `demo.html` contained `https://` and `fetched`, which fail the `demo.md` grep check. Fixed before writing.
- Manual entry (Phase 1) needed `tz_convert.py`, but it was scheduled in Phase 2 (SG-12). Moved to SG-03b.
- System type (step 5) and all UI choices (step 6) were defaulted, never asked (A3, A7). This breaks "never chosen silently" in step 5.

## Proposed improvements

| # | File | Change | Expected effect |
|---|---|---|---|
| 1 | `.claude/agents/design-lead-sub-agent.md` | Add rule: one phase per pass; never return phases B, C and D in one reply. `demo.html` always gets its own pass. | Shorter passes; no 14-minute single reply |
| 2 | `.claude/commands/project-design.md` | Raise the pass cap from 6 to 8, or count only PACKAGE-building passes. Remove "keep batches minimal" pressure from the relay message. | Stops the agent from skipping step 5 and 6 questions |
| 3 | `.claude/commands/project-design.md` step 1 | Ask the skill step 1 constraints in the first question: OS, online/offline, deadline, hours per day and days per week. | Removes later question rounds and the A5 guess |
| 4 | `.claude/skills/project-design-steps/SKILL.md` | Merge step 5 (system type) and step 6 first UI batch into one question batch when depth is Light. | One fewer pass for small projects |
| 5 | `.claude/skills/project-design-steps/demo.md` | Ask the agent to self-run the grep check list before returning the demo. | Avoids main-session fix-ups |
| 6 | `.claude/skills/project-design-steps/SKILL.md` central cross-check | Add: "every answer Qn is quoted exactly in risks and assumptions" and "every Phase 1 item's dependencies are also Phase 1". | Catches the OQ-1 and SG-12 errors |
| 7 | `.claude/skills/project-design-steps/state-schema.md` | After pass 1, send only a STATE diff (changed lines), not the full block. | Fewer output tokens per pass |
| 8 | `.claude/agents/design-lead-sub-agent.md` | Review the `model:` line: `claude-sonnet-4-6` is an older model id. Check it before changing. | Possible speed and quality gain (not verified) |

Each change above needs its own Rule 3 approval, then the Python audit (system change under `.claude/`).
