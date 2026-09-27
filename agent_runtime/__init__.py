"""A stdlib-only state machine that sequences Claude Code subagent invocations.

This package never calls an LLM API. It decides *which* agent runs next and
*when a run must stop*; Claude Code does the actual model work using the
personas in `.claude/agents/`. That split is deliberate — see README.md.
"""

__all__ = ["chains", "cli", "registry", "state", "transcript"]
