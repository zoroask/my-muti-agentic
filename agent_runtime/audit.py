"""Whole-project audit: the facts a machine can establish without judgement.

Every check here is deterministic and free — no model, no network. The parts
that need judgement are left to the `PA Right-Hand Audit & Testing` subagent,
whose findings are merged in by `report.py`.

Severities match the scale already used by `.claude/skills/repo-security-audit.md`:
[H] breaks operation, leaks data or silently misbehaves; [M] noticeable gap;
[L] cosmetic.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import chains, registry, transcript

# Directories never worth auditing as if they were this project's own code.
ALWAYS_SKIP = {".git", "runs", "__pycache__", "node_modules", ".venv", ".mypy_cache"}

SEVERITY_ORDER = {"H": 0, "M": 1, "L": 2}

# Files that should never be tracked in git, and how bad it is if they are.
TRACKED_RULES: tuple[tuple[str, str, str], ...] = (
    (r"(^|/)\.env$", "H", "environment file with secrets is tracked in git"),
    (r"(^|/)\.env\.(?!example$)", "H", "environment file variant is tracked in git"),
    (r"\.db(-wal|-shm)?$", "H", "database file is tracked in git"),
    (r"\.pdf$", "H", "personal document is tracked in git"),
    (r"\.bak", "M", "backup file is tracked in git"),
    (r"\.log$", "M", "log file is tracked in git"),
    (r"(^|/)__pycache__/", "L", "compiled cache is tracked in git"),
    (r"\.pyc$", "L", "compiled bytecode is tracked in git"),
)

SECRET_FILENAMES = re.compile(r"(^|/)\.env($|\.)")

# Extensions treated as runnable hook scripts in `.claude/hooks/`.
HOOK_SCRIPT_SUFFIXES = (".py", ".ps1", ".sh")

# A hook script invoked by something other than a settings file — an OS protocol
# handler, say — declares it with this marker so it is not reported as dead.
EXTERNAL_MARKER = "hook-wiring: external"


@dataclass(frozen=True)
class Finding:
    """One thing worth a human's attention."""

    severity: str
    check: str
    location: str
    message: str

    @property
    def rank(self) -> int:
        return SEVERITY_ORDER.get(self.severity, 9)


@dataclass
class Check:
    """The outcome of one deterministic check."""

    name: str
    detail: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.findings


@dataclass
class TestOutcome:
    """Result of running the project's own test suite."""

    ran: int = 0
    ok: bool = False
    skipped: bool = False
    detail: str = ""


@dataclass
class AuditResult:
    root: Path
    generated_at: str
    inventory: dict[str, list[str]]
    checks: list[Check]
    tests: TestOutcome
    agent_findings: list[Finding] = field(default_factory=list)

    @property
    def machine_findings(self) -> list[Finding]:
        found: list[Finding] = []
        for check in self.checks:
            found.extend(check.findings)
        return found

    @property
    def all_findings(self) -> list[Finding]:
        combined = self.machine_findings + self.agent_findings
        return sorted(combined, key=lambda f: (f.rank, f.check, f.location))

    @property
    def file_count(self) -> int:
        return sum(len(paths) for paths in self.inventory.values())

    def count(self, severity: str) -> int:
        return sum(1 for finding in self.all_findings if finding.severity == severity)


# --- inventory -----------------------------------------------------------


def categorise(relative: str) -> str:
    """Which part of the project a file belongs to. First match wins."""
    if relative.startswith(".claude/agents/"):
        return "Agent personas"
    if relative.startswith(".claude/skills/"):
        return "Skills"
    if relative.startswith(".claude/commands/"):
        return "Commands"
    if relative.startswith(".claude/hooks/"):
        return "Hooks"
    if relative.startswith(".claude/"):
        return "Claude config"
    if relative.startswith("agent_runtime/"):
        return "Runtime"
    if relative.startswith("tests/"):
        return "Tests"
    if relative.startswith("my-project/"):
        return "Subprojects"
    if relative.startswith("references/"):
        return "Vendored references"
    if relative.startswith("docs/"):
        return "Docs"
    return "Root files"


