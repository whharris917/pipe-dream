"""Inbox watcher — monitors agent inbox directories for changes.

Ported from docker/scripts/inbox-watcher.py. Uses watchdog for
cross-platform file system monitoring.
"""

import asyncio
import logging
from pathlib import Path
from typing import Callable, Awaitable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileDeletedEvent

from agent_hub.config import HubConfig

logger = logging.getLogger(__name__)

# Type for the callback: (agent_id, inbox_count, new_filename_or_none)
InboxChangeCallback = Callable[[str, int, str | None], Awaitable[None]]


class _InboxEventHandler(FileSystemEventHandler):
    """Watchdog handler that detects inbox file changes."""

    def __init__(
        self,
        agent_id: str,
        inbox_path: Path,
        loop: asyncio.AbstractEventLoop,
        callback: InboxChangeCallback,
    ):
        super().__init__()
        self.agent_id = agent_id
        self.inbox_path = inbox_path
        self.loop = loop
        self.callback = callback
        self._processed: set[str] = set()

    def on_created(self, event: FileCreatedEvent) -> None:
        if event.is_directory:
            return
        filepath = Path(event.src_path)
        key = str(filepath)
        if key in self._processed:
            return
        self._processed.add(key)

        count = self._count_tasks()
        asyncio.run_coroutine_threadsafe(
            self.callback(self.agent_id, count, filepath.name),
            self.loop,
        )

    def on_deleted(self, event: FileDeletedEvent) -> None:
        if event.is_directory:
            return
        filepath = Path(event.src_path)
        self._processed.discard(str(filepath))

        count = self._count_tasks()
        asyncio.run_coroutine_threadsafe(
            self.callback(self.agent_id, count, None),
            self.loop,
        )

    def _count_tasks(self) -> int:
        if not self.inbox_path.exists():
            return 0
        return len(list(self.inbox_path.glob("*.md")))


class InboxWatcher:
    """Watches all agent inbox directories and triggers callbacks on change."""

    def __init__(self, config: HubConfig, callback: InboxChangeCallback):
        self.config = config
        self.callback = callback
        self._observer: Observer | None = None

    async def start(self) -> None:
        """Start watching all inbox directories."""
        loop = asyncio.get_running_loop()
        self._observer = Observer()

        for agent_id in self.config.agents:
            inbox_path = self.config.inbox_path(agent_id)
            inbox_path.mkdir(parents=True, exist_ok=True)

            handler = _InboxEventHandler(
                agent_id=agent_id,
                inbox_path=inbox_path,
                loop=loop,
                callback=self.callback,
            )
            self._observer.schedule(handler, str(inbox_path), recursive=False)

            # Initial count
            count = handler._count_tasks()
            if count > 0:
                await self.callback(agent_id, count, None)

        self._observer.start()
        logger.info(
            "Inbox watcher started for %d agents", len(self.config.agents)
        )

    async def stop(self) -> None:
        """Stop watching."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
            logger.info("Inbox watcher stopped")

    def get_inbox_count(self, agent_id: str) -> int:
        """Get current inbox count for an agent."""
        inbox_path = self.config.inbox_path(agent_id)
        if not inbox_path.exists():
            return 0
        return len(list(inbox_path.glob("*.md")))
