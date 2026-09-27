"""Chain definitions — which agent runs when, declared as plain data.

Nothing here calls a model. These objects only describe order and stop
conditions; `state.py` walks them and Claude Code performs each step.

The two chains mirror the existing slash commands so both surfaces behave the
same way: `audit` mirrors `.claude/commands/audit-chain.md`, and `pipeline`
mirrors the Pipeline Planner orchestration used by `/focus-project`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    """One stage of a chain.

    agents:      invoked in parallel when more than one is listed.
    instruction: what this stage asks of the agent.
    gate:        if set, the run pauses for user approval after this stage,
                 and the string says what is being approved.
    verdict:     if set, this stage decides PASS/FAIL and can restart the
                 chain. Either "audit" or "json" — see state.classify.
    """

    agents: tuple[str, ...]
    instruction: str
    gate: str | None = None
    verdict: str | None = None


@dataclass(frozen=True)
class Chain:
    """A fixed sequence of steps, plus the limits on re-running it."""

    name: str
    description: str
    steps: tuple[Step, ...]
    max_passes: int = 3
    final_gate: str | None = None


AUDIT = Chain(
    name="audit",
    description="Design -> propose -> apply -> verify, looping on audit failure.",
    max_passes=3,
    steps=(
        Step(
            agents=("Architect Advisor",),
            instruction=(
                "Design the change. Name the exact files to touch and the approach "
                "you recommend, and say what you deliberately are NOT doing."
            ),
        ),
        Step(
            agents=("Bug Fixer",),
            instruction=(
                "Read the files named in the plan above and propose a concrete "
                "before/after diff. Do NOT apply anything yet."
            ),
            gate="Apply the proposed diff to the working tree",
        ),
        Step(
            agents=("Bug Fixer",),
            instruction="Apply the diff the user approved, exactly as approved.",
        ),
        Step(
            agents=("PA Right-Hand Audit & Testing",),
            instruction=(
                "Audit the changed area. Report findings as [x] (failed) and "
                "[ ] (passed) bullets, or exactly 'AUDIT CLEAN - no issues found'."
            ),
            verdict="audit",
        ),
    ),
)


PIPELINE = Chain(
    name="pipeline",
    description="Plan -> code in parallel -> review, looping on review failure.",
    max_passes=3,
    final_gate="Write the generated files to disk",
    steps=(
        Step(
            agents=("Pipeline Planner",),
            instruction="Produce the project plan as valid JSON only, per your schema.",
        ),
        Step(
            agents=("Pipeline Frontend Coder", "Pipeline Backend Coder"),
            instruction=(
                "Generate your half of the project from the plan above, as "
                "=== FILE === blocks. You have no write tools: output only."
            ),
        ),
        Step(
            agents=("Pipeline Reviewer",),
            instruction=(
                "Review both file sets against the plan. Return JSON with a "
                '"status" of "PASS" or "FAIL", plus frontend_feedback and '
                "backend_feedback when failing."
            ),
            verdict="json",
        ),
    ),
)


CHAINS: dict[str, Chain] = {chain.name: chain for chain in (AUDIT, PIPELINE)}


def get(name: str) -> Chain:
    """Look up a chain by name, with a readable error listing the valid ones."""
    try:
        return CHAINS[name]
    except KeyError:
        known = ", ".join(sorted(CHAINS))
        raise KeyError(f"unknown chain {name!r} (known: {known})") from None


def agent_names(chain: Chain) -> list[str]:
    """Every agent a chain can invoke, in first-use order, without duplicates."""
    ordered: list[str] = []
    for step in chain.steps:
        for agent in step.agents:
            if agent not in ordered:
                ordered.append(agent)
    return ordered
