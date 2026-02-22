#!/usr/bin/env python3
"""
PreCompact Hook — Compaction Event Logger

Fires before context compaction occurs. Logs the compaction event
to the current session's compaction-log.txt for audit purposes.

Input (JSON via stdin):
  - trigger: "manual" or "auto"
  - transcript_path: path to the conversation transcript
  - cwd: project working directory

This hook runs with async: true to avoid blocking compaction.
"""
import json
import os
import sys
from datetime import datetime


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    trigger = input_data.get("trigger", "unknown")
    transcript_path = input_data.get("transcript_path", "")
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

    session_dir = os.path.join(cwd, ".claude", "sessions", session_id)
    os.makedirs(session_dir, exist_ok=True)

    log_file = os.path.join(session_dir, "compaction-log.txt")
    timestamp = datetime.now().isoformat(timespec="seconds")
    entry = f"{timestamp} | COMPACTION ({trigger}) | transcript: {transcript_path}\n"

    with open(log_file, "a") as f:
        f.write(entry)


if __name__ == "__main__":
    main()
