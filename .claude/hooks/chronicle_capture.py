#!/usr/bin/env python3
"""
Chronicle Capture Hook

This script runs at SessionEnd to capture the session transcript
and append it to the Chronicle in human-readable Markdown format.

Invoked automatically by Claude Code via the SessionEnd hook.

Session Naming Convention: Session-YYYY-MM-DD-NNN
Where NNN is a zero-padded sequence number for that date.
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


def get_next_session_number(chronicles_dir: str, date_str: str) -> int:
    """
    Find the next available session number for the given date.
    Scans existing Session-YYYY-MM-DD-NNN.md files and returns the next number.
    """
    pattern = re.compile(rf'^Session-{re.escape(date_str)}-(\d{{3}})\.md$')
    max_num = 0

    if os.path.exists(chronicles_dir):
        for filename in os.listdir(chronicles_dir):
            match = pattern.match(filename)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num

    return max_num + 1


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
        # Try to extract the actual text content
        # The message structure can vary - check multiple paths
        content = ""

        # Path 1: message.content (standard format)
        message_obj = msg.get('message', {})
        if isinstance(message_obj, dict):
            content = extract_text_content(message_obj.get('content', ''))

        # Path 2: Direct content field
        if not content:
            content = extract_text_content(msg.get('content', ''))

        # Path 3: Text field directly
        if not content:
            content = extract_text_content(msg.get('text', ''))

        # Skip if no actual content found
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

        # Skip empty assistant messages (tool-only responses)
        if not content:
            return ""

        return f"**Claude:**\n\n{content}\n"

    # Skip unknown internal types silently
    else:
        return ""


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

    # Generate chronicle filename using Session-YYYY-MM-DD-NNN format
    date_str = datetime.now().strftime('%Y-%m-%d')
    session_num = get_next_session_number(chronicles_dir, date_str)
    session_name = f"Session-{date_str}-{session_num:03d}"
    chronicle_filename = f"{session_name}.md"
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
        f"# Chronicle: {session_name}",
        f"",
        f"**Date:** {date_str}",
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

    # Remove trailing separator if present
    if markdown_parts and markdown_parts[-1] == "---\n":
        markdown_parts.pop()

    markdown_parts.append(f"\n*End of Chronicle - {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")

    # Write chronicle
    chronicle_content = '\n'.join(markdown_parts)
    with open(chronicle_path, 'w', encoding='utf-8') as f:
        f.write(chronicle_content)

    print(f"Chronicle saved: {chronicle_path}", file=sys.stderr)

    # Update the index - append new entry
    index_path = os.path.join(chronicles_dir, 'INDEX.md')
    index_entry = f"- [{session_name}]({chronicle_filename})\n"

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

    print(f"Index updated: {index_path}", file=sys.stderr)
    sys.exit(0)


if __name__ == '__main__':
    main()