def take_inventory(root: Path, include_references: bool = False) -> dict[str, list[str]]:
    """Every auditable file, grouped by category."""
    skip = set(ALWAYS_SKIP)
    if not include_references:
        skip.add("references")

    grouped: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(part in skip for part in path.relative_to(root).parts):
            continue
        grouped.setdefault(categorise(relative), []).append(relative)
    return grouped


def files_of(inventory: dict[str, list[str]], *categories: str) -> list[str]:
    result: list[str] = []
    for category in categories:
        result.extend(inventory.get(category, []))
    return result


# --- checks --------------------------------------------------------------


def check_personas(root: Path) -> Check:
    """Persona files must declare a name, description, model and a body."""
    directory = root / ".claude" / "agents"
    findings: list[Finding] = []
    seen: dict[str, str] = {}
    retired = 0
    total = 0

    for path in sorted(directory.glob("*.md")):
        relative = path.relative_to(root).as_posix()
        fields, body = registry.parse_frontmatter(path.read_text(encoding="utf-8-sig"))
        name = fields.get("name")
        if not name:
            findings.append(Finding("H", "personas", relative, "no `name:` in frontmatter"))
            continue

        total += 1
        if name in seen:
            findings.append(
                Finding("H", "personas", relative, f"duplicate agent name {name!r}, also in {seen[name]}")
            )
        seen[name] = relative

        for required, severity in (("description", "M"), ("model", "M")):
            if not fields.get(required):
                findings.append(
                    Finding(severity, "personas", relative, f"missing `{required}:` in frontmatter")
                )
        if not body.strip():
            findings.append(Finding("H", "personas", relative, "persona body is empty"))
        if fields.get("description", "").startswith("[RETIRED]"):
            retired += 1

    detail = f"{total} personas, {retired} retired"
    return Check("Agent personas", detail, findings)


def _table_entries(text: str, cell_pattern: str) -> set[str]:
    """Names in the first cell of a markdown table row.

    Scoped to table rows on purpose: a backticked filename mentioned in prose
    elsewhere in the document is not an index entry.
    """
    found: set[str] = set()
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells:
            continue
        match = re.fullmatch(cell_pattern, cells[0])
        if match:
            found.add(match.group(1))
    return found


def check_skill_table(root: Path) -> Check:
    """`.claude/skills/README.md` must list exactly the skills on disk."""
    readme = root / ".claude" / "skills" / "README.md"
    directory = root / ".claude" / "skills"
    if not readme.exists():
        return Check("Skill index", "no README.md", [
            Finding("H", "skills", ".claude/skills/README.md", "skill index is missing")
        ])

    listed = _table_entries(readme.read_text(encoding="utf-8-sig"), r"`([\w.-]+\.md)`")
    on_disk = {path.name for path in directory.glob("*.md") if path.name != "README.md"}

    findings = [
        Finding("H", "skills", f".claude/skills/README.md", f"index lists {name!r}, which does not exist")
        for name in sorted(listed - on_disk)
    ]
    findings += [
        Finding("M", "skills", f".claude/skills/{name}", "skill file is not listed in README.md, so it has no trigger")
        for name in sorted(on_disk - listed)
    ]
    return Check("Skill index", f"{len(on_disk)} skills, {len(listed)} indexed", findings)


def check_command_table(root: Path) -> Check:
    """CLAUDE.md's command table must match `.claude/commands/`."""
    claude_md = root / "CLAUDE.md"
    directory = root / ".claude" / "commands"
    if not claude_md.exists():
        return Check("Command index", "no CLAUDE.md", [
            Finding("H", "commands", "CLAUDE.md", "CLAUDE.md is missing")
        ])

    documented = _table_entries(claude_md.read_text(encoding="utf-8-sig"), r"`/([\w-]+)`")
    on_disk = {path.stem for path in directory.glob("*.md")}

    findings = [
        Finding("M", "commands", f".claude/commands/{name}.md", "command exists but is not in the CLAUDE.md table")
        for name in sorted(on_disk - documented)
    ]
    findings += [
        Finding("H", "commands", "CLAUDE.md", f"table documents /{name}, which has no command file")
        for name in sorted(documented - on_disk)
    ]
    return Check("Command index", f"{len(on_disk)} commands, {len(documented)} documented", findings)


