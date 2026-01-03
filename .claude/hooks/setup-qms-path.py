#!/usr/bin/env python3
"""
SessionStart hook to add .claude directory to PATH.

This allows agents to invoke 'qms' directly instead of 'python .claude/qms.py'.
Uses CLAUDE_ENV_FILE to persist environment variables for the session.
"""

import os
import sys

def main():
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")

    if not env_file:
        print("CLAUDE_ENV_FILE not set - not in SessionStart context", file=sys.stderr)
        return 1

    if not project_dir:
        print("CLAUDE_PROJECT_DIR not set", file=sys.stderr)
        return 1

    claude_dir = os.path.join(project_dir, ".claude")

    # Write PATH export to env file (bash syntax works in Claude Code)
    with open(env_file, "a") as f:
        f.write(f'export PATH="{claude_dir}:$PATH"\n')

    print(f"Added {claude_dir} to PATH")
    return 0

if __name__ == "__main__":
    sys.exit(main())
