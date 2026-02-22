#!/usr/bin/env python3
"""
QMS Write Guard Hook

Intercepts Write and Edit tool calls and blocks direct modifications to:
  - QMS/ directory (controlled documents — use qms CLI instead)
  - qms-cli/ directory (governed submodule — use .test-env/qms-cli/ instead)
  - flow-state/ directory (governed submodule — use .test-env/flow-state/ instead)

Note: Claude Code deny rules in settings.local.json are non-functional due to a
known platform bug (GitHub issues #8961, #6699, #6631). This PreToolUse hook is
the actual enforcement mechanism. The deny rules are retained as defense-in-depth
for when the platform bug is eventually fixed.
"""
import json
import sys
import os


# Protected directories and their error messages
PROTECTED_DIRS = {
    "QMS": (
        "Direct writes to QMS/ are restricted. "
        "The Quality Management System is a controlled document repository. "
        "Use the `qms` CLI tool to create, edit, and manage QMS documents."
    ),
    "qms-cli": (
        "Direct writes to qms-cli/ are restricted. "
        "This is a governed submodule. Per SOP-005 Section 7.1, "
        "develop in .test-env/qms-cli/ and merge to main via PR."
    ),
    "flow-state": (
        "Direct writes to flow-state/ are restricted. "
        "This is a governed submodule. Per SOP-005 Section 7.1, "
        "develop in .test-env/flow-state/ and merge to main via PR."
    ),
}


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Let normal permission flow handle it

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Normalize path for comparison
    normalized_path = os.path.normpath(file_path).replace("\\", "/")

    # Allow writes to designated development directories
    # .test-env/ is the permitted local development location per SOP-005 Section 7.1
    if "/.test-env/" in normalized_path or normalized_path.startswith(".test-env/"):
        sys.exit(0)

    for dir_name, reason in PROTECTED_DIRS.items():
        # Match both absolute paths (containing /dir_name/) and relative paths
        pattern_in_path = f"/{dir_name}/"
        pattern_starts = f"{dir_name}/"
        if pattern_in_path in normalized_path or normalized_path.startswith(pattern_starts):
            output = {
                "decision": "block",
                "reason": reason,
            }
            print(json.dumps(output))
            sys.exit(0)

    # Allow other files through
    sys.exit(0)


if __name__ == "__main__":
    main()
