#!/usr/bin/env python3
"""
QMS Write Guard Hook

Intercepts Write and Edit tool calls and blocks direct modifications
to the QMS/ directory. Agents must use the qms CLI instead.
"""
import json
import sys
import os


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Let normal permission flow handle it

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Normalize path for comparison
    normalized_path = os.path.normpath(file_path).replace("\\", "/")

    # Check if writing to QMS directory
    if "/QMS/" in normalized_path or normalized_path.startswith("QMS/"):
        output = {
            "decision": "block",
            "reason": (
                "Direct writes to QMS/ are restricted. "
                "The Quality Management System is a controlled document repository. "
                "Use the `qms` CLI tool to create, edit, and manage QMS documents."
            )
        }
        print(json.dumps(output))
        sys.exit(0)

    # Allow other files through
    sys.exit(0)


if __name__ == "__main__":
    main()
