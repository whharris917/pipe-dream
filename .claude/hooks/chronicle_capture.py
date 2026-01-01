#!/usr/bin/env python3
"""
Chronicle Capture Hook

This script runs at SessionEnd to capture the session transcript
and append it to the Chronicle in human-readable Markdown format.

Invoked automatically by Claude Code via the SessionEnd hook.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

def parse_message(msg: dict) -> str:
    """Convert a single message to Markdown format."""
    role = msg.get('type', 'unknown')

    if role == 'human':
        # User message
        content = msg.get('message', {}).get('content', '')
        if isinstance(content, list):
            # Handle content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = '\n'.join(text_parts)
        return f"**User:**\n\n{content}\n"

    elif role == 'assistant':
        # Assistant message
        content = msg.get('message', {}).get('content', '')
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = '\n'.join(text_parts)
        return f"**The Primus:**\n\n{content}\n"

    elif role == 'summary':
        # Context summary (internal, may skip or note)
        return ""  # Skip summaries in Chronicle

    else:
        # Unknown type - preserve for debugging
        return f"**[{role}]:** {json.dumps(msg)[:200]}...\n"


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Error: Could not parse hook input JSON", file=sys.stderr)
        sys.exit(1)

    # Extract relevant fields
    transcript_path = hook_input.get('transcript_path', '')
    session_id = hook_input.get('session_id', 'unknown')
    stop_reason = hook_input.get('reason', 'unknown')

    if not transcript_path or not os.path.exists(transcript_path):
        print(f"Warning: Transcript not found at {transcript_path}", file=sys.stderr)
        sys.exit(0)

    # Determine project directory
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '')
    if not project_dir:
        # Fallback: derive from script location
        project_dir = str(Path(__file__).parent.parent.parent)

    # Create chronicles directory
    chronicles_dir = os.path.join(project_dir, '.claude', 'chronicles')
    Path(chronicles_dir).mkdir(parents=True, exist_ok=True)

    # Generate chronicle filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    chronicle_filename = f"{timestamp}_{session_id[:8]}.md"
    chronicle_path = os.path.join(chronicles_dir, chronicle_filename)

    # Read and parse transcript
    messages = []
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    msg = json.loads(line)
                    messages.append(msg)
                except json.JSONDecodeError:
                    continue

    # Convert to Markdown
    markdown_parts = [
        f"# Chronicle: Session {session_id[:8]}",
        f"",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        f"**Session ID:** {session_id}",
        f"**Stop Reason:** {stop_reason}",
        f"**Transcribed by:** Chronicle Capture Hook (Automated)",
        f"",
        f"---",
        f"",
    ]

    for msg in messages:
        parsed = parse_message(msg)
        if parsed:
            markdown_parts.append(parsed)
            markdown_parts.append("---\n")

    markdown_parts.append(f"\n*End of Chronicle - {datetime.now().isoformat()}*\n")

    # Write chronicle
    chronicle_content = '\n'.join(markdown_parts)
    with open(chronicle_path, 'w', encoding='utf-8') as f:
        f.write(chronicle_content)

    print(f"Chronicle saved: {chronicle_path}", file=sys.stderr)

    # Also update the index
    index_path = os.path.join(chronicles_dir, 'INDEX.md')
    index_entry = f"- [{timestamp}]({chronicle_filename}) - Session {session_id[:8]} ({stop_reason})\n"

    # Create or append to index
    if os.path.exists(index_path):
        with open(index_path, 'a', encoding='utf-8') as f:
            f.write(index_entry)
    else:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Chronicle Index\n\n")
            f.write("All session chronicles, in chronological order.\n\n")
            f.write("---\n\n")
            f.write(index_entry)

    print(f"Index updated: {index_path}", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
