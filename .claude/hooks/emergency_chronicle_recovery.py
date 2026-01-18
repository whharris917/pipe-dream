#!/usr/bin/env python3
"""
Emergency Chronicle Recovery Script

Reproduces the chronicle_capture.py functionality for a session that
ended unexpectedly (e.g., system reboot) without the SessionEnd hook running.

Usage:
    python emergency_chronicle_recovery.py <transcript_path> <session_name>

Example:
    python emergency_chronicle_recovery.py /path/to/transcript.jsonl Session-2026-01-05-002
"""

import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime


# Message types to skip entirely
SKIP_TYPES = {
    'file-history-snapshot',
    'summary',
}


def extract_text_content(content) -> str:
    """Extract text from various content formats."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        return '\n'.join(text_parts).strip()
    return ""


def parse_message(msg: dict) -> str:
    """Convert a single message to Markdown format."""
    msg_type = msg.get('type', 'unknown')

    # Skip internal/metadata message types
    if msg_type in SKIP_TYPES:
        return ""

    # Handle human/user messages
    if msg_type in ('human', 'user'):
        content = ""

        message_obj = msg.get('message', {})
        if isinstance(message_obj, dict):
            content = extract_text_content(message_obj.get('content', ''))

        if not content:
            content = extract_text_content(msg.get('content', ''))

        if not content:
            content = extract_text_content(msg.get('text', ''))

        if not content:
            return ""

        return f"**User:**\n\n{content}\n"

    # Handle assistant messages
    elif msg_type == 'assistant':
        message_obj = msg.get('message', {})
        content = ""

        if isinstance(message_obj, dict):
            content = extract_text_content(message_obj.get('content', ''))

        if not content:
            content = extract_text_content(msg.get('content', ''))

        if not content:
            return ""

        return f"**Claude:**\n\n{content}\n"

    else:
        return ""


def main():
    if len(sys.argv) != 3:
        print("Usage: python emergency_chronicle_recovery.py <transcript_path> <session_name>")
        print("Example: python emergency_chronicle_recovery.py /path/to/transcript.jsonl Session-2026-01-05-002")
        sys.exit(1)

    transcript_path = sys.argv[1]
    session_name = sys.argv[2]

    if not os.path.exists(transcript_path):
        print(f"Error: Transcript not found at {transcript_path}", file=sys.stderr)
        sys.exit(1)

    # Validate session name format
    if not re.match(r'^Session-\d{4}-\d{2}-\d{2}-\d{3}$', session_name):
        print(f"Error: Session name must match format Session-YYYY-MM-DD-NNN", file=sys.stderr)
        sys.exit(1)

    # Extract date from session name
    date_str = session_name[8:18]  # Extract YYYY-MM-DD

    # Determine project directory (script is in .claude/hooks/)
    project_dir = str(Path(__file__).parent.parent.parent)
    sessions_dir = os.path.join(project_dir, '.claude', 'sessions')
    Path(sessions_dir).mkdir(parents=True, exist_ok=True)

    # Create session folder
    session_folder = os.path.join(sessions_dir, session_name)
    Path(session_folder).mkdir(parents=True, exist_ok=True)

    transcript_filename = f"{session_name}-Transcript.md"
    chronicle_path = os.path.join(session_folder, transcript_filename)

    # Check if chronicle already exists
    if os.path.exists(chronicle_path):
        print(f"Warning: Transcript already exists at {chronicle_path}", file=sys.stderr)
        print("Aborting to prevent overwrite. Delete manually if you want to regenerate.", file=sys.stderr)
        sys.exit(1)

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
        f"# Chronicle: {session_name}",
        f"",
        f"**Date:** {date_str}",
        f"**Stop Reason:** unexpected_termination (recovered)",
        f"**Transcribed by:** Emergency Chronicle Recovery (Manual)",
        f"",
        f"---",
        f"",
    ]

    for msg in messages:
        parsed = parse_message(msg)
        if parsed:
            markdown_parts.append(parsed)
            markdown_parts.append("---\n")

    # Remove trailing separator if present
    if markdown_parts and markdown_parts[-1] == "---\n":
        markdown_parts.pop()

    markdown_parts.append(f"\n*End of Chronicle - Recovered {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Write chronicle
    chronicle_content = '\n'.join(markdown_parts)
    with open(chronicle_path, 'w', encoding='utf-8') as f:
        f.write(chronicle_content)

    print(f"Chronicle saved: {chronicle_path}")

    # Update the index
    index_path = os.path.join(sessions_dir, 'INDEX.md')
    index_entry = f"- [{session_name}]({session_name}/{transcript_filename}) *(recovered)*\n"

    if os.path.exists(index_path):
        with open(index_path, 'a', encoding='utf-8') as f:
            f.write(index_entry)
    else:
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# Chronicle Index\n\n")
            f.write("All session chronicles, in chronological order.\n\n")
            f.write("**Naming Convention:** `Session-YYYY-MM-DD-NNN` where NNN is a zero-padded sequence number for that date.\n\n")
            f.write("---\n\n")
            f.write(index_entry)

    print(f"Index updated: {index_path}")


if __name__ == '__main__':
    main()
