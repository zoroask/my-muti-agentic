---
name: project-schedule
user-invocable: false
description: "Estimate a milestone's work items or fit them to the user's dates, place them on a dated timetable with a buffer, critical path, gantt and risk list. Used by project-design-steps step 8, or any milestone plan."
---

# Skill: Project Schedule

Estimate the project duration or fit it to the user's dates, and place the Start → Goal items on a timetable. Questions follow the project-design-steps Conventions. Formulas and the Light table are in `reference.md`; read it when step 3 starts.

## Steps
1. **Mode** — ask (Conventions; "Decide for me" takes A):
   - A. Estimate for me (Recommended) — the skill estimates every item
   - B. I define it — the user gives a deadline or per-item durations; the skill fits the items and reports feasibility
   - C. Mixed — the user fixes some items or the deadline; the skill estimates the rest
2. **Inputs** — ask for any of these not already captured at intake: who builds (the user, Claude Code sessions, or a mix; it changes the estimates), start date, capacity (hours per day, days per week), blocked dates or holidays, deadline (mode B: ask it up front; mode C: estimate first, show the numbers, then ask the deadline so the user can choose it knowing the estimate).
3. **Estimate** (modes A and C), per item, in days, as in `reference.md` (Full: three-point; Light: the Light table):
   - confidence (Low / Medium / High) and a one-line basis; with no history of similar work, use Low or Medium
   - no item longer than 3 days; split it if so
   - a 20% buffer on the critical path, shown as its own line, never hidden inside items
4. **Place dates** — order items by `Depends on`, mark the critical path, set Start and End per item, skip weekends and blocked dates. Assume one serial work stream unless the user says otherwise (the user's review is the usual bottleneck); then every item is on the critical path, so say "all items serial" once instead of marking each row.
5. **Feasibility** (modes B and C with a deadline) — if critical path + buffer exceeds the deadline, show the gap and offer three options: cut scope (nice-to-haves first), add capacity, or move the deadline. Never shorten an estimate to fit.

## Output
- the dated item table, a `gantt` (dependencies via `after`), the total as a date range (expected finish with buffer, and pessimistic finish; Light omits the pessimistic finish), and a risk list naming the three least certain items
- the pessimistic finish adds every item's worst case at once: label it an upper bound, not a forecast
- gantt bars cannot show fractions of a day, so they round up to whole days; say so beside the chart, and keep the exact estimates in the table
- only the first milestone gets exact dates; later milestones get date ranges at milestone level
- label every estimate as a hypothesis, not a commitment; state the capacity and holiday assumptions beside the dates
