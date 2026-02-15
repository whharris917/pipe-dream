import { useEffect, useRef, useCallback } from "react";
import { HUB_WS_URL, RECONNECT_BASE_MS, RECONNECT_MAX_MS } from "../constants";
import { useAgentStore } from "./useAgentStore";
import type { Terminal } from "@xterm/xterm";
import type { ServerMessage, ClientMessage } from "../types";

/**
 * Decodes a base64 string to a Uint8Array.
 * Used for PTY output — xterm.js handles ANSI from raw bytes.
 */
function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Strip or convert escape sequences that interfere with the monitoring GUI.
 *
 * With tmux control mode, we receive Claude Code's raw PTY output
 * (not tmux's re-rendered viewport), so most workarounds are no longer
 * needed.  We still handle:
 *
 * 1. Mouse tracking modes (1000, 1002, 1003, 1005, 1006, 1015):
 *    Claude Code enables mouse tracking, which causes xterm.js to forward
 *    wheel events to the application instead of scrolling the buffer.
 *
 * 2. Alternate screen modes (47, 1047, 1049):
 *    Defensive — alt screen has zero scrollback in xterm.js.
 *
 * 3. Clear scrollback (ESC[3J) → converted to erase screen (ESC[2J):
 *    Claude Code sends ESC[3J before every full re-render (startup, resize).
 *    ESC[3J destroys scrollback; ESC[2J erases only the visible screen,
 *    so the re-render draws fresh content without duplication while
 *    preserving scrollback history.
 *
 * 4. Full reset (ESC c): stripped entirely.
 */
const STRIP_MODES_RE =
  /\x1b\[\?(?:\d+;)*(1000|1002|1003|1005|1006|1015|47|1047|1049)(?:;\d+)*[hl]/g;

function stripTerminalModes(data: Uint8Array): Uint8Array {
  const str = new TextDecoder().decode(data);
  const filtered = str
    .replace(STRIP_MODES_RE, "")
    .replace(/\x1b\[3J/g, "\x1b[2J")
    .replace(/\x1bc/g, "");
  if (filtered === str) return data;
  return new TextEncoder().encode(filtered);
}

/**
 * Singleton WebSocket connection manager.
 * Lives outside React lifecycle — Zustand store dispatches are called directly.
 */
class HubConnection {
  private ws: WebSocket | null = null;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = RECONNECT_BASE_MS;
  private terminals = new Map<string, Terminal>();
  private muteInput = new Set<string>();
  private intentionalClose = false;
  /** Agents awaiting a re-render after resize — first output clears the screen */
  private pendingRerender = new Set<string>();
  /** Fallback timers to restore ring buffer if resize doesn't trigger a re-render */
  private rerenderFallback = new Map<string, ReturnType<typeof setTimeout>>();

  connect() {
    this.intentionalClose = false;
    useAgentStore.getState().setConnectionStatus("connecting");

    try {
      this.ws = new WebSocket(HUB_WS_URL);
    } catch {
      useAgentStore.getState().setConnectionStatus("error");
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      useAgentStore.getState().setConnectionStatus("connected");
      this.reconnectDelay = RECONNECT_BASE_MS;
      // Re-subscribe to all open tabs after reconnect
      const { openTabs } = useAgentStore.getState();
      for (const agentId of openTabs) {
        this.send({ type: "subscribe", agent_id: agentId });
      }
    };

    this.ws.onclose = () => {
      if (!this.intentionalClose) {
        useAgentStore.getState().setConnectionStatus("disconnected");
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = () => {
      useAgentStore.getState().setConnectionStatus("error");
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const msg = JSON.parse(event.data as string) as ServerMessage;
        this.dispatch(msg);
      } catch {
        // Ignore malformed messages
      }
    };
  }

  disconnect() {
    this.intentionalClose = true;
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    useAgentStore.getState().setConnectionStatus("disconnected");
  }

  private scheduleReconnect() {
    if (this.reconnectTimer !== null) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, RECONNECT_MAX_MS);
      this.connect();
    }, this.reconnectDelay);
  }

  private dispatch(msg: ServerMessage) {
    const store = useAgentStore.getState();

    switch (msg.type) {
      case "subscribed": {
        const term = this.terminals.get(msg.agent_id);
        const bufferData = msg.buffer
          ? stripTerminalModes(base64ToBytes(msg.buffer))
          : null;

        if (term) {
          // Clear visible screen before resize.  The resize triggers a
          // fresh re-render from Claude Code at the correct dimensions.
          // Without this, the ring buffer content (at container dimensions)
          // persists and the re-render appends below it — duplication.
          term.write("\x1b[2J\x1b[H");
          this.sendResizeInternal(msg.agent_id, term.cols, term.rows);

          // Fallback: if no output arrives within 1.5s (resize didn't
          // trigger a re-render because dimensions already matched),
          // display the ring buffer so the screen isn't blank.
          if (bufferData) {
            const agentId = msg.agent_id;
            const existing = this.rerenderFallback.get(agentId);
            if (existing) clearTimeout(existing);
            this.rerenderFallback.set(
              agentId,
              setTimeout(() => {
                this.rerenderFallback.delete(agentId);
                this.pendingRerender.delete(agentId);
                const t = this.terminals.get(agentId);
                if (t) {
                  this.muteInput.add(agentId);
                  t.write(bufferData, () => this.muteInput.delete(agentId));
                }
              }, 1500),
            );
          }
        }
        break;
      }
      case "output": {
        const term = this.terminals.get(msg.agent_id);
        if (term) {
          // Cancel ring buffer fallback — real output arrived
          const fb = this.rerenderFallback.get(msg.agent_id);
          if (fb) {
            clearTimeout(fb);
            this.rerenderFallback.delete(msg.agent_id);
          }
          // First output after a resize — clear the entire terminal
          // (viewport + scrollback) so the re-render replaces all stale
          // content.  Claude Code's re-render includes the full conversation
          // at the correct width, so no content is lost.
          if (this.pendingRerender.has(msg.agent_id)) {
            term.clear();
            this.pendingRerender.delete(msg.agent_id);
          }
          term.write(stripTerminalModes(base64ToBytes(msg.data)));
        }
        break;
      }
      case "agent_state_changed":
        store.updateAgentState(msg.agent_id, msg.state, msg.agent);
        break;
      case "inbox_changed":
        store.updateInboxCount(msg.agent_id, msg.count);
        break;
      case "error":
        console.warn("[Hub WS] Error:", msg.message);
        break;
      case "unsubscribed":
        // No action needed — terminal cleanup handled by tab close
        break;
    }
  }

  send(msg: ClientMessage) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    }
  }

  subscribe(agentId: string) {
    this.send({ type: "subscribe", agent_id: agentId });
  }

  unsubscribe(agentId: string) {
    this.send({ type: "unsubscribe", agent_id: agentId });
  }

  sendInput(agentId: string, data: string) {
    if (this.muteInput.has(agentId)) return;
    this.send({ type: "input", agent_id: agentId, data });
  }

  sendResize(agentId: string, cols: number, rows: number) {
    this.sendResizeInternal(agentId, cols, rows);
  }

  private sendResizeInternal(agentId: string, cols: number, rows: number) {
    // Track that a re-render is expected — the output handler will clear
    // the screen before writing the first chunk after resize.
    this.pendingRerender.add(agentId);
    this.send({ type: "resize", agent_id: agentId, cols, rows });
    // Auto-expire if no re-render arrives (dimensions didn't change)
    setTimeout(() => this.pendingRerender.delete(agentId), 2000);
  }

  /** Register a terminal instance for receiving output */
  registerTerminal(agentId: string, terminal: Terminal) {
    this.terminals.set(agentId, terminal);
  }

  /** Unregister a terminal instance */
  unregisterTerminal(agentId: string) {
    this.terminals.delete(agentId);
  }
}

/** Singleton instance */
export const hubConnection = new HubConnection();

/**
 * React hook that manages the WebSocket connection lifecycle.
 * Call once in the root App component.
 */
export function useHubConnection() {
  const connectionRef = useRef(false);

  useEffect(() => {
    if (!connectionRef.current) {
      connectionRef.current = true;
      hubConnection.connect();
    }
    return () => {
      hubConnection.disconnect();
      connectionRef.current = false;
    };
  }, []);

  const subscribe = useCallback((agentId: string) => {
    hubConnection.subscribe(agentId);
  }, []);

  const unsubscribe = useCallback((agentId: string) => {
    hubConnection.unsubscribe(agentId);
  }, []);

  const sendInput = useCallback((agentId: string, data: string) => {
    hubConnection.sendInput(agentId, data);
  }, []);

  const sendResize = useCallback((agentId: string, cols: number, rows: number) => {
    hubConnection.sendResize(agentId, cols, rows);
  }, []);

  return { subscribe, unsubscribe, sendInput, sendResize };
}
