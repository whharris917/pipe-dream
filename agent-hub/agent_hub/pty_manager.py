"""PTY Manager -- persistent terminal I/O sessions for agent containers.

Uses the Docker SDK's low-level exec API to attach to each agent's tmux
session with a TTY-allocated socket. Captures output into a ring buffer,
dispatches to registered callbacks, and accepts input writes.

The callback interface is designed for a future WebSocket endpoint:
    - register_callback(fn) to receive (agent_id, data) on output
    - get_buffer(agent_id) for scrollback on late-joining clients
    - write(agent_id, data) for keystroke injection
    - resize(agent_id, cols, rows) for terminal resize
"""

import asyncio
import logging
from typing import Callable, Awaitable

import docker

from agent_hub.config import HubConfig

logger = logging.getLogger(__name__)

# Callback signature: async def on_output(agent_id: str, data: bytes)
PTYOutputCallback = Callable[[str, bytes], Awaitable[None]]


class PTYSession:
    """Manages a single agent's PTY connection via Docker exec socket.

    The connection uses exec_create(tty=True) + exec_start(socket=True),
    which gives a bidirectional byte stream to a PTY inside the container.
    The read loop runs in a thread (socket is blocking) and dispatches
    output to an async callback.
    """

    def __init__(
        self,
        agent_id: str,
        container_name: str,
        docker_client: docker.DockerClient,
        buffer_size: int,
        on_output: PTYOutputCallback,
    ):
        self.agent_id = agent_id
        self.container_name = container_name
        self._client = docker_client
        self._buffer = bytearray()
        self._buffer_size = buffer_size
        self._on_output = on_output
        self._socket = None
        self._exec_id: str | None = None
        self._read_task: asyncio.Task | None = None
        self._active = False

    async def attach(self) -> None:
        """Attach to the agent's tmux session via Docker exec socket."""
        container = await asyncio.to_thread(
            self._client.containers.get, self.container_name
        )

        exec_result = await asyncio.to_thread(
            self._client.api.exec_create,
            container.id,
            cmd=["tmux", "attach", "-t", "agent"],
            stdin=True,
            tty=True,
            stdout=True,
            stderr=True,
        )
        self._exec_id = exec_result["Id"]

        self._socket = await asyncio.to_thread(
            self._client.api.exec_start,
            self._exec_id,
            tty=True,
            socket=True,
        )

        self._active = True
        self._read_task = asyncio.create_task(self._read_loop())
        logger.info("PTY attached for %s", self.agent_id)

    async def _read_loop(self) -> None:
        """Continuously read output from the PTY socket."""
        try:
            while self._active:
                try:
                    data = await asyncio.to_thread(self._recv, 4096)
                except Exception:
                    if not self._active:
                        break
                    raise

                if not data:
                    break

                # Append to ring buffer, trim if over limit
                self._buffer.extend(data)
                if len(self._buffer) > self._buffer_size:
                    del self._buffer[:len(self._buffer) - self._buffer_size]

                # Dispatch to callback
                try:
                    await self._on_output(self.agent_id, bytes(data))
                except Exception as e:
                    logger.warning(
                        "PTY output callback error for %s: %s",
                        self.agent_id, e,
                    )

        except Exception as e:
            if self._active:
                logger.warning(
                    "PTY read loop ended for %s: %s", self.agent_id, e
                )
        finally:
            self._active = False
            logger.info("PTY read loop stopped for %s", self.agent_id)

    def _recv(self, size: int) -> bytes:
        """Read from the exec socket (blocking, runs in thread)."""
        sock = self._socket
        if sock is None:
            return b""
        try:
            if hasattr(sock, "recv"):
                return sock.recv(size)
            if hasattr(sock, "read"):
                return sock.read(size)
            return b""
        except OSError:
            return b""

    def _send(self, data: bytes) -> None:
        """Write to the exec socket (blocking, runs in thread)."""
        sock = self._socket
        if sock is None:
            return
        try:
            if hasattr(sock, "send"):
                sock.send(data)
            elif hasattr(sock, "write"):
                sock.write(data)
        except OSError:
            pass

    async def write(self, data: bytes) -> None:
        """Write input to the PTY stdin."""
        if self._socket is None or not self._active:
            return
        await asyncio.to_thread(self._send, data)

    async def resize(self, cols: int, rows: int) -> None:
        """Resize the PTY dimensions."""
        if self._exec_id is None:
            return
        try:
            await asyncio.to_thread(
                self._client.api.exec_resize,
                self._exec_id,
                height=rows,
                width=cols,
            )
        except Exception as e:
            logger.warning(
                "PTY resize failed for %s: %s", self.agent_id, e
            )

    def get_buffer(self) -> bytes:
        """Return current scrollback buffer contents."""
        return bytes(self._buffer)

    async def detach(self) -> None:
        """Detach from the PTY session."""
        self._active = False

        # Close socket to unblock any pending recv
        if self._socket is not None:
            try:
                if hasattr(self._socket, "close"):
                    self._socket.close()
            except Exception:
                pass
            self._socket = None

        # Cancel and await the read task
        if self._read_task is not None:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
            self._read_task = None

        logger.info("PTY detached for %s", self.agent_id)


