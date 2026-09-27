"""Load agent personas from `.claude/agents/*.md`.

The persona files stay the single source of truth: Claude Code reads them to
spawn subagents, and this module reads the same files so a chain can be checked
against the agents that actually exist before a run starts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

FENCE = "---"


@dataclass(frozen=True)
class Agent:
    """One persona file, parsed."""

    name: str
    description: str
    model: str
    system_prompt: str
    path: Path

    @property
    def is_retired(self) -> bool:
        return self.description.startswith("[RETIRED]")


def project_root() -> Path:
    """The repository root — the nearest ancestor of this file holding `.claude`."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / ".claude").is_dir():
            return candidate
    raise FileNotFoundError("no .claude directory found above agent_runtime/")


def agents_dir() -> Path:
    return project_root() / ".claude" / "agents"


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a persona file into its frontmatter fields and its body.

    Only flat `key: value` pairs are supported, because that is all the persona
    files use. Outer quotes are stripped from values. A file with no opening
    fence is treated as body-only.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        return {}, text.strip()

    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == FENCE:
            return fields, "\n".join(lines[index + 1 :]).strip()
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip().strip('"').strip("'")

    # Unterminated frontmatter — treat the remainder as body rather than crash.
    return fields, "\n".join(lines[1:]).strip()


def load_agents(directory: Path | None = None) -> dict[str, Agent]:
    """Return every persona in `directory`, keyed by its declared name.

    Files without a `name:` field are skipped: they are notes, not personas.
    """
    directory = directory or agents_dir()
    agents: dict[str, Agent] = {}
    for path in sorted(directory.glob("*.md")):
        # utf-8-sig so a persona saved with a BOM still parses its frontmatter.
        fields, body = parse_frontmatter(path.read_text(encoding="utf-8-sig"))
        name = fields.get("name")
        if not name:
            continue
        agents[name] = Agent(
            name=name,
            description=fields.get("description", ""),
            model=fields.get("model", ""),
            system_prompt=body,
            path=path,
        )
    return agents
