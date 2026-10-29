List all available skills in `.claude/skills/` with their purpose and how to invoke each one.

## Available Skills

| Skill | File | Purpose | How to invoke |
|---|---|---|---|
| Debug Agent | `debug-agent/SKILL.md` | Diagnose why an agent produced bad, empty, or malformed output | "use the debug-agent skill" |
| Scaffold Agent | `scaffold-agent/SKILL.md` | Create a new agent definition from scratch | "use the scaffold-agent skill" |
| Refine Prompt | `refine-prompt/SKILL.md` | Improve an agent's system prompt using structured reasoning | "use the refine-prompt skill" |
| Challenge Plan | `challenge-plan/SKILL.md` | Four-question adversarial challenge before committing to a recommendation | "use the challenge-plan skill" |
| Token Optimization | `token-optimization/SKILL.md` | Proactive session setup to cut token cost | "use the token-optimization skill" |
| Rescue Tokens | `rescue-tokens/SKILL.md` | Emergency response to rate limits or a nearly full context | "use the rescue-tokens skill" |
| Constrained Decoding | `constrained-decoding/SKILL.md` | Make machine-parsed outputs structurally valid via schemas | "use the constrained-decoding skill" |
| Long Context Placement | `long-context-lost-in-the-middle/SKILL.md` | Place critical facts at the start and end of long prompts | "use the long-context-lost-in-the-middle skill" |
| Maths Olympiad | `maths-olympiad/SKILL.md` | Parallel solve, isolated verification, calibrated abstention | "use the maths-olympiad skill" |
| Diagnose | `diagnose/SKILL.md` | Feedback-loop-first diagnosis for hard or flaky bugs | "use the diagnose skill" |
| TDD Hybrid | `tdd-hybrid/SKILL.md` | Test-first development with LIGHT/FULL triage | "use the tdd-hybrid skill" |
| Intent Guard Shield | `intent-guard-shield/SKILL.md` | Prevent silent workarounds and false successes | "use the intent-guard-shield skill" |
| Repo Security Audit | `repo-security-audit/SKILL.md` | Repo/subproject audit with optional GitHub issues | "use the repo-security-audit skill" |
| Find Bugs | `find-bugs/SKILL.md` | Single-file bug scan with confirm-before-fix | "use the find-bugs skill" |
| Improve Codebase Architecture | `improve-codebase-architecture/SKILL.md` | Find shallow modules, propose deepening refactors | "use the improve-codebase-architecture skill" |
| Agentic Loop | `agentic-loop/SKILL.md` | Observe-decide-act-verify loop with attempt caps | "use the agentic-loop skill" |
| Rigorous Verification | `verification-rigoureuse/SKILL.md` | Sourced, certainty-labelled factual answers | "use the verification-rigoureuse skill" |
| Python Automation Standards | `python-automation-standards/SKILL.md` | Shared rules for Python automation scripts (location, approval flow, script checklist) | "use the python-automation-standards skill" |
| Project Design Steps | `project-design-steps/SKILL.md` | Requirement intake, requirement audit, system-type options, UI design, system design, schedule and standalone demo before any build | `/project-design` (runs it via Design Lead) |
| UI Design Selection | `ui-design-selection/SKILL.md` | Choose a UI design in detail and record it as a UI spec | "use the ui-design-selection skill" |
| Requirement Audit | `requirement-audit/SKILL.md` | Audit requirements for correctness, coverage and conflicts; returns a verdict | "use the requirement-audit skill" |
| Project Schedule | `project-schedule/SKILL.md` | Estimate and date a milestone plan with buffer, gantt and risks | used by `/project-design` (step 8) |
| Caveman | `caveman/SKILL.md` | Terse reply mode that cuts output tokens, on until "stop caveman" | "use the caveman skill" |
| Godot Game Standards | `godot-game-standards/SKILL.md` | Shared rules for Godot 4 pixel-art games (layout, ownership, pixel settings, original-work rule, review loop) | "use the godot-game-standards skill" |
| Security Learning Standards | `security-learning-standards/SKILL.md` | Shared rules for the Security Learning cluster (authorization/scope gate, defensive-only boundary, evidence, output) | "use the security-learning-standards skill" |
| Core Process | `core-process/SKILL.md` | Standard 10-stage path for multi-stage requests (history → skills → plan → design → STOP → assign → audit → summary → learn) | "use the core-process skill" |

## Skills vs Agents

- **Skill** — a step-by-step procedure Claude follows itself. No persona, no memory.
- **Agent** — an AI persona with role, context, and behavioral rules. Runs as a subagent.

Use `/list-agents` to see all available agents.