class PTYManager:
    """Manages PTY sessions for all agents.

    Provides the interface that a future WebSocket endpoint will consume:
        - register_callback / unregister_callback for output streaming
        - get_buffer for scrollback on connect
        - write for keystroke input
        - resize for terminal dimensions
    """

    def __init__(self, config: HubConfig, docker_client: docker.DockerClient):
        self._config = config
        self._client = docker_client
        self._sessions: dict[str, PTYSession] = {}
        self._callbacks: list[PTYOutputCallback] = []

    async def attach(self, agent_id: str) -> None:
        """Attach to an agent's terminal session."""
        if agent_id in self._sessions:
            logger.warning("PTY already attached for %s", agent_id)
            return

        container_name = f"{self._config.container_prefix}{agent_id}"
        session = PTYSession(
            agent_id=agent_id,
            container_name=container_name,
            docker_client=self._client,
            buffer_size=self._config.pty_buffer_size,
            on_output=self._dispatch_output,
        )

        try:
            await session.attach()
            self._sessions[agent_id] = session
        except Exception as e:
            logger.error("Failed to attach PTY for %s: %s", agent_id, e)
            raise

    async def detach(self, agent_id: str) -> None:
        """Detach from an agent's terminal session."""
        session = self._sessions.pop(agent_id, None)
        if session is not None:
            await session.detach()

    async def write(self, agent_id: str, data: bytes) -> None:
        """Write input to an agent's PTY."""
        session = self._sessions.get(agent_id)
        if session is not None:
            await session.write(data)

    async def resize(self, agent_id: str, cols: int, rows: int) -> None:
        """Resize an agent's PTY."""
        session = self._sessions.get(agent_id)
        if session is not None:
            await session.resize(cols, rows)

    def get_buffer(self, agent_id: str) -> bytes:
        """Get an agent's scrollback buffer."""
        session = self._sessions.get(agent_id)
        if session is not None:
            return session.get_buffer()
        return b""

    def is_attached(self, agent_id: str) -> bool:
        """Check if a PTY session is attached for an agent."""
        return agent_id in self._sessions

    def register_callback(self, callback: PTYOutputCallback) -> None:
        """Register a callback for PTY output across all agents."""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: PTYOutputCallback) -> None:
        """Unregister a PTY output callback."""
        try:
            self._callbacks.remove(callback)
        except ValueError:
            pass

    async def detach_all(self) -> None:
        """Detach all PTY sessions."""
        for agent_id in list(self._sessions.keys()):
            await self.detach(agent_id)

    async def _dispatch_output(self, agent_id: str, data: bytes) -> None:
        """Fan out PTY output to all registered callbacks."""
        for callback in self._callbacks:
            try:
                await callback(agent_id, data)
            except Exception as e:
                logger.warning("PTY callback error for %s: %s", agent_id, e)
