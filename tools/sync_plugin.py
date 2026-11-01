"""Keep plugins/data-analysis-and-quality-plugin in step with .claude/.

Each plugin file is its .claude/ source with a few mechanical rules applied
(RULES below). Some plugin files also carry hand edits. Overwriting those
would lose them, so git is the baseline: the source as it was at the plugin
file's last commit.

Status per file:
  ok      plugin == rules(source)
  custom  hand-edited, but the source has not changed since; nothing to do
  update  source changed, plugin had no hand edits; --write updates it
  new     source exists, plugin copy missing; --write creates it
  manual  source changed AND plugin has hand edits; fix by hand (--diff)
  orphan  plugin copy whose source no longer exists; remove by hand

Stdlib only, no network, no LLM.

    python tools/sync_plugin.py            # check, exit 1 on drift
    python tools/sync_plugin.py --diff     # also show diffs for manual files
    python tools/sync_plugin.py --write    # apply update/new
"""

from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = Path("plugins") / "data-analysis-and-quality-plugin"

# Plain text replacements, applied in order after CRLF -> LF.
RULES: list[tuple[str, str]] = [
    (" (`D:" + "\\my-muti-agentic`)", ""),
    ("my-project/", "<project-root>/"),
]

# (source dir, plugin dir, recursive, excluded names). Paths are relative to ROOT.
MAPPINGS = [
    (".claude/agents", "agents", False, {"monitor-agent.md"}),
    (
        ".claude/commands",
        "commands",
        False,
        {
            "commit-push-github.md",
            "full-audit-and-testing.md",
            "list-my-command.md",
            "run-agents.md",
            "tcg.md",
            "update-detail-project.md",
        },
    ),
    (".claude/skills", "skills", True, set()),
]
HOOKS = ["env_guard.py", "syntax_check.py"]

# Plugin files with no .claude/ source, never reported as orphans.
PLUGIN_ONLY_PREFIXES = ("skills/plugin-rules/",)

FAILING = {"update", "new", "manual", "orphan"}


@dataclass
class Entry:
    source: str  # relative to root, "/" separators
    target: str  # relative to root, "/" separators
    status: str = ""
    expected: str = ""


def transform(text: str) -> str:
    text = text.replace("\r\n", "\n")
    for old, new in RULES:
        text = text.replace(old, new)
    return text


def read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def git(root: Path, *args: str) -> str | None:
    """Run git in root; None when it fails (no repo, path not in commit)."""
    result = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, timeout=30
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8")


def baseline_source(root: Path, entry: Entry) -> str | None:
    """The source text at the commit that last touched the plugin file."""
    commit = git(root, "log", "-1", "--format=%H", "--", entry.target)
    if not commit or not commit.strip():
        return None
    return git(root, "show", f"{commit.strip()}:{entry.source}")


def collect(root: Path) -> list[Entry]:
    entries: list[Entry] = []
    for source_dir, plugin_dir, recursive, excluded in MAPPINGS:
        base = root / source_dir
        files = base.rglob("*") if recursive else base.glob("*.md")
        for path in sorted(files):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(base).as_posix()
            if relative.split("/")[0] in excluded:
                continue
            entries.append(
                Entry(f"{source_dir}/{relative}", (PLUGIN / plugin_dir / relative).as_posix())
            )
    for name in HOOKS:
        entries.append(Entry(f".claude/hooks/{name}", (PLUGIN / "hooks" / name).as_posix()))
    return entries


def classify(root: Path, entry: Entry) -> None:
    entry.expected = transform(read(root / entry.source))
    target = root / entry.target
    if not target.exists():
        entry.status = "new"
        return
    current = read(target).replace("\r\n", "\n")
    if current == entry.expected:
        entry.status = "ok"
        return
    old_source = baseline_source(root, entry)
    if old_source is None:
        entry.status = "manual"
    elif transform(old_source) == entry.expected:
        entry.status = "custom"
    elif transform(old_source) == current:
        entry.status = "update"
    else:
        entry.status = "manual"


def orphans(root: Path, entries: list[Entry]) -> list[Entry]:
    known = {entry.target for entry in entries}
    found: list[Entry] = []
    for _, plugin_dir, recursive, _ in MAPPINGS:
        base = root / PLUGIN / plugin_dir
        files = base.rglob("*") if recursive else base.glob("*.md")
        for path in sorted(files):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            target = path.relative_to(root).as_posix()
            inner = path.relative_to(root / PLUGIN).as_posix()
            if target not in known and not inner.startswith(PLUGIN_ONLY_PREFIXES):
                found.append(Entry("", target, "orphan"))
    return found


def sync(root: Path, write: bool = False) -> list[Entry]:
    entries = collect(root)
    for entry in entries:
        classify(root, entry)
    if write:
        for entry in entries:
            if entry.status in {"update", "new"}:
                target = root / entry.target
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(entry.expected.encode("utf-8"))
                entry.status = "written"
    return entries + orphans(root, entries)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="apply update/new")
    parser.add_argument("--diff", action="store_true", help="show diffs for manual files")
    args = parser.parse_args(argv)

    entries = sync(ROOT, write=args.write)
    counts: dict[str, int] = {}
    for entry in entries:
        counts[entry.status] = counts.get(entry.status, 0) + 1
        if entry.status not in {"ok", "custom"}:
            print(f"{entry.status.upper():7} {entry.target}")
        if args.diff and entry.status == "manual":
            current = read(ROOT / entry.target).replace("\r\n", "\n")
            sys.stdout.writelines(
                difflib.unified_diff(
                    current.splitlines(keepends=True),
                    entry.expected.splitlines(keepends=True),
                    f"plugin/{entry.target}",
                    f"rules({entry.source})",
                )
            )
    print("SUMMARY " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 1 if FAILING & counts.keys() else 0


if __name__ == "__main__":
    sys.exit(main())