def check_hook_wiring(root: Path) -> Check:
    """Hook scripts and settings files must agree with each other.

    A script nothing references never runs, and a settings file naming a script
    that is not on disk fails silently at the moment it is needed.
    """
    hooks_dir = root / ".claude" / "hooks"
    settings_files = [
        path
        for path in (
            root / ".claude" / "settings.json",
            root / ".claude" / "settings.local.json",
        )
        if path.exists()
    ]
    if not settings_files:
        return Check("Hook wiring", "no settings file found", [])

    wiring = "\n".join(path.read_text(encoding="utf-8-sig") for path in settings_files)
    scripts = sorted(
        path.name
        for path in hooks_dir.glob("*")
        if path.is_file() and path.suffix in HOOK_SCRIPT_SUFFIXES
    )

    findings: list[Finding] = []
    external = 0
    for name in scripts:
        if name in wiring:
            continue
        body = (hooks_dir / name).read_text(encoding="utf-8-sig", errors="replace")
        if EXTERNAL_MARKER in body:
            external += 1  # invoked by something outside the settings files
            continue
        findings.append(
            Finding(
                "M",
                "hooks",
                f".claude/hooks/{name}",
                "hook script is referenced by no settings file, so it never runs",
            )
        )

    referenced = {
        match.group(1)
        for match in re.finditer(r"\.claude[/\\]hooks[/\\]([\w.\-]+)", wiring)
    }
    findings += [
        Finding(
            "H",
            "hooks",
            ".claude/settings.json",
            f"hook command references missing script {name!r}",
        )
        for name in sorted(referenced)
        if not (hooks_dir / name).exists()
    ]

    detail = f"{len(scripts)} scripts, {len(settings_files)} settings file(s)"
    if external:
        detail += f", {external} externally invoked"
    return Check("Hook wiring", detail, findings)


def check_chains(root: Path) -> Check:
    """Every agent a chain names must exist and must not be retired."""
    agents = registry.load_agents(root / ".claude" / "agents")
    findings: list[Finding] = []
    for chain in chains.CHAINS.values():
        for name in chains.agent_names(chain):
            agent = agents.get(name)
            if agent is None:
                findings.append(
                    Finding("H", "chains", f"agent_runtime/chains.py", f"chain {chain.name!r} names missing agent {name!r}")
                )
            elif agent.is_retired:
                findings.append(
                    Finding("M", "chains", "agent_runtime/chains.py", f"chain {chain.name!r} uses retired agent {name!r}")
                )
    return Check("Chain wiring", f"{len(chains.CHAINS)} chains checked", findings)


def check_python_syntax(root: Path, inventory: dict[str, list[str]]) -> Check:
    """Every Python file must parse."""
    python_files = [
        relative
        for relative in sum(inventory.values(), [])
        if relative.endswith(".py")
    ]
    findings: list[Finding] = []
    for relative in python_files:
        path = root / relative
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except SyntaxError as error:
            findings.append(
                Finding("H", "syntax", f"{relative}:{error.lineno or 0}", f"syntax error: {error.msg}")
            )
        except UnicodeDecodeError:
            findings.append(Finding("M", "syntax", relative, "file is not valid UTF-8"))
    return Check("Python syntax", f"{len(python_files)} files parsed", findings)


def check_doc_links(root: Path, inventory: dict[str, list[str]]) -> Check:
    """Relative links inside markdown must point at files that exist."""
    link = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    findings: list[Finding] = []
    checked = 0

    for relative in sorted(sum(inventory.values(), [])):
        if not relative.endswith(".md"):
            continue
        path = root / relative
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for match in link.finditer(text):
            target = match.group(1).split("#")[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "#")):
                continue
            checked += 1
            if not (path.parent / target).exists():
                findings.append(
                    Finding("M", "docs", relative, f"link target does not exist: {target}")
                )
    return Check("Doc links", f"{checked} relative links checked", findings)


