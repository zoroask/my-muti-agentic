List all available skills in `.claude/skills/` with their purpose and how to invoke each one.

## Available Skills

| Skill | File | Purpose | How to invoke |
|---|---|---|---|
| Debug Agent | `debug-agent.md` | Diagnose why an agent produced bad, empty, or malformed output | "use the debug-agent skill" |
| Scaffold Agent | `scaffold-agent.md` | Create a new agent definition from scratch | "use the scaffold-agent skill" |
| Refine Prompt | `refine-prompt.md` | Improve an agent's system prompt using structured reasoning | "use the refine-prompt skill" |
| Challenge Plan | `challenge-plan.md` | Four-question adversarial challenge before committing to a recommendation | "use the challenge-plan skill" |
| Token Optimization | `token-optimization.md` | Proactive session setup to cut token cost | "use the token-optimization skill" |
| Rescue Tokens | `rescue-tokens.md` | Emergency response to rate limits or a nearly full context | "use the rescue-tokens skill" |
| Constrained Decoding | `constrained-decoding.md` | Make machine-parsed outputs structurally valid via schemas | "use the constrained-decoding skill" |
| Long Context Placement | `long-context-lost-in-the-middle.md` | Place critical facts at the start and end of long prompts | "use the long-context-lost-in-the-middle skill" |
| Maths Olympiad | `maths-olympiad.md` | Parallel solve, isolated verification, calibrated abstention | "use the maths-olympiad skill" |
| Diagnose | `diagnose.md` | Feedback-loop-first diagnosis for hard or flaky bugs | "use the diagnose skill" |
| TDD Hybrid | `tdd-hybrid.md` | Test-first development with LIGHT/FULL triage | "use the tdd-hybrid skill" |
| Intent Guard Shield | `intent-guard-shield.md` | Prevent silent workarounds and false successes | "use the intent-guard-shield skill" |
| Repo Security Audit | `repo-security-audit.md` | Repo/subproject audit with optional GitHub issues | "use the repo-security-audit skill" |
| Find Bugs | `find-bugs.md` | Single-file bug scan with confirm-before-fix | "use the find-bugs skill" |
| Improve Codebase Architecture | `improve-codebase-architecture.md` | Find shallow modules, propose deepening refactors | "use the improve-codebase-architecture skill" |
| Agentic Loop | `agentic-loop.md` | Observe-decide-act-verify loop with attempt caps | "use the agentic-loop skill" |
| Rigorous Verification | `verification-rigoureuse.md` | Sourced, certainty-labelled factual answers | "use the verification-rigoureuse skill" |

## Skills vs Agents

- **Skill** — a step-by-step procedure Claude follows itself. No persona, no memory.
- **Agent** — an AI persona with role, context, and behavioral rules. Runs as a subagent.

Use `/list-agents` to see all available agents.
