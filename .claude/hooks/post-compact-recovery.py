#!/usr/bin/env python3
"""
Post-Compaction Recovery Hook (SessionStart with compact matcher)

Fires after context compaction completes. Reads session notes from
disk and prints them to stdout, which Claude Code injects into the
post-compaction model context.

Input (JSON via stdin):
  - cwd: project working directory

Output (stdout → injected as model context):
  - Recovery banner with session notes content, or
  - Notice directing to PROJECT_STATE.md if no notes exist
"""
import json
import os
import sys


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cwd = input_data.get("cwd", "")
    if not cwd:
        sys.exit(0)

    session_file = os.path.join(cwd, ".claude", "sessions", "CURRENT_SESSION")
    if not os.path.isfile(session_file):
        sys.exit(0)

    with open(session_file, "r") as f:
        session_id = f.read().strip()

    if not session_id:
        sys.exit(0)

    notes_file = os.path.join(cwd, ".claude", "sessions", session_id, "notes.md")

    if os.path.isfile(notes_file):
        with open(notes_file, "r") as f:
            notes_content = f.read()

        print("=== POST-COMPACTION RECOVERY ===")
        print(f"Session: {session_id}")
        print("A context compaction has just occurred. Your session notes from before compaction are below.")
        print("Use these to verify your compaction summary and resume work from the correct point.")
        print("")
        print(notes_content)
        print("")
        print("=== END RECOVERY CONTEXT ===")
    else:
        print("=== POST-COMPACTION NOTICE ===")
        print(f"Session: {session_id}")
        print("Context compaction occurred. No session notes found.")
        print("Read .claude/PROJECT_STATE.md and .claude/sessions/CURRENT_SESSION for context.")
        print("=== END NOTICE ===")


if __name__ == "__main__":
    main()
