#!/usr/bin/env python3
"""
inbox-watcher.py - Monitor agent inboxes and display notifications

Usage: python inbox-watcher.py [agent1] [agent2] ...

When a new file appears in an agent's inbox directory, this script:
1. Detects the file type (task-, msg-, notif-)
2. Generates an appropriate notification message
3. Displays the notification in this terminal

Platform behavior:
- Windows: Run in a separate terminal window. Notifications appear here;
  the user watches this window and switches to the appropriate agent terminal.
- Linux (tmux): Future enhancement could use tmux send-keys to inject
  notifications directly into agent panes.

The notification prompts the user to switch to the agent's terminal and
run 'qms inbox' to process the new item.

Requires: watchdog library (pip install watchdog)
"""

import os
import sys
import time
import subprocess
import re
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
except ImportError:
    print("Error: watchdog library not installed")
    print("Install with: pip install watchdog")
    sys.exit(1)


# Find project root (parent of docker/scripts/)
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent


class InboxEventHandler(FileSystemEventHandler):
    """Handle filesystem events for inbox directories."""

    def __init__(self, agents: list[str]):
        super().__init__()
        self.agents = agents
        self.processed_files = set()  # Avoid duplicate notifications

    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Avoid processing the same file twice (watchdog can fire multiple events)
        if str(filepath) in self.processed_files:
            return
        self.processed_files.add(str(filepath))

        # Extract agent from path: .claude/users/{agent}/inbox/
        try:
            parts = filepath.parts
            users_idx = parts.index('users')
            agent = parts[users_idx + 1]
        except (ValueError, IndexError):
            return

        # Only process for agents we're watching
        if agent not in self.agents:
            return

        # Check if the agent's container is running
        container_name = f"agent-{agent}"
        if not self._container_running(container_name):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Container {container_name} not running, skipping notification")
            return

        # Generate and send notification
        filename = filepath.name
        notification = self._generate_notification(agent, filename, filepath)
        self._send_notification(container_name, notification)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] {agent}: {filename}")

    def _container_running(self, container_name: str) -> bool:
        """Check if a Docker container is running."""
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "true"
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _generate_notification(self, agent: str, filename: str, filepath: Path) -> str:
        """Generate a notification message based on file type.

        Uses ASCII box characters for Windows console compatibility.
        """

        agent_upper = agent.upper()

        # Determine type by prefix
        if filename.startswith("task-"):
            # Extract doc_id from filename: task-CR-056-pre_review-v0-1.md
            match = re.search(r'task-([A-Z]+-\d+)', filename)
            doc_id = match.group(1) if match else "document"

            # Determine task type
            if "review" in filename.lower():
                action = "Review"
            elif "approval" in filename.lower():
                action = "Approve"
            else:
                action = "Process"

            return f'''
+---------------------------------------------------+
|  [TASK] [{agent_upper}] New task: {action} {doc_id:<14}    |
|  Switch to {agent}'s terminal and run: qms inbox  |
+---------------------------------------------------+
'''

        elif filename.startswith("msg-"):
            # Extract sender from filename: msg-claude-2026-02-04-143022.md
            match = re.search(r'msg-([a-z_]+)-', filename)
            sender = match.group(1) if match else "unknown"

            # Try to extract subject from file
            subject = "New message"
            try:
                content = filepath.read_text(encoding='utf-8')
                subject_match = re.search(r'subject:\s*["\']?([^"\'\n]+)', content, re.IGNORECASE)
                if subject_match:
                    subject = subject_match.group(1)[:25]
            except Exception:
                pass

            return f'''
+---------------------------------------------------+
|  [MSG] [{agent_upper}] Message from {sender:<18}  |
|  Subject: {subject:<36}  |
|  Switch to {agent}'s terminal and run: qms inbox  |
+---------------------------------------------------+
'''

        elif filename.startswith("notif-"):
            # Extract doc_id and event from filename
            match = re.search(r'([A-Z]+-\d+)', filename)
            doc_id = match.group(1) if match else "document"

            # Try to extract event from file
            event = "update"
            try:
                content = filepath.read_text(encoding='utf-8')
                event_match = re.search(r'event:\s*([A-Z_]+)', content)
                if event_match:
                    event = event_match.group(1).lower().replace('_', ' ')
            except Exception:
                pass

            return f'''
+---------------------------------------------------+
|  [NOTIF] [{agent_upper}] {doc_id}: {event:<22}    |
|  Switch to {agent}'s terminal and run: qms inbox  |
+---------------------------------------------------+
'''

        else:
            # Generic notification
            return f'''
+---------------------------------------------------+
|  [INBOX] [{agent_upper}] New inbox item           |
|  Switch to {agent}'s terminal and run: qms inbox  |
+---------------------------------------------------+
'''

    def _send_notification(self, container_name: str, notification: str):
        """Display notification for the agent.

        On Windows with separate terminal windows, we can't easily inject text
        into another window. Instead, we print to this console - the user watches
        this console and switches to the appropriate agent terminal.

        Future enhancement: On Linux with tmux, could use tmux send-keys.
        """
        # Print to our own stdout - user watches this console
        print(notification, flush=True)


def main():
    # Parse command line arguments for agent list
    if len(sys.argv) > 1:
        agents = sys.argv[1:]
    else:
        agents = ["claude", "qa"]

    # Validate agents
    valid_agents = {"claude", "qa", "tu_ui", "tu_scene", "tu_sketch", "tu_sim", "bu"}
    for agent in agents:
        if agent not in valid_agents:
            print(f"Error: Invalid agent '{agent}'")
            print(f"Valid agents: {', '.join(sorted(valid_agents))}")
            sys.exit(1)

    # Build list of inbox directories to watch
    inbox_dirs = []
    for agent in agents:
        inbox_dir = PROJECT_ROOT / ".claude" / "users" / agent / "inbox"
        if inbox_dir.exists():
            inbox_dirs.append(str(inbox_dir))
        else:
            print(f"Warning: Inbox directory not found for {agent}: {inbox_dir}")

    if not inbox_dirs:
        print("Error: No valid inbox directories found")
        sys.exit(1)

    print(f"Inbox Watcher started")
    print(f"  Watching agents: {', '.join(agents)}")
    print(f"  Inbox directories:")
    for d in inbox_dirs:
        print(f"    - {d}")
    print()

    # Set up the file system observer
    event_handler = InboxEventHandler(agents)
    observer = Observer()

    for inbox_dir in inbox_dirs:
        observer.schedule(event_handler, inbox_dir, recursive=False)

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping inbox watcher...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