def check_tracked_hygiene(root: Path) -> Check:
    """Secrets, databases and personal documents must not be tracked in git.

    File *names* only — this never reads the contents of a secret file.
    """
    try:
        listed = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return Check("Git hygiene", "skipped: git unavailable", [])

    tracked = [line.strip() for line in listed.splitlines() if line.strip()]
    findings: list[Finding] = []
    for relative in tracked:
        for pattern, severity, message in TRACKED_RULES:
            if re.search(pattern, relative):
                findings.append(Finding(severity, "hygiene", relative, message))
                break

    # A secret file that is neither tracked nor ignored is one `git add .` away.
    for path in root.rglob(".env*"):
        relative = path.relative_to(root).as_posix()
        if not path.is_file() or relative.endswith(".example"):
            continue
        if any(part in ALWAYS_SKIP for part in path.relative_to(root).parts):
            continue
        if relative in tracked or not SECRET_FILENAMES.search(relative):
            continue
        if not _is_ignored(root, relative):
            findings.append(
                Finding("H", "hygiene", relative, "secret file is neither tracked nor gitignored")
            )

    return Check("Git hygiene", f"{len(tracked)} tracked files checked", findings)


def _is_ignored(root: Path, relative: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", relative],
            cwd=root,
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return True  # cannot tell; do not raise a false alarm
    return result.returncode == 0


def run_tests(root: Path) -> TestOutcome:
    """Run the project's own unittest suite and summarise it."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return TestOutcome(skipped=True, detail=f"could not run tests: {error}")

    output = result.stderr + result.stdout
    match = re.search(r"Ran (\d+) test", output)
    ran = int(match.group(1)) if match else 0
    ok = result.returncode == 0
    if ok:
        detail = f"{ran} tests passed"
    else:
        summary = re.search(r"(FAILED \(.*\))", output)
        detail = summary.group(1) if summary else "test suite failed"
    return TestOutcome(ran=ran, ok=ok, detail=detail)


# --- findings supplied by the subagent -----------------------------------

FINDING_LINE = re.compile(r"^\s*[-*]?\s*\[([HMLx ])\]\s+(.*\S)\s*$")
SPLITTERS = (" — ", " – ", " -- ", " - ")


def parse_findings(text: str, check: str = "subagent") -> list[Finding]:
    """Read `[H] path:line — message` lines from an agent's report.

    `[x]` is accepted and treated as [M], because `PA Right-Hand Audit &
    Testing` writes checkbox findings by default; nothing is silently dropped.
    `[ ]` means a passed check and is ignored.
    """
    findings: list[Finding] = []
    # A file saved on Windows often starts with a UTF-8 BOM. Left in place it
    # would stop the first line matching and silently drop a finding.
    for line in text.lstrip("﻿").splitlines():
        match = FINDING_LINE.match(line)
        if not match:
            continue
        marker, remainder = match.group(1), match.group(2)
        if marker == " ":
            continue
        severity = "M" if marker == "x" else marker

        location, message = "", remainder
        for splitter in SPLITTERS:
            if splitter in remainder:
                location, message = remainder.split(splitter, 1)
                break
        findings.append(Finding(severity, check, location.strip(), message.strip()))
    return findings


# --- driver --------------------------------------------------------------


def run_audit(
    root: Path | None = None,
    include_references: bool = False,
    with_tests: bool = True,
) -> AuditResult:
    """Run every deterministic check over the project."""
    root = root or registry.project_root()
    inventory = take_inventory(root, include_references)
    checks = [
        check_personas(root),
        check_skill_table(root),
        check_command_table(root),
        check_hook_wiring(root),
        check_chains(root),
        check_python_syntax(root, inventory),
        check_doc_links(root, inventory),
        check_tracked_hygiene(root),
    ]
    tests = run_tests(root) if with_tests else TestOutcome(skipped=True, detail="skipped by --no-tests")
    return AuditResult(
        root=root,
        generated_at=transcript.timestamp(),
        inventory=inventory,
        checks=checks,
        tests=tests,
    )
