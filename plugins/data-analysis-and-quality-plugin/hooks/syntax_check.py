"""
PostToolUse hook: checks Python syntax after Write/Edit tool calls.
Receives tool result JSON on stdin.
"""
import sys
import json
import ast


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path.endswith(".py"):
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        print(f"[syntax-check] OK: {file_path}")
    except SyntaxError as e:
        print(f"[syntax-check] SYNTAX ERROR in {file_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
