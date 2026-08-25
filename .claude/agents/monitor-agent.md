---
name: Monitor
description: "[RETIRED] Historical persona for the deleted Python pipeline's live terminal progress tracker (Rich UI). No longer functional — kept for historical reference only. Do not invoke for active work; use Project Manager or Workflow Monitor instead."
model: claude-sonnet-4-6
---

## Status: Retired

This persona documented `agents/monitor.py`, a Rich-based terminal progress
table that tracked live status of the Planner → Frontend Coder → Backend
Coder → Reviewer pipeline while `python main.py` was running.

The entire Python runtime (`main.py`, `core/`, `agents/*.py`) has been
deleted. This project is now a Claude Code configuration library only —
personas, skills, commands, and hooks. There is no running process left for
this persona to monitor, and there won't be one again under the current
project direction.

## What to use instead

There is no direct replacement — a live progress table has no meaning
without a running pipeline. For a status overview of this repo's actual
content, invoke **Project Manager** / **PA Project Manager** (next actions,
open items) or **Workflow Monitor** / **PA Workflow Monitor** (dashboard of
persona/skill/command consistency) instead.

This file is kept only as a historical record of what the pipeline used to
track. It has no active behavioral role.
