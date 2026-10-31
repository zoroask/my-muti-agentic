---
name: challenge-plan
description: "Four-question adversarial challenge before committing to a recommendation. Use when the user says 'review this plan', 'is this over-engineered', or similar."
---

# Skill: Challenge Plan

Before finalizing any architectural recommendation, apply these four
challenge questions to the proposed change:

1. **Break it** — what is the most likely way this change fails in actual
   use? Name the specific file or interaction where it could go wrong.
2. **Skip it** — what happens if you do not make this change at all? If
   the project continues to work correctly without it, reconsider whether
   it is necessary.
3. **Minimize it** — what is the smallest version of this change that
   still solves the stated problem? Prefer that over the full proposal
   when it covers the core need.
4. **Maintain it** — who has to update this when the project changes?
   If the answer is "every time someone adds a persona, skill, or command,"
   flag the maintenance cost explicitly before recommending.

A proposal that survives all four questions is a strong recommendation.
A proposal that fails one or more should be revised or rejected before
presenting it to the user.

For a project design (project-design-steps step 9), read "file" as
"component or Start → Goal item", and question 4 as "who owns it after
the build".
