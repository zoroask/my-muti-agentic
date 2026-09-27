"""Command line surface, designed to be read by Claude Code rather than a human.

Every command prints `KEY=value` lines so the calling session can act on the
result without guessing. Long text is wrapped in `<<<` / `>>>` markers.

    python -m agent_runtime start audit "harden env_guard.py"
    python -m agent_runtime record --agent "Architect Advisor" --output-file plan.md
    python -m agent_runtime approve
    python -m agent_runtime status
    python -m agent_runtime list
    python -m agent_runtime validate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import audit, chains, registry, report, state, transcript
from .state import AWAITING_APPROVAL, RUNNING, TERMINAL, Run, StateError

NEXT_STEP_HINT = {
    state.DONE: "Chain complete. Report the result to the user.",
    state.STALLED: "Findings repeated across passes. Stop and show the user the "
    "repeated findings verbatim; do not start another pass.",
    state.EXHAUSTED: "Pass cap reached while still failing. Stop and report the "
    "remaining findings to the user.",
    state.REJECTED: "User rejected the gate. Stop; do not apply anything.",
}


def default_runs_dir() -> Path:
    return registry.project_root() / "runs"


def build_prompt(run: Run, step: chains.Step) -> str:
    """Assemble what the subagent should be told for the current step."""
    parts = [f"TASK: {run.task}", "", step.instruction]
    if run.findings:
        parts += [
            "",
            f"This is pass {run.pass_number}. The previous pass failed verification:",
        ]
        parts += [f"  - {finding}" for finding in run.findings]
    return "\n".join(parts)


def render(run: Run, chain: chains.Chain, runs_dir: Path) -> str:
    """The full status block for one run."""
    lines = [
        f"RUN={run.run_id}",
        f"CHAIN={run.chain}",
        f"STATUS={run.status}",
        f"PASS={run.pass_number}/{chain.max_passes}",
    ]

    if run.status == RUNNING:
        step = run.current_step(chain)
        assert step is not None  # RUNNING always has a step
        pending = run.pending_agents(chain)
        lines += [
            f"STEP={run.step_index + 1}/{len(chain.steps)}",
            f"PARALLEL={'yes' if len(step.agents) > 1 else 'no'}",
            f"NEXT_AGENTS={'|'.join(pending)}",
            "PROMPT<<<",
            build_prompt(run, step),
            ">>>",
        ]
    elif run.status == AWAITING_APPROVAL:
        lines += [
            "GATE=approval_required",
            f"GATE_REASON={run.gate_reason}",
            "NOTE=Show the user Summary / Action plan / Before-After and STOP. "
            "Then run `approve` or `reject`.",
        ]

    for finding in run.findings:
        lines.append(f"FINDING={finding}")

    if run.status in TERMINAL:
        lines.append(f"NOTE={NEXT_STEP_HINT[run.status]}")

    lines.append(f"LEDGER={run.ledger_path(runs_dir)}")
    return "\n".join(lines)


def read_output(args: argparse.Namespace) -> str:
    """The agent's report, from a file, an inline string, or stdin."""
    if args.output_file:
        # utf-8-sig: a report saved on Windows may carry a BOM.
        return Path(args.output_file).read_text(encoding="utf-8-sig")
    if args.text is not None:
        return args.text
    return sys.stdin.read()


# --- commands ------------------------------------------------------------


