"""PTY Manager -- persistent terminal I/O sessions for agent containers.

Uses the Docker SDK's low-level exec API to attach to each agent's tmux
session in **control mode** (`tmux -CC`).  Control mode emits a line-based
protocol where `%output` notifications carry the raw PTY bytes from the
program running inside tmux -- bypassing tmux's viewport rendering entirely.
This allows xterm.js on the GUI side to handle scrollback naturally.

Protocol overview (tmux control mode):
    - Initial handshake: DCS 1000p, %begin/%end, %session-changed
    - Pane output:  %output %PANE_ID OCTAL_ESCAPED_DATA
    - Command responses: %begin TIMESTAMP FLAGS ... %end TIMESTAMP FLAGS
    - Input:  send-keys -t PANE -H XX XX ...
    - Resize: refresh-client -C WxH
    - Lines terminated with \\r\\n (CRLF)

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


def _decode_octal(payload: str) -> bytes:
    """Decode tmux control mode octal-escaped output to raw bytes.

    tmux escapes bytes < 32 (control chars) and backslash itself using
    three-digit octal sequences: \\033 = ESC, \\015 = CR, \\012 = LF,
    \\134 = backslash, etc.  Printable ASCII (32-126 except backslash)
    passes through literally.  Non-ASCII characters (e.g. box-drawing
    glyphs from TUI applications) may also pass through unescaped and
    are re-encoded to UTF-8 bytes.
    """
    result = bytearray()
    i = 0
    n = len(payload)
    while i < n:
        ch = payload[i]
        if ch == '\\' and i + 3 < n:
            octal = payload[i + 1:i + 4]
            try:
                result.append(int(octal, 8))
                i += 4
                continue
            except ValueError:
                pass
        result.extend(ch.encode('utf-8'))
        i += 1
    return bytes(result)


def _decode_control_output(line: str) -> bytes | None:
    """Parse a tmux control mode line and return decoded bytes if %output.

    Returns decoded raw bytes for %output lines, or None for all other
    control mode messages (%begin, %end, %session-changed, etc.).

    Format: %output %PANE_ID PAYLOAD
    """
    if not line.startswith('%output '):
        return None
    # Skip '%output ', then skip pane ID (e.g., '%0 ')
    rest = line[8:]  # after '%output '
    space = rest.find(' ')
    if space < 0:
        return b""
    payload = rest[space + 1:]
    return _decode_octal(payload)


def _encode_send_keys(data: bytes) -> bytes:
    """Encode input bytes as a tmux send-keys -H command.

    Converts each byte to a two-digit hex string, producing:
        send-keys -t agent -H 68 65 6C 6C 6F\\n
    for input b"hello".
    """
    hex_parts = ' '.join(f'{b:02x}' for b in data)
    return f'send-keys -t agent -H {hex_parts}\n'.encode()


class PTYSession:
    """Manages a single agent's PTY connection via Docker exec socket.

    Uses tmux control mode (-CC) which provides a line-based protocol
    instead of rendered terminal output.  The read loop parses %output
    notifications and decodes octal-escaped payloads back to raw bytes.

    After attaching, sends ``capture-pane -p -e -t %0`` to retrieve the
    current pane content (control mode only delivers NEW output, not what
    was already on screen).  The capture response arrives as a
    %begin/%end block which the read loop collects and dispatches.
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
        self._read_task: asyncio.Task | None = None
        self._active = False

    async def attach(self) -> None:
        """Attach to the agent's tmux session in control mode."""
        container = await asyncio.to_thread(
            self._client.containers.get, self.container_name
        )

        # stty raw -echo: prevent the intermediary shell from echoing the
        # tmux command or interpreting control characters.
        # exec tmux -CC: replace the shell with tmux in control mode.
        exec_result = await asyncio.to_thread(
            self._client.api.exec_create,
            container.id,
            cmd=["sh", "-c", "stty raw -echo && exec tmux -CC attach -t agent"],
            stdin=True,
            tty=True,
            stdout=True,
            stderr=True,
        )

        self._socket = await asyncio.to_thread(
            self._client.api.exec_start,
            exec_result["Id"],
            tty=True,
            socket=True,
        )

        self._active = True
        self._read_task = asyncio.create_task(self._read_loop())
        logger.info("PTY attached (control mode) for %s", self.agent_id)

        # Request initial pane content — control mode only delivers output
        # produced AFTER attaching, so we capture what's already on screen.
        # Short delay to let the handshake complete first.
        await asyncio.sleep(0.2)
        await asyncio.to_thread(
            self._send,
            b'capture-pane -p -e -t %0\n',
        )
        logger.info("PTY capture-pane requested for %s", self.agent_id)

    async def _read_loop(self) -> None:
        """Read control mode output, parse protocol lines, dispatch bytes.

        Handles two types of content:
        - ``%output`` lines: ongoing pane output (octal-decoded, dispatched)
        - ``%begin``/``%end`` blocks: responses to commands we send
          (e.g. capture-pane content, dispatched as raw text)
        """
        line_buf = b""
        # State for collecting %begin/%end command response blocks
        in_block = False
        block_lines: list[str] = []

        try:
            while self._active:
                try:
                    chunk = await asyncio.to_thread(self._recv, 4096)
                except Exception:
                    if not self._active:
                        break
                    raise

                if not chunk:
                    logger.warning("PTY socket EOF for %s", self.agent_id)
                    break

                line_buf += chunk
                # Process all complete lines
                while b'\n' in line_buf:
                    line_bytes, line_buf = line_buf.split(b'\n', 1)
                    # Strip \r from CRLF line endings
                    line = line_bytes.decode('utf-8', errors='replace').rstrip('\r')

                    # --- %begin/%end block collection ---
                    if line.startswith('%begin '):
                        in_block = True
                        block_lines = []
                        continue
                    if line.startswith('%end ') and in_block:
                        in_block = False
                        if block_lines:
                            # Command response (e.g. capture-pane output).
                            # Join lines with \r\n and dispatch as terminal content.
                            text = '\r\n'.join(block_lines) + '\r\n'
                            data = text.encode('utf-8')
                            logger.info(
                                "PTY block [%s] %d lines, %d bytes",
                                self.agent_id, len(block_lines), len(data),
                            )
                            self._buffer.extend(data)
                            if len(self._buffer) > self._buffer_size:
                                del self._buffer[:len(self._buffer) - self._buffer_size]
                            try:
                                await self._on_output(self.agent_id, data)
                            except Exception as e:
                                logger.warning(
                                    "PTY output callback error for %s: %s",
                                    self.agent_id, e,
                                )
                        block_lines = []
                        continue
                    if line.startswith('%error ') and in_block:
                        logger.warning(
                            "tmux command error [%s]: %s",
                            self.agent_id, line,
                        )
                        in_block = False
                        block_lines = []
                        continue
                    if in_block:
                        block_lines.append(line)
                        continue

                    # --- %output: ongoing pane output ---
                    decoded = _decode_control_output(line)
                    if decoded is not None and len(decoded) > 0:
                        # Append to ring buffer, trim if over limit
                        self._buffer.extend(decoded)
                        if len(self._buffer) > self._buffer_size:
                            del self._buffer[:len(self._buffer) - self._buffer_size]

                        # Dispatch to callback
                        try:
                            await self._on_output(self.agent_id, decoded)
                        except Exception as e:
                            logger.warning(
                                "PTY output callback error for %s: %s",
                                self.agent_id, e,
                            )
                    elif decoded is None and line:
                        # Non-%output control message — log for debugging
                        # Strip DCS prefix from initial handshake for readability
                        display = line.lstrip('\x1b').lstrip('P1000p')
                        logger.debug(
                            "tmux control [%s]: %s",
                            self.agent_id, display[:120],
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
        """Send input to the tmux pane via send-keys -H."""
        if self._socket is None or not self._active:
            return
        cmd = _encode_send_keys(data)
        await asyncio.to_thread(self._send, cmd)

    async def resize(self, cols: int, rows: int) -> None:
        """Resize the tmux client via refresh-client -C."""
        if self._socket is None or not self._active:
            return
        cmd = f'refresh-client -C {cols}x{rows}\n'.encode()
        await asyncio.to_thread(self._send, cmd)

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
