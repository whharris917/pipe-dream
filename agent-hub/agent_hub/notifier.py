"""Notification injection into agent tmux sessions.

Ported from docker/scripts/inbox-watcher.py. Uses docker exec + tmux
send-keys to inject text into a running agent's terminal. Claude Code's
pending message queue captures the injection as a pending message.
"""

import asyncio
import logging
import re
import subprocess

logger = logging.getLogger(__name__)


def build_notification_text(agent_id: str, filename: str) -> str:
    """Build a concise instruction for tmux injection.

    The message starts with "Task notification:" — the leading "T" is not
    a valid Claude Code permission dialog response (y/n/a/i), mitigating
    the edge case where send-keys arrives during a permission prompt.
    """
    if filename.startswith("task-"):
        match = re.search(r"task-([A-Z]+-\d+)", filename)
        doc_id = match.group(1) if match else "unknown"

        if "review" in filename.lower():
            action = "review"
        elif "approval" in filename.lower():
            action = "approval"
        else:
            action = "task"

        return (
            f"Task notification: {doc_id} {action} is in your inbox. "
            f"Please run qms_inbox() to see your pending tasks."
        )

    elif filename.startswith("msg-"):
        match = re.search(r"msg-([a-z_]+)-", filename)
        sender = match.group(1) if match else "unknown"
        return (
            f"Task notification: New message from {sender} in your inbox. "
            f"Please run qms_inbox() to see your pending tasks."
        )

    elif filename.startswith("notif-"):
        match = re.search(r"([A-Z]+-\d+)", filename)
        doc_id = match.group(1) if match else "unknown"
        return (
            f"Task notification: Update on {doc_id} in your inbox. "
            f"Please run qms_inbox() to see your pending tasks."
        )

    return (
        "Task notification: New item in your inbox. "
        "Please run qms_inbox() to see your pending tasks."
    )


async def inject_notification(container_name: str, text: str) -> bool:
    """Inject notification text into an agent's tmux session.

    Uses two subprocess calls:
    1. tmux send-keys -t agent -l "text" — sends text literally
    2. tmux send-keys -t agent Enter — submits the text

    Returns True if injection succeeded.
    """
    try:
        # Send the notification text literally
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name,
            "tmux", "send-keys", "-t", "agent", "-l", text,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.wait(), timeout=10)

        # Send Enter to submit
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name,
            "tmux", "send-keys", "-t", "agent", "Enter",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.wait(), timeout=10)

        logger.info("Notification injected into %s", container_name)
        return True

    except asyncio.TimeoutError:
        logger.warning("tmux send-keys timed out for %s", container_name)
        return False
    except Exception as e:
        logger.warning("tmux injection failed for %s: %s", container_name, e)
        return False
