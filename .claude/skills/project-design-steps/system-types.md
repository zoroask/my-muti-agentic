# Project Design — System types and owners (step 5)

Always show all five, ranked for this requirement, recommended first, as one single-select question; never choose silently.

| Type | Fits when | Trade-offs | Owner in this library |
|---|---|---|---|
| GUI app | one person, local desktop window, offline | per-OS packaging; harder to share | **none** (see Gaps) |
| TUI app | technical users, terminal, SSH or remote | no rich visuals | **none** (see Gaps) |
| Web app | several users, any device, shared data | server to host; auth and security | Web App Lead |
| Automation | no human in the loop; scheduled or triggered | no UI; must be idempotent | Python Automation Lead |
| Other | game, library change, anything else | name it | Game Lead / `/audit-chain` / none |

## Gaps (state them, never paper over them)
- GUI and TUI apps have no build cluster. Desktop Automation Coder controls existing desktop apps; it does not build them. Offer: (a) re-scope to a web app or automation, or (b) a new cluster designed via Architect Advisor (scaffold-agent).
- "Other" with no owner: say so and stop at the design.

## Maintenance
Update the owner table above whenever a build cluster is added or retired.
