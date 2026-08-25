"""
PreToolUse hook: blocks Write/Edit/Read on files outside the project directory.
Receives tool input JSON on stdin. Exits with code 2 to block the action.
"""
import sys
import json
import os

PROJECT_ROOT = os.path.normpath("D:/my-muti-agentic")


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return

    if os.path.isabs(file_path):
        normalized = os.path.normpath(file_path)
    else:
        normalized = os.path.normpath(os.path.join(PROJECT_ROOT, file_path))

    if not normalized.startswith(PROJECT_ROOT + os.sep):
        print(
            f"[path-guard] BLOCKED: '{file_path}' is outside the project root.\n"
            f"  Allowed: {PROJECT_ROOT}\n"
            f"  Request explicit user permission before modifying files outside this project.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