def cmd_start(args: argparse.Namespace) -> int:
    chain = chains.get(args.chain)
    run = state.start(chain, args.task, args.runs_dir)
    print(render(run, chain, args.runs_dir))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    run = Run.load(args.runs_dir, args.run)
    chain = chains.get(run.chain)
    output = read_output(args)
    pass_number = run.pass_number  # the pass this output belongs to

    run.record(chain, args.agent, output)
    run.save(args.runs_dir)
    transcript.append(
        run.ledger_path(args.runs_dir),
        "record",
        agent=args.agent,
        pass_number=pass_number,
        output=output,
    )
    print(render(run, chain, args.runs_dir))
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    run = Run.load(args.runs_dir, args.run)
    chain = chains.get(run.chain)
    reason = run.gate_reason
    run.approve(chain)
    run.save(args.runs_dir)
    transcript.append(run.ledger_path(args.runs_dir), "approve", gate=reason)
    print(render(run, chain, args.runs_dir))
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    run = Run.load(args.runs_dir, args.run)
    chain = chains.get(run.chain)
    reason = run.gate_reason
    run.reject()
    run.save(args.runs_dir)
    transcript.append(run.ledger_path(args.runs_dir), "reject", gate=reason)
    print(render(run, chain, args.runs_dir))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    run = Run.load(args.runs_dir, args.run)
    print(render(run, chains.get(run.chain), args.runs_dir))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    agents = registry.load_agents()
    print(f"AGENTS_LOADED={len(agents)}")
    for chain in chains.CHAINS.values():
        print(f"CHAIN={chain.name}")
        print(f"  DESCRIPTION={chain.description}")
        print(f"  MAX_PASSES={chain.max_passes}")
        if chain.final_gate:
            print(f"  FINAL_GATE={chain.final_gate}")
        for index, step in enumerate(chain.steps, start=1):
            marks = []
            if step.gate:
                marks.append(f"gate: {step.gate}")
            if step.verdict:
                marks.append(f"verdict: {step.verdict}")
            suffix = f"  [{'; '.join(marks)}]" if marks else ""
            print(f"  STEP{index}={'|'.join(step.agents)}{suffix}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    """Audit every file, optionally merge subagent findings, write the report."""
    result = audit.run_audit(
        include_references=args.include_references,
        with_tests=not args.no_tests,
    )
    if args.findings:
        text = Path(args.findings).read_text(encoding="utf-8-sig")
        result.agent_findings = audit.parse_findings(text)

    destination = Path(args.html) if args.html else result.root / "audit-report.html"
    written = report.write(result, destination)

    failed = [check for check in result.checks if not check.passed]
    print(f"FILES_AUDITED={result.file_count}")
    print(f"CHECKS_PASSED={len(result.checks) - len(failed)}/{len(result.checks)}")
    print(f"TESTS={result.tests.detail}")
    for level in "HML":
        print(f"{'HIGH' if level == 'H' else 'MEDIUM' if level == 'M' else 'LOW'}={result.count(level)}")
    print(f"SUBAGENT_FINDINGS={len(result.agent_findings)}")
    for check in result.checks:
        state_word = "pass" if check.passed else "fail"
        print(f"CHECK={check.name}|{state_word}|{check.detail}")
    for finding in result.all_findings:
        location = finding.location or "-"
        print(f"FINDING=[{finding.severity}] {location} | {finding.check} | {finding.message}")
    print(f"REPORT={written}")

    attention = result.count("H") > 0 or not (result.tests.ok or result.tests.skipped)
    print(f"RESULT={'ATTENTION' if attention else 'OK'}")
    return 1 if (attention and args.strict) else 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every agent named by every chain actually exists as a persona."""
    agents = registry.load_agents()
    missing: list[str] = []
    for chain in chains.CHAINS.values():
        for name in chains.agent_names(chain):
            if name not in agents:
                missing.append(f"{chain.name} -> {name}")
                continue
            if agents[name].is_retired:
                print(f"WARNING={chain.name} uses retired agent {name!r}")

    print(f"AGENTS_LOADED={len(agents)}")
    print(f"CHAINS_CHECKED={len(chains.CHAINS)}")
    if missing:
        for entry in missing:
            print(f"MISSING_AGENT={entry}")
        print("RESULT=FAIL")
        return 1
    print("RESULT=OK")
    return 0


# --- argument parsing ----------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m agent_runtime",
        description="Sequence Claude Code subagents. Never calls an LLM API.",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=None,
        help="where run state and ledgers live (default: <project>/runs)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="begin a chain run")
    start.add_argument("chain", choices=sorted(chains.CHAINS))
    start.add_argument("task")
    start.set_defaults(func=cmd_start)

    record = sub.add_parser("record", help="log an agent's output and advance")
    record.add_argument("--agent", required=True)
    record.add_argument("--output-file", help="file holding the agent's report")
    record.add_argument("--text", help="the agent's report, inline")
    record.add_argument("--run", help="run id (default: the current run)")
    record.set_defaults(func=cmd_record)

    approve = sub.add_parser("approve", help="clear the pending approval gate")
    approve.add_argument("--run")
    approve.set_defaults(func=cmd_approve)

    reject = sub.add_parser("reject", help="refuse the pending approval gate")
    reject.add_argument("--run")
    reject.set_defaults(func=cmd_reject)

    status = sub.add_parser("status", help="show where a run stands")
    status.add_argument("--run")
    status.set_defaults(func=cmd_status)

    listing = sub.add_parser("list", help="show the available chains")
    listing.set_defaults(func=cmd_list)

    validate = sub.add_parser("validate", help="check chains against the personas")
    validate.set_defaults(func=cmd_validate)

    auditor = sub.add_parser("audit", help="audit every file and write the HTML report")
    auditor.add_argument("--html", help="report destination (default: audit-report.html)")
    auditor.add_argument("--findings", help="a subagent report to merge in")
    auditor.add_argument(
        "--include-references",
        action="store_true",
        help="also audit references/ (vendored third-party skills)",
    )
    auditor.add_argument("--no-tests", action="store_true", help="skip running the test suite")
    auditor.add_argument(
        "--strict", action="store_true", help="exit 1 when there are High findings"
    )
    auditor.set_defaults(func=cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.runs_dir is None:
        args.runs_dir = default_runs_dir()
    if not hasattr(args, "run"):
        args.run = None
    try:
        return args.func(args)
    except (StateError, KeyError, FileNotFoundError, ValueError) as error:
        print(f"ERROR={error}")
        return 2
