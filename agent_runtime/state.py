"""The chain state machine.

This module is the reason the project has Python at all. The pass cap, the
stagnation stop and the approval gate live here as control flow, so a subagent
cannot talk its way past them the way it could past a prompt instruction.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from . import transcript
from .chains import Chain, Step

RUNNING = "RUNNING"
AWAITING_APPROVAL = "AWAITING_APPROVAL"
DONE = "DONE"
STALLED = "STALLED"
EXHAUSTED = "EXHAUSTED"
REJECTED = "REJECTED"

TERMINAL = frozenset({DONE, STALLED, EXHAUSTED, REJECTED})


class StateError(Exception):
    """Raised when a caller tries to do something the current state forbids."""


@dataclass
class Run:
    """One in-flight (or finished) walk through a chain."""

    run_id: str
    chain: str
    task: str
    status: str = RUNNING
    pass_number: int = 1
    step_index: int = 0
    gate_reason: str | None = None
    gate_is_final: bool = False
    # Agents that have reported in for the current step; only a parallel step
    # ever holds more than one name here.
    reported: list[str] = field(default_factory=list)
    # Findings from the latest failed verdict, and from the one before it. The
    # comparison between the two is what detects a stalled run.
    findings: list[str] = field(default_factory=list)
    previous_findings: list[str] = field(default_factory=list)

    # --- persistence -----------------------------------------------------

    @staticmethod
    def new_id(chain_name: str) -> str:
        return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{chain_name}"

    def directory(self, runs_dir: Path) -> Path:
        return runs_dir / self.run_id

    def state_path(self, runs_dir: Path) -> Path:
        return self.directory(runs_dir) / "state.json"

    def ledger_path(self, runs_dir: Path) -> Path:
        return self.directory(runs_dir) / "transcript.jsonl"

    def save(self, runs_dir: Path) -> None:
        path = self.state_path(runs_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        (runs_dir / "CURRENT").write_text(self.run_id, encoding="utf-8")

    @classmethod
    def load(cls, runs_dir: Path, run_id: str | None = None) -> Run:
        run_id = run_id or current_run_id(runs_dir)
        path = runs_dir / run_id / "state.json"
        if not path.exists():
            raise StateError(f"no run state at {path}")
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    # --- reading the current position ------------------------------------

    def current_step(self, chain: Chain) -> Step | None:
        """The step waiting to be run, or None if the chain is past its end."""
        if self.step_index >= len(chain.steps):
            return None
        return chain.steps[self.step_index]

    def pending_agents(self, chain: Chain) -> list[str]:
        """Agents this step still needs before it can be settled."""
        step = self.current_step(chain)
        if step is None or self.status != RUNNING:
            return []
        return [agent for agent in step.agents if agent not in self.reported]

    # --- advancing -------------------------------------------------------

    def record(self, chain: Chain, agent: str, output: str) -> None:
        """Log one agent's output and move the run forward.

        Refuses any agent the current step did not ask for — that refusal is
        the whole point of keeping the sequence in code.
        """
        if self.status != RUNNING:
            raise StateError(f"cannot record while status is {self.status}")
        step = self.current_step(chain)
        if step is None:
            raise StateError("chain is already past its last step")
        if agent not in step.agents:
            expected = " or ".join(step.agents)
            raise StateError(f"step {self.step_index + 1} expects {expected}, got {agent!r}")
        if agent in self.reported:
            raise StateError(f"{agent!r} already reported for this step")

        self.reported.append(agent)
        if self.pending_agents(chain):
            return  # a parallel step still has an agent outstanding

        self.reported = []
        if step.verdict:
            self._settle_verdict(chain, step, output)
        elif step.gate:
            self.status = AWAITING_APPROVAL
            self.gate_reason = step.gate
            self.gate_is_final = False
        else:
            self._advance(chain)

    def approve(self, chain: Chain) -> None:
        if self.status != AWAITING_APPROVAL:
            raise StateError(f"nothing to approve while status is {self.status}")
        self.gate_reason = None
        if self.gate_is_final:
            self.gate_is_final = False
            self.status = DONE
        else:
            self.status = RUNNING
            self._advance(chain)

    def reject(self) -> None:
        if self.status != AWAITING_APPROVAL:
            raise StateError(f"nothing to reject while status is {self.status}")
        self.gate_reason = None
        self.status = REJECTED

    def _advance(self, chain: Chain) -> None:
        self.step_index += 1
        if self.step_index >= len(chain.steps):
            self._finish(chain)

    def _finish(self, chain: Chain) -> None:
        """Reached the end of the chain — either done, or pending a last gate."""
        if chain.final_gate:
            self.status = AWAITING_APPROVAL
            self.gate_reason = chain.final_gate
            self.gate_is_final = True
        else:
            self.status = DONE

    def _settle_verdict(self, chain: Chain, step: Step, output: str) -> None:
        """Apply a verifier's PASS/FAIL, looping the chain only when allowed."""
        passed, findings = classify(step.verdict or "", output)
        if passed:
            self.findings = []
            self._finish(chain)
            return

        # Identical findings two passes running means the loop is not making
        # progress. Stop rather than burn another pass on the same failure.
        if findings and findings == self.previous_findings:
            self.findings = findings
            self.status = STALLED
            return

        if self.pass_number >= chain.max_passes:
            self.findings = findings
            self.status = EXHAUSTED
            return

        self.previous_findings = findings
        self.findings = findings
        self.pass_number += 1
        self.step_index = 0


def classify(mode: str, output: str) -> tuple[bool, list[str]]:
    """Decide PASS/FAIL from a verifier agent's output.

    "audit" — findings are the lines marked `[x]`; a clean report has none.
    "json"  — the first JSON object must carry "status": "PASS".
    """
    if mode == "audit":
        findings = [line.strip() for line in output.splitlines() if "[x]" in line]
        return not findings, findings
    if mode == "json":
        data = first_json_object(output)
        if data is None:
            return False, ["verifier did not return a JSON object"]
        if str(data.get("status", "")).strip().upper() == "PASS":
            return True, []
        return False, json_findings(data)
    raise ValueError(f"unknown verdict mode: {mode!r}")


def first_json_object(text: str) -> dict | None:
    """Parse the outermost JSON object in `text`, tolerating prose around it."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        value = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def json_findings(data: dict) -> list[str]:
    """Collect a reviewer's feedback fields into a stable, comparable list."""
    findings = [
        f"{key}: {value}"
        for key, value in sorted(data.items())
        if key.endswith("feedback") and value
    ]
    return findings or ["reviewer returned FAIL with no feedback"]


def current_run_id(runs_dir: Path) -> str:
    """The run id recorded by the most recent `start`."""
    pointer = runs_dir / "CURRENT"
    if not pointer.exists():
        raise StateError(f"no current run: {pointer} is missing (run `start` first)")
    return pointer.read_text(encoding="utf-8").strip()


def start(chain: Chain, task: str, runs_dir: Path) -> Run:
    """Begin a run, persist it, and open its ledger."""
    run = Run(run_id=Run.new_id(chain.name), chain=chain.name, task=task)
    run.save(runs_dir)
    transcript.append(run.ledger_path(runs_dir), "start", chain=chain.name, task=task)
    return run
